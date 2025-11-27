from datetime import datetime, timedelta
from functools import lru_cache
import time

import pandas as pd
from dash import html, dcc, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine
from apps.analytical_app.components import filters as common_filters


type_page = "appointment_analysis"
TABLE_LIST_ID = f"result-table-{type_page}"
TABLE_ANALYSIS_ID = f"result-table-analysis-{type_page}"
DATE_RANGE_ID = f"date-picker-range-{type_page}"
SCHEDULE_FILTER_ID = f"dropdown-schedule-{type_page}"
SOURCE_FILTER_ID = f"dropdown-source-{type_page}"
DEPARTMENT_FILTER_ID = f"dropdown-department-{type_page}"
APPLY_BUTTON_ID = f"apply-button-{type_page}"
RESET_BUTTON_ID = f"reset-button-{type_page}"
STATUS_TEXT_ID = f"query-status-{type_page}"


def _default_dates():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    return start_date, end_date


def _format_status(duration: float, record_count: int) -> str:
    if duration < 1:
        time_text = f"{duration * 1000:.0f}мс"
    else:
        time_text = f"{duration:.1f}с"
    return f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"


@lru_cache(maxsize=1)
def _get_filter_options(column: str) -> list:
    query = text(f"""
        SELECT DISTINCT {column}
        FROM load_data_journal_appeals
        WHERE COALESCE(NULLIF({column}, '-'), '') <> ''
        ORDER BY {column}
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()
    return [{'label': row[0], 'value': row[0]} for row in rows if row and row[0]]


def _fetch_appointments(
    date_from: datetime,
    date_to: datetime,
    schedule_types: list,
    record_sources: list,
    departments: list
) -> pd.DataFrame:
    conditions = ["acceptance_ts BETWEEN :date_from AND :date_to"]
    params = {"date_from": date_from, "date_to": date_to}

    if schedule_types:
        conditions.append("schedule_type = ANY(:schedule_types)")
        params["schedule_types"] = schedule_types
    if record_sources:
        conditions.append("record_source = ANY(:record_sources)")
        params["record_sources"] = record_sources
    if departments:
        conditions.append("department = ANY(:departments)")
        params["departments"] = departments

    query = text(f"""
        WITH data AS (
            SELECT *,
                   CASE
                       WHEN acceptance_date ~ '^\\d{{2}}\\.\\d{{2}}\\.\\d{{4}} \\d{{2}}:\\d{{2}}$' THEN
                           to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI')
                       WHEN acceptance_date ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{1,2}}:\\d{{2}}(:\\d{{2}})?$' THEN
                           to_timestamp(
                               regexp_replace(
                                   replace(
                                       regexp_replace(acceptance_date, 'T(\\d):', 'T0\\1:', 1, 0, 'g'),
                                       'T',
                                       ' '
                                   ),
                                   '(\\d{{2}}:\\d{{2}})(?!:)',
                                   '\\1:00',
                                   1,
                                   0,
                                   'g'
                               ),
                               'YYYY-MM-DD HH24:MI:SS'
                           )
                       ELSE NULL
                   END AS acceptance_ts
            FROM load_data_journal_appeals
        )
        SELECT *
        FROM data
        WHERE acceptance_ts IS NOT NULL
          AND {' AND '.join(conditions)}
        ORDER BY acceptance_ts DESC
    """)

    return pd.read_sql_query(query, engine, params=params, parse_dates=['acceptance_ts'])


schedule_options = _get_filter_options("schedule_type")
source_options = _get_filter_options("record_source")
department_options = _get_filter_options("department")
default_start, default_end = _default_dates()


appointment_analysis_page = html.Div(
    [
        dbc.Card(
            dbc.CardBody([
                html.H4("Фильтры", className="mb-3"),
                dbc.Row([
                    dbc.Col(common_filters.date_picker(type_page), md=4, xs=12, className="mb-3"),
                    dbc.Col([
                        html.Label("Тип расписания", className="fw-bold"),
                        dcc.Dropdown(
                            id=SCHEDULE_FILTER_ID,
                            options=schedule_options,
                            multi=True,
                            placeholder="Все типы",
                            clearable=True
                        )
                    ], md=4, xs=12, className="mb-3"),
                    dbc.Col([
                        html.Label("Источник записи", className="fw-bold"),
                        dcc.Dropdown(
                            id=SOURCE_FILTER_ID,
                            options=source_options,
                            multi=True,
                            placeholder="Все источники",
                            clearable=True
                        )
                    ], md=4, xs=12, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Label("Подразделение", className="fw-bold"),
                        dcc.Dropdown(
                            id=DEPARTMENT_FILTER_ID,
                            options=department_options,
                            multi=True,
                            placeholder="Все подразделения",
                            clearable=True
                        )
                    ], md=8, xs=12, className="mb-3"),
                    dbc.Col(
                        dbc.ButtonGroup([
                            dbc.Button("Применить", id=APPLY_BUTTON_ID, color="primary"),
                            dbc.Button("Сбросить", id=RESET_BUTTON_ID, color="secondary", className="ms-2"),
                        ], className="mt-4"),
                        md=4, xs=12, className="mb-3 d-flex justify-content-end"
                    )
                ])
            ]),
            className="mb-4"
        ),
        html.Div(id=STATUS_TEXT_ID, className="text-muted mt-3"),
        dcc.Tabs([
            dcc.Tab(
                label="Список записанных",
                children=[card_table(TABLE_LIST_ID, "Список записанных", page_size=20)]
            ),
            dcc.Tab(
                label="Анализ записанных",
                children=[card_table(TABLE_ANALYSIS_ID, "Рейтинг пациентов по числу записей", page_size=20)]
            )
        ]),
    ],
    style={"padding": "20px"}
)


@app.callback(
    Output(TABLE_LIST_ID, 'data'),
    Output(TABLE_LIST_ID, 'columns'),
    Output(TABLE_ANALYSIS_ID, 'data'),
    Output(TABLE_ANALYSIS_ID, 'columns'),
    Output(DATE_RANGE_ID, 'start_date'),
    Output(DATE_RANGE_ID, 'end_date'),
    Output(STATUS_TEXT_ID, 'children'),
    Input(APPLY_BUTTON_ID, 'n_clicks'),
    Input(RESET_BUTTON_ID, 'n_clicks'),
    State(DATE_RANGE_ID, 'start_date'),
    State(DATE_RANGE_ID, 'end_date'),
    State(SCHEDULE_FILTER_ID, 'value'),
    State(SOURCE_FILTER_ID, 'value'),
    State(DEPARTMENT_FILTER_ID, 'value'),
    prevent_initial_call=True
)
def update_appointments(
    apply_clicks,
    reset_clicks,
    start_date,
    end_date,
    schedule_types,
    record_sources,
    departments
):
    if not apply_clicks and not reset_clicks:
        raise PreventUpdate

    trigger = ctx.triggered_id
    if trigger == RESET_BUTTON_ID:
        current_start = default_start.isoformat()
        current_end = default_end.isoformat()
        schedule_types = None
        record_sources = None
        departments = None
    else:
        current_start = start_date or default_start.isoformat()
        current_end = end_date or default_end.isoformat()

    parsed_start = datetime.fromisoformat(current_start).replace(hour=0, minute=0, second=0, microsecond=0)
    parsed_end = datetime.fromisoformat(current_end).replace(hour=23, minute=59, second=59, microsecond=999999)

    query_start = time.time()
    df = _fetch_appointments(parsed_start, parsed_end, schedule_types, record_sources, departments)
    execution_time = time.time() - query_start
    status_text = _format_status(execution_time, len(df))

    if df.empty:
        return [], [], [], [], current_start, current_end, status_text

    df['Пациент'] = (
        df['patient_last_name'].str.title() + ' ' +
        df['patient_first_name'].str.title() + ' ' +
        df['patient_middle_name'].str.title()
    )
    employee_cols = ['employee_last_name', 'employee_first_name', 'employee_middle_name']
    for col in employee_cols:
        if col in df.columns:
            df[col] = df[col].fillna('')

    df['Врач'] = (
        df['employee_last_name'].str.title().str.strip() + ' ' +
        df['employee_first_name'].str.title().str.strip() + ' ' +
        df['employee_middle_name'].str.title().str.strip()
    ).str.replace(r'\s+', ' ', regex=True).str.strip().replace({'- - -': '', '-': ''})

    df['Дата приема'] = df['acceptance_ts'].dt.strftime('%d.%m.%Y %H:%M')

    list_df = df.rename(columns={
        'birth_date': 'Дата рождения',
        'gender': 'Пол',
        'phone': 'Телефон',
        'enp': 'ЕНП',
        'attachment': 'Прикрепление',
        'series': 'Серия',
        'number': 'Номер',
        'record_date': 'Дата записи',
        'schedule_type': 'Тип расписания',
        'record_source': 'Источник записи',
        'department': 'Подразделение',
        'position': 'Должность',
        'creator': 'Создавший',
        'no_show': 'Не явился',
        'epmz': 'ЭПМЗ'
    })

    hidden_cols = [
        'patient_last_name', 'patient_first_name', 'patient_middle_name',
        'employee_last_name', 'employee_first_name', 'employee_middle_name',
        'acceptance_ts'
    ]
    list_df.drop(columns=[col for col in hidden_cols if col in list_df.columns], inplace=True)

    desired_order = [
        'Пациент', 'Дата рождения', 'Пол', 'Телефон', 'ЕНП', 'Прикрепление',
        'Врач', 'Должность', 'Подразделение', 'Дата приема', 'Дата записи',
        'Тип расписания', 'Источник записи', 'Создавший', 'Не явился', 'ЭПМЗ'
    ]
    list_df = list_df[[col for col in desired_order if col in list_df.columns]]

    if 'Врач' in list_df.columns:
        list_df['_missing_doctor'] = list_df['Врач'].isna() | (list_df['Врач'].astype(str).str.strip() == '')
        list_df.sort_values(by=['_missing_doctor'], ascending=True, inplace=True)
        list_df.drop(columns=['_missing_doctor'], inplace=True)
    list_columns = [{"name": col, "id": col} for col in list_df.columns]

    analysis_group_cols = [
        col for col in ['Пациент', 'Дата рождения', 'ЕНП', 'Прикрепление']
        if col in list_df.columns
    ]

    if analysis_group_cols:
        analysis_df = (
            list_df.groupby(analysis_group_cols, dropna=False)
            .size()
            .reset_index(name='Количество записей')
            .sort_values('Количество записей', ascending=False)
        )
    else:
        analysis_df = pd.DataFrame(columns=['Количество записей'])

    analysis_columns = [{"name": col, "id": col} for col in analysis_df.columns]

    return (
        list_df.to_dict('records'),
        list_columns,
        analysis_df.to_dict('records'),
        analysis_columns,
        current_start,
        current_end,
        status_text
    )
