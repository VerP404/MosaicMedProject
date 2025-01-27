from datetime import datetime

from dash import dcc, html, Output, Input, exceptions, State
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_doctors, TableUpdater
from apps.analytical_app.components.filters import filter_doctors, filter_years, filter_months, \
    get_current_reporting_month, get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors, get_departments_by_doctor, \
    get_doctor_details, filter_inogorod, filter_sanction, filter_amount_null, date_picker, filter_report_type, \
    update_buttons
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.pages.doctor.doctor.query import sql_query_amb_def, sql_query_dd_def, sql_query_stac_def
from apps.analytical_app.query_executor import engine

type_page = "doctor-talon"

doctor_talon = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                    dbc.Col(filter_report_type(type_page), width=2),
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(filter_months(type_page), width=12),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Label("Выберите дату", id=f'label-date-{type_page}',
                                                                   style={'font-weight': 'bold', 'display': 'none'}),
                                                        width="auto"
                                                    ),
                                                    dbc.Col(date_picker(f'input-{type_page}'), width=4,
                                                            id=f'col-input-{type_page}', style={'display': 'none'}),
                                                    dbc.Col(date_picker(f'treatment-{type_page}'), width=4,
                                                            id=f'col-treatment-{type_page}', style={'display': 'none'}),
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
                                    dbc.Col(filter_building(type_page), width=6),  # Увеличено до 6
                                    dbc.Col(filter_department(type_page), width=6),  # Увеличено до 6
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_profile(type_page), width=6),
                                    dbc.Col(filter_doctor(type_page), width=6),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=9),
                                    dbc.Col(html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=3)
                                ]
                            ),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                            html.Div(
                                id=f'selected-filters-{type_page}',
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
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "По категориям"),
        card_table(f'result-table2-{type_page}', "По целям"),
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
    [
        Output(f'dropdown-building-{type_page}', 'options'),
        Output(f'dropdown-department-{type_page}', 'options'),
        Output(f'dropdown-profile-{type_page}', 'options'),
        Output(f'dropdown-doctor-{type_page}', 'options')
    ],
    [
        Input(f'dropdown-building-{type_page}', 'value'),
        Input(f'dropdown-department-{type_page}', 'value'),
        Input(f'dropdown-profile-{type_page}', 'value'),
        Input(f'dropdown-doctor-{type_page}', 'value'),
        Input(f'dropdown-year-{type_page}', 'value'),
    ]
)
def update_filters(building_id, department_id, profile_id, doctor_id, selected_year):
    # Установим текущий год, если selected_year не передан
    if not selected_year:
        selected_year = datetime.now().year

    # Получаем доступные корпуса
    buildings = get_available_buildings()

    # Определяем доступные отделения
    if doctor_id:
        departments = get_departments_by_doctor(doctor_id)
    elif building_id:
        departments = get_available_departments(building_id)
    else:
        departments = get_available_departments()

    # Определяем доступные профили
    if building_id or department_id:
        profiles = get_available_profiles(building_id, department_id)
    else:
        profiles = get_available_profiles()

    # Определяем доступных врачей
    doctors = get_available_doctors(building_id, department_id, profile_id, selected_year)

    return buildings, departments, profiles, doctors



@app.callback(
    Output(f'selected-filters-{type_page}', 'children'),
    [Input(f'dropdown-doctor-{type_page}', 'value')]
)
def update_selected_filters(doctor_ids):
    if not doctor_ids:
        raise exceptions.PreventUpdate

    # Преобразуем строку с идентификаторами в список чисел
    if isinstance(doctor_ids, str):
        doctor_ids = [int(id.strip()) for id in doctor_ids.split(',') if id.strip().isdigit()]
    elif isinstance(doctor_ids, int):
        doctor_ids = [doctor_ids]

    # Получаем информацию о врачах
    details_list = get_doctor_details(doctor_ids)
    selected_text = [
        html.Div([
            f"Врач: {details['doctor_name']}",
            f"Специальность: {details['specialty']}",
            f"Отделение: {details['department']}",
            f"Корпус: {details['building']}"
        ])
        for details in details_list
    ]
    return selected_text




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
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-doctor-{type_page}', 'value'),
     State(f'dropdown-profile-{type_page}', 'value'),
     State(f'range-slider-month-{type_page}', 'value'),
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
     State(f'dropdown-report-type-{type_page}', 'value')]
)
def update_table(n_clicks, value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction, amount_null,
                 building_ids, department_ids, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type):
    # Если кнопка не была нажата, обновление не происходит
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    # Проверка и обработка значения value_doctor
    if value_doctor:
        if isinstance(value_doctor, str):
            selected_doctor_ids = [int(id) for id in value_doctor.split(',') if id.strip().isdigit()]
        else:
            selected_doctor_ids = [int(id) for id in value_doctor if isinstance(id, (int, str)) and str(id).isdigit()]
    else:
        selected_doctor_ids = []

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
        sql_query_amb_def(
            selected_year,
            ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)]),
            inogorodniy, sanction, amount_null,
            building_ids, department_ids,
            value_profile,
            selected_doctor_ids,
            start_date_input_formatted, end_date_input_formatted,
            start_date_treatment_formatted, end_date_treatment_formatted
        )
    )

    columns2, data2 = TableUpdater.query_to_df(
        engine,
        sql_query_dd_def(
            selected_year,
            ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)]),
            inogorodniy, sanction, amount_null,
            building_ids, department_ids,
            value_profile,
            selected_doctor_ids,
            start_date_input_formatted, end_date_input_formatted,
            start_date_treatment_formatted, end_date_treatment_formatted
        )
    )

    return columns1, data1, columns2, data2, loading_output
