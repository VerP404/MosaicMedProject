from datetime import datetime
from dash import html, Output, Input
import dash_bootstrap_components as dbc
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import  TableUpdater, get_selected_dates
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import date_start, date_end
from services.MosaicMed.pages.dispensary.children.query import sql_query_pn, sql_query_ds2,sql_query_pn_uniq_tal


type_page = "tab1-dс"

tab1_layout_dc = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    date_start('сформирован с:', type_page),
                                    date_end('сформирован по:', type_page),
                                ]
                            ),
                            html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        card_table(f'result-table1-{type_page}', "Профосмотр несовершеннолетних"),
        card_table(f'result-table2-{type_page}', "Диспансеризация детей сирот"),
        card_table(f'result-table3-{type_page}', "Уникальные дети в оплаченных картах ПН1"),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    Output(f'selected-date-{type_page}', 'children'),
    Input(f'date-start-{type_page}', 'date'),
    Input(f'date-end-{type_page}', 'date')
)
def update_selected_dates(start_date, end_date):
    return get_selected_dates(start_date, end_date)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data')
     ],
    [Input(f'date-start-{type_page}', 'date'),
     Input(f'date-end-{type_page}', 'date')]
)
def update_table_dd(start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], [], [], [], [], []
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_pn(), bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_ds2(), bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_pn_uniq_tal(), bind_params)

    return columns1, data1, columns2, data2, columns3, data3
