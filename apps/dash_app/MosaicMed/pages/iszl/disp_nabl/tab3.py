from dash import html, Input, Output, dash_table, dcc, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.iszl.disp_nabl.query import sql_query_disp_nabl_fgs, sql_query_disp_nabl_fgs_168n, sql_query_zap_obr

# Отчет для сборки талонов
type_page = "iszl-disp-nab-fgs"

alert_text1 = """Уникальные по пациенту (ЕНП) и диагнозу.  
Отобраны пациенты с диагнозом K и D12.8
"""

tab3_layout_disp_nab_fgs = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Список пациентов из ИСЗЛ по 168н с диагнозами "K" и "D12.8" с отметками о записи на ЭГДС/Колоноскопию',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                dbc.Alert(
                    dcc.Markdown(alert_text1),
                    color="danger",
                    style={'padding': '0'},
                ),
                html.Div(
                    [
                        dbc.Button(
                            "Пациенты в ИСЗЛ с группировкой по диагнозу", id=f"alert-toggle-auto1-{type_page}",
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
                            "Количество записанных пациентов на ЭГДС/Колоноскопию",
                            id=f"alert-toggle-auto2-{type_page}",
                            className="me-1", n_clicks=0
                        ),
                        html.Hr(),
                        dbc.Alert(
                            html.Div(
                                [
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
                        dbc.Alert('Список пациентов из ИСЗЛ с записью на ЭГДС/Колоноскопию', color="warning"),
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
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],  # Добавляем компонент для отображения загрузки
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns, data = TableUpdater.query_to_df(engine, sql_query_disp_nabl_fgs)
        columns2, data2 = TableUpdater.query_to_df(engine, sql_query_disp_nabl_fgs_168n)
        columns3, data3 = TableUpdater.query_to_df(engine, sql_query_zap_obr)
        return columns, data, columns2, data2, columns3, data3, loading_output
    else:
        columns, data, columns2, data2, columns3, data3 = [], [], [], [], [], []
        loading_output = html.Div()  # Пустой контейнер для отображения после выполнения операции
    return columns, data, columns2, data2, columns3, data3, loading_output
