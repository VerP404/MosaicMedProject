from dash import html, Input, Output, dash_table, dcc, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.iszl.disp_nabl.query import sql_query_list_iszl, sql_query_list_oms, sql_query_list_iszl_oms, \
    sql_query_list_iszl_oms_report

# Отчет для сборки талонов
type_page = "tab4_disp_nab_cel_3"

alert_text1 = """После получения данных для открытия списков нажмите на соответствующую кнопку
"""
tab4_layout_disp_nab_cel_3 = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Список пациентов из ИСЗЛ',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                dbc.Alert(
                    dcc.Markdown(alert_text1),
                    color="danger",
                    style={'padding': '0'},
                ),
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Список пациентов из ИСЗЛ с диагнозами, запланированными на диспансерное наблюдение в текущем году",
                            id=f"alert-toggle-auto1-{type_page}",
                            className="me-1", n_clicks=0
                        ),
                        html.Hr(),
                        dbc.Alert(
                            html.Div(
                                [
                                    dash_table.DataTable(id=f'result-table1-{type_page}',
                                                         columns=[],
                                                         editable=True,
                                                         filter_action="native",
                                                         sort_action="native",
                                                         sort_mode='multi',
                                                         export_format='xlsx',
                                                         export_headers='display',
                                                         ),
                                ], className='block'),
                            id=f"alert-auto1-{type_page}",
                            color="light",
                            is_open=False,
                            style={'padding': '0 0 0 10px'}),
                    ]
                ),
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Список пациентов в талонах ОМС, выставленных в текущем году",
                            id=f"alert-toggle-auto2-{type_page}",
                            className="me-1", n_clicks=0
                        ),
                        html.Hr(),
                        dbc.Alert(
                            html.Div(
                                [
                                    dash_table.DataTable(id=f'result-table2-{type_page}',
                                                         columns=[],
                                                         editable=True,
                                                         filter_action="native",
                                                         sort_action="native",
                                                         sort_mode='multi',
                                                         export_format='xlsx',
                                                         export_headers='display',
                                                         style_table={'width': '600px'},
                                                         style_cell={'textAlign': 'center'}
                                                         ),
                                ], className='block'),
                            id=f"alert-auto2-{type_page}",
                            color="light",
                            is_open=False,
                            style={'padding': '0 0 0 10px'}),
                    ]
                ),
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Список пациентов, состоящих в ИСЗЛ на диспансерном наблюдении по 168н с отметкой о поданном талоне ОМС по диагнозу",
                            id=f"alert-toggle-auto3-{type_page}",
                            className="me-1", n_clicks=0
                        ),
                        html.P(),
                        dbc.Alert(
                            dcc.Markdown(
                                "Если поле 'Нет талона омс' пустое, то пациент осмотрен по всем диагнозам 168н по которым он был запланирован"),
                            color="danger",
                            style={'padding': '0'},
                        ),
                        html.Hr(),
                        dbc.Alert(
                            html.Div(
                                    html.Div([
                                        dash_table.DataTable(id=f'result-table3-{type_page}',
                                                             columns=[],
                                                             editable=True,
                                                             filter_action="native",
                                                             sort_action="native",
                                                             sort_mode='multi',
                                                             export_format='xlsx',
                                                             export_headers='display',
                                                             style_table={'width': '600px'},
                                                             style_cell={'textAlign': 'center'}
                                                             ),
                                        html.Hr(),

                                        dash_table.DataTable(id=f'result-table4-{type_page}',
                                                             columns=[],
                                                             editable=True,
                                                             filter_action="native",
                                                             sort_action="native",
                                                             sort_mode='multi',
                                                             export_format='xlsx',
                                                             export_headers='display',
                                                             style_table={'width': '600px'},
                                                             style_cell={'textAlign': 'center'}
                                                             )
                                    ]
                                    )
                            ),
                            id=f"alert-auto3-{type_page}",
                            color="light",
                            is_open=False,
                            style={'padding': '0 0 0 10px'}),
                    ]
                ),
            ],
        )
    ]
)


@app.callback(
    Output(f"alert-auto1-{type_page}", "is_open"),
    [Input(f"alert-toggle-auto1-{type_page}", "n_clicks")],
    [State(f"alert-auto1-{type_page}", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output(f"alert-auto2-{type_page}", "is_open"),
    [Input(f"alert-toggle-auto2-{type_page}", "n_clicks")],
    [State(f"alert-auto2-{type_page}", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output(f"alert-auto3-{type_page}", "is_open"),
    [Input(f"alert-toggle-auto3-{type_page}", "n_clicks")],
    [State(f"alert-auto3-{type_page}", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data'),
     Output(f'result-table4-{type_page}', 'columns'),
     Output(f'result-table4-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],  # Добавляем компонент для отображения загрузки
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns, data = TableUpdater.query_to_df(engine, sql_query_list_iszl)
        columns2, data2 = TableUpdater.query_to_df(engine, sql_query_list_oms)
        columns3, data3 = TableUpdater.query_to_df(engine, sql_query_list_iszl_oms_report)
        columns4, data4 = TableUpdater.query_to_df(engine, sql_query_list_iszl_oms)
        return columns, data, columns2, data2, columns3, data3, columns4, data4, loading_output
    else:
        columns, data, columns2, data2, columns3, data3, columns4, data4 = [], [], [], [], [], [], [], []
        loading_output = html.Div()  # Пустой контейнер для отображения после выполнения операции
    return columns, data, columns2, data2, columns3, data3, columns4, data4, loading_output
