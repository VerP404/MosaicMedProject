from datetime import datetime
import time
from functools import lru_cache

from dash import dcc, html, Output, Input, exceptions, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, filter_months, \
    get_current_reporting_month, get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors, get_departments_by_doctor, \
    get_doctor_details, filter_inogorod, filter_sanction, filter_amount_null, date_picker, filter_report_type, \
    update_buttons, filter_status, status_groups
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.indicators.query import sql_query_indicators, clear_cache
from apps.analytical_app.query_executor import engine

type_page = "econ-indicators"


# Кэшированная функция для SQL-запроса
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

econ_indicators = html.Div(
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
                                    dbc.Col(filter_status(type_page), width=6),
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
         # Улучшенная индикация загрузки с прогресс-баром
         dbc.Row([
             dbc.Col([
                 dbc.Progress(
                     id=f'progress-bar-{type_page}',
                     value=0,
                     striped=True,
                     animated=True,
                     style={'display': 'none'}
                 ),
                 html.Div(id=f'loading-status-{type_page}', style={'text-align': 'center', 'margin': '10px 0'}),
             ], width=12)
         ]),
         dcc.Loading(
             id=f'loading-output-{type_page}', 
             type='default',
             children=[card_table(f'result-table1-{type_page}', "Индикаторные показатели", page_size=25, 
                                 style_cell_conditional=[
                                     {'if': {'column_id': 'type'}, 'width': '25%'},
                                     {'if': {'column_id': 'К-во'}, 'width': '10%'},
                                     {'if': {'column_id': 'Сумма'}, 'width': '10%'},
                                     {'if': {'column_id': 'Условия фильтра'}, 'width': '55%'}
                                 ])]
         ),
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
def toggle_status_selection_mode(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:  # mode == 'individual'
        return {'display': 'none'}, {'display': 'block'}


# Callback для кнопки "Суммировать"
@app.callback(
    Output(f'sum-result-result-table1-{type_page}', 'children'),
    Input(f'sum-button-result-table1-{type_page}', 'n_clicks'),
    State(f'result-table1-{type_page}', 'derived_virtual_data'),
    State(f'result-table1-{type_page}', 'selected_cells')
)
def calculate_sum_and_count(n_clicks, rows, selected_cells):
    if n_clicks is None:
        raise PreventUpdate

    # Проверка на наличие данных и выделенных ячеек
    if rows is None or not selected_cells:
        return "Нет данных или не выбраны ячейки для подсчета."

    # Инициализация суммы и счетчика
    total_sum = 0
    count = 0

    # Суммируем значения только в выделенных ячейках и считаем их количество
    for cell in selected_cells:
        row_idx = cell['row']  # Индекс строки
        col_id = cell['column_id']  # ID столбца

        # Получаем значение ячейки и добавляем к сумме, если оно является числом
        value = rows[row_idx].get(col_id, 0)
        if isinstance(value, (int, float)):  # Проверяем, что значение является числом
            total_sum += value
            count += 1  # Увеличиваем счетчик для числовых значений

    # Округляем сумму до 2 знаков и форматируем с разделителями
    total_sum_formatted = f"{total_sum:,.2f}".replace(",", " ")

    # Формируем строку с результатом
    return f"Количество выбранных ячеек: {count}, Сумма значений: {total_sum}"


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
      Output(f'result-table1-{type_page}', 'data'),
      Output(f'progress-bar-{type_page}', 'value'),
      Output(f'progress-bar-{type_page}', 'style'),
      Output(f'loading-status-{type_page}', 'children')],
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
     State(f'dropdown-report-type-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value'),
     ]
)
def update_table(n_clicks, value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction,
                 amount_null, building_ids, department_ids, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type,
                 status_mode, selected_status_group, selected_individual_statuses):
    # Если кнопка не была нажата, обновление не происходит
    if n_clicks is None:
        raise exceptions.PreventUpdate

    # Проверяем, что год выбран
    if not selected_year:
        return [], [], 0, {'display': 'none'}, "Ошибка: Выберите год"

    try:
        # Показываем прогресс-бар и начинаем анимацию
        progress_style = {'display': 'block'}
        status_text = "Подготовка запроса..."
        progress_value = 10

        # Определяем список статусов в зависимости от выбранного режима
        status_text = "Обработка фильтров..."
        progress_value = 20
        
        if status_mode == 'group':
            selected_status_values = status_groups[selected_status_group]
        else:  # status_mode == 'individual'
            selected_status_values = selected_individual_statuses if selected_individual_statuses else []

        selected_status_tuple = tuple(selected_status_values)

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

        # Генерируем ключ кэша
        status_text = "Формирование SQL-запроса..."
        progress_value = 40
        cache_key = f"{selected_year}_{int(time.time() // 60)}"  # Обновляем кэш каждую минуту для исправления SQL

        # Получаем SQL-запрос из кэша (преобразуем списки в кортежи для кэширования)
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

        # Выполняем запрос с индикацией прогресса
        status_text = "Выполнение запроса к базе данных..."
        progress_value = 60

        start_time = time.time()
        columns1, data1 = TableUpdater.query_to_df(engine, sql_query)
        execution_time = time.time() - start_time

        # Форматируем время выполнения
        if execution_time < 1:
            time_text = f"{execution_time*1000:.0f}мс"
        else:
            time_text = f"{execution_time:.1f}с"

        status_text = f"Запрос выполнен за {time_text}. Найдено записей: {len(data1)}"
        progress_value = 100

        # Скрываем прогресс-бар после завершения
        progress_style = {'display': 'none'}

        return columns1, data1, progress_value, progress_style, status_text

    except Exception as e:
        # Обработка ошибок
        error_msg = f"Ошибка при выполнении запроса: {str(e)}"
        return [], [], 0, {'display': 'none'}, error_msg