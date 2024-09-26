import pandas as pd
from dash import html, Input, Output, dash_table, dcc, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.it_department.status_months.query import sql_query_stat_month

type_page = "stat-months"

tab_layout_other_stat_months = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Отчет по статусам помесячно',
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
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, sql_query_stat_month)
    else:
        columns, data = [], []
    return columns, data
