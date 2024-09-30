from dash import html, Input, Output, dash_table, dcc, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.it_department.generation_invoices.query import sql_gen_invoices, sql_gen_invoices_povt, sql_gen_name_check

# Отчет для сборки талонов
type_page = "gen_invoice"

image_path = r'\assets\img\name_accounts.jpg'
tab_layout_other_gen_invoices = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Отчет для сборки талонов по дате создания талона и цели. Первичных и повторных',
                    className='label'),

                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Обозначение счетов", id=f"alert-toggle-auto-{type_page}", className="me-1", n_clicks=0
                        ),
                        html.Hr(),
                        dbc.Alert(
                            html.Img(src=image_path, alt='My Image', style={'display': 'block', 'margin': 'auto'}),
                            id=f"alert-auto-{type_page}",
                            color="light",
                            is_open=False,
                            style={'padding': '0 0 0 10px'}),
                    ]
                ),
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Список счетов", id=f"alert-toggle-auto3-{type_page}",
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
                                                         ),
                                ], className='block'),
                            id=f"alert-auto3-{type_page}",
                            color="light",
                            is_open=False,
                            style={'padding': '0 0 0 10px'}),
                    ]
                ),
                html.Hr(),
                html.Div(
                    [
                        html.H5(
                            'Первичные - статус 1',
                            className='label'),
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
                html.Hr(),
                html.Div(
                    [
                        html.H5(
                            'Повторные - статусы 4, 6 и 8',
                            className='label'),
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
            ],
        )
    ]
)


@app.callback(
    Output(f"alert-auto-{type_page}", "is_open"),
    [Input(f"alert-toggle-auto-{type_page}", "n_clicks")],
    [State(f"alert-auto-{type_page}", "is_open")],
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
     Output(f'result-table1-{type_page}', 'data')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, sql_gen_invoices)
    else:
        columns, data = [], []
    return columns, data


@app.callback(
    [Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, sql_gen_invoices_povt)
    else:
        columns, data = [], []
    return columns, data


@app.callback(
    [Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, sql_gen_name_check)
    else:
        columns, data = [], []
    return columns, data