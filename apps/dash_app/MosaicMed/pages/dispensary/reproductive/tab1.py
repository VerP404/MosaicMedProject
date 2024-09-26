import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, dash_table, State, callback_context
from datetime import datetime
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.pages.dispensary.reproductive.query import sqlquery_people_reproductive, \
    sqlquery_people_reproductive_all

type_page = "tab1-reproductive"
alert_text = """Половозрастная структура прикрепленного населения по корпусам из ИСЗЛ для проведения диспансеризации 
"""

tab1_reproductive = html.Div([
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

            card_table(f'result-table-{type_page}', "Половозрастная структура прикрепленного населения по корпусам из ИСЗЛ для проведения репродуктивной диспансеризации"),

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
            columns, data = TableUpdater.query_to_df(engine, sqlquery_people_reproductive_all(), bind_params)
        else:
            bind_params = {
                'korp': report_type,
            }
            columns, data = TableUpdater.query_to_df(engine, sqlquery_people_reproductive(), bind_params)
        return columns, data, loading_output, html.H5(
            f'Половозрастная структура прикрепленного населения по {report_type}')
    else:
        return [], [], html.Div(), html.Div()
