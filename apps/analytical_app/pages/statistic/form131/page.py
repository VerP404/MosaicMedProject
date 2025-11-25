from datetime import datetime
from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
import time

from apps.analytical_app.app import app
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.statistic.form131.query import sql_query_form131
from apps.analytical_app.query_executor import engine
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years

type_page = "form131"

alert_text = """Условия:
- Отчет для 131 формы (до диспансеризации)
- Фильтрация по году
- Цели: ДВ4, ДВ2, ОПВ, УД1, УД2, ДР1, ДР2, ПН1, ДС1, ДС2
"""

statistic_form131 = html.Div(
    [
        html.Div(
            [
                html.H3('Фильтры', className='label'),
                dbc.Row(
                    [
                        filter_years(type_page),
                    ],
                    className="mb-3"
                ),
                html.Div(
                    [
                        dbc.Button('Получить данные', id=f'get-data-button-{type_page}', color="primary", className="mt-3"),
                        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                        html.Div(id=f'execution-time-{type_page}', className='filters-label', style={'marginTop': '10px'}),
                    ]
                ),
            ],
            className='filter'
        ),
        html.Div(
            [
                html.H3('Отчет для 131 формы', className='label'),
                dbc.Alert(dcc.Markdown(alert_text), color="info", style={'padding': '0 0 0 10px'}),
            ],
            className='block'
        ),
        html.Hr(),
        card_table(f'result-table-{type_page}', "Отчет для 131 формы", 20),
    ]
)


@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'execution-time-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value')]
)
def update_table(n_clicks, selected_year):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    
    if selected_year is None:
        return [], [], html.Div(), html.Div("Выберите год для получения данных", style={'color': 'red'})
    
    loading_output = html.Div([dcc.Loading(type="default")])
    start_time = time.time()
    
    try:
        bind_params = {
            'selected_year': str(selected_year)
        }
        columns, data = TableUpdater.query_to_df(engine, sql_query_form131, bind_params)
        
        execution_time = time.time() - start_time
        if execution_time < 1:
            time_text = f"{execution_time*1000:.0f}мс"
        else:
            time_text = f"{execution_time:.1f}с"
        
        record_count = len(data)
        status_text = f"Запрос выполнен за {time_text}. Найдено записей: {record_count}"
        
        return columns, data, loading_output, html.Div(status_text, style={'color': 'green', 'fontWeight': 'bold'})
    except Exception as e:
        execution_time = time.time() - start_time
        if execution_time < 1:
            time_text = f"{execution_time*1000:.0f}мс"
        else:
            time_text = f"{execution_time:.1f}с"
        error_text = f"Ошибка выполнения запроса за {time_text}: {str(e)}"
        return [], [], loading_output, html.Div(error_text, style={'color': 'red', 'fontWeight': 'bold'})

