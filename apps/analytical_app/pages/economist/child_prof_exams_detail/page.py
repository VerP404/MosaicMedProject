# -*- coding: utf-8 -*-
from datetime import datetime

from dash import html, dcc, Output, Input, exceptions, State
from sqlalchemy import text

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import *
from apps.analytical_app.components.toast import toast
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.app import app
from apps.analytical_app.pages.economist.child_prof_exams_detail.query import sql_child_prof_exams_detail
from apps.analytical_app.query_executor import engine

type_page = "child-prof-exams-detail"

economist_child_prof_exams_detail_layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            html.Button(id=f'page-load-{type_page}', style={'display': 'none'}),
                            dbc.Row(
                                [
                                    filter_status(type_page),
                                    filter_years(type_page),
                                ]
                            ),
                            dbc.Row(
                                [
                                    filter_months(type_page),
                                ]
                            ),
                            html.Div(
                                [
                                    dbc.Label("Выберите корпус:"),
                                    dbc.Checklist(
                                        id=f"building-checklist-{type_page}",
                                        inline=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    dbc.Label("Цель (профосмотр):"),
                                    dbc.Checklist(
                                        options=[
                                            {"label": "ПН1", "value": "ПН1"},
                                            {"label": "ДС2", "value": "ДС2"},
                                        ],
                                        value=["ПН1", "ДС2"],
                                        id=f"goal-checklist-{type_page}",
                                        inline=True,
                                    ),
                                ]
                            ),
                            html.P(
                                "Строки — по маршруту из детализации; столбцы как в «Диспансеризация по возрастам»: "
                                "Всего, Сумма, М, М Сумма, Ж, Ж Сумма и по каждому выбранному корпусу.",
                                className="text-muted small mb-2",
                            ),
                            html.Div(
                                id=f'selected-period-{type_page}',
                                className='filters-label',
                                style={'display': 'none'},
                            ),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                            html.Div(id=f'selected-month-{type_page}', className='filters-label'),
                            html.Button('Получить данные', id=f'get-data-button-{type_page}'),
                            dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        card_table(
            f'result-table-{type_page}',
            "Детские профосмотры: свод по маршруту (ПН1 / ДС2)",
            25,
        ),
        toast(type_page),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    [
        Output(f'status-group-container-{type_page}', 'style'),
        Output(f'status-individual-container-{type_page}', 'style')
    ],
    [Input(f'status-selection-mode-{type_page}', 'value')]
)
def toggle_status_selection_mode_child_prof(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    return {'display': 'none'}, {'display': 'block'}


@app.callback(
    [
        Output(f'building-checklist-{type_page}', 'options'),
        Output(f'building-checklist-{type_page}', 'value')
    ],
    [Input(f'page-load-{type_page}', 'n_clicks')]
)
def update_building_options_child_prof(n_clicks):
    with engine.connect() as connection:
        building_query = connection.execute(text("""
            SELECT DISTINCT building
            FROM load_data_oms_data
            WHERE goal IN ('ПН1', 'ДС2')
              AND building IS NOT NULL
              AND TRIM(building) <> ''
              AND building <> '-'
            ORDER BY building
        """))
        building_names = [row[0] for row in building_query.fetchall()]

    if not building_names:
        with engine.connect() as connection:
            fallback = connection.execute(
                text("SELECT DISTINCT name_kvazar FROM organization_building ORDER BY name_kvazar")
            )
            building_names = [row[0] for row in fallback.fetchall()]

    building_options = [{"label": b, "value": b} for b in building_names]
    return building_options, [o["value"] for o in building_options]


@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month_child_prof(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


@app.callback(
    Output(f'selected-month-{type_page}', 'children'),
    Input(f'range-slider-month-{type_page}', 'value')
)
def update_selected_month_child_prof(selected_months):
    if selected_months is None:
        return "Выбранный месяц: Не выбран"

    start_month, end_month = selected_months
    start_month_name = months_labels.get(start_month, 'Неизвестно')
    end_month_name = months_labels.get(end_month, 'Неизвестно')
    if start_month_name == end_month_name:
        return f'Выбранный месяц: {start_month_name}'
    return f'Выбранный месяц: с {start_month_name} по {end_month_name}'


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [
        Input(f'range-slider-month-{type_page}', 'value'),
        Input(f'dropdown-year-{type_page}', 'value'),
        Input(f'current-month-name-{type_page}', 'children'),
    ]
)
def update_selected_period_child_prof(selected_months_range, selected_year, current_month_name):
    return get_selected_period(selected_months_range, selected_year, current_month_name)


@app.callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'loading-output-{type_page}', 'children'),
        Output(f'no-data-toast-{type_page}', 'is_open'),
    ],
    [Input(f'get-data-button-{type_page}', 'n_clicks')],
    [
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'building-checklist-{type_page}', 'value'),
        State(f'goal-checklist-{type_page}', 'value'),
        State(f'status-selection-mode-{type_page}', 'value'),
        State(f'status-group-radio-{type_page}', 'value'),
        State(f'status-individual-dropdown-{type_page}', 'value'),
        State(f'range-slider-month-{type_page}', 'value'),
    ],
)
def update_table_child_prof(n_clicks, *state_values):
    """
    Dash передаёт 1 Input + N State. Через *state_values избегаем рассинхрона
    (например, после reload), если число State когда-то отличалось.
    """
    if n_clicks is None:
        raise exceptions.PreventUpdate

    if len(state_values) == 7:
        (
            selected_year,
            selected_buildings,
            selected_goals,
            status_mode,
            selected_status_group,
            selected_individual_statuses,
            selected_months_range,
        ) = state_values
    elif len(state_values) == 6:
        (
            selected_year,
            selected_buildings,
            status_mode,
            selected_status_group,
            selected_individual_statuses,
            selected_months_range,
        ) = state_values
        selected_goals = ['ПН1', 'ДС2']
    else:
        raise exceptions.PreventUpdate

    if not selected_goals:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    if status_mode == 'group':
        if selected_status_group is None:
            selected_status_values = status_groups['Все статусы']
        else:
            selected_status_values = status_groups[selected_status_group]
    else:
        selected_status_values = selected_individual_statuses if selected_individual_statuses else []

    if not selected_status_values:
        selected_status_values = ['2']

    selected_status_tuple = tuple(selected_status_values)

    if not selected_buildings:
        try:
            with engine.connect() as connection:
                building_query = connection.execute(text("""
                    SELECT DISTINCT building FROM load_data_oms_data
                    WHERE goal IN ('ПН1', 'ДС2')
                      AND building IS NOT NULL AND TRIM(building) <> '' AND building <> '-'
                """))
                selected_buildings = [row[0] for row in building_query.fetchall()]
                if not selected_buildings:
                    building_query = connection.execute(
                        text("SELECT DISTINCT name_kvazar FROM organization_building")
                    )
                    selected_buildings = [row[0] for row in building_query.fetchall()]
                if not selected_buildings:
                    selected_buildings = ['ГП1']
        except Exception:
            selected_buildings = ['ГП1']

    if selected_months_range:
        try:
            report_months = list(range(
                int(selected_months_range[0]),
                int(selected_months_range[1]) + 1,
            ))
        except (TypeError, ValueError, IndexError):
            report_months = list(range(1, 13))
    else:
        report_months = list(range(1, 13))

    if not report_months:
        report_months = list(range(1, 13))

    if not selected_year:
        selected_year = datetime.now().year

    try:
        sql_query = sql_child_prof_exams_detail(selected_buildings)
        bind_params = {
            'goal_list': tuple(selected_goals),
            'report_year': int(selected_year),
            'report_months': tuple(report_months),
            'status_list': selected_status_tuple,
            'building_list': tuple(selected_buildings) if selected_buildings else tuple(['ГП1']),
        }
        columns, data = TableUpdater.query_to_df(engine, sql_query, bind_params)
        if len(data) == 0:
            return [], [], loading_output, True
        return columns, data, loading_output, False
    except Exception:
        return [], [], loading_output, True
