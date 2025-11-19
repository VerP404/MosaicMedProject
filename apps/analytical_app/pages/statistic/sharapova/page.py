from datetime import datetime, timedelta
import time
from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from apps.analytical_app.callback import get_selected_dates, TableUpdater
from apps.analytical_app.app import app
from apps.analytical_app.pages.statistic.sharapova.query import sql_query_sharapova, sql_query_sharapova_doctors
from apps.analytical_app.query_executor import engine
from apps.analytical_app.elements import card_table

type_page = "sharapova"

# Контент для вкладки "По подразделениям"
departments_tab = html.Div(
    [
        dbc.Row([
            dbc.Col([
                html.Div(id=f'loading-status-{type_page}-departments', style={'text-align': 'center', 'margin': '10px 0'}),
            ], width=12)
        ]),
        dcc.Loading(id=f'loading-output-{type_page}-departments', type='default'),
        card_table(f'result-table-{type_page}-departments', "Отчет по подразделениям", page_size=25),
    ],
    style={"padding": "0rem"}
)

# Контент для вкладки "По врачам"
doctors_tab = html.Div(
    [
        dbc.Row([
            dbc.Col([
                html.Div(id=f'loading-status-{type_page}-doctors', style={'text-align': 'center', 'margin': '10px 0'}),
            ], width=12)
        ]),
        dcc.Loading(id=f'loading-output-{type_page}-doctors', type='default'),
        card_table(f'result-table-{type_page}-doctors', "Отчет по врачам", page_size=25),
    ],
    style={"padding": "0rem"}
)

statistic_sharapova = html.Div(
    [
        # Блок фильтров
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row([
                                dbc.Col(
                                    dbc.Button(
                                        "Получить данные",
                                        id=f'update-button-{type_page}',
                                        color="primary",
                                        className="mt-3"
                                    ),
                                    width=2
                                ),
                                dbc.Col(
                                    dbc.Alert(
                                        [
                                            html.P("Категории диагнозов:", style={"margin-bottom": "5px", "font-weight": "bold"}),
                                            html.Ul([
                                                html.Li("БСК - болезни системы кровообращения (I00-I99)"),
                                                html.Li("Онко - онкологические заболевания (C00-C97)"),
                                                html.Li("Хобл - хроническая обструктивная болезнь легких (J44)"),
                                                html.Li("СД - сахарный диабет (E10-E11)"),
                                                html.Li("Другая - все остальные диагнозы, не относящиеся к вышеперечисленным категориям"),
                                            ]),
                                        ],
                                        color="info"
                                    ),
                                    width=10
                                ),
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Label('Дата начала:', style={'font-weight': 'bold', 'margin-bottom': '5px'}),
                                    dcc.DatePickerSingle(
                                        id=f'date-picker-start-{type_page}',
                                        first_day_of_week=1,
                                        date=datetime.now().date() - timedelta(days=1),
                                        display_format='DD.MM.YYYY'
                                    ),
                                ], width=3),
                                dbc.Col([
                                    html.Label('Дата окончания:', style={'font-weight': 'bold', 'margin-bottom': '5px'}),
                                    dcc.DatePickerSingle(
                                        id=f'date-picker-end-{type_page}',
                                        first_day_of_week=1,
                                        date=datetime.now().date() - timedelta(days=1),
                                        display_format='DD.MM.YYYY'
                                    ),
                                ], width=3),
                                dbc.Col([
                                    html.Div(id=f'selected-date-{type_page}', className='filters-label'),
                                ], width=6),
                            ], className="mb-3"),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        # Вкладки
        dbc.Tabs(
            [
                dbc.Tab(
                    label="По подразделениям",
                    tab_id=f"tab-departments-{type_page}",
                    children=departments_tab
                ),
                dbc.Tab(
                    label="По врачам",
                    tab_id=f"tab-doctors-{type_page}",
                    children=doctors_tab
                ),
            ],
            active_tab=f"tab-departments-{type_page}",
            id=f"tabs-{type_page}"
        ),
    ],
    style={"padding": "0rem"}
)


# строка с выбранными датами
@app.callback(
    Output(f'selected-date-{type_page}', 'children'),
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_selected_dates(start_date, end_date):
    return get_selected_dates(start_date, end_date)


# Callback для таблицы по подразделениям
@app.callback(
    [Output(f'result-table-{type_page}-departments', 'columns'),
     Output(f'result-table-{type_page}-departments', 'data'),
     Output(f'loading-output-{type_page}-departments', 'children'),
     Output(f'loading-status-{type_page}-departments', 'children')],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'date-picker-start-{type_page}', 'date'),
    State(f'date-picker-end-{type_page}', 'date')
)
def update_table_departments(n_clicks, start_date, end_date):
    if n_clicks is None:
        raise PreventUpdate
    
    if (start_date is None) or (end_date is None):
        return [], [], html.Div(), "Выберите даты начала и окончания"
    
    loading_output = html.Div([dcc.Loading(type="default")])
    
    start_time = time.time()
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_sharapova, bind_params)
    execution_time = time.time() - start_time
    
    # Формируем статус загрузки
    if execution_time < 1:
        time_text = f"{execution_time*1000:.0f}мс"
    else:
        time_text = f"{execution_time:.1f}с"
    
    record_count = len(data)
    status_text = f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"
    
    return columns, data, loading_output, status_text


# Callback для таблицы по врачам
@app.callback(
    [Output(f'result-table-{type_page}-doctors', 'columns'),
     Output(f'result-table-{type_page}-doctors', 'data'),
     Output(f'loading-output-{type_page}-doctors', 'children'),
     Output(f'loading-status-{type_page}-doctors', 'children')],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'date-picker-start-{type_page}', 'date'),
    State(f'date-picker-end-{type_page}', 'date')
)
def update_table_doctors(n_clicks, start_date, end_date):
    if n_clicks is None:
        raise PreventUpdate
    
    if (start_date is None) or (end_date is None):
        return [], [], html.Div(), "Выберите даты начала и окончания"
    
    loading_output = html.Div([dcc.Loading(type="default")])
    
    start_time = time.time()
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_sharapova_doctors, bind_params)
    execution_time = time.time() - start_time
    
    # Формируем статус загрузки
    if execution_time < 1:
        time_text = f"{execution_time*1000:.0f}мс"
    else:
        time_text = f"{execution_time:.1f}с"
    
    record_count = len(data)
    status_text = f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"
    
    return columns, data, loading_output, status_text
