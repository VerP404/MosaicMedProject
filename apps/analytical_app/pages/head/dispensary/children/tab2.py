from datetime import datetime
from sqlalchemy import text

from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_dates, TableUpdater
from apps.analytical_app.components.filters import filter_status, date_start, date_end, status_groups, filter_years, \
    filter_report_type, filter_inogorod, filter_sanction, filter_amount_null, update_buttons, \
    get_current_reporting_month, date_picker, filter_months, get_available_buildings, get_departments_by_doctor, \
    get_available_departments, filter_building, filter_department
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.adults.query import sql_query_dispensary_age
from apps.analytical_app.pages.head.dispensary.children.query import sql_query_dispensary_age_children
from apps.analytical_app.query_executor import engine

type_page = "tab2-dc"

children_dn2 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Card(
                                dbc.Row(
                                    [
                                        dbc.Col(update_buttons(type_page), width=2),
                                        dbc.Col(filter_years(type_page), width=1),
                                        dbc.Col(filter_report_type(type_page), width=3),
                                        dbc.Col(filter_inogorod(type_page), width=2),
                                        dbc.Col(filter_sanction(type_page), width=2),
                                        dbc.Col(filter_amount_null(type_page), width=2),
                                    ],
                                    align="center",
                                    justify="between",
                                ),
                            ),
                            dbc.Card(
                                dbc.Row(
                                    [
                                        filter_status(type_page),  # фильтр по статусам
                                    ]
                                ),
                            ),
                            dbc.Card(
                                dbc.Row(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(filter_months(type_page), width=12),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            html.Label("Выберите дату", id=f'label-date-{type_page}',
                                                                       style={'font-weight': 'bold',
                                                                              'display': 'none'}),
                                                            width="auto"
                                                        ),
                                                        dbc.Col(date_picker(f'input-{type_page}'), width=4,
                                                                id=f'col-input-{type_page}', style={'display': 'none'}),
                                                        dbc.Col(date_picker(f'treatment-{type_page}'), width=4,
                                                                id=f'col-treatment-{type_page}',
                                                                style={'display': 'none'}),
                                                    ],
                                                    align="center",
                                                    style={"display": "flex", "align-items": "center",
                                                           "margin-bottom": "10px"}
                                                )
                                            ]
                                        ),
                                    ]
                                ),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_building(type_page), width=6),  # Увеличено до 6
                                    dbc.Col(filter_department(type_page), width=6),  # Увеличено до 6
                                ]
                            ),
                            dbc.Card(
                                dbc.Row(
                                    html.Div(
                                        [
                                            dbc.Label("Выберите тип диспансеризации:"),
                                            dbc.Checklist(
                                                options=[
                                                    {"label": "ПН1", "value": 'ПН1'},
                                                    {"label": "ПН2", "value": 'ПН2'},
                                                    {"label": "ДС1", "value": 'ДС1'},
                                                    {"label": "ДС2", "value": 'ДС2'},
                                                ],
                                                value=['ПН1'],
                                                id=f"checklist-input-{type_page}",
                                                inline=True,
                                            ),
                                        ]
                                    ),
                                ),
                            ),

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
        card_table(f'result-table1-{type_page}',
                   "Отчет по всем видам диспансеризации детей с разбивкой по возрастам")
    ],
    style={"padding": "0rem"}
)


@app.callback(
    [
        Output(f'range-slider-month-{type_page}', 'style'),
        Output(f'date-picker-range-input-{type_page}', 'style'),
        Output(f'date-picker-range-treatment-{type_page}', 'style')
    ],
    [Input(f'dropdown-report-type-{type_page}', 'value')]
)
def toggle_filters(report_type):
    if report_type == 'month':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    elif report_type == 'initial_input':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}


@app.callback(
    [
        Output(f'col-input-{type_page}', 'style'),
        Output(f'col-treatment-{type_page}', 'style'),
    ],
    [Input(f'dropdown-report-type-{type_page}', 'value')]
)
def toggle_datepickers(report_type):
    if report_type == 'initial_input':
        return {'display': 'block'}, {'display': 'none'}
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@app.callback(
    Output(f'label-date-{type_page}', 'style'),
    [
        Input(f'dropdown-report-type-{type_page}', 'value'),
        Input(f'date-picker-range-input-{type_page}', 'start_date'),
        Input(f'date-picker-range-input-{type_page}', 'end_date'),
        Input(f'date-picker-range-treatment-{type_page}', 'start_date'),
        Input(f'date-picker-range-treatment-{type_page}', 'end_date')
    ]
)
def toggle_label_visibility(report_type, start_date_input, end_date_input, start_date_treatment, end_date_treatment):
    # Показать подпись только если выбран тип "initial_input" или "treatment", и установлены даты
    if report_type in ['initial_input', 'treatment'] and (
            start_date_input or end_date_input or start_date_treatment or end_date_treatment):
        return {'display': 'block'}
    # В противном случае скрыть подпись
    return {'display': 'none'}


@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [Input(f'range-slider-month-{type_page}', 'value'),
     Input(f'dropdown-year-{type_page}', 'value'),
     Input(f'current-month-name-{type_page}', 'children'),
     ]
)
def update_selected_period_list(selected_months_range, selected_year, current_month_name):
    return selected_months_range


@app.callback(
    [
        Output(f'dropdown-building-{type_page}', 'options'),
        Output(f'dropdown-department-{type_page}', 'options'),
    ],
    [
        Input(f'dropdown-building-{type_page}', 'value'),
    ]
)
def update_filters(building_id):
    # Получаем доступные корпуса
    buildings = get_available_buildings()

    # Определяем доступные отделения
    if building_id:
        # Если выбран корпус, фильтруем по корпусу
        departments = get_available_departments(building_id)
    else:
        # Если ничего не выбрано, возвращаем все отделения
        departments = get_available_departments()

    return buildings, departments


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'range-slider-month-{type_page}', 'value'),
     State(f'dropdown-year-{type_page}', 'value'),
     State(f'dropdown-inogorodniy-{type_page}', 'value'),
     State(f'dropdown-sanction-{type_page}', 'value'),
     State(f'dropdown-amount-null-{type_page}', 'value'),
     State(f'dropdown-building-{type_page}', 'value'),
     State(f'dropdown-department-{type_page}', 'value'),
     State(f'date-picker-range-input-{type_page}', 'start_date'),
     State(f'date-picker-range-input-{type_page}', 'end_date'),
     State(f'date-picker-range-treatment-{type_page}', 'start_date'),
     State(f'date-picker-range-treatment-{type_page}', 'end_date'),
     State(f'dropdown-report-type-{type_page}', 'value'),
     State(f'checklist-input-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     ]
)
def update_table(n_clicks, selected_period, selected_year, inogorodniy, sanction,
                 amount_null,
                 building_ids, department_ids,
                 start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type,
                 selected_type_dv,
                 selected_status):
    # Если кнопка не была нажата, обновление не происходит
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    selected_type_dv_tuple = tuple(selected_type_dv)
    selected_status_values = status_groups[selected_status]
    selected_status_tuple = tuple(selected_status_values)
    # Определяем используемый период в зависимости от типа отчета
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

    # Генерация SQL-запроса с учетом всех фильтров
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_dispensary_age_children(
            selected_year,
            ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)]),
            inogorodniy,
            sanction,
            amount_null,
            building=building_ids,
            department=department_ids,
            profile=None,
            doctor=None,
            input_start=start_date_input_formatted,
            input_end=end_date_input_formatted,
            treatment_start=start_date_treatment_formatted,
            treatment_end=end_date_treatment_formatted,
            cel_list=selected_type_dv_tuple,
            status_list=selected_status_tuple
        )
    )
    return columns1, data1, loading_output
