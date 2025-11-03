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
    filter_status, status_groups, status_descriptions, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.administrator.generation_invoices.query import sql_query_fen_inv, sql_query_details
from apps.analytical_app.query_executor import engine
from sqlalchemy import text

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
        
        # Блок управления талонами (удаление и изменение статуса)
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H4("⚙️ Управление талонами", className="mb-0"),
                                html.Small("Удаление и изменение статуса записей по номеру талона", className="text-muted")
                            ]
                        ),
                        dbc.CardBody(
                            [
                                dbc.Tabs(
                                    [
                                        # Вкладка "Удаление"
                                        dbc.Tab(
                                            [
                                                dbc.Alert(
                                                    [
                                                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                                                        "Внимание! Удаление записей из базы данных невозможно отменить. "
                                                        "Перед удалением убедитесь, что талон был удален во внешней системе."
                                                    ],
                                                    color="warning",
                                                    className="mb-4"
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.InputGroupText("Номер талона:", className="fw-bold"),
                                                                    dbc.Input(
                                                                        id=f'talon-input-delete-{type_page}',
                                                                        type="text",
                                                                        placeholder="Введите номер талона",
                                                                        size="lg"
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(className="bi bi-search me-2"),
                                                                            "Найти записи"
                                                                        ],
                                                                        id=f'search-talon-button-{type_page}',
                                                                        color="info",
                                                                        size="lg"
                                                                    )
                                                                ],
                                                                className="mb-3"
                                                            ),
                                                            width=12
                                                        )
                                                    ],
                                                    className="mb-3"
                                                ),
                                                html.Div(id=f'talon-search-results-{type_page}', className="mb-3"),
                                                dbc.Modal(
                                                    [
                                                        dbc.ModalHeader(
                                                            [
                                                                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                                                                "Подтверждение удаления"
                                                            ]
                                                        ),
                                                        dbc.ModalBody(
                                                            [
                                                                dbc.Alert(
                                                                    "Вы уверены, что хотите удалить записи с указанным номером талона?",
                                                                    color="danger",
                                                                    className="mb-3"
                                                                ),
                                                                html.Div(id=f'delete-confirm-info-{type_page}')
                                                            ]
                                                        ),
                                                        dbc.ModalFooter(
                                                            [
                                                                dbc.Button(
                                                                    [
                                                                        html.I(className="bi bi-x-circle me-2"),
                                                                        "Отмена"
                                                                    ],
                                                                    id=f'cancel-delete-{type_page}',
                                                                    color="secondary",
                                                                    outline=True,
                                                                    className="me-2"
                                                                ),
                                                                dbc.Button(
                                                                    [
                                                                        html.I(className="bi bi-trash-fill me-2"),
                                                                        "Удалить"
                                                                    ],
                                                                    id=f'confirm-delete-{type_page}',
                                                                    color="danger"
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    id=f'delete-modal-{type_page}',
                                                    is_open=False,
                                                    centered=True
                                                ),
                                                html.Div(id=f'delete-result-{type_page}')
                                            ],
                                            label="🗑️ Удаление",
                                            tab_id="delete-tab"
                                        ),
                                        # Вкладка "Изменение статуса"
                                        dbc.Tab(
                                            [
                                                dbc.Alert(
                                                    [
                                                        html.I(className="bi bi-info-circle-fill me-2"),
                                                        "Изменение статуса записей в базе данных. "
                                                        "Статус будет изменен во всех таблицах для указанного номера талона."
                                                    ],
                                                    color="info",
                                                    className="mb-4"
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.InputGroupText("Номер талона:", className="fw-bold"),
                                                                    dbc.Input(
                                                                        id=f'talon-input-status-{type_page}',
                                                                        type="text",
                                                                        placeholder="Введите номер талона",
                                                                        size="lg"
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(className="bi bi-search me-2"),
                                                                            "Найти записи"
                                                                        ],
                                                                        id=f'search-talon-status-button-{type_page}',
                                                                        color="info",
                                                                        size="lg"
                                                                    )
                                                                ],
                                                                className="mb-3"
                                                            ),
                                                            width=12
                                                        )
                                                    ],
                                                    className="mb-3"
                                                ),
                                                html.Div(id=f'talon-status-search-results-{type_page}', className="mb-3"),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                dbc.Label("Новый статус:", className="mb-2 fw-bold"),
                                                                dcc.Dropdown(
                                                                    id=f'status-change-dropdown-{type_page}',
                                                                    options=[
                                                                        {'label': f"{status} - {desc}", 'value': status}
                                                                        for status, desc in status_descriptions.items()
                                                                    ],
                                                                    placeholder="Выберите статус",
                                                                    clearable=False,
                                                                    style={"width": "100%"}
                                                                )
                                                            ],
                                                            width=12,
                                                            className="mb-3"
                                                        )
                                                    ]
                                                ),
                                                dbc.Button(
                                                    [
                                                        html.I(className="bi bi-check-circle-fill me-2"),
                                                        "Изменить статус"
                                                    ],
                                                    id=f'change-status-button-{type_page}',
                                                    color="primary",
                                                    size="lg",
                                                    className="w-100 mb-3",
                                                    disabled=True
                                                ),
                                                dbc.Modal(
                                                    [
                                                        dbc.ModalHeader(
                                                            [
                                                                html.I(className="bi bi-check-circle-fill text-primary me-2"),
                                                                "Подтверждение изменения статуса"
                                                            ]
                                                        ),
                                                        dbc.ModalBody(
                                                            [
                                                                dbc.Alert(
                                                                    "Вы уверены, что хотите изменить статус записей с указанным номером талона?",
                                                                    color="warning",
                                                                    className="mb-3"
                                                                ),
                                                                html.Div(id=f'status-change-confirm-info-{type_page}')
                                                            ]
                                                        ),
                                                        dbc.ModalFooter(
                                                            [
                                                                dbc.Button(
                                                                    [
                                                                        html.I(className="bi bi-x-circle me-2"),
                                                                        "Отмена"
                                                                    ],
                                                                    id=f'cancel-status-change-{type_page}',
                                                                    color="secondary",
                                                                    outline=True,
                                                                    className="me-2"
                                                                ),
                                                                dbc.Button(
                                                                    [
                                                                        html.I(className="bi bi-check-circle-fill me-2"),
                                                                        "Изменить"
                                                                    ],
                                                                    id=f'confirm-status-change-{type_page}',
                                                                    color="primary"
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    id=f'status-change-modal-{type_page}',
                                                    is_open=False,
                                                    centered=True
                                                ),
                                                html.Div(id=f'status-change-result-{type_page}')
                                            ],
                                            label="🔄 Изменение статуса",
                                            tab_id="status-change-tab"
                                        )
                                    ],
                                    id=f'talon-management-tabs-{type_page}',
                                    active_tab="delete-tab"
                                )
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


# Callback для поиска записей по номеру талона
@app.callback(
    [
        Output(f'talon-search-results-{type_page}', 'children'),
        Output(f'delete-modal-{type_page}', 'is_open'),
        Output(f'delete-confirm-info-{type_page}', 'children')
    ],
    [
        Input(f'search-talon-button-{type_page}', 'n_clicks'),
        Input(f'confirm-delete-{type_page}', 'n_clicks'),
        Input(f'cancel-delete-{type_page}', 'n_clicks')
    ],
    [
        State(f'talon-input-delete-{type_page}', 'value'),
        State(f'delete-modal-{type_page}', 'is_open')
    ]
)
def search_and_delete_talon(search_clicks, confirm_clicks, cancel_clicks, talon_number, modal_is_open):
    """Поиск записей по номеру талона и удаление"""
    ctx = callback_context
    if not ctx.triggered:
        return '', False, ''
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Отмена
    if button_id == f'cancel-delete-{type_page}':
        return '', False, ''
    
    # Поиск записей
    if button_id == f'search-talon-button-{type_page}':
        if not talon_number or not talon_number.strip():
            return dbc.Alert("Пожалуйста, введите номер талона", color="warning"), False, ''
        
        talon_number = talon_number.strip()
        
        try:
            results = []
            counts = {}
            
            # Поиск в data_loader_omsdata
            with engine.connect() as connection:
                query = text("SELECT COUNT(*) FROM data_loader_omsdata WHERE talon = :talon")
                result = connection.execute(query, {"talon": talon_number})
                count_data_loader = result.scalar()
                counts['data_loader_omsdata'] = count_data_loader
                
                # Поиск в load_data_oms_data
                query = text("SELECT COUNT(*) FROM load_data_oms_data WHERE talon = :talon")
                result = connection.execute(query, {"talon": talon_number})
                count_load_data = result.scalar()
                counts['load_data_oms_data'] = count_load_data
                
                # Поиск в load_data_talons
                query = text("SELECT COUNT(*) FROM load_data_talons WHERE talon = :talon")
                result = connection.execute(query, {"talon": talon_number})
                count_load_talons = result.scalar()
                counts['load_data_talons'] = count_load_talons
            
            total_count = count_data_loader + count_load_data + count_load_talons
            
            if total_count == 0:
                return dbc.Alert(f"Записи с номером талона '{talon_number}' не найдены", color="info"), False, ''
            
            # Формируем информацию о найденных записях
            info_items = [
                html.H5(f"Найдено записей для талона: {talon_number}", className="mb-3"),
                dbc.ListGroup([
                    dbc.ListGroupItem(
                        [
                            html.Span("data_loader_omsdata:", className="fw-bold me-2"),
                            html.Span(f"{count_data_loader} записей", className="text-primary")
                        ],
                        className="d-flex justify-content-between align-items-center"
                    ),
                    dbc.ListGroupItem(
                        [
                            html.Span("load_data_oms_data:", className="fw-bold me-2"),
                            html.Span(f"{count_load_data} записей", className="text-primary")
                        ],
                        className="d-flex justify-content-between align-items-center"
                    ),
                    dbc.ListGroupItem(
                        [
                            html.Span("load_data_talons:", className="fw-bold me-2"),
                            html.Span(f"{count_load_talons} записей", className="text-primary")
                        ],
                        className="d-flex justify-content-between align-items-center"
                    ),
                    dbc.ListGroupItem(
                        [
                            html.Span("Всего:", className="fw-bold me-2"),
                            dbc.Badge(f"{total_count} записей", color="danger", pill=True)
                        ],
                        className="d-flex justify-content-between align-items-center bg-light"
                    )
                ], flush=True, className="mb-3")
            ]
            
            # Информация для модального окна
            confirm_info = dbc.Card(
                dbc.CardBody([
                    html.P([
                        html.Strong("Номер талона: "),
                        dbc.Badge(talon_number, color="primary", className="ms-2")
                    ], className="mb-3"),
                    html.P("Будет удалено записей:", className="fw-bold mb-2"),
                    dbc.ListGroup([
                        dbc.ListGroupItem(f"data_loader_omsdata: {count_data_loader}"),
                        dbc.ListGroupItem(f"load_data_oms_data: {count_load_data}"),
                        dbc.ListGroupItem(f"load_data_talons: {count_load_talons}")
                    ], flush=True),
                    dbc.Alert(
                        [
                            html.I(className="bi bi-exclamation-triangle-fill me-2"),
                            "Это действие нельзя отменить!"
                        ],
                        color="danger",
                        className="mt-3"
                    )
                ])
            )
            
            return dbc.Row([
                dbc.Col([
                    dbc.Alert(
                        html.Div(info_items),
                        color="warning",
                        className="mb-3"
                    ),
                    dbc.Button(
                        [
                            html.I(className="bi bi-trash-fill me-2"),
                            "Удалить все записи"
                        ],
                        id=f'open-delete-modal-{type_page}',
                        color="danger",
                        size="lg",
                        className="w-100"
                    )
                ], width=12)
            ]), False, confirm_info
            
        except Exception as e:
            error_msg = f"Ошибка при поиске записей: {str(e)}"
            return dbc.Alert(error_msg, color="danger"), False, ''
    
    # Подтверждение удаления
    if button_id == f'confirm-delete-{type_page}':
        if not talon_number or not talon_number.strip():
            return '', False, ''
        
        talon_number = talon_number.strip()
        
        try:
            with engine.begin() as connection:
                deleted_counts = {}
                
                # Удаление из data_loader_omsdata
                query = text("DELETE FROM data_loader_omsdata WHERE talon = :talon")
                result = connection.execute(query, {"talon": talon_number})
                deleted_counts['data_loader_omsdata'] = result.rowcount
                
                # Удаление из load_data_oms_data
                query = text("DELETE FROM load_data_oms_data WHERE talon = :talon")
                result = connection.execute(query, {"talon": talon_number})
                deleted_counts['load_data_oms_data'] = result.rowcount
                
                # Удаление из load_data_talons
                query = text("DELETE FROM load_data_talons WHERE talon = :talon")
                result = connection.execute(query, {"talon": talon_number})
                deleted_counts['load_data_talons'] = result.rowcount
                
                # commit происходит автоматически при выходе из with engine.begin()
            
            total_deleted = sum(deleted_counts.values())
            
            success_msg = dbc.Alert(
                [
                    html.Div([
                        html.I(className="bi bi-check-circle-fill me-2"),
                        html.Strong(f"Успешно удалено {total_deleted} записей с номером талона '{talon_number}'")
                    ], className="mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem(
                            [
                                html.Span("data_loader_omsdata:", className="fw-bold me-2"),
                                html.Span(f"{deleted_counts['data_loader_omsdata']} записей", className="text-success")
                            ],
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            [
                                html.Span("load_data_oms_data:", className="fw-bold me-2"),
                                html.Span(f"{deleted_counts['load_data_oms_data']} записей", className="text-success")
                            ],
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            [
                                html.Span("load_data_talons:", className="fw-bold me-2"),
                                html.Span(f"{deleted_counts['load_data_talons']} записей", className="text-success")
                            ],
                            className="d-flex justify-content-between align-items-center"
                        )
                    ], flush=True)
                ],
                color="success"
            )
            
            return success_msg, False, ''
            
        except Exception as e:
            error_msg = f"Ошибка при удалении записей: {str(e)}"
            return dbc.Alert(error_msg, color="danger"), False, ''
    
    return '', False, ''


# Callback для открытия модального окна удаления
@app.callback(
    Output(f'delete-modal-{type_page}', 'is_open', allow_duplicate=True),
    Input(f'open-delete-modal-{type_page}', 'n_clicks'),
    prevent_initial_call=True
)
def open_delete_modal(n_clicks):
    """Открывает модальное окно подтверждения удаления"""
    if n_clicks:
        return True
    return False


# Callback для отображения результата удаления
@app.callback(
    Output(f'delete-result-{type_page}', 'children'),
    Input(f'confirm-delete-{type_page}', 'n_clicks')
)
def show_delete_result(n_clicks):
    """Отображает результат удаления"""
    if n_clicks:
        return html.Div()  # Результат уже отображается в search_and_delete_talon
    return html.Div()


# Callback для поиска записей при изменении статуса
@app.callback(
    [
        Output(f'talon-status-search-results-{type_page}', 'children'),
        Output(f'change-status-button-{type_page}', 'disabled')
    ],
    Input(f'search-talon-status-button-{type_page}', 'n_clicks'),
    State(f'talon-input-status-{type_page}', 'value')
)
def search_talon_for_status_change(n_clicks, talon_number):
    """Поиск записей по номеру талона для изменения статуса"""
    if not n_clicks or not talon_number or not talon_number.strip():
        return '', True
    
    talon_number = talon_number.strip()
    
    try:
        counts = {}
        current_statuses = {}
        
        # Поиск в data_loader_omsdata
        with engine.connect() as connection:
            query = text("""
                SELECT COUNT(*), 
                       STRING_AGG(DISTINCT status, ', ') as statuses
                FROM data_loader_omsdata 
                WHERE talon = :talon
            """)
            result = connection.execute(query, {"talon": talon_number})
            row = result.fetchone()
            counts['data_loader_omsdata'] = row[0] if row else 0
            current_statuses['data_loader_omsdata'] = row[1] if row and row[1] else '-'
            
            # Поиск в load_data_oms_data
            query = text("""
                SELECT COUNT(*), 
                       STRING_AGG(DISTINCT status, ', ') as statuses
                FROM load_data_oms_data 
                WHERE talon = :talon
            """)
            result = connection.execute(query, {"talon": talon_number})
            row = result.fetchone()
            counts['load_data_oms_data'] = row[0] if row else 0
            current_statuses['load_data_oms_data'] = row[1] if row and row[1] else '-'
            
            # Поиск в load_data_talons
            query = text("""
                SELECT COUNT(*), 
                       STRING_AGG(DISTINCT status, ', ') as statuses
                FROM load_data_talons 
                WHERE talon = :talon
            """)
            result = connection.execute(query, {"talon": talon_number})
            row = result.fetchone()
            counts['load_data_talons'] = row[0] if row else 0
            current_statuses['load_data_talons'] = row[1] if row and row[1] else '-'
        
        total_count = sum(counts.values())
        
        if total_count == 0:
            return dbc.Alert(f"Записи с номером талона '{talon_number}' не найдены", color="info"), True
        
        # Формируем информацию о найденных записях
        info_items = [
            html.H5(f"Найдено записей для талона: {talon_number}", className="mb-3"),
            dbc.ListGroup([
                dbc.ListGroupItem(
                    [
                        html.Span("data_loader_omsdata:", className="fw-bold me-2"),
                        html.Span(f"{counts['data_loader_omsdata']} записей", className="text-primary me-2"),
                        html.Span(f"(текущий статус: {current_statuses['data_loader_omsdata']})", className="text-muted small")
                    ],
                    className="d-flex justify-content-between align-items-center"
                ),
                dbc.ListGroupItem(
                    [
                        html.Span("load_data_oms_data:", className="fw-bold me-2"),
                        html.Span(f"{counts['load_data_oms_data']} записей", className="text-primary me-2"),
                        html.Span(f"(текущий статус: {current_statuses['load_data_oms_data']})", className="text-muted small")
                    ],
                    className="d-flex justify-content-between align-items-center"
                ),
                dbc.ListGroupItem(
                    [
                        html.Span("load_data_talons:", className="fw-bold me-2"),
                        html.Span(f"{counts['load_data_talons']} записей", className="text-primary me-2"),
                        html.Span(f"(текущий статус: {current_statuses['load_data_talons']})", className="text-muted small")
                    ],
                    className="d-flex justify-content-between align-items-center"
                ),
                dbc.ListGroupItem(
                    [
                        html.Span("Всего:", className="fw-bold me-2"),
                        dbc.Badge(f"{total_count} записей", color="info", pill=True)
                    ],
                    className="d-flex justify-content-between align-items-center bg-light"
                )
            ], flush=True, className="mb-3")
        ]
        
        return dbc.Alert(html.Div(info_items), color="info"), False
        
    except Exception as e:
        error_msg = f"Ошибка при поиске записей: {str(e)}"
        return dbc.Alert(error_msg, color="danger"), True


# Callback для открытия модального окна изменения статуса
@app.callback(
    [
        Output(f'status-change-modal-{type_page}', 'is_open'),
        Output(f'status-change-confirm-info-{type_page}', 'children')
    ],
    [
        Input(f'change-status-button-{type_page}', 'n_clicks'),
        Input(f'confirm-status-change-{type_page}', 'n_clicks'),
        Input(f'cancel-status-change-{type_page}', 'n_clicks')
    ],
    [
        State(f'talon-input-status-{type_page}', 'value'),
        State(f'status-change-dropdown-{type_page}', 'value'),
        State(f'status-change-modal-{type_page}', 'is_open')
    ]
)
def toggle_status_change_modal(change_clicks, confirm_clicks, cancel_clicks, talon_number, new_status, is_open):
    """Управление модальным окном изменения статуса"""
    ctx = callback_context
    if not ctx.triggered:
        return False, ''
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Отмена
    if button_id == f'cancel-status-change-{type_page}':
        return False, ''
    
    # Подтверждение - закрываем модальное окно
    if button_id == f'confirm-status-change-{type_page}':
        return False, ''
    
    # Открытие модального окна
    if button_id == f'change-status-button-{type_page}':
        if not talon_number or not new_status:
            return False, ''
        
        # Формируем информацию для подтверждения
        status_desc = status_descriptions.get(new_status, 'Неизвестный статус')
        confirm_info = dbc.Card(
            dbc.CardBody([
                html.P([
                    html.Strong("Номер талона: "),
                    dbc.Badge(talon_number, color="primary", className="ms-2")
                ], className="mb-3"),
                html.P([
                    html.Strong("Новый статус: "),
                    dbc.Badge(f"{new_status} - {status_desc}", color="success", className="ms-2")
                ], className="mb-3"),
                html.P("Будет изменен статус во всех таблицах:", className="fw-bold mb-2"),
                dbc.ListGroup([
                    dbc.ListGroupItem("data_loader_omsdata"),
                    dbc.ListGroupItem("load_data_oms_data"),
                    dbc.ListGroupItem("load_data_talons")
                ], flush=True),
                dbc.Alert(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        "Это действие изменит статус всех найденных записей!"
                    ],
                    color="warning",
                    className="mt-3"
                )
            ])
        )
        
        return True, confirm_info
    
    return is_open, ''


# Callback для изменения статуса
@app.callback(
    Output(f'status-change-result-{type_page}', 'children'),
    Input(f'confirm-status-change-{type_page}', 'n_clicks'),
    [
        State(f'talon-input-status-{type_page}', 'value'),
        State(f'status-change-dropdown-{type_page}', 'value')
    ]
)
def change_status(n_clicks, talon_number, new_status):
    """Изменение статуса записей"""
    if not n_clicks or not talon_number or not new_status:
        return ''
    
    talon_number = talon_number.strip()
    
    try:
        updated_counts = {}
        
        with engine.begin() as connection:
            # Изменение статуса в data_loader_omsdata
            query = text("UPDATE data_loader_omsdata SET status = :new_status WHERE talon = :talon")
            result = connection.execute(query, {"new_status": new_status, "talon": talon_number})
            updated_counts['data_loader_omsdata'] = result.rowcount
            
            # Изменение статуса в load_data_oms_data
            query = text("UPDATE load_data_oms_data SET status = :new_status WHERE talon = :talon")
            result = connection.execute(query, {"new_status": new_status, "talon": talon_number})
            updated_counts['load_data_oms_data'] = result.rowcount
            
            # Изменение статуса в load_data_talons
            query = text("UPDATE load_data_talons SET status = :new_status WHERE talon = :talon")
            result = connection.execute(query, {"new_status": new_status, "talon": talon_number})
            updated_counts['load_data_talons'] = result.rowcount
        
        total_updated = sum(updated_counts.values())
        status_desc = status_descriptions.get(new_status, 'Неизвестный статус')
        
        success_msg = dbc.Alert(
            [
                html.Div([
                    html.I(className="bi bi-check-circle-fill me-2"),
                    html.Strong(f"Успешно изменен статус {total_updated} записей на '{new_status} - {status_desc}'")
                ], className="mb-3"),
                dbc.ListGroup([
                    dbc.ListGroupItem(
                        [
                            html.Span("data_loader_omsdata:", className="fw-bold me-2"),
                            html.Span(f"{updated_counts['data_loader_omsdata']} записей", className="text-success")
                        ],
                        className="d-flex justify-content-between align-items-center"
                    ),
                    dbc.ListGroupItem(
                        [
                            html.Span("load_data_oms_data:", className="fw-bold me-2"),
                            html.Span(f"{updated_counts['load_data_oms_data']} записей", className="text-success")
                        ],
                        className="d-flex justify-content-between align-items-center"
                    ),
                    dbc.ListGroupItem(
                        [
                            html.Span("load_data_talons:", className="fw-bold me-2"),
                            html.Span(f"{updated_counts['load_data_talons']} записей", className="text-success")
                        ],
                        className="d-flex justify-content-between align-items-center"
                    )
                ], flush=True)
            ],
            color="success"
        )
        
        return success_msg
        
    except Exception as e:
        error_msg = f"Ошибка при изменении статуса: {str(e)}"
        return dbc.Alert(error_msg, color="danger")
