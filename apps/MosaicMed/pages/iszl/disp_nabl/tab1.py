from dash import html, Input, Output, dash_table, dcc
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.iszl.disp_nabl.query import sql_query_disp_nabl_svod, sql_query_disp_nabl_talon

type_page = "iszl-disp-nab-svod"

alert_text1 = """Уникальные по пациенту (ЕНП) и диагнозу.  
Нарастающий итог.
План по БСК - 25135
План по онко - 3200
"""

tab1_layout_iszl_disp_nab_svod = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Сводная информация по пациентам из ИСЗЛ подлежащих диспансерному наблюдению по 168н и выставленным счетам ОМС',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                html.Div(
                    [
                        dash_table.DataTable(id=f'result-table2-{type_page}',
                                             columns=[],
                                             editable=False,
                                             sort_action="native",
                                             export_headers='display',
                                             style_header={'whiteSpace': 'normal', 'text-align': 'center'},
                                             style_data={'width': '147px',
                                                         'whiteSpace': 'normal',
                                                         'padding-right': '40px',
                                                         'text-align': 'right', },
                                             style_data_conditional=[
                                                 {
                                                     'if': {'column_id': 'Тип'},
                                                     'text-align': 'left',
                                                     'width': '240px',
                                                     'padding-left': '10px',
                                                 },
                                             ],
                                             ),
                    ], className='block'),
                html.Hr(),
                dbc.Alert(
                    dcc.Markdown(alert_text1),
                    color="danger",
                    style={'padding': '0'},
                ),
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
                                             style_header={'whiteSpace': 'normal', 'text-align': 'center'},
                                             style_data={'width': '147px',
                                                         'whiteSpace': 'normal',
                                                         'padding-right': '40px',
                                                         'text-align': 'right', },
                                             style_data_conditional=[
                                                 {
                                                     'if': {'column_id': 'Тип'},
                                                     'text-align': 'left',
                                                     'width': '240px',
                                                     'padding-left': '10px',
                                                 },
                                             ],
                                             ),
                    ], className='block'),
            ],
        )
    ]
)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        loading_output = html.Div([dcc.Loading(type="default")])
        data_df_tal = TableUpdater.query_to_df_data(engine, sql_query_disp_nabl_talon)
        data_df = TableUpdater.query_to_df_data(engine, sql_query_disp_nabl_svod)
        data_df['запланировано (70% от ИСЗЛ)'] = round(data_df['к-во в ИСЗЛ'] * 0.7, 0)
        data_df.iloc[0, 4] = 3200  # план для (C) онкология (пациенты)
        data_df.iloc[1, 4] = 25135  # план для (I) БСК (пациенты)
        data_df['% выставленных от запланированных 70%'] = round(
            data_df['выставлено'] / data_df['запланировано (70% от ИСЗЛ)'] * 100, 1).apply(
            lambda x: f"{x} %")

        data_df['% оплаченных от запланированных 70%'] = round(
            data_df['оплачено'] / data_df['запланировано (70% от ИСЗЛ)'] * 100, 1).apply(
            lambda x: f"{x} %")

        data_df['% выставленных от ИСЗЛ'] = round(
            data_df['выставлено'] / data_df['к-во в ИСЗЛ'] * 100, 1).apply(
            lambda x: f"{x} %")

        data_df['% оплаченных от ИСЗЛ'] = round(
            data_df['оплачено'] / data_df['к-во в ИСЗЛ'] * 100, 1).apply(
            lambda x: f"{x} %")

        columns1 = [{'name': col, 'id': col} for col in data_df.columns]
        data1 = data_df.to_dict('records')
        columns2 = [{'name': col, 'id': col} for col in data_df_tal.columns]
        data2 = data_df_tal.to_dict('records')
        return columns1, data1, columns2, data2, loading_output
    else:
        columns, data = [], []
        loading_output = html.Div()
    return columns, data, columns, data, loading_output
