from dash import html, dcc, Output, Input, dash_table, exceptions, callback_context
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater

from services.MosaicMed.pages.dispensary.adults.query import sql_query_flu_list, sql_query_flu_list2, sql_query_flu_list3, \
    sql_query_flu_report

type_page = "tab6-da"

tab6_layout_da = html.Div(
    [
        html.Hr(),
        html.H5("Фильтр по наличию даты флюорообследования в Флюоромониторинге:"),
        dcc.RadioItems(
            id=f'processing-type-{type_page}',
            options=[
                {'label': 'все записи', 'value': 'all'},
                {'label': 'Без даты флюры', 'value': 'not_fl'},
                {'label': 'Год флюры меньше года услуги', 'value': 'date_fl'},
            ],
            value='all'
        ),
        html.Hr(),
        html.Div([
            html.H3(),
            html.Button('Получить данные', id=f'get-data-button-{type_page}'),
            dcc.Loading(id=f'loading-output-{type_page}', type='default'), ]),
        html.Hr(),
        html.H5('Сводный отчет', className='label'),
        html.Div(
            [
                dash_table.DataTable(id=f'result-table1-{type_page}', columns=[],
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     style_table={'width': '800px'}
                                     ),
            ], className='block'),
        html.Hr(),
        html.H5('Список данных из карт ОПВ и ДВ4 с отметкой о дате прохождения флюорографии в Флюоромониторинге',
                className='label'),

        html.Div(
            [
                dash_table.DataTable(id=f'result-table2-{type_page}', columns=[],
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
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),
     Input(f'processing-type-{type_page}', 'value')]
)
def update_table(n_clicks, report_type):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == f'get-data-button-{type_page}':
        loading_output = html.Div([dcc.Loading(type="default")])
        columns1, data1 = TableUpdater.query_to_df(engine, sql_query_flu_report, '')

        if report_type == 'all':
            columns2, data2 = TableUpdater.query_to_df(engine, sql_query_flu_list, '')
        elif report_type == 'not_fl':
            columns2, data2 = TableUpdater.query_to_df(engine, sql_query_flu_list2, '')
        elif report_type == 'date_fl':
            columns2, data2 = TableUpdater.query_to_df(engine, sql_query_flu_list3, '')
        else:
            return [], [], [], [], html.Div()
        return columns1, data1, columns2, data2, loading_output
    else:
        return [], [], [], [], html.Div()
