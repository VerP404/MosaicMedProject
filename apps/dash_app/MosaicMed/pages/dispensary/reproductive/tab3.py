from dash import html, Input, Output, dash_table, dcc
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.pages.dispensary.reproductive.query import sqlquery_people_reproductive_tab3

type_page = "tab3-reproductive"

tab3_reproductive = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Пациенты прошедшие ДВ4 или ОПВ (по оплаченным) в текущем году с отметкой о прохождении ДР1 (все статусы).',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                card_table(f'result-table1-{type_page}',
                           "Список пациентов прошедших ДВ4 или ОПВ (по оплаченным) в текущем году"),

            ],
        )
    ]
)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns, data = TableUpdater.query_to_df(engine, sqlquery_people_reproductive_tab3)
        return columns, data, loading_output
    else:
        columns, data = [], []
        loading_output = html.Div()  # Пустой контейнер для отображения после выполнения операции
    return columns, data, loading_output
