import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, dash_table
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater
from datetime import datetime

from services.MosaicMed.generate_pages.elements import card_table

type_page = "children_list"

def get_birthdate_cutoff():
    current_year = datetime.now().year
    birthdate_cutoff = datetime(current_year - 2, 10, 1)
    return birthdate_cutoff.strftime('%d-%m-%Y')

tab4_layout_other_children_list = html.Div(
    [
        html.Div(
            [
                html.H3(id=f'header-{type_page}', className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                card_table(f'result-table-{type_page}', "Список детей до 1.5 лет с профилактическими осмотрами (ПН1)", 15),
            ], className='block'),
    ]
)

query_download_children_list_template = '''
    SELECT "Пациент",
           "Дата рождения",
           "Пол",
           "Подразделение"                                                                as Корпус,
           STRING_AGG(concat("Окончание лечения", ' ', SPLIT_PART("Врач", ' ', 2)), ', ') AS "Талон: Дата и врач",
           COUNT(*)                                                                       AS "К-во талонов",
           round(SUM(CAST("Сумма" AS numeric(15, 2)))::numeric, 2)                                                as Сумма
    FROM oms.oms_data
    WHERE "Цель" = 'ПН1'
      AND to_date("Дата рождения", 'DD-MM-YYYY') > '{birthdate_cutoff}'      
      and "Статус" in ('1', '2', '3', '6', '8') 
    GROUP BY "Пациент", "Дата рождения", "Пол", "Подразделение"
'''

@app.callback(
    Output(f'header-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_header(n_intervals):
    birthdate_cutoff = get_birthdate_cutoff()
    return f'Список детей до 1.5 лет с профилактическими осмотрами (ПН1) (дата рождения позже {birthdate_cutoff})'

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
        birthdate_cutoff = get_birthdate_cutoff()
        query_download_children_list = query_download_children_list_template.format(birthdate_cutoff=birthdate_cutoff)
        columns, data = TableUpdater.query_to_df(engine, query_download_children_list)
    else:
        columns, data = [], []

    return columns, data, loading_output
