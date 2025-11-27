from datetime import datetime, timedelta
import re
import time
from functools import lru_cache

import pandas as pd
from dash import html, dcc, Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.components import filters as common_filters
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine


type_page = "registry-analysis-orders"
TABLE_ID = f"result-table-{type_page}"
TABLE_DOCTORS_ID = f"result-table-doctors-{type_page}"
TABLE_PATIENTS_ID = f"result-table-patients-{type_page}"
TABLE_DEPARTMENTS_ID = f"result-table-departments-{type_page}"
DATE_RANGE_ID = f"date-picker-range-{type_page}"
PAYMENT_DROPDOWN_ID = f"payment-source-{type_page}"
ATTACHMENT_FILTER_ID = f"attachment-filter-{type_page}"
APPLY_BUTTON_ID = f"apply-filters-{type_page}"
RESET_BUTTON_ID = f"reset-filters-{type_page}"
SERVICES_SWITCH_ID = f"services-codes-only-{type_page}"
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


def _payment_source_options():
    query = text("""
        SELECT DISTINCT payment_source
        FROM load_data_kvazar_analysis_orders
        WHERE payment_source IS NOT NULL
          AND payment_source <> '-'
        ORDER BY payment_source
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()
    options = [{'label': 'Все источники', 'value': 'all'}]
    options.extend(
        {'label': row[0], 'value': row[0]}
        for row in rows if row and row[0]
    )
    return options


@lru_cache(maxsize=1)
def _get_attachment_enps():
    query = text("""
        SELECT DISTINCT regexp_replace(enp, '\\D', '', 'g') AS enp_norm
        FROM data_loader_iszlpeople
        WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()
    return {row[0] for row in rows if row and row[0]}


def _fetch_orders(
    date_from: datetime,
    date_to: datetime,
    payment_source: str,
    services_codes_only: bool,
    attachment_filter: str
) -> pd.DataFrame:
    query = text("""
        WITH data AS (
            SELECT
                number,
                status,
                lis,
                patient,
                doctor,
                operator,
                diagnosis,
                services,
                payment_source,
                emd_status,
                nns_vimis_status,
                rns_vimis_status,
                created_at,
                updated_at,
                to_timestamp(NULLIF(order_created_at, '-'), 'YYYY-MM-DD"T"HH24:MI') AS order_created_at_ts
            FROM load_data_kvazar_analysis_orders
        )
        SELECT
            number,
            status,
            lis,
            patient,
            doctor,
            operator,
            diagnosis,
            services,
            payment_source,
            emd_status,
            nns_vimis_status,
            rns_vimis_status,
            created_at,
            updated_at,
            order_created_at_ts
        FROM data
        WHERE order_created_at_ts IS NOT NULL
          AND order_created_at_ts BETWEEN :date_from AND :date_to
          AND (:payment_source = 'all' OR payment_source = :payment_source)
        ORDER BY order_created_at_ts DESC
    """)

    df = pd.read_sql_query(
        query,
        engine,
        params={
            "date_from": date_from,
            "date_to": date_to,
            "payment_source": payment_source or 'all',
        },
        parse_dates=['order_created_at_ts', 'created_at', 'updated_at']
    )

    if df.empty:
        return df

    df['Создан'] = df['order_created_at_ts'].dt.strftime('%d.%m.%Y %H:%M')
    df['Загружено в систему'] = pd.to_datetime(df['created_at']).dt.strftime('%d.%m.%Y %H:%M')
    df['Обновлено'] = pd.to_datetime(df['updated_at']).dt.strftime('%d.%m.%Y %H:%M')

    df = df.rename(columns={
        'number': 'Номер',
        'status': 'Статус',
        'lis': 'ЛИС',
        'patient': 'Пациент',
        'doctor': 'Врач',
        'operator': 'Оператор',
        'diagnosis': 'Диагноз',
        'services': 'Услуги',
        'payment_source': 'Источник оплаты',
        'emd_status': 'Статус ЭМД',
        'nns_vimis_status': 'Статус ННС ВИМИС',
        'rns_vimis_status': 'Статус (Р)НС ВИМИС',
    })

    def _split_person_field(value):
        if not value or value == '-':
            return '-', '-', '-'
        parts = [part.strip() for part in value.split(',', 2)]
        while len(parts) < 3:
            parts.append('-')
        return parts[0], parts[1], parts[2]

    def _split_patient_field(value: str):
        if not value or value == '-':
            return '-', '-', '-'
        parts = [part.strip() for part in value.split(',')]
        fio = parts[0] if parts else '-'
        birth = parts[1].split('(')[0].strip() if len(parts) > 1 and parts[1] else '-'
        enp = parts[2] if len(parts) > 2 else '-'
        return fio, birth, enp

    for col, prefix in [('Врач', 'Врач'), ('Оператор', 'Оператор')]:
        if col in df.columns:
            fio_col = f"{prefix} ФИО"
            role_col = f"{prefix} должность"
            dept_col = f"{prefix} подразделение"
            splits = df[col].apply(_split_person_field).tolist()
            if splits:
                df[[fio_col, role_col, dept_col]] = pd.DataFrame(splits, index=df.index)
            df.drop(columns=[col], inplace=True)

    if 'Пациент' in df.columns:
        patient_splits = df['Пациент'].apply(_split_patient_field).tolist()
        if patient_splits:
            df[['Пациент ФИО', 'Пациент ДР', 'Пациент ЕНП']] = pd.DataFrame(patient_splits, index=df.index)
        df.drop(columns=['Пациент'], inplace=True)
    attachment_enps = _get_attachment_enps()
    df['Пациент ЕНП норм'] = (
        df.get('Пациент ЕНП', pd.Series(dtype=str))
        .astype(str)
        .str.replace(r'\D', '', regex=True)
    )
    df['Прикрепление'] = df['Пациент ЕНП норм'].apply(
        lambda val: 'Да' if val and val in attachment_enps else 'Нет'
    )
    if attachment_filter == 'attached':
        df = df[df['Прикрепление'] == 'Да']
    elif attachment_filter == 'not_attached':
        df = df[df['Прикрепление'] == 'Нет']
    df.drop(columns=['Пациент ЕНП норм'], errors='ignore', inplace=True)

    df.drop(columns=[
        'Статус ЭМД',
        'Статус ННС ВИМИС',
        'Статус (Р)НС ВИМИС',
        'Загружено в систему',
        'Обновлено'
    ], inplace=True, errors='ignore')

    if services_codes_only and 'Услуги' in df.columns:
        code_pattern = re.compile(r'([A-Za-zА-Яа-я]\d{2}\.\d{2,3}\.\d{3}(?:\.\d{3})?)', re.IGNORECASE)
        df['Услуги'] = df['Услуги'].apply(
            lambda value: ', '.join(match.upper() for match in code_pattern.findall(str(value)))
            if code_pattern.search(str(value)) else value
        )

    desired_order = [
        'Номер', 'Создан', 'Источник оплаты', 'Статус', 'ЛИС',
        'Пациент ФИО', 'Пациент ДР', 'Пациент ЕНП',
        'Прикрепление',
        'Врач ФИО', 'Врач должность', 'Врач подразделение',
        'Оператор ФИО', 'Оператор должность', 'Оператор подразделение',
        'Диагноз', 'Услуги'
    ]
    existing_order = [col for col in desired_order if col in df.columns]
    return df[existing_order]


payment_options = _payment_source_options()
default_start, default_end = _default_dates()

analysis_orders_page = html.Div(
    [
        dbc.Card(
            dbc.CardBody([
                html.H5("Фильтры отбора", className="mb-3"),
                dbc.Row([
                    dbc.Col(common_filters.date_picker(type_page), md=4, xs=12, className="mb-3"),
                    dbc.Col(
                        [
                            html.Label("Источник оплаты", className="fw-bold"),
                            dcc.Dropdown(
                                id=PAYMENT_DROPDOWN_ID,
                                options=payment_options,
                                value='all',
                                clearable=False,
                                placeholder="Выберите источник оплаты..."
                            )
                        ],
                        md=3, xs=12, className="mb-3"
                    ),
                    dbc.Col(
                        [
                            html.Label("Формат услуг", className="fw-bold"),
                            dbc.Checklist(
                                options=[{"label": "Показывать только коды услуг", "value": "codes"}],
                                value=["codes"],
                                id=SERVICES_SWITCH_ID,
                                switch=True
                            )
                        ],
                        md=3, xs=12, className="mb-3"
                    ),
                    dbc.Col(
                        [
                            html.Label("Прикрепление", className="fw-bold"),
                            dcc.Dropdown(
                                id=ATTACHMENT_FILTER_ID,
                                options=[
                                    {'label': 'Все', 'value': 'all'},
                                    {'label': 'Прикреплены', 'value': 'attached'},
                                    {'label': 'Без прикрепления', 'value': 'not_attached'},
                                ],
                                value='all',
                                clearable=False,
                                placeholder="Фильтр по прикреплению"
                            )
                        ],
                        md=2, xs=12, className="mb-3"
                    ),
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.ButtonGroup(
                            [
                                dbc.Button("Применить", id=APPLY_BUTTON_ID, color="primary"),
                                dbc.Button("Сбросить", id=RESET_BUTTON_ID, color="secondary", className="ms-2"),
                            ],
                            className="mt-2"
                        ),
                        md=3, xs=12, className="mb-3 d-flex align-items-end justify-content-start"
                    )
                ])
            ]),
            className="mb-4"
        ),
        html.Div(id=STATUS_TEXT_ID, className="text-muted mb-3"),
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Журнал заказов анализов",
                    children=[
                        card_table(TABLE_ID, "Журнал заказов анализов", page_size=15)
                    ]
                ),
                dcc.Tab(
                    label="Анализ выдачи: по врачам",
                    children=[
                        card_table(TABLE_DOCTORS_ID, "Количество заказов по врачам", page_size=15)
                    ]
                ),
                dcc.Tab(
                    label="Анализ выдачи: по пациентам",
                    children=[
                        card_table(TABLE_PATIENTS_ID, "Количество заказов по пациентам", page_size=15)
                    ]
                ),
                dcc.Tab(
                    label="Анализ выдачи: по подразделениям",
                    children=[
                        card_table(TABLE_DEPARTMENTS_ID, "Количество заказов по подразделениям", page_size=15)
                    ]
                )
            ]
        )
    ],
    style={"padding": "20px"}
)


@app.callback(
    Output(TABLE_ID, 'data'),
    Output(TABLE_ID, 'columns'),
    Output(TABLE_DOCTORS_ID, 'data'),
    Output(TABLE_DOCTORS_ID, 'columns'),
    Output(TABLE_PATIENTS_ID, 'data'),
    Output(TABLE_PATIENTS_ID, 'columns'),
    Output(TABLE_DEPARTMENTS_ID, 'data'),
    Output(TABLE_DEPARTMENTS_ID, 'columns'),
    Output(DATE_RANGE_ID, 'start_date'),
    Output(DATE_RANGE_ID, 'end_date'),
    Output(PAYMENT_DROPDOWN_ID, 'value'),
    Output(ATTACHMENT_FILTER_ID, 'value'),
    Output(STATUS_TEXT_ID, 'children'),
    Input(APPLY_BUTTON_ID, 'n_clicks'),
    Input(RESET_BUTTON_ID, 'n_clicks'),
    State(SERVICES_SWITCH_ID, 'value'),
    State(DATE_RANGE_ID, 'start_date'),
    State(DATE_RANGE_ID, 'end_date'),
    State(PAYMENT_DROPDOWN_ID, 'value'),
    State(ATTACHMENT_FILTER_ID, 'value'),
    prevent_initial_call=True
)
def update_analysis_orders_table(
    apply_clicks,
    reset_clicks,
    services_mode,
    start_date,
    end_date,
    payment_value,
    attachment_value
):
    if not apply_clicks and not reset_clicks:
        raise PreventUpdate

    trigger = ctx.triggered_id
    services_codes_only = services_mode is None or ("codes" in services_mode)

    if trigger == RESET_BUTTON_ID:
        current_start = default_start.isoformat()
        current_end = default_end.isoformat()
        current_payment = 'all'
        current_attachment = 'all'
    else:
        current_start = start_date or default_start.isoformat()
        current_end = end_date or default_end.isoformat()
        current_payment = payment_value or 'all'
        current_attachment = attachment_value or 'all'

    parsed_start = datetime.fromisoformat(current_start).replace(hour=0, minute=0, second=0, microsecond=0)
    parsed_end = datetime.fromisoformat(current_end).replace(hour=23, minute=59, second=59, microsecond=999999)

    query_start = time.time()
    df = _fetch_orders(parsed_start, parsed_end, current_payment, services_codes_only, current_attachment)
    execution_time = time.time() - query_start
    status_text = _format_status(execution_time, len(df))

    if df.empty:
        empty_resp = ([], [])
        return (
            *empty_resp,
            *empty_resp,
            *empty_resp,
            *empty_resp,
            current_start,
            current_end,
            current_payment,
            current_attachment,
            status_text
        )

    main_columns = [{"name": col, "id": col} for col in df.columns]

    doctor_group = (
        df.groupby(['Врач ФИО', 'Врач должность', 'Врач подразделение'], dropna=False)
        .size()
        .reset_index(name='Количество заказов')
        .sort_values('Количество заказов', ascending=False)
    )
    doctor_columns = [{"name": col, "id": col} for col in doctor_group.columns]

    patient_group = (
        df.groupby(['Пациент ФИО', 'Пациент ДР', 'Пациент ЕНП', 'Прикрепление'], dropna=False)
        .size()
        .reset_index(name='Количество заказов')
        .sort_values('Количество заказов', ascending=False)
    )
    patient_columns = [{"name": col, "id": col} for col in patient_group.columns]

    department_group = (
        df.groupby(['Врач подразделение'], dropna=False)
        .size()
        .reset_index(name='Количество заказов')
        .sort_values('Количество заказов', ascending=False)
    )
    department_columns = [{"name": col, "id": col} for col in department_group.columns]

    return (
        df.to_dict('records'), main_columns,
        doctor_group.to_dict('records'), doctor_columns,
        patient_group.to_dict('records'), patient_columns,
        department_group.to_dict('records'), department_columns,
        current_start, current_end, current_payment, current_attachment,
        status_text
    )

