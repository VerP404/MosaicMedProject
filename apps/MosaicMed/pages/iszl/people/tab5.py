from dash import html, dcc, Output, Input, dash_table, State, callback_context
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc
from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.iszl.people.query import sql_query_people_iszl_all_168n_oms, sql_query_people_iszl_168n_oms

type_page = "people-iszl-168n-oms"
alert_text = """Половозрастная структура прикрепленного населения по корпусам из ИСЗЛ находящихся на диспансреном наблюдении по приказу 168н и поданными талонами (статусы 1,2,3,6,8)
"""

tab5_layout_people_iszl = html.Div([
    dbc.Alert(dcc.Markdown(alert_text), color="danger", style={'padding': '0 0 0 10px'}),
    html.H5("Выберите подразделение:"),
    dcc.RadioItems(
        id='processing-type',
        options=[
            {'label': 'По корпусам', 'value': 'БУЗ ВО \'ВГП №3\''},
            {'label': 'ГП №3', 'value': 'ГП3'},
            {'label': 'ГП №11', 'value': 'ГП11'},
            {'label': 'ОАПП №1', 'value': 'ОАПП1'},
            {'label': 'ОАПП №2', 'value': 'ОАПП2'},
            {'label': 'ДП №1', 'value': 'ДП1'},
            {'label': 'ДП №8', 'value': 'ДП8'},
            {'label': 'Распределить', 'value': 'распределить'},
        ],
        value='БУЗ ВО \'ВГП №3\''
    ),
    html.Hr(),
    html.Button('Получить данные', id=f'get-data-button-{type_page}'),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    html.Hr(),
    html.Div(
        [
            html.Div(id=f'name-table-{type_page}'),

            dash_table.DataTable(id=f'result-table-{type_page}', columns=[],
                                 editable=True,
                                 filter_action="native",
                                 sort_action="native",
                                 sort_mode='multi',
                                 export_format='xlsx',
                                 export_headers='display',
                                 style_table={'width': '1200px'},
                                 style_header={'whiteSpace': 'normal', 'text-align': 'center'},
                                 style_data={'width': '100px',
                                             'whiteSpace': 'normal',
                                             'padding-right': '20px',
                                             'text-align': 'right', },
                                 ),
        ], className='block'),

])


@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'name-table-{type_page}', 'children'),
     ],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),
     Input('processing-type', 'value')])
def data_processing(n_clicks, report_type):
    if n_clicks is None:
        return [], [], html.Div(), html.Div()
    # Получить контекст вызова
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == f'get-data-button-{type_page}':
        loading_output = html.Div([dcc.Loading(type="default")])
        if report_type == 'БУЗ ВО \'ВГП №3\'':
            bind_params = ''
            columns, data = TableUpdater.query_to_df(engine, sql_query_people_iszl_all_168n_oms, bind_params)
        else:
            bind_params = {
                'korp': report_type,
            }
            columns, data = TableUpdater.query_to_df(engine, sql_query_people_iszl_168n_oms, bind_params)
        return columns, data, loading_output, html.H5(
            f'Половозрастная структура прикрепленного населения из подлежащих диспансерному наблюдению по 168н по {report_type}')
    else:
        return [], [], html.Div(), html.Div()
