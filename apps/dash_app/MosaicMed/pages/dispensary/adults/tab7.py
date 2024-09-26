import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, dash_table
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.dispensary.adults.query import sql_query_list_of_failed

type_page = "tab7-da"

tab7_layout_da = html.Div(
    [
        html.Div(
            [
                html.H3('Список прикрепленных без диспансеризации (ДВ4) и профосмотра (ОПВ)', className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                dash_table.DataTable(id=f'result-table-{type_page}',
                                     columns=[],
                                     page_size=15,
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
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
    loading_output = html.Div()

    if n_clicks > 0:
        loading_output = html.Div([dcc.Loading(type="default")])
        columns, data = TableUpdater.query_to_df(engine, sql_query_list_of_failed)
    else:
        columns, data = [], []

    return columns, data, loading_output
