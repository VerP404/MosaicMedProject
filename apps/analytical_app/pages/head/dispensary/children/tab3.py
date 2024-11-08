import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, dash_table

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.children.query import query_download_children_list_not_pn1
from apps.analytical_app.query_executor import engine
from apps.analytical_app.app import app

type_page = "hildren-list-not-pn"

children_list_not_pn = html.Div(
    [
        html.Div(
            [
                html.H3('Список прикрепленных детей без профилактического осмотра (ПН1)', className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                card_table(f'result-table-{type_page}',
                           "Отчет по всем видам диспансеризации детей с разбивкой по возрастам",
                           page_size=10)
            ], className='block',),
    ]
)


@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    loading_output = html.Div([dcc.Loading(type="default")])
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, query_download_children_list_not_pn1)
    else:
        columns, data = [], []

    return columns, data, loading_output
