import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, dash_table
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.pages.dispensary.children.query import query_download_children_list_not_pn1

type_page = "children_list_not_pn"

tab5_layout_children_list_not_pn = html.Div(
    [
        html.Div(
            [
                html.H3('Список прикрепленных детей без профилактического осмотра (ПН1)', className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                card_table(f'result-table-{type_page}',
                           "Список прикрепленных детей без профилактического осмотра (ПН1)", 15),

            ], className='block'),
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
