from dash import html, Input, Output, dash_table, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.it_department.for_smo.query import sql_query_for_smo

type_page = "for-smo"

tab_layout_for_smo = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Отчет по страховым помесячно',
                    className='label'),

                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                html.Hr(),
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
                    ], className='block', style={'width': '500px'}),
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
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, sql_query_for_smo)
    else:
        columns, data = [], []
    return columns, data
