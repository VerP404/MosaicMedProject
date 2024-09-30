from datetime import datetime

from dash import html, Output, Input
import dash_bootstrap_components as dbc
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.callback.date_reports import get_selected_year
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import filter_years, filter_months
from services.MosaicMed.pages.dispensary.children.query import sql_query_pn_talon, sql_query_pn_uniq

type_page = "tab2-dc"




tab2_layout_dc = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    filter_years(type_page)  # фильтр по годам
                                ]
                            ),
                            html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        card_table(f'result-table1-{type_page}', "Карты профосмотров"),
        card_table(f'result-table2-{type_page}', "Уникальные пациенты в картах"),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    Input(f'dropdown-year-{type_page}', 'value')
)
def update_selected_period(selected_year):
    return get_selected_year(selected_year)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data')],
    [Input(f'selected-period-{type_page}', 'children')]
)
def update_table_dd(selected_period):
    if not selected_period:
        return [], [], [], []

    year_placeholder = selected_period[0]
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_pn_talon(year_placeholder))
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_pn_uniq(year_placeholder))
    return columns1, data1, columns2, data2
