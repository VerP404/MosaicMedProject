from datetime import datetime

from dash import dcc, html, Output, Input, exceptions, State, callback_context, no_update
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_doctors, TableUpdater
from apps.analytical_app.components.filters import filter_doctors, filter_years, filter_months, \
    get_current_reporting_month, get_available_buildings, filter_building, get_available_departments, filter_department, \
    filter_profile, filter_doctor, get_available_profiles, get_available_doctors, get_departments_by_doctor, \
    get_doctor_details, filter_inogorod, filter_sanction, filter_amount_null, date_picker, filter_report_type, \
    update_buttons, parse_doctor_ids
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.pages.doctor.doctor.query import sql_query_amb_def, sql_query_dd_def, sql_query_stac_def, sql_query_details
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
        dcc.Loading(
            children=[
                card_table(f'result-table1-{type_page}', "По категориям"),
                card_table(f'result-table2-{type_page}', "По целям"),
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Детализация",
                            id=f'details-button-{type_page}',
                            color="primary",
                            size="sm",
                            className="mt-2"
                        ), width="auto"
                    )
                ]),
                dcc.Store(id=f'details-store-{type_page}'),
                dbc.Card([
                    dbc.CardHeader("Детализация"),
                    dbc.CardBody([
                        html.Div(id=f'details-title-{type_page}', style={"fontWeight": "bold", "marginBottom": "10px"}),
                        card_table(f'details-table-inline-{type_page}', "Детали", page_size=20)
                    ])
                ], className="mt-3")
                ,
                # Отладочный SQL (свернутый блок)
                dbc.Collapse(
                    dbc.Card([
                        dbc.CardHeader("SQL детализации"),
                        dbc.CardBody(
                            html.Pre(
                                id=f'details-sql-{type_page}',
                                style={
                                    "background-color": "#f8f9fa",
                                    "border": "1px solid #dee2e6",
                                    "border-radius": "0.375rem",
                                    "padding": "1rem",
                                    "font-size": "0.875rem",
                                    "white-space": "pre-wrap",
                                    "word-break": "break-all",
                                    "max-height": "400px",
                                    "overflow-y": "auto"
                                }
                            )
                        )
                    ]),
                    id=f'details-sql-collapse-{type_page}',
                    is_open=False
                ),
                dbc.Button(
                    "Показать/Скрыть SQL детализации",
                    id=f'details-sql-toggle-{type_page}',
                    color="secondary",
                    size="sm",
                    className="mt-2"
                )
            ],
            type="circle",
            fullscreen=True,
            color="#0d6efd",
            style={"backgroundColor": "rgba(255,255,255,0.8)"}
        ),
    ],
    style={"padding": "0rem"}
)


# Колбэк возвращает только данные для таблиц, без текста загрузки
@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data')],
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
def update_table(n_clicks, value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction,
                 amount_null, building_ids, department_ids, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type):
    if not n_clicks:
        raise exceptions.PreventUpdate

    selected_doctor_ids = parse_doctor_ids(value_doctor)

    start_date_input_formatted, end_date_input_formatted = None, None
    start_date_treatment_formatted, end_date_treatment_formatted = None, None

    if report_type == 'month':
        pass
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

    return columns1, data1, columns2, data2


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
    if not selected_year:
        selected_year = datetime.now().year

    # Получаем список корпусов
    buildings = get_available_buildings()

    # Определяем варианты отделений
    if doctor_id:
        # Получаем отделения, связанные с выбранным врачом
        departments_by_doctor = get_departments_by_doctor(doctor_id)

        # Если уже выбрано отделение, проверяем, присутствует ли оно в списке отделений врача
        if department_id:
            # Приводим department_id к списку (на случай, если это одиночное значение)
            if isinstance(department_id, list):
                selected_departments = department_id
            else:
                selected_departments = [department_id]

            valid = all(
                any(item['value'] == d for item in departments_by_doctor)
                for d in selected_departments
            )
            if not valid:
                # Если выбранное отделение не найдено, дополнительно получаем отделения по корпусу
                if building_id:
                    departments_by_building = get_available_departments(building_id)
                else:
                    departments_by_building = get_available_departments()
                # Объединяем оба списка, исключая дубликаты
                merged = {item['value']: item for item in departments_by_doctor}
                for item in departments_by_building:
                    merged.setdefault(item['value'], item)
                departments = list(merged.values())
            else:
                departments = departments_by_doctor
        else:
            departments = departments_by_doctor
    elif building_id:
        departments = get_available_departments(building_id)
    else:
        departments = get_available_departments()

    # Обновляем варианты профилей
    if building_id or department_id:
        profiles = get_available_profiles(building_id, department_id)
    else:
        profiles = get_available_profiles()

    # Получаем список врачей согласно фильтрам
    doctors = get_available_doctors(building_id, department_id, profile_id, selected_year)

    return buildings, departments, profiles, doctors


@app.callback(
    Output(f'selected-filters-{type_page}', 'children'),
    [Input(f'dropdown-doctor-{type_page}', 'value')]
)
def update_selected_filters(doctor_ids):
    parsed_ids = parse_doctor_ids(doctor_ids)
    if not parsed_ids:
        raise exceptions.PreventUpdate

    # Получаем информацию о врачах по списку ID
    details_list = get_doctor_details(parsed_ids)
    # Один аккордеон с одной секцией, внутри список записей по врачам и кодам
    items = []
    for details in details_list:
        items.append(
            html.Div([
                html.Div([
                    html.Strong(details['doctor_name']),
                    dbc.Badge(details['code'], color="info", pill=True, className="ms-2"),
                ], className="mb-1"),
                html.Ul([
                    html.Li([html.Strong("Специальность: "), details['specialty']]),
                    html.Li([html.Strong("Отделение: "), details['department']]),
                    html.Li([html.Strong("Корпус: "), details['building']]),
                ], style={"list-style-type": "none", "margin": 0, "padding": 0}),
            ], className="p-2 mb-2", style={"border": "1px solid #f1f3f5", "borderRadius": "0.375rem"})
        )

    header = html.Span([
        html.Span("Выбранные врачи"),
        dbc.Badge(str(len(details_list)), color="secondary", pill=True, className="ms-2")
    ])

    accordion = dbc.Accordion([
        dbc.AccordionItem(
            html.Div(items),
            title=header
        )
    ], start_collapsed=True, always_open=False, className="mb-2",
       style={"border": "1px solid #e9ecef", "borderRadius": "0.5rem"})

    return accordion


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
    Output(f'details-sql-collapse-{type_page}', 'is_open'),
    Output(f'details-sql-toggle-{type_page}', 'children'),
    Input(f'details-sql-toggle-{type_page}', 'n_clicks'),
    State(f'details-sql-collapse-{type_page}', 'is_open')
)
def toggle_details_sql(n_clicks, is_open):
    if n_clicks:
        return (not is_open), ("Скрыть SQL детализации" if not is_open else "Показать/Скрыть SQL детализации")
    return is_open, "Показать/Скрыть SQL детализации"

@app.callback(
    [
        Output(f'details-title-{type_page}', 'children'),
        Output(f'details-table-inline-{type_page}', 'columns'),
        Output(f'details-table-inline-{type_page}', 'data'),
        Output(f'details-sql-{type_page}', 'children')
    ],
    [
        Input(f'details-button-{type_page}', 'n_clicks'),
        Input(f'result-table1-{type_page}', 'active_cell'),
        Input(f'result-table2-{type_page}', 'active_cell')
    ],
    [
        State(f'result-table1-{type_page}', 'data'),
        State(f'result-table1-{type_page}', 'columns'),
        State(f'result-table2-{type_page}', 'data'),
        State(f'result-table2-{type_page}', 'columns'),
        State(f'dropdown-doctor-{type_page}', 'value'),
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
        State(f'dropdown-report-type-{type_page}', 'value')
    ]
)
def show_details(n_clicks_details, active_cell1, active_cell2,
                 data1, columns1, data2, columns2,
                 value_doctor, value_profile, selected_period, selected_year, inogorodniy, sanction,
                 amount_null, building_ids, department_ids, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type):
    ctx = callback_context
    if not ctx.triggered:
        raise exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id']
    # Выполняем детализацию только по кнопке
    if not triggered_id.startswith(f'details-button-{type_page}'):
        # Если пользователь просто переключил ячейку — очищаем детализацию
        return '', [], [], ''

    # Определяем текущую активную ячейку (если есть)
    is_from_table1 = True if active_cell1 else False if active_cell2 else True
    active_cell = active_cell1 if is_from_table1 else active_cell2
    if not active_cell:
        raise exceptions.PreventUpdate

    row_index = active_cell.get('row')
    row_data = (data1 or [])[row_index] if is_from_table1 else (data2 or [])[row_index]
    cols = columns1 if is_from_table1 else columns2

    # Берем значение ключевой колонки явно: в таблице 1 колонка называется "Группа", в таблице 2 — id 'goal'
    first_value = None
    if row_data:
        if is_from_table1:
            first_value = row_data.get('Группа')
        else:
            first_value = row_data.get('goal')

    # Определяем статус по заголовку столбца
    column_id = cols[active_cell.get('column')]['id'] if cols and active_cell.get('column') is not None else None
    status_filter = None
    # Не учитывать клики по самой первой колонке (название группы/цели)
    if column_id and column_id not in ['Группа', 'goal']:
        # Примеры заголовков: "Всего", "1", "Оплачен(3 )", "В работе(1,2,3,4,6,8)"
        if column_id == 'Всего':
            status_filter = None
        else:
            import re
            nums = re.findall(r"\d+", column_id)
            status_filter = [n for n in nums] if nums else None

    group_name = first_value if is_from_table1 else None
    goal_value = first_value if not is_from_table1 else None

    start_date_input_formatted, end_date_input_formatted = None, None
    start_date_treatment_formatted, end_date_treatment_formatted = None, None
    if report_type == 'initial_input' and start_date_input and end_date_input:
        start_date_input_formatted = datetime.strptime(start_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date_input_formatted = datetime.strptime(end_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        selected_period = (1, 12)
    elif report_type == 'treatment' and start_date_treatment and end_date_treatment:
        start_date_treatment_formatted = datetime.strptime(start_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date_treatment_formatted = datetime.strptime(end_date_treatment.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        selected_period = (1, 12)

    months_list = ', '.join([str(m) for m in range(selected_period[0], selected_period[1] + 1)]) if selected_period else '1'

    selected_doctor_ids = parse_doctor_ids(value_doctor)
    sql_text = sql_query_details(
        selected_year,
        months_list,
        inogorodniy, sanction, amount_null,
        building_ids, department_ids,
        value_profile,
        selected_doctor_ids,
        start_date_input_formatted, end_date_input_formatted,
        start_date_treatment_formatted, end_date_treatment_formatted,
        group_name, goal_value, status_filter
    )
    columns, data = TableUpdater.query_to_df(engine, sql_text)

    status_title = f", Статус: {column_id}" if (column_id and column_id not in ['Группа', 'goal']) else ''
    title_text = (f"Группа: {group_name}" if group_name else f"Цель: {goal_value}") + status_title
    count_badge = dbc.Badge(
        f" {len(data)}",
        color="primary",
        pill=True,
        className="ms-2"
    )
    title = html.Span([title_text, count_badge])
    return title, columns, data, sql_text
