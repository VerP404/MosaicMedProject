from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_doctors, TableUpdater
from apps.analytical_app.components.filters import filter_doctors, filter_years, filter_months, \
    get_current_reporting_month, get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors
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
                                    dbc.Col(
                                        dbc.Switch(id=f'switch-inogorodniy-{type_page}', label="Иногородние",
                                                   value=False),
                                        width=2),
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
        Input(f'dropdown-profile-{type_page}', 'value')
    ]
)
def update_filters(building_id, department_id, profile_id):
    # Получаем доступные корпуса
    buildings = get_available_buildings()

    # Получаем доступные отделения в зависимости от выбранного корпуса
    departments = get_available_departments(building_id)

    # Получаем доступные профили в зависимости от корпуса и отделения
    profiles = get_available_profiles(building_id, department_id)

    # Получаем доступных врачей в зависимости от корпуса, отделения и профиля
    doctors = get_available_doctors(building_id, department_id, profile_id)

    return buildings, departments, profiles, doctors


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
     Input(f'switch-inogorodniy-{type_page}', 'value'),
     Input(f'dropdown-building-{type_page}', 'value'),
     Input(f'dropdown-department-{type_page}', 'value')]
)
def update_table(value_doctor, value_profile, selected_period, selected_year, inogorodniy, building_ids, department_ids):
    if not selected_period:
        return [], []

    months_placeholder = ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)])

    # Генерация SQL-запроса с учетом всех фильтров, включая профиль и врача
    columns1, data1 = TableUpdater.query_to_df(engine,
                                               sql_query_amb_def(
                                                   selected_year,
                                                   months_placeholder,
                                                   inogorodniy,
                                                   building_ids,
                                                   department_ids,
                                                   value_profile,  # Добавляем фильтр по профилю
                                                   value_doctor    # Добавляем фильтр по врачу
                                               ))

    return columns1, data1

