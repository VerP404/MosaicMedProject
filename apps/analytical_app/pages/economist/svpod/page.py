from datetime import datetime
import time
from functools import lru_cache

from dash import html, dcc, Output, Input, State, ALL, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, update_buttons, filter_months, \
    get_current_reporting_month, get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors, get_departments_by_doctor, \
    get_doctor_details, filter_inogorod, filter_sanction, filter_amount_null, date_picker, filter_report_type, \
    filter_status, status_groups
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.svpod.query import sql_query_rep, get_filter_conditions, sql_query_svpod_details, get_cumulative_report_for_all_groups, sql_query_indicators, sql_query_indicators_details, clear_cache, get_groups_for_indicators_report, get_plan_by_months_for_group, sql_query_plans
import pandas as pd
from apps.analytical_app.query_executor import engine

type_page = "econ-sv-pod"
type_page_indicators = "econ-sv-pod-indicators"


def get_level_options(parent_id=None):
    """Возвращает список опций для выбора уровня."""
    if parent_id is None:
        query = "SELECT DISTINCT id, name FROM plan_groupindicators WHERE parent_id IS NULL"
    else:
        query = f"SELECT id, name FROM plan_groupindicators WHERE parent_id = {parent_id}"
    levels = pd.read_sql(query, engine)
    return [{'label': level['name'], 'value': level['id']} for _, level in levels.iterrows()]


# Кэшированная функция для SQL-запроса индикаторов
@lru_cache(maxsize=64)
def get_cached_indicators_query(selected_year, months_placeholder, inogorod, sanction, amount_null, 
                               building_ids_tuple, department_ids_tuple, value_profile_tuple, selected_doctor_ids_tuple,
                               start_date_input_formatted, end_date_input_formatted,
                               start_date_treatment_formatted, end_date_treatment_formatted,
                               selected_status_tuple, cache_key):
    """Кэшированный результат SQL-запроса для ускорения повторных запросов"""
    # Преобразуем кортежи обратно в списки для передачи в SQL-функции
    building_ids = list(building_ids_tuple) if building_ids_tuple else None
    department_ids = list(department_ids_tuple) if department_ids_tuple else None
    value_profile = list(value_profile_tuple) if value_profile_tuple else None
    selected_doctor_ids = list(selected_doctor_ids_tuple) if selected_doctor_ids_tuple else None
    
    return sql_query_indicators(
        selected_year,
        months_placeholder,
        inogorod, sanction, amount_null,
        building_ids, department_ids,
        value_profile,
        selected_doctor_ids,
        start_date_input_formatted, end_date_input_formatted,
        start_date_treatment_formatted, end_date_treatment_formatted,
        status_list=selected_status_tuple
    )


# Контент для основной вкладки (текущий отчет)
current_report_tab = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row([
                                dbc.Col(update_buttons(type_page), width=2),
                                dbc.Col(filter_years(type_page), width=1),
                                dbc.Col(dbc.Alert(
                                    "Отобраны талоны: без санкций, местные (по полису ОМС), сумма талона не равна 0",
                                    color="primary"), width=4),
                                dbc.Col(
                                    dbc.Alert(
                                        [
                                            html.P("Примененные фильтры:", style={"margin-bottom": "5px"}),
                                            html.Div(id=f"applied-filters-{type_page}", style={"margin-top": "10px"})
                                        ],
                                        color="warning"
                                    ),
                                    width=4
                                ),
                            ]),
                            dbc.Row([
                                html.Div(id='dropdown-container', children=[
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id={'type': 'dynamic-dropdown', 'index': 0},
                                            options=[],
                                            placeholder="Выберите уровень 1",
                                            value=None
                                        ),
                                        width=3
                                    ),
                                ]),
                            ]),
                            dbc.Row([
                                dbc.Col(
                                    [
                                        html.Label("Режим:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                        dcc.Dropdown(
                                            id=f'mode-toggle-{type_page}',
                                            options=[
                                                {'label': 'Объемы', 'value': 'volumes'},
                                                {'label': 'Финансы', 'value': 'finance'}
                                            ],
                                            value='volumes',
                                            clearable=False,
                                            style={"width": "100%"}
                                        ),
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Уникальные пациенты:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                        dbc.Checkbox(
                                            id=f'unique-toggle-{type_page}',
                                            label="Включить",
                                            value=False,
                                            className="mt-2"
                                        ),
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=f'month-selector-{type_page}',
                                        options=[
                                            {'label': 'Январь', 'value': 1},
                                            {'label': 'Февраль', 'value': 2},
                                            {'label': 'Март', 'value': 3},
                                            {'label': 'Апрель', 'value': 4},
                                            {'label': 'Май', 'value': 5},
                                            {'label': 'Июнь', 'value': 6},
                                            {'label': 'Июль', 'value': 7},
                                            {'label': 'Август', 'value': 8},
                                            {'label': 'Сентябрь', 'value': 9},
                                            {'label': 'Октябрь', 'value': 10},
                                            {'label': 'Ноябрь', 'value': 11},
                                            {'label': 'Декабрь', 'value': 12}
                                        ],
                                        placeholder="Выберите месяц",
                                        value=None
                                    ),
                                    width=2
                                )
                            ], style={'margin-bottom': '10px'})
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        dbc.Row([
            dbc.Col([
                html.Div(id=f'loading-status-{type_page}', style={'text-align': 'center', 'margin': '10px 0'}),
            ], width=12)
        ]),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "Данные", column_selectable='multi'),
        dcc.Store(id=f'selected-data-{type_page}'),
        # Таблица детализации
        dbc.Card([
            dbc.CardHeader("Детализация по талонам"),
            dbc.CardBody([
                html.Div(id=f'details-title-{type_page}', style={"fontWeight": "bold", "marginBottom": "10px"}),
                # Кнопка детализации
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Детализация",
                            id=f'details-button-{type_page}',
                            color="primary",
                            size="sm",
                            disabled=True,
                            className="mb-3"
                        ), width="auto"
                    )
                ]),
                card_table(f'details-table-{type_page}', "Детали", page_size=20)
            ])
        ], className="mt-3", style={
            "width": "100%",
            "padding": "0rem",
            "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
            "border-radius": "10px"
        })
    ],
    style={"padding": "0rem"}
)

# Контент для вкладки "Нарастающе по всем показателям"
cumulative_report_tab = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row([
                                dbc.Col(
                                    dbc.Button(
                                        "Сформировать отчет",
                                        id=f'generate-cumulative-{type_page}',
                                        color="primary",
                                        className="me-2"
                                    ),
                                    width=2
                                ),
                                dbc.Col(filter_years(f'{type_page}-cumulative'), width=1),
                                dbc.Col(
                                    [
                                        html.Label("Отчетный месяц:", style={"font-weight": "bold", "margin-right": "5px"}),
                                        dcc.Dropdown(
                                            id=f'reporting-month-cumulative-{type_page}',
                                            options=[
                                                {'label': f'{i} месяц', 'value': i} for i in range(1, 13)
                                            ],
                                            value=None,
                                            placeholder="Авто (по дате)",
                                            clearable=True,
                                            style={"width": "100%"}
                                        ),
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Тип отчета:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                        dcc.Dropdown(
                                            id=f'report-type-toggle-cumulative-{type_page}',
                                            options=[
                                                {'label': 'По месяцам', 'value': 'months'},
                                                {'label': 'Нарастающе', 'value': 'cumulative'}
                                            ],
                                            value='cumulative',
                                            clearable=False,
                                            style={"width": "100%"}
                                        ),
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Режим:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                        dcc.Dropdown(
                                            id=f'mode-toggle-cumulative-{type_page}',
                                            options=[
                                                {'label': 'Объемы', 'value': 'volumes'},
                                                {'label': 'Финансы', 'value': 'finance'}
                                            ],
                                            value='volumes',
                                            clearable=False,
                                            style={"width": "100%"}
                                        ),
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Тип оплаты:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                        dcc.Dropdown(
                                            id=f'payment-type-toggle-cumulative-{type_page}',
                                            options=[
                                                {'label': 'Предъявленные', 'value': 'presented'},
                                                {'label': 'Предъявленные 2,3', 'value': 'presented_2_3'},
                                                {'label': 'Оплаченные', 'value': 'paid'}
                                            ],
                                            value='presented',
                                            clearable=False,
                                            style={"width": "100%"}
                                        ),
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Уникальные пациенты:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                        dbc.Checkbox(
                                            id=f'unique-toggle-cumulative-{type_page}',
                                            label="Включить",
                                            value=False,
                                            className="mt-2"
                                        ),
                                    ],
                                    width=2
                                ),
                            ]),
                            dbc.Row([
                                dbc.Col(
                                    dbc.Alert(
                                        "Формируется отчет нарастающим итогом по всем показателям из базы данных",
                                        color="info"
                                    ),
                                    width=12
                                )
                            ]),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        dbc.Row([
            dbc.Col([
                html.Div(id=f'loading-status-cumulative-{type_page}', style={'text-align': 'center', 'margin': '10px 0'}),
            ], width=12)
        ]),
        dcc.Loading(id=f'loading-cumulative-{type_page}', type='default'),
        card_table(f'cumulative-table-{type_page}', "Отчет нарастающим итогом по всем показателям", column_selectable='multi'),
    ],
    style={"padding": "0rem"}
)

# Контент для вкладки "Выбранные индикаторы"
indicators_tab = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page_indicators), width=2),
                                    dbc.Col(filter_years(type_page_indicators), width=1),
                                    dbc.Col(filter_report_type(type_page_indicators), width=2),
                                    dbc.Col(filter_inogorod(type_page_indicators), width=2),
                                    dbc.Col(filter_sanction(type_page_indicators), width=2),
                                    dbc.Col(filter_amount_null(type_page_indicators), width=2),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(filter_months(type_page_indicators), width=12),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Label("Выберите дату", id=f'label-date-{type_page_indicators}',
                                                                   style={'font-weight': 'bold', 'display': 'none'}),
                                                        width="auto"
                                                    ),
                                                    dbc.Col(date_picker(f'input-{type_page_indicators}'), width=4,
                                                            id=f'col-input-{type_page_indicators}', style={'display': 'none'}),
                                                    dbc.Col(date_picker(f'treatment-{type_page_indicators}'), width=4,
                                                            id=f'col-treatment-{type_page_indicators}', style={'display': 'none'}),
                                                ],
                                                align="center",
                                                style={"display": "flex", "align-items": "center",
                                                       "margin-bottom": "10px"}
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_building(type_page_indicators), width=6),
                                    dbc.Col(filter_department(type_page_indicators), width=6),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_profile(type_page_indicators), width=6),
                                    dbc.Col(filter_doctor(type_page_indicators), width=6),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_status(type_page_indicators), width=6),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(html.Div(id=f'selected-doctor-{type_page_indicators}', className='filters-label',
                                                     style={'display': 'none'}), width=9),
                                    dbc.Col(html.Div(id=f'selected-period-{type_page_indicators}', className='filters-label',
                                                     style={'display': 'none'}), width=3)
                                ]
                            ),
                            html.Div(id=f'current-month-name-{type_page_indicators}', className='filters-label'),
                            html.Div(
                                id=f'selected-filters-{type_page_indicators}',
                                className='selected-filters-block',
                                style={'margin': '10px', 'padding': '10px', 'border': '1px solid #ccc',
                                       'border-radius': '5px'}
                            ),

                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
         # Улучшенная индикация загрузки с прогресс-баром
         dbc.Row([
             dbc.Col([
                 dbc.Progress(
                     id=f'progress-bar-{type_page_indicators}',
                     value=0,
                     striped=True,
                     animated=True,
                     style={'display': 'none'}
                 ),
                 html.Div(id=f'loading-status-{type_page_indicators}', style={'text-align': 'center', 'margin': '10px 0'}),
             ], width=12)
         ]),
         dcc.Loading(
             id=f'loading-output-{type_page_indicators}', 
             type='default',
             children=[card_table(f'result-table1-{type_page_indicators}', "Индикаторные показатели", page_size=25, 
                                 style_cell_conditional=[
                                     {'if': {'column_id': 'type'}, 'width': '20%'},
                                     {'if': {'column_id': 'План 1/12 (количество)'}, 'width': '8%'},
                                     {'if': {'column_id': 'План 1/12 (сумма)'}, 'width': '8%'},
                                     {'if': {'column_id': 'План (количество)'}, 'width': '8%'},
                                     {'if': {'column_id': 'План (сумма)'}, 'width': '8%'},
                                     {'if': {'column_id': 'К-во'}, 'width': '8%'},
                                     {'if': {'column_id': 'Сумма'}, 'width': '8%'},
                                     {'if': {'column_id': 'Условия фильтра'}, 'width': '32%'}
                                 ])]
         ),
         # Таблица детализации
         dbc.Card([
             dbc.CardHeader("Детализация по талонам"),
             dbc.CardBody([
                 html.Div(id=f'details-title-{type_page_indicators}', style={"fontWeight": "bold", "marginBottom": "10px"}),
                 # Кнопка детализации
                 dbc.Row([
                     dbc.Col(
                         dbc.Button(
                             "Детализация",
                             id=f'details-button-{type_page_indicators}',
                             color="primary",
                             size="sm",
                             disabled=True,
                             className="mb-3"
                         ), width="auto"
                     )
                 ]),
                 card_table(f'details-table-{type_page_indicators}', "Детали", page_size=20)
             ])
         ], className="mt-3", style={
             "width": "100%",
             "padding": "0rem",
             "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
             "border-radius": "10px"
         })
    ],
    style={"padding": "0rem"}
)


type_page_plans = "econ-sv-pod-plans"

# Контент для вкладки "Планы"
plans_tab = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row([
                                dbc.Col(
                                    dbc.Button(
                                        "Обновить",
                                        id=f'update-button-{type_page_plans}',
                                        color="primary",
                                        className="me-2"
                                    ),
                                    width=2
                                ),
                                dbc.Col(filter_years(type_page_plans), width=2),
                            ]),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                )
            )
        ),
        dcc.Loading(
            id=f'loading-output-{type_page_plans}',
            type='default',
            children=[card_table(f'plans-table-{type_page_plans}', "Планы", page_size=50, 
                                style_cell_conditional=[
                                    {'if': {'column_id': 'Показатель'}, 'width': '30%'},
                                    {'if': {'column_id': 'Итого'}, 'width': '5%'},
                                    {'if': {'column_id': '1'}, 'width': '5%'},
                                    {'if': {'column_id': '2'}, 'width': '5%'},
                                    {'if': {'column_id': '3'}, 'width': '5%'},
                                    {'if': {'column_id': '4'}, 'width': '5%'},
                                    {'if': {'column_id': '5'}, 'width': '5%'},
                                    {'if': {'column_id': '6'}, 'width': '5%'},
                                    {'if': {'column_id': '7'}, 'width': '5%'},
                                    {'if': {'column_id': '8'}, 'width': '5%'},
                                    {'if': {'column_id': '9'}, 'width': '5%'},
                                    {'if': {'column_id': '10'}, 'width': '5%'},
                                    {'if': {'column_id': '11'}, 'width': '5%'},
                                    {'if': {'column_id': '12'}, 'width': '5%'},
                                ])]
        )
    ],
    style={"padding": "0rem"}
)


# Основной layout с вкладками
economist_sv_pod = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(
                    label="Подробно по индикатору",
                    tab_id=f"tab-current-{type_page}",
                    children=current_report_tab
                ),
                dbc.Tab(
                    label="Сводная по индикаторам",
                    tab_id=f"tab-cumulative-{type_page}",
                    children=cumulative_report_tab
                ),
                dbc.Tab(
                    label="Выбранные индикаторы",
                    tab_id=f"tab-indicators-{type_page}",
                    children=indicators_tab
                ),
                dbc.Tab(
                    label="Планы",
                    tab_id=f"tab-plans-{type_page}",
                    children=plans_tab
                ),
            ],
            active_tab=f"tab-current-{type_page}",
            id=f"tabs-{type_page}"
        )
    ],
    style={"padding": "0rem"}
)


@app.callback(
    Output(f'sum-result-result-table1-{type_page}', 'children'),
    Input(f'sum-button-result-table1-{type_page}', 'n_clicks'),
    State(f'result-table1-{type_page}', 'derived_virtual_data'),
    State(f'result-table1-{type_page}', 'selected_cells'),
    State(f'mode-toggle-{type_page}', 'value')
)
def calculate_sum_and_count(n_clicks, rows, selected_cells, mode):
    if n_clicks is None:
        raise PreventUpdate

    if rows is None or not selected_cells:
        return "Нет данных или не выбраны ячейки для подсчета."

    total_sum = 0
    count = 0
    for cell in selected_cells:
        row_idx = cell['row']
        col_id = cell['column_id']
        value = rows[row_idx].get(col_id, 0)
        if isinstance(value, (int, float)):
            total_sum += value
            count += 1

    if mode == 'finance':
        total_sum = f"{total_sum:,.2f}".replace(",", " ")
    else:
        total_sum = f"{int(total_sum):,}".replace(",", " ")
    return f"Количество: {count}, Сумма: {total_sum}"


@app.callback(
    Output('dropdown-container', 'children'),
    Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
)
def display_dynamic_dropdowns(values):
    dropdowns = []
    level = 0
    options = get_level_options()
    value = values[0] if values else None

    dropdown = dbc.Col(
        dcc.Dropdown(
            id={'type': 'dynamic-dropdown', 'index': level},
            options=options,
            placeholder="Выберите уровень 1",
            value=value
        ),
        width=3
    )
    dropdowns.append(dropdown)

    while True:
        if value is None:
            break
        options = get_level_options(value)
        if not options:
            break
        level += 1
        value = values[level] if len(values) > level else None
        dropdown = dbc.Col(
            dcc.Dropdown(
                id={'type': 'dynamic-dropdown', 'index': level},
                options=options,
                placeholder=f"Выберите уровень {level + 1}",
                value=value
            ),
            width=3
        )
        dropdowns.append(dropdown)

    return dropdowns


def fetch_plan_data(selected_level, year, mode='volumes'):
    """Получение плановых данных (помесячно) из БД."""
    plan_field = "quantity" if mode == 'volumes' else "amount"
    query = text(f"""
        SELECT mp.month, SUM(mp.{plan_field}) AS plan
        FROM plan_monthlyplan AS mp
        INNER JOIN plan_annualplan AS ap ON mp.annual_plan_id = ap.id
        WHERE ap.group_id = :selected_level AND ap.year = :year
        GROUP BY mp.month
        ORDER BY mp.month
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"selected_level": selected_level, "year": year}).mappings()
        plan_data = {row["month"]: row["plan"] for row in result}
    return plan_data


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'applied-filters-{type_page}', 'children'),
     Output(f'loading-status-{type_page}', 'children'),
     ],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'mode-toggle-{type_page}', 'value'),
    State(f'unique-toggle-{type_page}', 'value'),
    State(f'dropdown-year-{type_page}', 'value'),
    State({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
    State(f'month-selector-{type_page}', 'value')
)
def update_table_with_plan_and_balance(n_clicks,
                                       mode,
                                       unique_flag,
                                       selected_year,
                                       selected_levels,
                                       selected_month):
    if n_clicks is None:
        raise PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    selected_levels = [lvl for lvl in selected_levels if lvl is not None]
    if not selected_levels:
        raise PreventUpdate

    selected_level = selected_levels[-1]
    filter_conditions = get_filter_conditions([selected_level], selected_year)

    unique = unique_flag if unique_flag is not None else False

    # Загружаем фактические данные с измерением времени
    start_time = time.time()
    fact_columns, fact_data_list = TableUpdater.query_to_df(
        engine,
        sql_query_rep(selected_year,
                      group_id=[selected_level],
                      filter_conditions=filter_conditions,
                      mode=mode,
                      unique_flag=unique)
    )
    execution_time = time.time() - start_time
    # Добавляем общую сумму "исправлено"
    total_ispravleno_all_months = sum(row.get("исправлено", 0) or 0 for row in fact_data_list)
    # Превращаем список словарей fact_data_list в dict по ключу "month"
    fact_dict = {}
    for row in fact_data_list:
        m = row["month"]
        fact_dict[m] = row

    # Загружаем плановые данные
    plan_data = fetch_plan_data(selected_level, selected_year, mode)

    today = datetime.today()
    default_month = today.month - 1 if today.day <= 5 else today.month
    current_day = today.day
    current_month = selected_month if selected_month is not None else default_month

    # Формируем список месяцев для отображения: от 1 до current_month
    months_to_show = list(range(1, current_month + 1))

    # Создаём «заготовку» для итоговой таблицы.
    # Для каждого месяца делаем словарь со всеми нужными полями, заполненными нулями.
    # Потом при наличии данных - перезапишем.
    fact_data = []
    for m in months_to_show:
        # Базовая заготовка на случай, если нет данных вообще
        row_template = {
            "month": m,
            "План 1/12": 0,
            "Входящий остаток": 0,
            "План": 0,
            "Факт": 0,
            "%": 0,
            "Остаток": 0,
            "новые": 0,
            "в_тфомс": 0,
            "оплачено": 0,
            "исправлено": 0,
            "отказано": 0,
            "отменено": 0,
        }

        # Если в fact_dict есть запись для этого месяца, берём данные
        if m in fact_dict:
            source = fact_dict[m]
            # mode='finance' -> суммы, mode='volumes' -> кол-во
            row_template["новые"] = source.get("новые", 0) or 0
            row_template["в_тфомс"] = source.get("в_тфомс", 0) or 0
            row_template["оплачено"] = source.get("оплачено", 0) or 0
            row_template["исправлено"] = source.get("исправлено", 0) or 0
            row_template["отказано"] = source.get("отказано", 0) or 0
            row_template["отменено"] = source.get("отменено", 0) or 0

        # Подставляем план, если он есть
        row_template["План 1/12"] = plan_data.get(m, 0)

        fact_data.append(row_template)

    # Теперь пробегаемся по fact_data и рассчитываем Факт, Остаток, % и т.д.
    incoming_balance = 0
    for row in fact_data:
        m = row["month"]
        row["Входящий остаток"] = incoming_balance
        row["План"] = (row["План 1/12"] or 0) + (row["Входящий остаток"] or 0)

        # Расчёт «Факт» по текущему дню.
        manually_selected = selected_month is not None and m == selected_month

        # Расчёт «Факт» по текущему дню.
        if manually_selected:
            # Если пользователь выбрал месяц, то как раньше — только оплаченные
            row["Факт"] = row.get("оплачено", 0)
        else:
            if m < current_month - 1:
                row["Факт"] = row.get("оплачено", 0)
            elif m == current_month - 1:
                if current_day <= 10:
                    # Используем total_ispravleno_all_months вместо row["исправлено"]
                    row["Факт"] = (
                            row.get("новые", 0) +
                            row.get("в_тфомс", 0) +
                            row.get("оплачено", 0) +
                            total_ispravleno_all_months
                    )
                else:
                    row["Факт"] = row.get("оплачено", 0)
            elif m == current_month:
                # Для текущего месяца тоже используем total_ispravleno_all_months
                row["Факт"] = (
                        row.get("новые", 0) +
                        row.get("в_тфомс", 0) +
                        row.get("оплачено", 0) +
                        total_ispravleno_all_months
                )
            else:
                row["Факт"] = 0

        if row["План"] > 0:
            row["%"] = round(row["Факт"] / row["План"] * 100, 1)
        else:
            row["%"] = 0

        row["Остаток"] = (row["План"] or 0) - (row["Факт"] or 0)
        incoming_balance = row["Остаток"]

    # Добавим строку «Нарастающе»
    if fact_data:
        total_plan_12 = sum(r["План 1/12"] for r in fact_data)
        total_fact = sum(r["Факт"] for r in fact_data)
        total_new = sum(r["новые"] for r in fact_data)
        total_tfoms = sum(r["в_тфомс"] for r in fact_data)
        total_oplacheno = sum(r["оплачено"] for r in fact_data)
        total_ispravleno = sum(r["исправлено"] for r in fact_data)
        total_otkazano = sum(r["отказано"] for r in fact_data)
        total_otmeneno = sum(r["отменено"] for r in fact_data)
        cumulative_row = {
            "month": "Нарастающе",
            "План 1/12": 0,
            "Входящий остаток": 0,
            "План": total_plan_12,
            "Факт": total_fact,
            "Остаток": fact_data[-1]["Остаток"],
            "%": round(total_fact / total_plan_12 * 100, 1) if total_plan_12 > 0 else 0,
            "новые": total_new,
            "в_тфомс": total_tfoms,
            "оплачено": total_oplacheno,
            "исправлено": total_ispravleno,
            "отказано": total_otkazano,
            "отменено": total_otmeneno,
        }
        fact_data.append(cumulative_row)

    # Добавим строку «Год» (1..12)
    year_plan = sum(plan_data.get(m, 0) for m in range(1, 13))
    if fact_data:
        total_fact_overall = sum(r["Факт"] for r in fact_data if isinstance(r["month"], int))
        year_row = {
            "month": "Год",
            "План 1/12": 0,
            "Входящий остаток": 0,
            "План": year_plan,
            "Факт": total_fact_overall,
            "Остаток": year_plan - total_fact_overall,
            "%": round(total_fact_overall / year_plan * 100, 1) if year_plan else 0,
            "новые": sum(r["новые"] for r in fact_data if isinstance(r["month"], int)),
            "в_тфомс": sum(r["в_тфомс"] for r in fact_data if isinstance(r["month"], int)),
            "оплачено": sum(r["оплачено"] for r in fact_data if isinstance(r["month"], int)),
            "исправлено": sum(r["исправлено"] for r in fact_data if isinstance(r["month"], int)),
            "отказано": sum(r["отказано"] for r in fact_data if isinstance(r["month"], int)),
            "отменено": sum(r["отменено"] for r in fact_data if isinstance(r["month"], int)),
        }
        fact_data.append(year_row)

    columns = [
        {"name": ["", "Месяц"], "id": "month"},
        {"name": ["Итог", "План"], "id": "План"},
        {"name": ["Итог", "Факт"], "id": "Факт"},
        {"name": ["Итог", "%"], "id": "%"},
        {"name": ["Итог", "Остаток"], "id": "Остаток"},
        {"name": ["Факт", "Новые"], "id": "новые"},
        {"name": ["Факт", "В ТФОМС"], "id": "в_тфомс"},
        {"name": ["Факт", "Оплачено"], "id": "оплачено"},
        {"name": ["Факт", "Исправлено"], "id": "исправлено"},
        {"name": ["Факт", "Отказано"], "id": "отказано"},
        {"name": ["Факт", "Отменено"], "id": "отменено"},
        {"name": ["План 1/12", "План 1/12"], "id": "План 1/12"},
        {"name": ["План 1/12", "Входящий остаток"], "id": "Входящий остаток"},
    ]

    # Формируем статус загрузки
    if execution_time < 1:
        time_text = f"{execution_time*1000:.0f}мс"
    else:
        time_text = f"{execution_time:.1f}с"
    
    # Подсчитываем количество записей (исключаем строки "Нарастающе" и "Год")
    record_count = len([r for r in fact_data if isinstance(r.get("month"), int)])
    status_text = f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"

    return columns, fact_data, loading_output, filter_conditions, status_text


# Callback для активации кнопки детализации при выборе строки
@app.callback(
    Output(f'details-button-{type_page}', 'disabled'),
    Input(f'result-table1-{type_page}', 'active_cell')
)
def update_details_button_state(active_cell):
    if not active_cell:
        return True
    
    # Проверяем, что выбрана допустимая колонка для детализации
    column_id = active_cell.get('column_id')
    allowed_columns = ['Факт', 'новые', 'в_тфомс', 'оплачено', 'исправлено', 'отказано', 'отменено']
    
    return column_id not in allowed_columns


# Callback для отображения детализации
@app.callback(
    [
        Output(f'details-title-{type_page}', 'children'),
        Output(f'details-table-{type_page}', 'columns'),
        Output(f'details-table-{type_page}', 'data')
    ],
    [
        Input(f'details-button-{type_page}', 'n_clicks')
    ],
    [
        State(f'result-table1-{type_page}', 'data'),
        State(f'result-table1-{type_page}', 'active_cell'),
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'month-selector-{type_page}', 'value'),
        State({'type': 'dynamic-dropdown', 'index': ALL}, 'value')
    ]
)
def show_svpod_details(n_clicks, table_data, active_cell, selected_year, selected_month, 
                      selected_levels):
    if not n_clicks or not active_cell or not table_data:
        return '', [], []
    
    # Получаем данные выбранной строки и колонки
    row_data = table_data[active_cell.get('row')]
    column_id = active_cell.get('column_id')
    month_name = row_data.get('month')
    
    if not month_name or not selected_year:
        return 'Ошибка: не удалось определить параметры для детализации', [], []
    
    # Проверяем, что выбрана допустимая колонка для детализации
    allowed_columns = ['Факт', 'новые', 'в_тфомс', 'оплачено', 'исправлено', 'отказано', 'отменено']
    if column_id not in allowed_columns:
        return f'Детализация доступна только для колонок: {", ".join(allowed_columns)}', [], []
    
    try:
        # Фильтруем None значения из selected_levels
        selected_levels = [lvl for lvl in selected_levels if lvl is not None]
        
        if not selected_levels:
            return 'Ошибка: не выбрана группа показателей', [], []
        
        # Берем последний выбранный уровень (самый глубокий)
        selected_level = selected_levels[-1]
        group_ids = [selected_level]
        
        # Получаем условия фильтрации
        filter_conditions = get_filter_conditions(group_ids, selected_year)
        
        # Определяем месяц для фильтрации (изначально)
        filter_month = selected_month if selected_month is not None else None
        
        # Если месяц не выбран в dropdown, но есть месяц в строке, используем его
        if filter_month is None and month_name:
            # Проверяем, является ли month_name числом (int или строка с цифрами)
            if isinstance(month_name, int):
                filter_month = month_name
            elif isinstance(month_name, str) and month_name.isdigit():
                filter_month = int(month_name)
        
        # Определяем статусы для фильтрации в зависимости от выбранной колонки
        status_filter = None
        if column_id == 'Факт':
            # Для "Факт" показываем записи, которые учитываются в расчете факта
            # Логика должна соответствовать расчету в основном запросе
            if month_name == "Нарастающе" or month_name == "Год":
                # Для нарастающих и годовых показателей "Факт" = сумма "Факт" по месяцам
                # Каждый месяц имеет свою логику расчета "Факт"
                # Создаем сложный запрос, который повторяет логику расчета для каждого месяца
                from datetime import datetime
                today = datetime.today()
                current_month = today.month
                current_day = today.day
                
                # Создаем условия для каждого месяца точно как в расчете "Факт"
                month_conditions = []
                for m in range(1, 13):
                    if m < current_month - 1:
                        # Прошлые месяцы: только оплаченные
                        month_conditions.append(f"(report_month_number = {m} AND status = '3')")
                    elif m == current_month - 1:
                        if current_day <= 10:
                            # Предыдущий месяц, день <= 10: новые+в_тфомс+оплачено+исправлено
                            # Исправлено берется из total_ispravleno_all_months (за ВСЕ месяцы)
                            month_conditions.append(f"(report_month_number = {m} AND status IN ('1', '2', '3'))")
                            # Добавляем исправленные записи за ВСЕ месяцы для предыдущего месяца
                            month_conditions.append(f"(status IN ('6', '8'))")
                        else:
                            # Предыдущий месяц, день > 10: только оплаченные
                            month_conditions.append(f"(report_month_number = {m} AND status = '3')")
                    elif m == current_month:
                        # Текущий месяц: новые+в_тфомс+оплачено+исправлено
                        # Исправлено берется из total_ispravleno_all_months (за ВСЕ месяцы)
                        month_conditions.append(f"(report_month_number = {m} AND status IN ('1', '2', '3'))")
                        # Добавляем исправленные записи за ВСЕ месяцы для текущего месяца
                        month_conditions.append(f"(status IN ('6', '8'))")
                    # Будущие месяцы не учитываются (Факт = 0)
                
                # Объединяем условия через OR
                if month_conditions:
                    # Передаем специальный параметр для сложной логики
                    status_filter = f"COMPLEX_LOGIC:{':'.join(month_conditions)}"
                else:
                    status_filter = ['3']  # Fallback
                
                # Убираем фильтр по месяцу для нарастающих показателей
                filter_month = None
            else:
                # Для конкретного месяца - логика зависит от того, выбран ли месяц вручную
                if selected_month is not None:
                    # Если пользователь выбрал месяц вручную - только оплаченные
                    status_filter = ['3']  # Только оплачено
                else:
                    # Если месяц выбран автоматически - зависит от текущего месяца
                    from datetime import datetime
                    today = datetime.today()
                    current_month = today.month
                    # Определяем номер месяца
                    if isinstance(month_name, int):
                        month_num = month_name
                    elif isinstance(month_name, str) and month_name.isdigit():
                        month_num = int(month_name)
                    else:
                        month_num = None
                    
                    if month_num and month_num < current_month - 1:
                        # Для прошлых месяцев - только оплаченные
                        status_filter = ['3']
                    elif month_num and (month_num == current_month - 1 or month_num == current_month):
                        # Для текущего и предыдущего месяца - новые + в_тфомс + оплачено + исправлено
                        status_filter = ['1', '2', '3', '6', '8']
                    else:
                        # По умолчанию - только оплаченные
                        status_filter = ['3']
        elif column_id == 'новые':
            status_filter = ['1']  # Новые талоны
        elif column_id == 'в_тфомс':
            status_filter = ['2']  # В ТФОМС
        elif column_id == 'оплачено':
            status_filter = ['3']  # Оплачено
        elif column_id == 'исправлено':
            status_filter = ['6', '8']  # Исправлено
        elif column_id == 'отказано':
            status_filter = ['5', '7', '12']  # Отказано
        elif column_id == 'отменено':
            status_filter = ['0', '13', '17']  # Отменено
        
        # Выполняем запрос детализации
        sql_query = sql_query_svpod_details(selected_year, filter_month, group_ids, filter_conditions, status_filter)
        
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        # Формируем заголовок
        if month_name == "Нарастающе" or month_name == "Год":
            # Для нарастающих показателей добавляем пояснение
            title_text = f"Детализация по показателям за {month_name} {selected_year} - {column_id} (приблизительно)"
        else:
            title_text = f"Детализация по показателям за {month_name} {selected_year} - {column_id}"
        
        count_badge = dbc.Badge(
            f" {len(data)}",
            color="primary",
            pill=True,
            className="ms-2"
        )
        title = html.Span([title_text, count_badge])
        
        return title, columns, data
        
    except Exception as e:
        error_msg = f"Ошибка при получении детализации: {str(e)}"
        return error_msg, [], []


# Callback для формирования отчета нарастающе по всем показателям
@app.callback(
    [
        Output(f'cumulative-table-{type_page}', 'columns'),
        Output(f'cumulative-table-{type_page}', 'data'),
        Output(f'cumulative-table-{type_page}', 'style_cell_conditional'),
        Output(f'loading-cumulative-{type_page}', 'children'),
        Output(f'loading-status-cumulative-{type_page}', 'children'),
    ],
    Input(f'generate-cumulative-{type_page}', 'n_clicks'),
    State(f'dropdown-year-{type_page}-cumulative', 'value'),
    State(f'report-type-toggle-cumulative-{type_page}', 'value'),
    State(f'mode-toggle-cumulative-{type_page}', 'value'),
    State(f'payment-type-toggle-cumulative-{type_page}', 'value'),
    State(f'reporting-month-cumulative-{type_page}', 'value'),
    State(f'unique-toggle-cumulative-{type_page}', 'value')
)
def generate_cumulative_report(n_clicks, selected_year, report_type, mode, payment_type, reporting_month, unique_flag):
    if n_clicks is None:
        raise PreventUpdate
    
    if not selected_year:
        return [], [], [], html.Div(dbc.Alert("Выберите год", color="warning")), ""
    
    loading_output = html.Div([dcc.Loading(type="default")])
    
    # Стили для столбцов - делаем "Группа показателей" или "Месяц" шире
    style_cell_conditional = [
        {
            'if': {'column_id': 'Группа показателей'},
            'minWidth': '300px',
            'maxWidth': '400px',
            'width': '350px'
        },
        {
            'if': {'column_id': 'month'},
            'minWidth': '150px',
            'maxWidth': '200px',
            'width': '180px'
        }
    ]
    
    try:
        unique = unique_flag if unique_flag is not None else False
        mode = mode or 'volumes'
        report_type = report_type or 'cumulative'
        payment_type = payment_type or 'presented'
        
        # Определяем отчетный месяц
        today = datetime.today()
        default_month = today.month - 1 if today.day <= 5 else today.month
        current_reporting_month = reporting_month if reporting_month is not None else default_month
        
        # Измеряем время выполнения
        start_time = time.time()
        
        if report_type == 'cumulative':
            # Режим "Нарастающе" - показываем все группы показателей
            df = get_cumulative_report_for_all_groups(
                selected_year=selected_year,
                mode=mode,
                unique_flag=unique,
                reporting_month=current_reporting_month,
                payment_type=payment_type
            )
            
            if df.empty:
                execution_time = time.time() - start_time
                if execution_time < 1:
                    time_text = f"{execution_time*1000:.0f}мс"
                else:
                    time_text = f"{execution_time:.1f}с"
                status_text = f"Запрос выполнен за {time_text}. Найдено записей: 0"
                return [], [], [], html.Div(dbc.Alert("Нет данных для отображения", color="info")), status_text
            
            # Преобразуем DataFrame в список словарей
            data = []
            for _, row in df.iterrows():
                # Если выбран режим "Оплаченные", меняем Факт на только оплаченные
                if payment_type == 'paid':
                    fact_value = row["оплачено"]
                else:
                    fact_value = row["Факт"]
                
                percent = round(fact_value / row["План 1/12"] * 100, 1) if row["План 1/12"] > 0 else 0
                remainder = row["План 1/12"] - fact_value
                
                data.append({
                    "Группа показателей": row["Группа показателей"],
                    "План 1/12": row["План 1/12"],
                    "Факт": fact_value,
                    "%": percent,
                    "Остаток": remainder,
                    "новые": row["новые"],
                    "в_тфомс": row["в_тфомс"],
                    "оплачено": row["оплачено"],
                    "исправлено": row["исправлено"],
                    "отказано": row["отказано"],
                    "отменено": row["отменено"],
                })
            
            # Добавляем строку "Итого" для всех групп
            if data:
                total_plan = sum(r["План 1/12"] for r in data)
                total_fact = sum(r["Факт"] for r in data)
                total_percent = round(total_fact / total_plan * 100, 1) if total_plan > 0 else 0
                total_remainder = total_plan - total_fact
                
                data.append({
                    "Группа показателей": "Итого",
                    "План 1/12": total_plan,
                    "Факт": total_fact,
                    "%": total_percent,
                    "Остаток": total_remainder,
                    "новые": sum(r["новые"] for r in data if r["Группа показателей"] != "Итого"),
                    "в_тфомс": sum(r["в_тфомс"] for r in data if r["Группа показателей"] != "Итого"),
                    "оплачено": sum(r["оплачено"] for r in data if r["Группа показателей"] != "Итого"),
                    "исправлено": sum(r["исправлено"] for r in data if r["Группа показателей"] != "Итого"),
                    "отказано": sum(r["отказано"] for r in data if r["Группа показателей"] != "Итого"),
                    "отменено": sum(r["отменено"] for r in data if r["Группа показателей"] != "Итого"),
                })
            
            # Формируем колонки для таблицы
            columns = [
                {"name": "Группа показателей", "id": "Группа показателей"},
                {"name": ["Итог", "План"], "id": "План 1/12"},
                {"name": ["Итог", "Факт"], "id": "Факт"},
                {"name": ["Итог", "%"], "id": "%"},
                {"name": ["Итог", "Остаток"], "id": "Остаток"},
                {"name": ["Факт", "Новые"], "id": "новые"},
                {"name": ["Факт", "В ТФОМС"], "id": "в_тфомс"},
                {"name": ["Факт", "Оплачено"], "id": "оплачено"},
                {"name": ["Факт", "Исправлено"], "id": "исправлено"},
                {"name": ["Факт", "Отказано"], "id": "отказано"},
                {"name": ["Факт", "Отменено"], "id": "отменено"},
            ]
            
            execution_time = time.time() - start_time
            if execution_time < 1:
                time_text = f"{execution_time*1000:.0f}мс"
            else:
                time_text = f"{execution_time:.1f}с"
            
            # Подсчитываем количество записей (исключаем строку "Итого")
            record_count = len([r for r in data if r.get("Группа показателей") != "Итого"])
            status_text = f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"
        else:
            # Режим "По месяцам" - нужно получить группы и показать данные по месяцам для каждой
            from apps.analytical_app.pages.economist.svpod.query import get_groups_for_cumulative_report
            
            groups = get_groups_for_cumulative_report(selected_year)
            
            if groups.empty:
                execution_time = time.time() - start_time
                if execution_time < 1:
                    time_text = f"{execution_time*1000:.0f}мс"
                else:
                    time_text = f"{execution_time:.1f}с"
                status_text = f"Запрос выполнен за {time_text}. Найдено записей: 0"
                return [], [], [], html.Div(dbc.Alert("Нет данных для отображения", color="info")), status_text
            
            # Получаем данные по месяцам для каждой группы
            columns = [
                {"name": ["", "Группа показателей"], "id": "group_name"},
                {"name": ["", "Месяц"], "id": "month"},
                {"name": ["Итог", "План"], "id": "План"},
                {"name": ["Итог", "Факт"], "id": "Факт"},
                {"name": ["Итог", "%"], "id": "%"},
                {"name": ["Итог", "Остаток"], "id": "Остаток"},
                {"name": ["Факт", "Новые"], "id": "новые"},
                {"name": ["Факт", "В ТФОМС"], "id": "в_тфомс"},
                {"name": ["Факт", "Оплачено"], "id": "оплачено"},
                {"name": ["Факт", "Исправлено"], "id": "исправлено"},
                {"name": ["Факт", "Отказано"], "id": "отказано"},
                {"name": ["Факт", "Отменено"], "id": "отменено"},
                {"name": ["План 1/12", "План 1/12"], "id": "План 1/12"},
                {"name": ["План 1/12", "Входящий остаток"], "id": "Входящий остаток"},
            ]
            
            data = []
            today = datetime.today()
            default_month = today.month - 1 if today.day <= 5 else today.month
            current_day = today.day
            current_month = current_reporting_month
            
            for _, group_row in groups.iterrows():
                group_id = group_row['id']
                group_name = group_row['name']
                
                filter_conditions = get_filter_conditions([group_id], selected_year)
                fact_columns, fact_data_list = TableUpdater.query_to_df(
                    engine,
                    sql_query_rep(selected_year,
                                  group_id=[group_id],
                                  filter_conditions=filter_conditions,
                                  mode=mode,
                                  unique_flag=unique)
                )
                
                fact_dict = {}
                for row in fact_data_list:
                    m = row["month"]
                    fact_dict[m] = row
                
                plan_data = fetch_plan_data(group_id, selected_year, mode)
                total_ispravleno_all_months = sum(row.get("исправлено", 0) or 0 for row in fact_data_list)
                
                incoming_balance = 0
                group_data = []
                
                # Показываем только месяцы от 1 до отчетного месяца включительно
                for m in range(1, current_month + 1):
                    month_data = fact_dict.get(m, {})
                    
                    # Сохраняем входящий остаток ДО расчета текущего месяца
                    incoming_balance_for_month = incoming_balance if m > 1 else 0
                    
                    # Рассчитываем Факт в зависимости от режима и отчетного месяца
                    if payment_type == 'paid':
                        # Режим "Оплаченные" - только оплаченные (status = '3')
                        month_fact = month_data.get("оплачено", 0) or 0
                    elif payment_type == 'presented_2_3':
                        # Режим "Предъявленные 2,3" - статусы 2 и 3 (только для отчетного месяца)
                        if m == current_month:
                            # Для отчетного месяца: статусы 2 (в_тфомс) и 3 (оплачено)
                            month_fact = (month_data.get("в_тфомс", 0) or 0) + (month_data.get("оплачено", 0) or 0)
                        else:
                            # Для других месяцев: только оплаченные (статус 3)
                            month_fact = month_data.get("оплачено", 0) or 0
                    else:
                        # Режим "Предъявленные" - текущая логика
                        if m < current_month:
                            # Для месяцев < отчетного: только оплаченные (статус 3)
                            month_fact = month_data.get("оплачено", 0) or 0
                        elif m == current_month:
                            # Для отчетного месяца: новые+в_тфомс+оплачено+исправлено
                            month_fact = (
                                (month_data.get("новые", 0) or 0) +
                                (month_data.get("в_тфомс", 0) or 0) +
                                (month_data.get("оплачено", 0) or 0) +
                                total_ispravleno_all_months
                            )
                        else:
                            month_fact = 0
                    
                    month_plan_12 = plan_data.get(m, 0) or 0
                    month_plan = month_plan_12 + incoming_balance
                    month_remainder = month_plan - month_fact
                    incoming_balance = month_remainder  # Обновляем для следующего месяца
                    
                    percent = round(month_fact / month_plan * 100, 1) if month_plan > 0 else 0
                    
                    group_data.append({
                        "group_name": group_name if m == 1 else "",
                        "month": m,
                        "План": month_plan,
                        "Факт": month_fact,
                        "%": percent,
                        "Остаток": month_remainder,
                        "новые": month_data.get("новые", 0) or 0,
                        "в_тфомс": month_data.get("в_тфомс", 0) or 0,
                        "оплачено": month_data.get("оплачено", 0) or 0,
                        "исправлено": month_data.get("исправлено", 0) or 0,
                        "отказано": month_data.get("отказано", 0) or 0,
                        "отменено": month_data.get("отменено", 0) or 0,
                        "План 1/12": month_plan_12,
                        "Входящий остаток": incoming_balance_for_month,
                    })
                
                # Добавляем данные группы
                data.extend(group_data)
                
                # Добавляем строку "Итого" для группы
                if group_data:
                    # Суммируем План 1/12 за месяцы от 1 до отчетного (нарастающе)
                    total_plan_12_group = sum(r["План 1/12"] for r in group_data)
                    # Входящий остаток для строки "Итого" всегда 0 (начало года)
                    total_incoming_balance_group = 0
                    # Итого План = сумма План 1/12 за месяцы от 1 до отчетного (нарастающе)
                    total_plan_group = total_plan_12_group
                    # Итого Факт = сумма фактов за месяцы от 1 до отчетного (нарастающе)
                    total_fact_group = sum(r["Факт"] for r in group_data)
                    # Итого Остаток = Итого План - Итого Факт (нарастающе до отчетного месяца)
                    total_remainder_group = total_plan_group - total_fact_group
                    total_percent_group = round(total_fact_group / total_plan_group * 100, 1) if total_plan_group > 0 else 0
                    
                    data.append({
                        "group_name": f"Итого ({group_name})",
                        "month": "Итого",
                        "План": total_plan_group,
                        "Факт": total_fact_group,
                        "%": total_percent_group,
                        "Остаток": total_remainder_group,
                        "новые": sum(r["новые"] for r in group_data),
                        "в_тфомс": sum(r["в_тфомс"] for r in group_data),
                        "оплачено": sum(r["оплачено"] for r in group_data),
                        "исправлено": sum(r["исправлено"] for r in group_data),
                        "отказано": sum(r["отказано"] for r in group_data),
                        "отменено": sum(r["отменено"] for r in group_data),
                        "План 1/12": total_plan_12_group,
                        "Входящий остаток": total_incoming_balance_group,
                    })
            
            execution_time = time.time() - start_time
            if execution_time < 1:
                time_text = f"{execution_time*1000:.0f}мс"
            else:
                time_text = f"{execution_time:.1f}с"
            
            # Подсчитываем количество записей (только строки с числовыми значениями месяца)
            record_count = len([r for r in data if isinstance(r.get("month"), int)])
            status_text = f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"
        
        return columns, data, style_cell_conditional, loading_output, status_text
        
    except Exception as e:
        error_msg = f"Ошибка при формировании отчета: {str(e)}"
        return [], [], [], html.Div(dbc.Alert(error_msg, color="danger")), ""


# ========== Callbacks для вкладки "Выбранные индикаторы" ==========

@app.callback(
    [
        Output(f'status-group-container-{type_page_indicators}', 'style'),
        Output(f'status-individual-container-{type_page_indicators}', 'style')
    ],
    [Input(f'status-selection-mode-{type_page_indicators}', 'value')]
)
def toggle_status_selection_mode_indicators(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:  # mode == 'individual'
        return {'display': 'none'}, {'display': 'block'}


@app.callback(
    Output(f'sum-result-result-table1-{type_page_indicators}', 'children'),
    Input(f'sum-button-result-table1-{type_page_indicators}', 'n_clicks'),
    State(f'result-table1-{type_page_indicators}', 'derived_virtual_data'),
    State(f'result-table1-{type_page_indicators}', 'selected_cells')
)
def calculate_sum_and_count_indicators(n_clicks, rows, selected_cells):
    if n_clicks is None:
        raise PreventUpdate

    if rows is None or not selected_cells:
        return "Нет данных или не выбраны ячейки для подсчета."

    total_sum = 0
    count = 0
    for cell in selected_cells:
        row_idx = cell['row']
        col_id = cell['column_id']
        value = rows[row_idx].get(col_id, 0)
        if isinstance(value, (int, float)):
            total_sum += value
            count += 1

    total_sum_formatted = f"{total_sum:,.2f}".replace(",", " ")
    return f"Количество выбранных ячеек: {count}, Сумма значений: {total_sum}"


@app.callback(
    [
        Output(f'range-slider-month-{type_page_indicators}', 'style'),
        Output(f'date-picker-range-input-{type_page_indicators}', 'style'),
        Output(f'date-picker-range-treatment-{type_page_indicators}', 'style')
    ],
    [Input(f'dropdown-report-type-{type_page_indicators}', 'value')]
)
def toggle_filters_indicators(report_type):
    if report_type == 'month':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    elif report_type == 'initial_input':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}


@app.callback(
    [
        Output(f'col-input-{type_page_indicators}', 'style'),
        Output(f'col-treatment-{type_page_indicators}', 'style'),
    ],
    [Input(f'dropdown-report-type-{type_page_indicators}', 'value')]
)
def toggle_datepickers_indicators(report_type):
    if report_type == 'initial_input':
        return {'display': 'block'}, {'display': 'none'}
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@app.callback(
    Output(f'label-date-{type_page_indicators}', 'style'),
    [
        Input(f'dropdown-report-type-{type_page_indicators}', 'value'),
        Input(f'date-picker-range-input-{type_page_indicators}', 'start_date'),
        Input(f'date-picker-range-input-{type_page_indicators}', 'end_date'),
        Input(f'date-picker-range-treatment-{type_page_indicators}', 'start_date'),
        Input(f'date-picker-range-treatment-{type_page_indicators}', 'end_date')
    ]
)
def toggle_label_visibility_indicators(report_type, start_date_input, end_date_input, start_date_treatment, end_date_treatment):
    if report_type in ['initial_input', 'treatment'] and (
            start_date_input or end_date_input or start_date_treatment or end_date_treatment):
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output(f'current-month-name-{type_page_indicators}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month_indicators(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


@app.callback(
    [
        Output(f'dropdown-building-{type_page_indicators}', 'options'),
        Output(f'dropdown-department-{type_page_indicators}', 'options'),
        Output(f'dropdown-profile-{type_page_indicators}', 'options'),
        Output(f'dropdown-doctor-{type_page_indicators}', 'options')
    ],
    [
        Input(f'dropdown-building-{type_page_indicators}', 'value'),
        Input(f'dropdown-department-{type_page_indicators}', 'value'),
        Input(f'dropdown-profile-{type_page_indicators}', 'value'),
        Input(f'dropdown-doctor-{type_page_indicators}', 'value')
    ]
)
def update_filters_indicators(building_id, department_id, profile_id, doctor_id):
    buildings = get_available_buildings()

    if doctor_id:
        departments = get_departments_by_doctor(doctor_id)
    elif building_id:
        departments = get_available_departments(building_id)
    else:
        departments = get_available_departments()

    if building_id or department_id:
        profiles = get_available_profiles(building_id, department_id)
    else:
        profiles = get_available_profiles()

    if department_id or profile_id:
        doctors = get_available_doctors(building_id, department_id, profile_id)
    else:
        doctors = get_available_doctors()

    return buildings, departments, profiles, doctors


@app.callback(
    Output(f'selected-filters-{type_page_indicators}', 'children'),
    [Input(f'dropdown-doctor-{type_page_indicators}', 'value')]
)
def update_selected_filters_indicators(doctor_id):
    if isinstance(doctor_id, list) and len(doctor_id) == 1:
        doctor_id = doctor_id[0]
    elif isinstance(doctor_id, str) and ',' not in doctor_id:
        doctor_id = int(doctor_id)
    else:
        return []

    details = get_doctor_details(doctor_id)
    if details:
        selected_text = [
            f"Врач: {details['doctor_name']}",
            f"Специальность: {details['specialty']}",
            f"Отделение: {details['department']}",
            f"Корпус: {details['building']}"
        ]
        return [html.Div(item) for item in selected_text]
    else:
        return []


@app.callback(
    Output(f'selected-period-{type_page_indicators}', 'children'),
    [Input(f'range-slider-month-{type_page_indicators}', 'value'),
     Input(f'dropdown-year-{type_page_indicators}', 'value'),
     Input(f'current-month-name-{type_page_indicators}', 'children'),
     ]
)
def update_selected_period_list_indicators(selected_months_range, selected_year, current_month_name):
    return selected_months_range


@app.callback(
     [Output(f'result-table1-{type_page_indicators}', 'columns'),
      Output(f'result-table1-{type_page_indicators}', 'data'),
      Output(f'progress-bar-{type_page_indicators}', 'value'),
      Output(f'progress-bar-{type_page_indicators}', 'style'),
      Output(f'loading-status-{type_page_indicators}', 'children')],
    [Input(f'update-button-{type_page_indicators}', 'n_clicks')],
    [State(f'dropdown-doctor-{type_page_indicators}', 'value'),
     State(f'dropdown-profile-{type_page_indicators}', 'value'),
     State(f'range-slider-month-{type_page_indicators}', 'value'),
     State(f'dropdown-year-{type_page_indicators}', 'value'),
     State(f'dropdown-inogorodniy-{type_page_indicators}', 'value'),
     State(f'dropdown-sanction-{type_page_indicators}', 'value'),
     State(f'dropdown-amount-null-{type_page_indicators}', 'value'),
     State(f'dropdown-building-{type_page_indicators}', 'value'),
     State(f'dropdown-department-{type_page_indicators}', 'value'),
     State(f'date-picker-range-input-{type_page_indicators}', 'start_date'),
     State(f'date-picker-range-input-{type_page_indicators}', 'end_date'),
     State(f'date-picker-range-treatment-{type_page_indicators}', 'start_date'),
     State(f'date-picker-range-treatment-{type_page_indicators}', 'end_date'),
     State(f'dropdown-report-type-{type_page_indicators}', 'value'),
     State(f'status-selection-mode-{type_page_indicators}', 'value'),
     State(f'status-group-radio-{type_page_indicators}', 'value'),
     State(f'status-individual-dropdown-{type_page_indicators}', 'value'),
     ]
)
def update_table_indicators(n_clicks, value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction,
                 amount_null, building_ids, department_ids, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type,
                 status_mode, selected_status_group, selected_individual_statuses):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    if not selected_year:
        return [], [], 0, {'display': 'none'}, "Ошибка: Выберите год"

    try:
        clear_cache()
        
        progress_style = {'display': 'block'}
        status_text = "Подготовка запроса..."
        progress_value = 10

        status_text = "Обработка фильтров..."
        progress_value = 20
        
        if status_mode == 'group':
            selected_status_values = status_groups[selected_status_group]
        else:
            selected_status_values = selected_individual_statuses if selected_individual_statuses else []

        selected_status_tuple = tuple(selected_status_values)

        if value_doctor:
            if isinstance(value_doctor, str):
                selected_doctor_ids = [int(id) for id in value_doctor.split(',') if id.strip().isdigit()]
            else:
                selected_doctor_ids = [int(id) for id in value_doctor if isinstance(id, (int, str)) and str(id).isdigit()]
        else:
            selected_doctor_ids = []

        start_date_input_formatted, end_date_input_formatted = None, None
        start_date_treatment_formatted, end_date_treatment_formatted = None, None

        if report_type == 'month':
            start_date_input_formatted, end_date_input_formatted = None, None
            start_date_treatment_formatted, end_date_treatment_formatted = None, None
        elif report_type == 'initial_input':
            selected_period = (1, 12)
            start_date_input_formatted = datetime.strptime(start_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
            end_date_input_formatted = datetime.strptime(end_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        elif report_type == 'treatment':
            selected_period = (1, 12)
            start_date_treatment_formatted = datetime.strptime(start_date_treatment.split('T')[0], '%Y-%m-%d').strftime(
                '%d-%m-%Y')
            end_date_treatment_formatted = datetime.strptime(end_date_treatment.split('T')[0], '%Y-%m-%d').strftime(
                '%d-%m-%Y')

        status_text = "Формирование SQL-запроса..."
        progress_value = 40
        cache_key = f"{selected_year}_{int(time.time() // 60)}"

        sql_query = get_cached_indicators_query(
            selected_year,
            ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)]),
            inogorodniy, sanction, amount_null,
            tuple(building_ids) if building_ids else None,
            tuple(department_ids) if department_ids else None,
            tuple(value_profile) if value_profile else None,
            tuple(selected_doctor_ids) if selected_doctor_ids else None,
            start_date_input_formatted, end_date_input_formatted,
            start_date_treatment_formatted, end_date_treatment_formatted,
            selected_status_tuple, cache_key
        )

        status_text = "Выполнение запроса к базе данных..."
        progress_value = 60

        start_time = time.time()
        columns1, data1 = TableUpdater.query_to_df(engine, sql_query)
        
        # Добавляем расчет нарастающего плана для каждой группы
        if data1:
            # Получаем список месяцев
            months_list = list(range(selected_period[0], selected_period[1] + 1))
            
            # Получаем группы для получения ID групп
            groups = get_groups_for_indicators_report(selected_year)
            group_name_to_id = {}
            if not groups.empty:
                group_name_to_id = dict(zip(groups['name'], groups['id']))
            
            # Для каждой строки рассчитываем нарастающий план
            for row in data1:
                group_name = row.get('type')
                group_id = group_name_to_id.get(group_name)
                
                if group_id:
                    # Получаем планы по месяцам для этой группы
                    # Нужны планы за все месяцы от 1 до последнего выбранного, чтобы правильно рассчитать входящие остатки
                    last_month = max(months_list) if months_list else 12
                    all_months_to_last = list(range(1, last_month + 1))
                    plan_by_months = get_plan_by_months_for_group(group_id, selected_year, all_months_to_last)
                    
                    # Рассчитываем нарастающий план с учетом входящего остатка
                    # Логика как в "Подробно по индикатору": план = план 1/12 + входящий остаток
                    # Входящий остаток передается от предыдущего месяца
                    incoming_balance_qty = 0
                    incoming_balance_amt = 0.0
                    cumulative_plan_qty = 0
                    cumulative_plan_amt = 0.0
                    
                    # Проходим по всем месяцам от 1 до последнего выбранного месяца
                    for month in sorted(all_months_to_last):
                        month_plan_qty, month_plan_amt = plan_by_months.get(month, (0, 0.0))
                        # План на месяц = План 1/12 + Входящий остаток
                        month_plan_with_balance_qty = month_plan_qty + incoming_balance_qty
                        month_plan_with_balance_amt = month_plan_amt + incoming_balance_amt
                        
                        # Если месяц входит в выбранные месяцы, добавляем к нарастающему плану
                        if month in months_list:
                            cumulative_plan_qty += month_plan_with_balance_qty
                            cumulative_plan_amt += month_plan_with_balance_amt
                        
                        # Входящий остаток для следующего месяца = план текущего месяца
                        # (без учета факта, так как факт не знаем по месяцам для каждой группы отдельно)
                        # В реальности остаток = план - факт, но для упрощения используем план
                        incoming_balance_qty = month_plan_with_balance_qty
                        incoming_balance_amt = month_plan_with_balance_amt
                    
                    # Добавляем нарастающий план в строку
                    row['План (количество)'] = cumulative_plan_qty
                    row['План (сумма)'] = round(cumulative_plan_amt, 2)
                else:
                    row['План (количество)'] = 0
                    row['План (сумма)'] = 0.0
            
            # Обновляем колонки, добавляя новые колонки для нарастающего плана
            # Находим индекс колонки "План 1/12 (сумма)" и добавляем после нее
            new_columns = []
            plan_12_sum_idx = None
            for i, col in enumerate(columns1):
                new_columns.append(col)
                if col.get('id') == 'План 1/12 (сумма)':
                    plan_12_sum_idx = i
                    # Добавляем колонки для нарастающего плана после "План 1/12 (сумма)"
                    new_columns.append({'name': 'План (количество)', 'id': 'План (количество)'})
                    new_columns.append({'name': 'План (сумма)', 'id': 'План (сумма)'})
            
            # Если индекс не найден, добавляем в конец
            if plan_12_sum_idx is None:
                new_columns.append({'name': 'План (количество)', 'id': 'План (количество)'})
                new_columns.append({'name': 'План (сумма)', 'id': 'План (сумма)'})
            
            columns1 = new_columns
        
        execution_time = time.time() - start_time

        if execution_time < 1:
            time_text = f"{execution_time*1000:.0f}мс"
        else:
            time_text = f"{execution_time:.1f}с"

        status_text = f"Запрос выполнен за {time_text}. Найдено записей: {len(data1)}"
        progress_value = 100

        progress_style = {'display': 'none'}

        return columns1, data1, progress_value, progress_style, status_text

    except Exception as e:
        error_msg = f"Ошибка при выполнении запроса: {str(e)}"
        return [], [], 0, {'display': 'none'}, error_msg


@app.callback(
    Output(f'details-button-{type_page_indicators}', 'disabled'),
    Input(f'result-table1-{type_page_indicators}', 'active_cell')
)
def update_details_button_state_indicators(active_cell):
    if not active_cell:
        return True
    
    column_id = active_cell.get('column_id')
    excluded_columns = ['type', 'Условия фильтра']
    
    return column_id in excluded_columns


@app.callback(
    [
        Output(f'details-title-{type_page_indicators}', 'children'),
        Output(f'details-table-{type_page_indicators}', 'columns'),
        Output(f'details-table-{type_page_indicators}', 'data')
    ],
    [
        Input(f'details-button-{type_page_indicators}', 'n_clicks')
    ],
    [
        State(f'result-table1-{type_page_indicators}', 'data'),
        State(f'result-table1-{type_page_indicators}', 'active_cell'),
        State(f'dropdown-doctor-{type_page_indicators}', 'value'),
        State(f'dropdown-profile-{type_page_indicators}', 'value'),
        State(f'range-slider-month-{type_page_indicators}', 'value'),
        State(f'dropdown-year-{type_page_indicators}', 'value'),
        State(f'dropdown-inogorodniy-{type_page_indicators}', 'value'),
        State(f'dropdown-sanction-{type_page_indicators}', 'value'),
        State(f'dropdown-amount-null-{type_page_indicators}', 'value'),
        State(f'dropdown-building-{type_page_indicators}', 'value'),
        State(f'dropdown-department-{type_page_indicators}', 'value'),
        State(f'date-picker-range-input-{type_page_indicators}', 'start_date'),
        State(f'date-picker-range-input-{type_page_indicators}', 'end_date'),
        State(f'date-picker-range-treatment-{type_page_indicators}', 'start_date'),
        State(f'date-picker-range-treatment-{type_page_indicators}', 'end_date'),
        State(f'dropdown-report-type-{type_page_indicators}', 'value'),
        State(f'status-selection-mode-{type_page_indicators}', 'value'),
        State(f'status-group-radio-{type_page_indicators}', 'value'),
        State(f'status-individual-dropdown-{type_page_indicators}', 'value')
    ]
)
def show_indicators_details(n_clicks, table_data, active_cell,
                           value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction,
                           amount_null, building_ids, department_ids, start_date_input, end_date_input,
                           start_date_treatment, end_date_treatment, report_type,
                           status_mode, selected_status_group, selected_individual_statuses):
    if not n_clicks or not active_cell or not table_data:
        return '', [], []
    
    row_data = table_data[active_cell.get('row')]
    indicator_type = row_data.get('type')
    
    if not indicator_type:
        return 'Ошибка: не удалось определить тип индикатора', [], []
    
    try:
        if status_mode == 'group':
            selected_status_values = status_groups[selected_status_group]
        else:
            selected_status_values = selected_individual_statuses if selected_individual_statuses else []
        
        selected_status_tuple = tuple(selected_status_values)
        
        if value_doctor:
            if isinstance(value_doctor, str):
                selected_doctor_ids = [int(id) for id in value_doctor.split(',') if id.strip().isdigit()]
            else:
                selected_doctor_ids = [int(id) for id in value_doctor if isinstance(id, (int, str)) and str(id).isdigit()]
        else:
            selected_doctor_ids = []
        
        start_date_input_formatted, end_date_input_formatted = None, None
        start_date_treatment_formatted, end_date_treatment_formatted = None, None
        
        if report_type == 'initial_input':
            selected_period = (1, 12)
            start_date_input_formatted = datetime.strptime(start_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
            end_date_input_formatted = datetime.strptime(end_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        elif report_type == 'treatment':
            selected_period = (1, 12)
            start_date_treatment_formatted = datetime.strptime(start_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
            end_date_treatment_formatted = datetime.strptime(end_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        
        sql_query = sql_query_indicators_details(
            selected_year,
            ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)]),
            inogorodniy, sanction, amount_null,
            building_ids, department_ids,
            value_profile,
            selected_doctor_ids,
            start_date_input_formatted, end_date_input_formatted,
            start_date_treatment_formatted, end_date_treatment_formatted,
            indicator_type, selected_status_tuple
        )
        
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        title_text = f"Детализация по индикатору: {indicator_type}"
        count_badge = dbc.Badge(
            f" {len(data)}",
            color="primary",
            pill=True,
            className="ms-2"
        )
        title = html.Span([title_text, count_badge])
        
        return title, columns, data
        
    except Exception as e:
        error_msg = f"Ошибка при получении детализации: {str(e)}"
        return error_msg, [], []


# ========== Callbacks для вкладки "Планы" ==========

@app.callback(
    [
        Output(f'plans-table-{type_page_plans}', 'columns'),
        Output(f'plans-table-{type_page_plans}', 'data'),
        Output(f'plans-table-{type_page_plans}', 'style_data_conditional')
    ],
    [
        Input(f'update-button-{type_page_plans}', 'n_clicks')
    ],
    [
        State(f'dropdown-year-{type_page_plans}', 'value')
    ]
)
def update_plans_table(n_clicks, selected_year):
    if n_clicks is None:
        return [], [], []
    
    if isinstance(selected_year, str):
        selected_year = int(selected_year)
    
    sql_query = sql_query_plans(selected_year)
    columns, data = TableUpdater.query_to_df(engine, sql_query)
    
    # Создаем стили для выделения строк с одинаковым показателем
    style_data_conditional = []
    if data:
        # Цвета для чередования показателей
        colors = [
            {'backgroundColor': '#f0f8ff', 'color': 'black'},  # Светло-голубой
            {'backgroundColor': '#f5f5f5', 'color': 'black'},  # Светло-серый
            {'backgroundColor': '#fff8dc', 'color': 'black'},  # Светло-бежевый
            {'backgroundColor': '#f0fff0', 'color': 'black'},  # Светло-зеленый
            {'backgroundColor': '#ffe4e1', 'color': 'black'},  # Светло-розовый
            {'backgroundColor': '#e6e6fa', 'color': 'black'},  # Лавандовый
        ]
        
        # Группируем строки по показателю (убираем " - Объемы" и " - Финансы")
        indicator_groups = {}
        for idx, row in enumerate(data):
            indicator = row.get('Показатель', '')
            # Извлекаем название показателя без типа
            if ' - Объемы' in indicator:
                base_indicator = indicator.replace(' - Объемы', '')
            elif ' - Финансы' in indicator:
                base_indicator = indicator.replace(' - Финансы', '')
            else:
                base_indicator = indicator
            
            if base_indicator not in indicator_groups:
                indicator_groups[base_indicator] = []
            indicator_groups[base_indicator].append(idx)
        
        # Применяем цвета к группам
        color_idx = 0
        for base_indicator, row_indices in indicator_groups.items():
            color = colors[color_idx % len(colors)]
            for row_idx in row_indices:
                style_data_conditional.append({
                    'if': {'row_index': row_idx},
                    **color
                })
            color_idx += 1
    
    return columns, data, style_data_conditional
