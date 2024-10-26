from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_doctors, TableUpdater
from apps.analytical_app.components.filters import filter_doctors, filter_years, filter_months, \
    get_current_reporting_month, get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors, get_departments_by_doctor, \
    get_doctor_details, filter_inogorod, filter_sanction, filter_amount_null
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
                                    dbc.Col(filter_years(type_page), width=1),  # Увеличено с 1 до 2 для баланса
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                ]
                            ),
                            dbc.Row(
                                [
                                    filter_months(type_page)  # фильтр по месяцам
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
        card_table(f'result-table1-{type_page}', "Амбулаторная помощь"),
    ],
    style={"padding": "0rem"}
)


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
        Input(f'dropdown-doctor-{type_page}', 'value')
    ]
)
def update_filters(building_id, department_id, profile_id, doctor_id):
    # Получаем доступные корпуса
    buildings = get_available_buildings()

    # Определяем доступные отделения
    if doctor_id:
        # Если выбран врач, фильтруем отделения по врачу
        departments = get_departments_by_doctor(doctor_id)
    elif building_id:
        # Если выбран корпус, фильтруем по корпусу
        departments = get_available_departments(building_id)
    else:
        # Если ничего не выбрано, возвращаем все отделения
        departments = get_available_departments()

    # Определяем доступные профили
    if building_id or department_id:
        # Фильтруем профили по корпусу и/или отделению
        profiles = get_available_profiles(building_id, department_id)
    else:
        # Если фильтры не выбраны, возвращаем все профили
        profiles = get_available_profiles()

    # Определяем доступных врачей
    if department_id or profile_id:
        # Фильтруем врачей по отделению или профилю
        doctors = get_available_doctors(building_id, department_id, profile_id)
    else:
        # Если фильтры не выбраны, возвращаем всех врачей
        doctors = get_available_doctors()

    return buildings, departments, profiles, doctors


@app.callback(
    Output(f'selected-filters-{type_page}', 'children'),
    [Input(f'dropdown-doctor-{type_page}', 'value')]
)
def update_selected_filters(doctor_id):
    # Проверяем, выбран ли один врач
    if isinstance(doctor_id, list) and len(doctor_id) == 1:
        doctor_id = doctor_id[0]
    elif isinstance(doctor_id, str) and ',' not in doctor_id:
        # Если передана строка, и это не список
        doctor_id = int(doctor_id)
    else:
        return []

    # Получаем информацию о враче
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
     Output(f'result-table1-{type_page}', 'data')],
    [Input(f'dropdown-doctor-{type_page}', 'value'),
     Input(f'dropdown-profile-{type_page}', 'value'),  # Добавляем фильтр по профилю
     Input(f'selected-period-{type_page}', 'children'),
     Input(f'dropdown-year-{type_page}', 'value'),
     Input(f'dropdown-inogorodniy-{type_page}', 'value'),
     Input(f'dropdown-sanction-{type_page}', 'value'),
     Input(f'dropdown-amount-null-{type_page}', 'value'),
     Input(f'dropdown-building-{type_page}', 'value'),
     Input(f'dropdown-department-{type_page}', 'value'),
     ]
)
def update_table(value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction, amount_null,
                 building_ids,
                 department_ids):
    # Проверка на наличие выбранного периода
    if not selected_period:
        return [], []

    # Проверка и обработка значения value_doctor
    if value_doctor:
        if isinstance(value_doctor, str):
            # Разделяем строку на части и преобразуем каждую в int
            selected_doctor_ids = [int(id) for id in value_doctor.split(',') if id.strip().isdigit()]
        else:
            # Если это список, конвертируем каждый элемент в int
            selected_doctor_ids = [int(id) for id in value_doctor if isinstance(id, (int, str)) and str(id).isdigit()]
    else:
        selected_doctor_ids = []

    # Проверка и обработка значения value_profile
    if not value_profile:
        value_profile = []

    # Генерация списка месяцев для SQL-запроса
    months_placeholder = ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)])

    # Генерация SQL-запроса с учетом всех фильтров
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_amb_def(
            selected_year,
            months_placeholder,
            inogorodniy,
            sanction,
            amount_null,
            building_ids,
            department_ids,
            value_profile,  # Фильтр по профилю
            selected_doctor_ids,  # Фильтр по врачу
        )
    )
    return columns1, data1
