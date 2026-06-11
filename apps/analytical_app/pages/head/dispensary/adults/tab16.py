from dash import html, dcc, Output, Input, State, exceptions
import traceback
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.components.filters import filter_years, date_picker, update_buttons
from apps.analytical_app.query_executor import engine
from apps.analytical_app.pages.head.dispensary.adults.query import (
    sql_query_procedure_appointments_list,
    sql_query_procedure_appointments_analytics,
    sql_query_procedure_appointments_goal_breakdown,
)


type_page = "tab16-da"

_filters_card = dbc.Card(
    dbc.CardBody([
        dbc.CardHeader("Фильтры"),
        dbc.Row([
            dbc.Col(update_buttons(type_page), width=2),
            dbc.Col(filter_years(type_page), width=2),
            dbc.Col(html.Div([html.Label("Даты приема (журнал)")]), width="auto"),
            dbc.Col(date_picker(type_page), width=3),
        ], align="center", className="mb-2"),
        dbc.Row([
            dbc.Col([
                html.Label("Процедура"),
                dcc.Dropdown(
                    id=f'dropdown-procedure-{type_page}',
                    options=[],
                    placeholder="Выберите процедуру",
                    clearable=False,
                ),
            ], width=4),
            dbc.Col([
                html.Label("Услуга (детализация)"),
                dcc.Dropdown(
                    id=f'dropdown-service-{type_page}',
                    options=[],
                    placeholder="Выберите услугу",
                    clearable=False,
                ),
            ], width=4),
            dbc.Col([
                html.Label("Только подразделения"),
                dcc.Dropdown(
                    id=f'dropdown-include-dept-{type_page}',
                    options=[],
                    multi=True,
                    placeholder="Все подразделения (если не выбрано)",
                    style={'minHeight': '60px'},
                ),
            ], width=4),
        ], align="center"),
    ]),
    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)", "border-radius": "10px"}
)

adults_dv16 = html.Div([
    _filters_card,
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    dbc.Tabs([
        dbc.Tab(label="Список", tab_id="list", children=[
            html.Div(id=f'stat-block-{type_page}', className='filters-label', style={'marginTop': '12px'}),
            card_table(f'result-table-{type_page}', "Записаны на процедуру", page_size=15),
        ]),
        dbc.Tab(label="Аналитика", tab_id="analytics", children=[
            html.Div(id=f'analytics-kpi-{type_page}', className='filters-label', style={'marginTop': '12px'}),
            card_table(f'analytics-table-{type_page}', "Сводные показатели", page_size=15),
            html.Hr(),
            card_table(f'goal-breakdown-table-{type_page}', "По целям (ОМС)", page_size=10),
        ]),
    ], id=f'tabs-{type_page}', active_tab="list"),
    html.Details([
        html.Summary("Отладка (показать/скрыть)"),
        html.Pre(id=f'debug-info-{type_page}', style={"whiteSpace": "pre-wrap"})
    ], open=False),
])


@app.callback(
    [
        Output(f'dropdown-procedure-{type_page}', 'options'),
        Output(f'dropdown-service-{type_page}', 'options'),
        Output(f'dropdown-include-dept-{type_page}', 'options'),
    ],
    [Input(f'dropdown-year-{type_page}', 'value')],
)
def load_filter_options(_year_value):
    procedure_options = []
    service_options = []
    dept_options = []
    try:
        with engine.connect() as conn:
            proc_rows = conn.execute(text("""
                SELECT DISTINCT procedure
                FROM load_data_journal_appeals
                WHERE COALESCE(NULLIF(procedure, '-'), '') <> ''
                ORDER BY procedure
            """)).fetchall()
            procedure_options = [{'label': r[0], 'value': r[0]} for r in proc_rows]

            svc_rows = conn.execute(text("""
                SELECT DISTINCT service_name, service_nomenclature
                FROM load_data_detailed_medical_examination
                WHERE service_status = 'Да'
                  AND COALESCE(NULLIF(service_name, '-'), '') <> ''
                ORDER BY service_name, service_nomenclature
                LIMIT 500
            """)).fetchall()
            for name, nom in svc_rows:
                label = f"{name} ({nom})" if nom and nom != '-' else name
                service_options.append({'label': label, 'value': name})

            dept_rows = conn.execute(text("""
                SELECT DISTINCT department
                FROM load_data_journal_appeals
                WHERE COALESCE(NULLIF(department, '-'), '') <> ''
                ORDER BY department
            """)).fetchall()
            dept_options = [{'label': r[0], 'value': r[0]} for r in dept_rows]
    except Exception:
        pass
    return procedure_options, service_options, dept_options


@app.callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'analytics-table-{type_page}', 'columns'),
        Output(f'analytics-table-{type_page}', 'data'),
        Output(f'goal-breakdown-table-{type_page}', 'columns'),
        Output(f'goal-breakdown-table-{type_page}', 'data'),
        Output(f'stat-block-{type_page}', 'children'),
        Output(f'analytics-kpi-{type_page}', 'children'),
        Output(f'debug-info-{type_page}', 'children'),
        Output(f'loading-output-{type_page}', 'children'),
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'date-picker-range-{type_page}', 'start_date'),
        State(f'date-picker-range-{type_page}', 'end_date'),
        State(f'dropdown-procedure-{type_page}', 'value'),
        State(f'dropdown-service-{type_page}', 'value'),
        State(f'dropdown-include-dept-{type_page}', 'value'),
    ],
)
def update_procedure_report(n_clicks, year_value, start_date, end_date,
                            procedure, service_key, include_depts):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading = html.Div([dcc.Loading(type="default")])
    empty = [], [], [], [], [], [], '', '', '', loading

    if not year_value or not start_date or not end_date:
        return (*empty[:-3], 'Укажите год и период дат', '', loading)
    if not procedure:
        return (*empty[:-3], 'Выберите процедуру', '', loading)
    if not service_key:
        return (*empty[:-3], 'Выберите услугу из детализации', '', loading)

    start_date_sql = start_date.split('T')[0]
    end_date_sql = end_date.split('T')[0]
    include_depts = include_depts or []

    list_query = sql_query_procedure_appointments_list(
        int(year_value), start_date_sql, end_date_sql,
        procedure, service_key, include_depts,
    )
    analytics_query = sql_query_procedure_appointments_analytics(
        int(year_value), start_date_sql, end_date_sql,
        procedure, service_key, include_depts,
    )
    breakdown_query = sql_query_procedure_appointments_goal_breakdown(
        int(year_value), start_date_sql, end_date_sql,
        procedure, include_depts,
    )

    try:
        list_columns, list_data = TableUpdater.query_to_df(engine, list_query)
        analytics_columns, analytics_data = TableUpdater.query_to_df(engine, analytics_query)
        breakdown_columns, breakdown_data = TableUpdater.query_to_df(engine, breakdown_query)
    except Exception as e:
        err = f"Ошибка выполнения запроса: {e}\n\n{traceback.format_exc()}"
        return [], [], [], [], [], [], 'Ошибка загрузки', '', err, loading

    total_rows = len(list_data)
    unique_enp = len({row.get('ЕНП') for row in list_data}) if list_data else 0
    stat_text = f"Записей: {total_rows} | Уникальных пациентов: {unique_enp}"

    kpi_parts = []
    if analytics_data:
        for row in analytics_data:
            kpi_parts.append(
                dbc.Col(
                    dbc.Card(dbc.CardBody([
                        html.Div(row.get('Показатель', ''), className="text-muted small"),
                        html.H5(str(row.get('Значение', '')), className="mb-0"),
                    ])),
                    md=4, xs=12, className="mb-2",
                )
            )
    kpi_row = dbc.Row(kpi_parts) if kpi_parts else html.Div("Нет данных для аналитики")

    dbg = (
        f"Год: {year_value}; Период: {start_date_sql} .. {end_date_sql}\n"
        f"Процедура: {procedure}; Услуга: {service_key}\n"
        f"Подразделения: {include_depts or 'все'}"
    )

    return (
        list_columns, list_data,
        analytics_columns, analytics_data,
        breakdown_columns, breakdown_data,
        stat_text, kpi_row, dbg, loading,
    )
