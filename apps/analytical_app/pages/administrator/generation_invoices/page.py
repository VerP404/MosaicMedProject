from datetime import datetime, timedelta

from dash import dcc, html, Output, Input, exceptions, State, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, \
    get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors, get_departments_by_doctor, \
    get_doctor_details, filter_inogorod, filter_amount_null, \
    filter_status, status_groups, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.administrator.generation_invoices.query import sql_query_fen_inv, sql_query_details
from apps.analytical_app.query_executor import engine

type_page = "admin-gen-inv"


def date_picker_custom(type_page):
    """Date picker с датой начала 1 января текущего года"""
    current_year = datetime.now().year
    year_start = datetime(current_year, 1, 1).date()
    today = datetime.now().date()
    
    return html.Div(
        [
            dcc.DatePickerRange(
                id=f'date-picker-range-{type_page}',
                start_date_placeholder_text="Начало",
                end_date_placeholder_text="Конец",
                start_date=year_start,
                end_date=today,
                display_format="DD.MM.YYYY",
                calendar_orientation='horizontal',
                style={'margin': '10px'},
                first_day_of_week=1
            )
        ]
    )


admin_gen_inv = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader([
                                html.H4("🔍 Фильтры и настройки", className="mb-0"),
                                html.Small("Настройте параметры для формирования отчета", className="text-muted")
                            ]),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=2),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id=f'dropdown-report-type-{type_page}',
                                            options=[
                                                {'label': 'По дате формирования', 'value': 'initial_input'},
                                                {'label': 'По дате окончания лечения', 'value': 'treatment'}
                                            ],
                                            value='initial_input',
                                            clearable=False
                                        ),
                                        width=2
                                    ),
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Период", id=f'label-date-{type_page}', 
                                                       style={'font-weight': 'bold', 'margin-bottom': '10px'}),
                                            dbc.Col(date_picker_custom(f'input-{type_page}'), width=12,
                                                    id=f'col-input-{type_page}'),
                                        ],
                                        width=6,
                                        id=f'date-container-input-{type_page}',
                                        style={'display': 'none'}
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Период", id=f'label-treatment-{type_page}',
                                                       style={'font-weight': 'bold', 'margin-bottom': '10px'}),
                                            dbc.Col(date_picker_custom(f'treatment-{type_page}'), width=12,
                                                    id=f'col-treatment-{type_page}'),
                                        ],
                                        width=6,
                                        id=f'date-container-treatment-{type_page}',
                                        style={'display': 'none'}
                                    ),
                                ],
                                className="mb-3"
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
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_status(type_page, default_status_group='Готовые к сборке (1,4,6,8,19)'), width=12),
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=12),
                                ]
                            ),
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
        card_table(f'result-table1-{type_page}', "Талоны для формирования", page_size=20),
        
        
        # Простой блок с суммой
        dbc.Row(
            dbc.Col(
                html.Div([
                    html.Span("Сумма выделенных ячеек: ", style={"font-size": "18px"}),
                    html.Span(id=f'summary-stats-{type_page}', children="0", 
                            style={"font-size": "24px", "font-weight": "bold", "color": "#007bff"})
                ], className="text-center p-3 bg-light rounded"),
                width=12,
                className="mt-3"
            )
        ),
        
        # Таблица детализации
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Детализация по талонам"),
                        dbc.CardBody(
                            [
                                html.Div(id=f'details-title-{type_page}', style={"fontWeight": "bold", "marginBottom": "10px"}),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Детализация",
                                                id=f'details-button-{type_page}',
                                                color="primary",
                                                size="sm",
                                                disabled=True,
                                                className="mb-3"
                                            ),
                                            width="auto"
                                        )
                                    ]
                                ),
                                card_table(f'details-table-{type_page}', "Детали", page_size=20)
                            ]
                        )
                    ],
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12,
                className="mt-3"
            )
        ),
    ],
    style={"padding": "0rem"}
)


# Callback для очистки выделений при смене страницы
@app.callback(
    Output(f'result-table1-{type_page}', 'selected_cells', allow_duplicate=True),
    Input(f'result-table1-{type_page}', 'page_current'),
    prevent_initial_call=True
)
def clear_selection_on_page_change(page_current):
    """Очищает выделение ячеек при смене страницы"""
    return []


# Callback для подсчета суммы выделенных ячеек
@app.callback(
    Output(f'summary-stats-{type_page}', 'children'),
    [Input(f'result-table1-{type_page}', 'selected_cells'),
     Input(f'result-table1-{type_page}', 'derived_viewport_data')]
)
def update_summary_stats(selected_cells, viewport_data):
    """Суммирует выбранные ячейки на текущей странице (видимые данные)."""
    if not viewport_data or not selected_cells:
        return "0"

    total_sum = 0
    for cell in selected_cells:
        row_idx = cell.get('row')
        col_id = cell.get('column_id')
        if row_idx is not None and col_id and 0 <= row_idx < len(viewport_data):
            value = viewport_data[row_idx].get(col_id, 0)
            if isinstance(value, (int, float)):
                total_sum += value

    return f"{int(total_sum):,}".replace(",", " ")


# Callback для кнопки "Суммировать" (оставляем для совместимости)
@app.callback(
    Output(f'sum-result-result-table1-{type_page}', 'children'),
    Input(f'sum-button-result-table1-{type_page}', 'n_clicks'),
    State(f'result-table1-{type_page}', 'derived_virtual_data'),
    State(f'result-table1-{type_page}', 'selected_cells')
)
def calculate_sum_and_count(n_clicks, visible_data, selected_cells):
    """Суммирует выбранные ячейки на текущей странице"""
    if n_clicks is None:
        raise PreventUpdate

    # Проверка на наличие данных и выделенных ячеек
    if visible_data is None or not selected_cells:
        return "Нет данных или не выбраны ячейки для подсчета."

    # Инициализация суммы и счетчика
    total_sum = 0
    count = 0

    # Суммируем значения только в выделенных ячейках и считаем их количество
    for cell in selected_cells:
        # row_idx в selected_cells - это индекс относительно видимых данных (derived_virtual_data)
        row_idx = cell['row']  # Индекс строки
        col_id = cell['column_id']  # ID столбца

        # Проверяем, что индекс строки в пределах видимых данных
        if row_idx < len(visible_data):
            # Получаем значение ячейки и добавляем к сумме, если оно является числом
            value = visible_data[row_idx].get(col_id, 0)
            if isinstance(value, (int, float)):  # Проверяем, что значение является числом
                total_sum += value
                count += 1  # Увеличиваем счетчик для числовых значений

    # Округляем сумму до 2 знаков и форматируем с разделителями
    total_sum_formatted = f"{int(total_sum):,}".replace(",", " ")

    # Формируем строку с результатом
    return f"Количество выбранных ячеек: {count}, Сумма значений: {total_sum_formatted}"


@app.callback(
    [
        Output(f'date-container-input-{type_page}', 'style'),
        Output(f'date-container-treatment-{type_page}', 'style'),
        Output(f'label-date-{type_page}', 'children'),
        Output(f'label-treatment-{type_page}', 'children'),
    ],
    [Input(f'dropdown-report-type-{type_page}', 'value')]
)
def toggle_date_fields(report_type):
    """Показывает/скрывает поля дат в зависимости от типа отчета"""
    if report_type == 'initial_input':
        return {'display': 'block'}, {'display': 'none'}, 'Период по дате формирования', 'Период'
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'block'}, 'Период', 'Период по дате окончания лечения'
    else:
        return {'display': 'none'}, {'display': 'none'}, 'Период', 'Период'


@app.callback(
    [
        Output(f'status-group-container-{type_page}', 'style'),
        Output(f'status-individual-container-{type_page}', 'style')
    ],
    [Input(f'status-selection-mode-{type_page}', 'value')]
)
def toggle_status_selection_mode(mode):
    """Переключает между групповым и индивидуальным выбором статусов"""
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:  # mode == 'individual'
        return {'display': 'none'}, {'display': 'block'}


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
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table1-{type_page}', 'style_data_conditional'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-doctor-{type_page}', 'value'),
     State(f'dropdown-profile-{type_page}', 'value'),
     State(f'dropdown-year-{type_page}', 'value'),
     State(f'dropdown-inogorodniy-{type_page}', 'value'),
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
     State(f'status-individual-dropdown-{type_page}', 'value')]
)
def update_table(n_clicks, value_doctor, value_profile, selected_year, inogorodniy,
                 amount_null,
                 building_ids, department_ids, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type,
                 status_selection_mode, status_group_value, status_individual_values):
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

    # Определяем статусы для фильтрации
    status_list = []
    if status_selection_mode == 'group':
        if status_group_value and status_group_value in status_groups:
            status_list = status_groups[status_group_value]
    elif status_selection_mode == 'individual':
        if status_individual_values:
            status_list = status_individual_values if isinstance(status_individual_values, list) else [status_individual_values]
    
    # Форматируем даты в зависимости от типа отчета
    start_date_input_formatted, end_date_input_formatted = None, None
    start_date_treatment_formatted, end_date_treatment_formatted = None, None

    if report_type == 'initial_input' and start_date_input and end_date_input:
        start_date_input_formatted = datetime.strptime(start_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date_input_formatted = datetime.strptime(end_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
    elif report_type == 'treatment' and start_date_treatment and end_date_treatment:
        start_date_treatment_formatted = datetime.strptime(start_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date_treatment_formatted = datetime.strptime(end_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')

    # Генерация SQL-запроса с учетом всех фильтров
    # Для months передаем все месяцы, так как фильтр по месяцам не используется
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_fen_inv(
            selected_year,
            ', '.join(map(str, range(1, 13))),  # Все месяцы
            inogorodniy, None, amount_null,  # sanction = None
            building_ids, department_ids,
            value_profile,
            selected_doctor_ids,
            start_date_input_formatted, end_date_input_formatted,
            start_date_treatment_formatted, end_date_treatment_formatted,
            status_list  # Фильтр по статусам
        )
    )

    # Добавляем стили для зеленого выделения ненулевых значений
    style_data_conditional = []
    if columns1:
        # Получаем все колонки кроме input_date
        numeric_columns = [col['id'] for col in columns1 if col['id'] != 'input_date']
        for col_id in numeric_columns:
            # Используем проверку через filter_query для числовых значений
            # В Dash DataTable значения могут быть строками, поэтому проверяем и числовое, и строковое представление
            style_data_conditional.append({
                'if': {
                    'filter_query': f'{{{col_id}}} != 0 && {{{col_id}}} != "0" && {{{col_id}}} != null && {{{col_id}}} != ""',
                    'column_id': col_id
                },
                'backgroundColor': '#d4edda',  # светло-зеленый цвет
                'color': '#155724'  # темно-зеленый цвет текста
            })
    
    return columns1, data1, style_data_conditional, loading_output


# Callback для активации кнопки детализации при выборе ячейки
@app.callback(
    Output(f'details-button-{type_page}', 'disabled'),
    Input(f'result-table1-{type_page}', 'active_cell')
)
def update_details_button_state(active_cell):
    """Активирует кнопку детализации при выборе ячейки в колонке цели"""
    if not active_cell:
        return True
    
    # Проверяем, что выбрана допустимая колонка для детализации
    column_id = active_cell.get('column_id')
    allowed_columns = ['1', '3', '305,307 D', '113,114,14 Z', '64 G', '541,561 E', '22 N', 
                      '30,301 O', 'C', '5,7,9,10,32 P', 'SD', 'ДВ4 V', 'ДВ2 T', 'ОПВ P',
                      'УД1 U', 'УД2 Y', 'ДР1 R', 'ДР2 Q', 'ПН1 N', 'ДС2 S']
    
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
        State(f'result-table1-{type_page}', 'derived_viewport_data'),
        State(f'result-table1-{type_page}', 'active_cell'),
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'dropdown-inogorodniy-{type_page}', 'value'),
        State(f'dropdown-amount-null-{type_page}', 'value'),
        State(f'dropdown-building-{type_page}', 'value'),
        State(f'dropdown-department-{type_page}', 'value'),
        State(f'dropdown-profile-{type_page}', 'value'),
        State(f'dropdown-doctor-{type_page}', 'value'),
        State(f'date-picker-range-input-{type_page}', 'start_date'),
        State(f'date-picker-range-input-{type_page}', 'end_date'),
        State(f'date-picker-range-treatment-{type_page}', 'start_date'),
        State(f'date-picker-range-treatment-{type_page}', 'end_date'),
        State(f'dropdown-report-type-{type_page}', 'value'),
        State(f'status-selection-mode-{type_page}', 'value'),
        State(f'status-group-radio-{type_page}', 'value'),
        State(f'status-individual-dropdown-{type_page}', 'value')
    ]
)
def show_details(n_clicks, viewport_data, active_cell, selected_year, inogorodniy, amount_null,
                 building_ids, department_ids, value_profile, value_doctor,
                 start_date_input, end_date_input, start_date_treatment, end_date_treatment,
                 report_type, status_selection_mode, status_group_value, status_individual_values):
    """Отображает детализацию талонов по выбранной ячейке"""
    if not n_clicks or not active_cell or not viewport_data:
        return '', [], []
    
    try:
        # active_cell.row - это индекс относительно derived_viewport_data (данных текущей страницы)
        row_idx = active_cell.get('row')
        if row_idx is None or row_idx >= len(viewport_data):
            return 'Ошибка: неверный индекс строки', [], []
        
        # Получаем данные выбранной строки из данных текущей страницы
        row_data = viewport_data[row_idx]
        column_id = active_cell.get('column_id')
        input_date = row_data.get('input_date')
        
        if not input_date or not selected_year:
            return 'Ошибка: не удалось определить параметры для детализации', [], []
        
        # Проверяем, что выбрана допустимая колонка для детализации
        allowed_columns = ['1', '3', '305,307 D', '113,114,14 Z', '64 G', '541,561 E', '22 N', 
                          '30,301 O', 'C', '5,7,9,10,32 P', 'SD', 'ДВ4 V', 'ДВ2 T', 'ОПВ P',
                          'УД1 U', 'УД2 Y', 'ДР1 R', 'ДР2 Q', 'ПН1 N', 'ДС2 S']
        if column_id not in allowed_columns:
            return f'Детализация доступна только для колонок: {", ".join(allowed_columns)}', [], []
        
        # Обработка фильтров (аналогично update_table)
        if value_doctor:
            if isinstance(value_doctor, str):
                selected_doctor_ids = [int(id) for id in value_doctor.split(',') if id.strip().isdigit()]
            else:
                selected_doctor_ids = [int(id) for id in value_doctor if isinstance(id, (int, str)) and str(id).isdigit()]
        else:
            selected_doctor_ids = []
        
        # Определяем статусы для фильтрации
        status_list = []
        if status_selection_mode == 'group':
            if status_group_value and status_group_value in status_groups:
                status_list = status_groups[status_group_value]
        elif status_selection_mode == 'individual':
            if status_individual_values:
                status_list = status_individual_values if isinstance(status_individual_values, list) else [status_individual_values]
        
        # Форматируем даты
        start_date_input_formatted, end_date_input_formatted = None, None
        start_date_treatment_formatted, end_date_treatment_formatted = None, None
        
        if report_type == 'initial_input' and start_date_input and end_date_input:
            start_date_input_formatted = datetime.strptime(start_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
            end_date_input_formatted = datetime.strptime(end_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        elif report_type == 'treatment' and start_date_treatment and end_date_treatment:
            start_date_treatment_formatted = datetime.strptime(start_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
            end_date_treatment_formatted = datetime.strptime(end_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        
        # Выполняем запрос детализации
        sql_query = sql_query_details(
            selected_year,
            ', '.join(map(str, range(1, 13))),
            inogorodniy, None, amount_null,
            building_ids, department_ids,
            value_profile,
            selected_doctor_ids,
            start_date_input_formatted, end_date_input_formatted,
            start_date_treatment_formatted, end_date_treatment_formatted,
            status_list,
            input_date,
            column_id
        )
        
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        # Формируем заголовок
        title_text = f"Детализация по дате {input_date} - {column_id}"
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
