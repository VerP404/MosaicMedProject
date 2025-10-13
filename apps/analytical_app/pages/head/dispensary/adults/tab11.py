from datetime import datetime

from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    update_buttons,
    filter_years,
    filter_months,
    filter_status,
    filter_building,
    status_groups,
    get_current_reporting_month,
)
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine
from sqlalchemy import text


# Уникальный идентификатор страницы: используйте в id элементов
type_page = "tab11-da"


adults_dv11 = html.Div(
    [
        # Блок фильтров
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=2),
                                    dbc.Col(filter_months(type_page), width=8),
                                ],
                                align="center",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_building(type_page), width=6),
                                    dbc.Col(
                                        html.Div([
                                            html.Label("Наличие ЭМД", style={"font-weight": "bold"}),
                                            dcc.RadioItems(
                                                id=f"emd-presence-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Есть ЭМД", "value": "with"},
                                                    {"label": "Нет ЭМД", "value": "without"},
                                                ],
                                                value="all",
                                                inline=True,
                                            )
                                        ]),
                                        width=6,
                                    ),
                                ]
                            ),
                            dbc.Card(
                                dbc.Row(
                                    [
                                        filter_status(type_page),
                                    ]
                                ),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(id=f"selected-period-{type_page}", className="filters-label"),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        html.Div(id=f"current-month-name-{type_page}", className="filters-label"),
                                        width=6,
                                    ),
                                ]
                            ),
                        ]
                    ),

                ),
                width=12,
            ),
            style={"margin": "0 auto", "padding": "0rem"},
        ),

        # Вкладки: Список и Анализ
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dcc.Tabs(id=f"tabs-{type_page}", value="list", children=[
                                dcc.Tab(label="Список карт", value="list", children=[
                                    dcc.Loading(id=f"loading-list-{type_page}", type="default"),
                                    card_table(f"result-table-list-{type_page}", "Список карт (ОМС + ЭМД)")
                                ]),
                                dcc.Tab(label="Анализ", value="analysis", children=[
                                    dcc.Loading(id=f"loading-analysis-{type_page}", type="default"),
                                    card_table(f"result-table-buildings-{type_page}", "Статистика по корпусам"),
                                    card_table(f"result-table-doctors-{type_page}", "Статистика по врачам (разбивка по целям и статусу ЭМД)")
                                ]),
                            ])
                        ]
                    )
                ),
                width=12
            )
        )
    ],
    style={"padding": "0rem"},
)


# ——— Колбэки вспомогательные ———
@app.callback(
    [Output(f'status-group-container-{type_page}', 'style'),
     Output(f'status-individual-container-{type_page}', 'style')],
    [Input(f'status-selection-mode-{type_page}', 'value')]
)
def toggle_status_selection_mode(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}


@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval-main', 'n_intervals')
)
def update_current_month(_):
    _, name = get_current_reporting_month()
    return name


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [Input(f'range-slider-month-{type_page}', 'value'),
     Input(f'dropdown-year-{type_page}', 'value')]
)
def show_period(months, year):
    if not months or not year:
        return ""
    return f"Год: {year}, месяцы: {months}"


# ——— Основной колбэк: строим таблицы ———
@app.callback(
    [
        Output(f'result-table-list-{type_page}', 'columns'),
        Output(f'result-table-list-{type_page}', 'data'),
        Output(f'result-table-buildings-{type_page}', 'columns'),
        Output(f'result-table-buildings-{type_page}', 'data'),
        Output(f'result-table-doctors-{type_page}', 'columns'),
        Output(f'result-table-doctors-{type_page}', 'data'),
        Output(f'loading-list-{type_page}', 'children'),
        Output(f'loading-analysis-{type_page}', 'children'),
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [
        State(f'range-slider-month-{type_page}', 'value'),
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'dropdown-building-{type_page}', 'value'),
        State(f'emd-presence-{type_page}', 'value'),
        State(f'status-selection-mode-{type_page}', 'value'),
        State(f'status-group-radio-{type_page}', 'value'),
        State(f'status-individual-dropdown-{type_page}', 'value'),
    ]
)
def build_tables(n_clicks, months_range, year, building_ids,
                 emd_presence, status_mode, status_group, status_individual):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    # Параметры
    if not months_range:
        months_range = [1, 12]
    m1, m2 = int(months_range[0]), int(months_range[1])

    # Выбранные статусы
    if status_mode == 'group':
        statuses = status_groups.get(status_group, ['2', '3'])
    else:
        statuses = status_individual or ['2', '3']

    statuses_list = ", ".join(f"'{s}'" for s in statuses)

    # Имена корпусов по выбранным id (если выбраны)
    buildings_filter_sql = ""
    if building_ids:
        if not isinstance(building_ids, list):
            building_ids = [building_ids]
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM organization_building WHERE id = ANY(:ids)"),
                {"ids": building_ids}
            ).fetchall()
        building_names = [r[0] for r in rows]
        if building_names:
            buildings_list = ", ".join(f"'{b}'" for b in building_names)
            buildings_filter_sql = f" AND oms.building IN ({buildings_list})"

    # Фильтр по наличию ЭМД
    emd_filter_sql = ""
    if emd_presence == "with":
        emd_filter_sql = " AND emd.sending_status IS NOT NULL AND emd.sending_status <> ''"
    elif emd_presence == "without":
        emd_filter_sql = " AND emd.sending_status IS NULL"

    # Общие фильтры
    base_where = f"""
        WHERE
            oms.report_year = {int(year)}
            AND oms.report_month BETWEEN {m1} AND {m2}
            AND oms.goal IN ('ДВ4','ДВ2','ОПВ','УД1','УД2')
            AND oms.status IN ({statuses_list})
            {buildings_filter_sql}
            {emd_filter_sql}
    """

    # — Список карт —
    sql_list = f"""
        SELECT
            COALESCE(emd.sending_status, 'нет ЭМД') AS sending_status,
            oms.talon,
            oms.source_id,
            oms.report_month,
            oms.report_year,
            oms.status,
            oms.goal,
            oms.patient,
            oms.birth_date,
            oms.treatment_start,
            oms.treatment_end,
            oms.enp,
            oms.building,
            oms.doctor_code,
            oms.doctor
        FROM load_data_oms_data oms
        LEFT JOIN load_data_emd emd
            ON oms.source_id = emd.original_epmz_id
            AND emd.document_type = 'Эпикриз по результатам диспансеризации/профилактического медицинского осмотра'
        {base_where}
        ORDER BY oms.building, oms.doctor, oms.report_month, oms.talon
    """

    columns_list, data_list = TableUpdater.query_to_df(engine, sql_list)

    # — Анализ по корпусам —
    sql_buildings = f"""
        SELECT
            oms.building AS корпус,
            COALESCE(emd.sending_status, 'нет ЭМД') AS sending_status,
            COUNT(*) FILTER (WHERE oms.goal='ДВ4') AS dv4,
            COUNT(*) FILTER (WHERE oms.goal='ДВ2') AS dv2,
            COUNT(*) FILTER (WHERE oms.goal='ОПВ') AS opv,
            COUNT(*) FILTER (WHERE oms.goal='УД1') AS ud1,
            COUNT(*) FILTER (WHERE oms.goal='УД2') AS ud2,
            COUNT(*) AS итого
        FROM load_data_oms_data oms
        LEFT JOIN load_data_emd emd
            ON oms.source_id = emd.original_epmz_id
            AND emd.document_type = 'Эпикриз по результатам диспансеризации/профилактического медицинского осмотра'
        {base_where}
        GROUP BY oms.building, COALESCE(emd.sending_status, 'нет ЭМД')
        ORDER BY oms.building, sending_status
    """

    columns_bld, data_bld = TableUpdater.query_to_df(engine, sql_buildings)

    # — Анализ по врачам —
    sql_doctors = f"""
        SELECT
            oms.building AS корпус,
            oms.doctor AS врач,
            COALESCE(emd.sending_status, 'нет ЭМД') AS sending_status,
            COUNT(*) FILTER (WHERE oms.goal='ДВ4') AS dv4,
            COUNT(*) FILTER (WHERE oms.goal='ДВ2') AS dv2,
            COUNT(*) FILTER (WHERE oms.goal='ОПВ') AS opv,
            COUNT(*) FILTER (WHERE oms.goal='УД1') AS ud1,
            COUNT(*) FILTER (WHERE oms.goal='УД2') AS ud2,
            COUNT(*) AS итого
        FROM load_data_oms_data oms
        LEFT JOIN load_data_emd emd
            ON oms.source_id = emd.original_epmz_id
            AND emd.document_type = 'Эпикриз по результатам диспансеризации/профилактического медицинского осмотра'
        {base_where}
        GROUP BY oms.building, oms.doctor, COALESCE(emd.sending_status, 'нет ЭМД')
        ORDER BY oms.building, oms.doctor, sending_status
    """

    columns_doc, data_doc = TableUpdater.query_to_df(engine, sql_doctors)

    loading_dummy = html.Div([dcc.Loading(type="default")])
    return (columns_list, data_list,
            columns_bld, data_bld,
            columns_doc, data_doc,
            loading_dummy, loading_dummy)


