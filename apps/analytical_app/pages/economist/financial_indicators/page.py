from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from dash import dash_table
from datetime import datetime

from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.financial_indicators.query import sql_query_financial_indicators
from apps.analytical_app.components.filters import (
    filter_years, filter_building, filter_department,
    get_available_buildings, get_available_departments
)
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.query_executor import engine


def layout(type_page="econ-financial-indicators"):
    """Layout для страницы финансовых показателей"""
    
    # Получаем текущий год и месяц
    current_year = datetime.now().year
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
                    # Год
                    dbc.Col([
                        html.Label("Год:", className="fw-bold"),
                        filter_years(type_page)
                    ], width=2),
                    
                    # Отчетный период
                    dbc.Col([
                        html.Label("Отчетный период:", className="fw-bold"),
                        dcc.Dropdown(
                            id=f'dropdown-period-{type_page}',
                            placeholder='Выберите месяц...',
                            clearable=False,
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
                            value=current_month
                        )
                    ], width=3),
                    
                    # Корпус
                    dbc.Col([
                        html.Label("Корпус:", className="fw-bold"),
                        filter_building(type_page)
                    ], width=3),
                    
                    # Отделение
                    dbc.Col([
                        html.Label("Отделение:", className="fw-bold"),
                        filter_department(type_page)
                    ], width=3),
                    
                    # Кнопка обновления
                    dbc.Col([
                        html.Label("", className="fw-bold"),  # Пустая метка для выравнивания
                        dbc.Button("Обновить", id=f'update-button-{type_page}', color="primary",
                                   className="mt-3")
                    ], width=1)
                ], className="mb-3"),
                
                # Информационные блоки
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(
                            "Отобраны талоны: оплаченные (статус 3)",
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
    Output(f'dropdown-department-econ-financial-indicators', 'options'),
    Input(f'dropdown-building-econ-financial-indicators', 'value')
)
def update_departments(selected_buildings):
    if not selected_buildings:
        return []
    return get_available_departments(selected_buildings)


# Callback для обновления примененных фильтров
@callback(
    Output(f'applied-filters-econ-financial-indicators', 'children'),
    [
        Input(f'dropdown-year-econ-financial-indicators', 'value'),
        Input(f'dropdown-period-econ-financial-indicators', 'value'),
        Input(f'dropdown-building-econ-financial-indicators', 'value'),
        Input(f'dropdown-department-econ-financial-indicators', 'value')
    ]
)
def update_applied_filters(selected_year, selected_period, selected_buildings, selected_departments):
    filters = []
    
    if selected_year:
        filters.append(f"Год: {selected_year}")
    
    if selected_period:
        month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        month_name = month_names.get(selected_period, f'Месяц {selected_period}')
        filters.append(f"Период: {month_name} {selected_year}")
    
    if selected_buildings:
        buildings = get_available_buildings()
        building_names = [b['label'] for b in buildings if b['value'] in selected_buildings]
        filters.append(f"Корпус: {', '.join(building_names)}")
    
    if selected_departments:
        departments = get_available_departments(selected_buildings)
        department_names = [d['label'] for d in departments if d['value'] in selected_departments]
        filters.append(f"Отделение: {', '.join(department_names)}")
    
    if filters:
        return f"Примененные фильтры: {'; '.join(filters)}"
    else:
        return "Фильтры не применены"


# Callback для обновления таблицы
@callback(
    [
        Output(f'result-table-econ-financial-indicators', 'columns'),
        Output(f'result-table-econ-financial-indicators', 'data')
    ],
    Input(f'update-button-econ-financial-indicators', 'n_clicks'),
    [
        State(f'dropdown-year-econ-financial-indicators', 'value'),
        State(f'dropdown-period-econ-financial-indicators', 'value'),
        State(f'dropdown-building-econ-financial-indicators', 'value'),
        State(f'dropdown-department-econ-financial-indicators', 'value')
    ]
)
def update_table(n_clicks, selected_year, selected_period, selected_buildings, selected_departments):
    if not n_clicks or not selected_year or not selected_period:
        return [], []
    
    try:
        # Используем выбранный месяц напрямую
        selected_month = selected_period
        
        # Выполняем запрос
        sql_query = sql_query_financial_indicators(
            selected_year=selected_year,
            selected_month=selected_month,
            building_ids=selected_buildings,
            department_ids=selected_departments
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
        
        return formatted_columns, data
        
    except Exception as e:
        print(f"Ошибка при обновлении таблицы: {str(e)}")
        return [], []
