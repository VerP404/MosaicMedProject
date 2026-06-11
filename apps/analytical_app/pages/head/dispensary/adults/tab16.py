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
    sql_query_procedure_source_journal,
    sql_query_procedure_source_oms,
    sql_query_procedure_source_detailing,
    SOURCE_PREVIEW_LIMIT,
)


type_page = "tab16-da"

_MULTI_DROPDOWN_STYLE = {
    'minHeight': '72px',
    'width': '100%',
}

_LABEL_MAX_LEN = 72


def _truncate_label(text: str, max_len: int = _LABEL_MAX_LEN) -> str:
    text = str(text or '').strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + '…'


def _as_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v and str(v).strip()]
    v = str(value).strip()
    return [v] if v else []


def _kpi_card(title: str, value, hint: str, border: str, *, large: bool = False) -> dbc.Card:
    value_tag = html.H2(str(value), className="mb-0 text-center") if large else html.H5(str(value), className="mb-0 text-center")
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, className="text-muted small text-center"),
            value_tag,
            html.Div(hint, className="text-muted text-center mt-1", style={'fontSize': '0.7rem'}),
        ], className="py-2 px-2 d-flex flex-column justify-content-center"),
        className=f"border-{border} border-2 h-100",
    )


def _build_analytics_kpi(analytics_data: list[dict]):
    if not analytics_data:
        return html.Div("Нет данных для аналитики")

    metrics = {row.get('Показатель', ''): row.get('Значение', '') for row in analytics_data}
    m = lambda key, default=0: metrics.get(key, default)

    volume_row = dbc.Row([
        dbc.Col(_kpi_card(
            'Записей на приём', m('Записей на приём'),
            'строк журнала за период', 'primary',
        ), md=6, xs=12, className="mb-2"),
        dbc.Col(_kpi_card(
            'Уникальных пациентов', m('Уникальных пациентов'),
            'уникальных ЕНП', 'primary',
        ), md=6, xs=12, className="mb-2"),
    ], className="g-2 mb-2")

    channels_stack = html.Div([
        html.Div(_kpi_card('→ Услуга', m('  → Услуга (детализация)'), 'детализация', 'success'), className="mb-2"),
        html.Div(_kpi_card('→ Диспансеризация', m('  → Диспансеризация (цель ОМС)'), 'цель ОМС', 'success'), className="mb-2"),
        html.Div(_kpi_card('→ 541', m('  → 541 в дату приёма'), 'дата приёма', 'success')),
    ], className="h-100 d-flex flex-column")

    result_problem_row = dbc.Row([
        dbc.Col([
            html.Div("Результат", className="text-muted small fw-semibold mb-1"),
            dbc.Row([
                dbc.Col(_kpi_card(
                    'Есть результат', m('Есть результат (любой канал)'),
                    'любой канал', 'success', large=True,
                ), md=4, xs=12, className="mb-2 mb-md-0"),
                dbc.Col(channels_stack, md=5, xs=12, className="mb-2 mb-md-0"),
            ], className="g-2 align-items-stretch h-100"),
        ], md=9, xs=12),
        dbc.Col([
            html.Div("Проблема", className="text-muted small fw-semibold mb-1"),
            _kpi_card(
                'Без результата', m('Без результата'),
                'ни услуги, ни диспансеризации, ни 541', 'danger', large=True,
            ),
        ], md=3, xs=12, className="mb-2 d-flex flex-column"),
    ], className="g-2 mb-2 align-items-stretch")

    intersections_row = dbc.Row([
        dbc.Col(html.Div("Пересечения", className="text-muted small fw-semibold mb-1"), width=12),
        dbc.Col(_kpi_card(
            'Услуга + диспансеризация', m('Услуга + диспансеризация'),
            'оба канала', 'secondary',
        ), md=3, xs=6, className="mb-2"),
        dbc.Col(_kpi_card(
            'Услуга + 541', m('Услуга + 541'),
            'оба канала', 'secondary',
        ), md=3, xs=6, className="mb-2"),
        dbc.Col(_kpi_card(
            'Диспансеризация + 541', m('Диспансеризация + 541'),
            'оба канала', 'secondary',
        ), md=3, xs=6, className="mb-2"),
        dbc.Col(_kpi_card(
            'Все три канала', m('Все три канала'),
            'услуга, диспансеризация, 541', 'secondary',
        ), md=3, xs=6, className="mb-2"),
    ], className="g-2")

    return html.Div([volume_row, result_problem_row, intersections_row])


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
                html.Label("Процедуры"),
                dcc.Dropdown(
                    id=f'dropdown-procedure-{type_page}',
                    options=[],
                    multi=True,
                    placeholder="Выберите одну или несколько процедур",
                    style=_MULTI_DROPDOWN_STYLE,
                ),
            ], width=4),
            dbc.Col([
                html.Label("Услуги (детализация)"),
                dcc.Dropdown(
                    id=f'dropdown-service-{type_page}',
                    options=[],
                    multi=True,
                    placeholder="Выберите одну или несколько услуг",
                    style=_MULTI_DROPDOWN_STYLE,
                ),
            ], width=4),
            dbc.Col([
                html.Label("Только подразделения"),
                dcc.Dropdown(
                    id=f'dropdown-include-dept-{type_page}',
                    options=[],
                    multi=True,
                    placeholder="Все подразделения (если не выбрано)",
                    style=_MULTI_DROPDOWN_STYLE,
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
            card_table(f'goal-breakdown-table-{type_page}', "По целям (ОМС и 541)", page_size=12),
        ]),
        dbc.Tab(label="Исходные данные", tab_id="sources", children=[
            dbc.Alert(
                f"Для проверки: выборка до {SOURCE_PREVIEW_LIMIT} строк по каждому источнику "
                "(только пациенты из выбранных записей журнала). Полный дамп таблиц не выводится — "
                "скачивание через Export в каждой таблице.",
                color="info",
                className="mt-2 mb-2",
            ),
            html.Div(id=f'source-stat-{type_page}', className='filters-label'),
            card_table(f'source-journal-{type_page}', "Журнал обращений (load_data_journal_appeals)", page_size=15),
            html.Hr(),
            card_table(f'source-oms-{type_page}', "Талоны ОМС (load_data_oms_data)", page_size=15),
            html.Hr(),
            card_table(f'source-detail-{type_page}', "Детализация (load_data_detailed_medical_examination)", page_size=15),
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
            for r in proc_rows:
                full = r[0]
                procedure_options.append({
                    'label': _truncate_label(full),
                    'value': full,
                    'title': full,
                })

            svc_rows = conn.execute(text("""
                SELECT DISTINCT service_name, service_nomenclature
                FROM load_data_detailed_medical_examination
                WHERE service_status = 'Да'
                  AND COALESCE(NULLIF(service_name, '-'), '') <> ''
                ORDER BY service_name, service_nomenclature
                LIMIT 500
            """)).fetchall()
            for name, nom in svc_rows:
                full_label = f"{name} ({nom})" if nom and nom != '-' else name
                service_options.append({
                    'label': _truncate_label(full_label),
                    'value': name,
                    'title': full_label,
                })

            dept_rows = conn.execute(text("""
                SELECT DISTINCT department
                FROM load_data_journal_appeals
                WHERE COALESCE(NULLIF(department, '-'), '') <> ''
                ORDER BY department
            """)).fetchall()
            for r in dept_rows:
                full = r[0]
                dept_options.append({
                    'label': _truncate_label(full),
                    'value': full,
                    'title': full,
                })
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
        Output(f'source-journal-{type_page}', 'columns'),
        Output(f'source-journal-{type_page}', 'data'),
        Output(f'source-oms-{type_page}', 'columns'),
        Output(f'source-oms-{type_page}', 'data'),
        Output(f'source-detail-{type_page}', 'columns'),
        Output(f'source-detail-{type_page}', 'data'),
        Output(f'stat-block-{type_page}', 'children'),
        Output(f'source-stat-{type_page}', 'children'),
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
                            procedures, service_keys, include_depts):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading = html.Div([dcc.Loading(type="default")])
    _empty_tables = ([],) * 12

    def _empty_return(stat_msg: str = '', dbg_msg: str = ''):
        return (*_empty_tables, stat_msg, '', '', dbg_msg, loading)

    procedures = _as_list(procedures)
    service_keys = _as_list(service_keys)
    include_depts = _as_list(include_depts)

    if not year_value or not start_date or not end_date:
        return _empty_return('Укажите год и период дат')
    if not procedures:
        return _empty_return('Выберите хотя бы одну процедуру')
    if not service_keys:
        return _empty_return('Выберите хотя бы одну услугу из детализации')

    start_date_sql = start_date.split('T')[0]
    end_date_sql = end_date.split('T')[0]

    list_query = sql_query_procedure_appointments_list(
        int(year_value), start_date_sql, end_date_sql,
        procedures, service_keys, include_depts,
    )
    analytics_query = sql_query_procedure_appointments_analytics(
        int(year_value), start_date_sql, end_date_sql,
        procedures, service_keys, include_depts,
    )
    breakdown_query = sql_query_procedure_appointments_goal_breakdown(
        int(year_value), start_date_sql, end_date_sql,
        procedures, include_depts,
    )
    journal_src_query = sql_query_procedure_source_journal(
        start_date_sql, end_date_sql, procedures, include_depts,
    )
    oms_src_query = sql_query_procedure_source_oms(
        int(year_value), start_date_sql, end_date_sql, procedures, include_depts,
    )
    detail_src_query = sql_query_procedure_source_detailing(
        start_date_sql, end_date_sql, procedures, service_keys, include_depts,
    )

    try:
        list_columns, list_data = TableUpdater.query_to_df(engine, list_query)
        analytics_columns, analytics_data = TableUpdater.query_to_df(engine, analytics_query)
        breakdown_columns, breakdown_data = TableUpdater.query_to_df(engine, breakdown_query)
        journal_src_cols, journal_src_data = TableUpdater.query_to_df(engine, journal_src_query)
        oms_src_cols, oms_src_data = TableUpdater.query_to_df(engine, oms_src_query)
        detail_src_cols, detail_src_data = TableUpdater.query_to_df(engine, detail_src_query)
    except Exception as e:
        err = f"Ошибка выполнения запроса: {e}\n\n{traceback.format_exc()}"
        return _empty_return('Ошибка загрузки', err)

    total_rows = len(list_data)
    unique_enp = len({row.get('ЕНП') for row in list_data}) if list_data else 0
    no_result = sum(1 for row in list_data if row.get('Результат') == 'Без результата') if list_data else 0
    stat_text = (
        f"Записей: {total_rows} | Уникальных пациентов: {unique_enp} | "
        f"Без результата: {no_result} | Процедур: {len(procedures)} | Услуг: {len(service_keys)}"
    )

    kpi_row = _build_analytics_kpi(analytics_data)

    source_stat = (
        f"Исходные данные: журнал {len(journal_src_data)} | "
        f"ОМС {len(oms_src_data)} | детализация {len(detail_src_data)} строк "
        f"(лимит {SOURCE_PREVIEW_LIMIT} на таблицу)"
    )

    dbg = (
        f"Год: {year_value}; Период: {start_date_sql} .. {end_date_sql}\n"
        f"Процедуры ({len(procedures)}): {', '.join(procedures)}\n"
        f"Услуги ({len(service_keys)}): {', '.join(service_keys)}\n"
        f"Подразделения: {include_depts or 'все'}"
    )

    return (
        list_columns, list_data,
        analytics_columns, analytics_data,
        breakdown_columns, breakdown_data,
        journal_src_cols, journal_src_data,
        oms_src_cols, oms_src_data,
        detail_src_cols, detail_src_data,
        stat_text, source_stat, kpi_row, dbg, loading,
    )
