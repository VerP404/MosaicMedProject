from dash import dcc, html, Input, Output, State, callback, exceptions
import dash_bootstrap_components as dbc
from datetime import datetime

from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.financial_indicators.query import sql_query_financial_indicators
from apps.analytical_app.components.filters import (
    filter_years, filter_building, filter_department,
    filter_profile,
    filter_doctor, filter_inogorod, filter_amount_null, filter_status, filter_report_type,
    get_available_buildings, get_available_departments, get_available_doctors, get_available_profiles,
    parse_doctor_ids, status_groups
)
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.query_executor import engine


# Список целей, входящих в правила "Сверхподушевик"
SVERHPOD_GOALS = [
    'ДВ4', 'ДВ2', 'ОПВ', 'ДР1', 'ДР2', 'УД1', 'УД2',
    'ПН1', 'ДС2', '3', '113', '307', '22', '541',
    '64', '301', '305', '14', 'В дневном стационаре', 'На дому'
]

def layout(type_page="econ-financial-indicators"):
    """Layout для страницы финансовых показателей"""
    
    current_month = datetime.now().month
    
    return html.Div([
        # Заголовок страницы
        dbc.Row([
            dbc.Col([
                html.H3("Финансовые показатели", className="mb-3")
            ])
        ]),
        
        # Фильтры
        dbc.Card([
            dbc.CardHeader("Фильтры"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Год:", className="fw-bold"),
                        filter_years(type_page)
                    ], width=2),
                    dbc.Col([
                        html.Label("Отчетный период:", className="fw-bold"),
                        dcc.RangeSlider(
                            id=f'range-slider-month-{type_page}',
                            min=1,
                            max=12,
                            marks={
                                1: 'Янв', 2: 'Фев', 3: 'Мар', 4: 'Апр',
                                5: 'Май', 6: 'Июн', 7: 'Июл', 8: 'Авг',
                                9: 'Сен', 10: 'Окт', 11: 'Ноя', 12: 'Дек'
                            },
                            value=[current_month, current_month],
                            step=1
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("Тип отчета:", className="fw-bold"),
                        filter_report_type(type_page)
                    ], width=2),
                    dbc.Col([
                        html.Label("", className="fw-bold"),
                        dbc.Button("Обновить", id=f'update-button-{type_page}', color="primary",
                                   className="mt-3", style={"width": "100%"})
                    ], width=2)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.Label("Местные/иногородние:", className="fw-bold"),
                        filter_inogorod(type_page)
                    ], width=2),
                    dbc.Col([
                        html.Label("Сумма талона:", className="fw-bold"),
                        filter_amount_null(type_page)
                    ], width=2),
                    dbc.Col([
                        html.Label("Корпус:", className="fw-bold"),
                        filter_building(type_page)
                    ], width=4),
                    dbc.Col([
                        html.Label("Отделение:", className="fw-bold"),
                        filter_department(type_page)
                    ], width=4),
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.Label("Дата формирования:", className="fw-bold"),
                        dcc.DatePickerRange(
                            id=f'date-picker-range-input-{type_page}',
                            start_date=datetime(datetime.now().year, 1, 1).date(),
                            end_date=datetime.now().date(),
                            display_format="DD.MM.YYYY",
                            first_day_of_week=1
                        )
                    ], width=6, id=f'date-container-input-{type_page}', style={'display': 'none'}),
                    dbc.Col([
                        html.Label("Дата окончания лечения:", className="fw-bold"),
                        dcc.DatePickerRange(
                            id=f'date-picker-range-treatment-{type_page}',
                            start_date=datetime(datetime.now().year, 1, 1).date(),
                            end_date=datetime.now().date(),
                            display_format="DD.MM.YYYY",
                            first_day_of_week=1
                        )
                    ], width=6, id=f'date-container-treatment-{type_page}', style={'display': 'none'}),
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.Label("Специальность:", className="fw-bold"),
                        filter_profile(type_page)
                    ], width=4),
                    dbc.Col([
                        html.Label("Врач:", className="fw-bold"),
                        filter_doctor(type_page)
                    ], width=4),
                    dbc.Col([
                        filter_status(type_page, default_status_group='Оплаченные (3)')
                    ], width=4),
                ], className="mb-3"),
                
                # Информационные блоки
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(
                            "Поддерживаются фильтры по статусам, местным/иногородним, нулевым суммам, датам, корпусам, отделениям и врачам",
                            color="info",
                            className="mb-2"
                        )
                    ])
                ]),
                
                # Примененные фильтры
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(
                            id=f'applied-filters-{type_page}',
                            color="warning",
                            className="mb-2"
                        )
                    ])
                ])
            ])
        ], className="mb-3"),
        
        # Основная таблица
        dcc.Loading(
            id=f'loading-output-{type_page}',
            type='default',
            children=[
                card_table(
                    f'result-table-{type_page}',
                    "Финансовые показатели по целям и СМО",
                    page_size=50,
                    style_cell_conditional=[
                        {'if': {'column_id': 'goal'}, 'width': '20%'},
                        {'if': {'column_id': 'count_records'}, 'width': '8%'},
                        {'if': {'column_id': 'total_amount'}, 'width': '10%'},
                        {'if': {'column_id': 'count_inkomed'}, 'width': '8%'},
                        {'if': {'column_id': 'sum_inkomed'}, 'width': '10%'},
                        {'if': {'column_id': 'count_sogaz'}, 'width': '8%'},
                        {'if': {'column_id': 'sum_sogaz'}, 'width': '10%'},
                        {'if': {'column_id': 'count_inogor'}, 'width': '8%'},
                        {'if': {'column_id': 'sum_inogor'}, 'width': '10%'},
                    ]
                )
            ]
        )
    ])


# Callback для обновления отделений при выборе корпуса
@callback(
    [
        Output(f'dropdown-building-econ-financial-indicators', 'options'),
        Output(f'dropdown-department-econ-financial-indicators', 'options'),
        Output(f'dropdown-profile-econ-financial-indicators', 'options'),
        Output(f'dropdown-doctor-econ-financial-indicators', 'options')
    ],
    [
        Input(f'dropdown-year-econ-financial-indicators', 'value'),
        Input(f'dropdown-building-econ-financial-indicators', 'value'),
        Input(f'dropdown-department-econ-financial-indicators', 'value'),
        Input(f'dropdown-profile-econ-financial-indicators', 'value'),
        Input(f'dropdown-doctor-econ-financial-indicators', 'value')
    ]
)
def update_filters(selected_year, selected_buildings, selected_departments, selected_profiles, selected_doctors):
    selected_year = selected_year or datetime.now().year
    buildings = get_available_buildings()
    departments = get_available_departments(selected_buildings)
    profiles = get_available_profiles(selected_buildings, selected_departments)
    doctors = get_available_doctors(
        building_ids=selected_buildings,
        department_ids=selected_departments,
        profile_ids=selected_profiles,
        selected_year=selected_year
    )
    return buildings, departments, profiles, doctors


@callback(
    [
        Output(f'date-container-input-econ-financial-indicators', 'style'),
        Output(f'date-container-treatment-econ-financial-indicators', 'style'),
    ],
    Input(f'dropdown-report-type-econ-financial-indicators', 'value')
)
def toggle_date_containers(report_type):
    if report_type == 'initial_input':
        return {'display': 'block'}, {'display': 'none'}
    if report_type == 'treatment':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@callback(
    [
        Output(f'status-group-container-econ-financial-indicators', 'style'),
        Output(f'status-individual-container-econ-financial-indicators', 'style')
    ],
    Input(f'status-selection-mode-econ-financial-indicators', 'value')
)
def toggle_status_selection_mode(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    return {'display': 'none'}, {'display': 'block'}


# Callback для обновления примененных фильтров
@callback(
    Output(f'applied-filters-econ-financial-indicators', 'children'),
    [
        Input(f'dropdown-year-econ-financial-indicators', 'value'),
        Input(f'range-slider-month-econ-financial-indicators', 'value'),
        Input(f'dropdown-report-type-econ-financial-indicators', 'value'),
        Input(f'dropdown-inogorodniy-econ-financial-indicators', 'value'),
        Input(f'dropdown-amount-null-econ-financial-indicators', 'value'),
        Input(f'dropdown-building-econ-financial-indicators', 'value'),
        Input(f'dropdown-department-econ-financial-indicators', 'value'),
        Input(f'dropdown-profile-econ-financial-indicators', 'value'),
        Input(f'dropdown-doctor-econ-financial-indicators', 'value'),
        Input(f'status-selection-mode-econ-financial-indicators', 'value'),
        Input(f'status-group-radio-econ-financial-indicators', 'value'),
        Input(f'status-individual-dropdown-econ-financial-indicators', 'value')
    ]
)
def update_applied_filters(
    selected_year, selected_period, report_type, inogorodniy, amount_null, selected_buildings,
    selected_departments, selected_profiles, selected_doctors,
    status_selection_mode, status_group_value, status_individual_values
):
    filters = []
    
    # Правила отбора для "Сверхподушевик" (должны соответствовать SQL в query.py)
    sverhpod_text = "Правила 'Сверхподушевик': цели " + ', '.join(SVERHPOD_GOALS)

    if selected_year:
        filters.append(f"Год: {selected_year}")
    
    if selected_period and isinstance(selected_period, list) and len(selected_period) == 2:
        month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        start_month = month_names.get(selected_period[0], f'Месяц {selected_period[0]}')
        end_month = month_names.get(selected_period[1], f'Месяц {selected_period[1]}')
        filters.append(f"Период: {start_month} - {end_month} {selected_year}")

    report_type_labels = {
        'month': 'По отчетному месяцу',
        'initial_input': 'По дате формирования',
        'treatment': 'По дате окончания лечения'
    }
    if report_type:
        filters.append(f"Тип отчета: {report_type_labels.get(report_type, report_type)}")

    inogor_labels = {'1': 'Местные', '2': 'Иногородние', '3': 'Все'}
    if inogorodniy:
        filters.append(f"Местные/иногородние: {inogor_labels.get(inogorodniy, inogorodniy)}")

    amount_labels = {'1': 'Не нулевые', '2': 'Нулевые', '3': 'Все'}
    if amount_null:
        filters.append(f"Сумма талона: {amount_labels.get(amount_null, amount_null)}")
    
    if selected_buildings:
        buildings = get_available_buildings()
        building_names = [b['label'] for b in buildings if b['value'] in selected_buildings]
        filters.append(f"Корпус: {', '.join(building_names)}")
    
    if selected_departments:
        departments = get_available_departments(selected_buildings)
        department_names = [d['label'] for d in departments if d['value'] in selected_departments]
        filters.append(f"Отделение: {', '.join(department_names)}")

    if selected_profiles:
        profile_count = len(selected_profiles) if isinstance(selected_profiles, list) else 1
        filters.append(f"Специальности: {profile_count} выбрано")

    if selected_doctors:
        doctor_count = len(selected_doctors) if isinstance(selected_doctors, list) else 1
        filters.append(f"Врачи: {doctor_count} выбрано")

    status_list = []
    if status_selection_mode == 'group' and status_group_value and status_group_value in status_groups:
        status_list = status_groups[status_group_value]
    elif status_selection_mode == 'individual' and status_individual_values:
        status_list = (
            status_individual_values
            if isinstance(status_individual_values, list)
            else [status_individual_values]
        )
    if status_list:
        filters.append(f"Статусы: {', '.join(status_list)}")
    
    if filters:
        return f"Примененные фильтры: {'; '.join(filters)}; {sverhpod_text}"
    else:
        return f"Фильтры не применены; {sverhpod_text}"


# Callback для обновления таблицы
@callback(
    [
        Output(f'result-table-econ-financial-indicators', 'columns'),
        Output(f'result-table-econ-financial-indicators', 'data'),
        Output(f'result-table-econ-financial-indicators', 'style_data_conditional')
    ],
    Input(f'update-button-econ-financial-indicators', 'n_clicks'),
    [
        State(f'dropdown-year-econ-financial-indicators', 'value'),
        State(f'range-slider-month-econ-financial-indicators', 'value'),
        State(f'dropdown-report-type-econ-financial-indicators', 'value'),
        State(f'dropdown-inogorodniy-econ-financial-indicators', 'value'),
        State(f'dropdown-amount-null-econ-financial-indicators', 'value'),
        State(f'dropdown-building-econ-financial-indicators', 'value'),
        State(f'dropdown-department-econ-financial-indicators', 'value'),
        State(f'dropdown-profile-econ-financial-indicators', 'value'),
        State(f'dropdown-doctor-econ-financial-indicators', 'value'),
        State(f'date-picker-range-input-econ-financial-indicators', 'start_date'),
        State(f'date-picker-range-input-econ-financial-indicators', 'end_date'),
        State(f'date-picker-range-treatment-econ-financial-indicators', 'start_date'),
        State(f'date-picker-range-treatment-econ-financial-indicators', 'end_date'),
        State(f'status-selection-mode-econ-financial-indicators', 'value'),
        State(f'status-group-radio-econ-financial-indicators', 'value'),
        State(f'status-individual-dropdown-econ-financial-indicators', 'value')
    ]
)
def update_table(
    n_clicks, selected_year, selected_period, report_type, inogorodniy, amount_null,
    selected_buildings, selected_departments, selected_profiles, selected_doctors,
    start_date_input, end_date_input, start_date_treatment, end_date_treatment,
    status_selection_mode, status_group_value, status_individual_values
):
    if not n_clicks:
        raise exceptions.PreventUpdate
    if not selected_year:
        return [], [], []
    if (report_type or 'month') == 'month' and (not selected_period or len(selected_period) != 2):
        return [], [], []
    
    try:
        selected_months = selected_period

        status_list = []
        if status_selection_mode == 'group':
            if status_group_value and status_group_value in status_groups:
                status_list = status_groups[status_group_value]
        elif status_selection_mode == 'individual':
            if status_individual_values:
                status_list = (
                    status_individual_values
                    if isinstance(status_individual_values, list)
                    else [status_individual_values]
                )

        selected_doctor_ids = parse_doctor_ids(selected_doctors)

        start_date_input_formatted = None
        end_date_input_formatted = None
        start_date_treatment_formatted = None
        end_date_treatment_formatted = None
        if report_type == 'initial_input' and start_date_input and end_date_input:
            start_date_input_formatted = datetime.strptime(
                start_date_input.split('T')[0], '%Y-%m-%d'
            ).strftime('%d-%m-%Y')
            end_date_input_formatted = datetime.strptime(
                end_date_input.split('T')[0], '%Y-%m-%d'
            ).strftime('%d-%m-%Y')
        elif report_type == 'treatment' and start_date_treatment and end_date_treatment:
            start_date_treatment_formatted = datetime.strptime(
                start_date_treatment.split('T')[0], '%Y-%m-%d'
            ).strftime('%d-%m-%Y')
            end_date_treatment_formatted = datetime.strptime(
                end_date_treatment.split('T')[0], '%Y-%m-%d'
            ).strftime('%d-%m-%Y')
        
        # Выполняем запрос
        sql_query = sql_query_financial_indicators(
            selected_year=selected_year,
            selected_months=selected_months,
            building_ids=selected_buildings,
            department_ids=selected_departments,
            profile_ids=selected_profiles,
            inogorodniy=inogorodniy,
            amount_null=amount_null,
            doctor_ids=selected_doctor_ids,
            report_type=report_type or 'month',
            input_start=start_date_input_formatted,
            input_end=end_date_input_formatted,
            treatment_start=start_date_treatment_formatted,
            treatment_end=end_date_treatment_formatted,
            status_list=status_list
        )
        
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        # Форматируем колонки
        formatted_columns = [
            {'name': 'Цель', 'id': 'goal'},
            {'name': 'Кол-во записей', 'id': 'count_records', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Общая сумма', 'id': 'total_amount', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
            {'name': 'Кол-во Инкомед', 'id': 'count_inkomed', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Сумма Инкомед', 'id': 'sum_inkomed', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
            {'name': 'Кол-во Согаз', 'id': 'count_sogaz', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Сумма Согаз', 'id': 'sum_sogaz', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
            {'name': 'Кол-во Иногородние', 'id': 'count_inogor', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Сумма Иногородние', 'id': 'sum_inogor', 'type': 'numeric', 'format': {'specifier': ',.2f'}}
        ]
        
        # Условное форматирование: подсветка строки "Сверхподушевик" и всех целей из правил
        style_data_conditional = [
            {
                'if': {'filter_query': '{goal} = "Сверхподушевик"'},
                'backgroundColor': '#d4edda',  # bootstrap alert-success bg
                'color': '#155724',            # bootstrap alert-success text
                'fontWeight': 'bold'
            }
        ] + [
            {
                'if': {'filter_query': f'{{goal}} = "{g}"'},
                'backgroundColor': '#d4edda',
                'color': '#155724',
                'fontWeight': 'bold'
            }
            for g in SVERHPOD_GOALS
        ]

        return formatted_columns, data, style_data_conditional
        
    except Exception as e:
        print(f"Ошибка при обновлении таблицы: {str(e)}")
        return [], [], []
