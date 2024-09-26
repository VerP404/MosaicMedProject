from datetime import datetime

from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater, get_selected_dates
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import filter_status, date_start, date_end
from services.MosaicMed.pages.doctors_talon.doctors_list.query import sql_query_by_doc_end_form
from services.MosaicMed.generate_pages.constants import status_groups

type_page = "tab3-doctor-talon-list"

tab3_doctor_talon_list = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    filter_status(type_page),  # фильтр по статусам
                                ]
                            ),
                            dbc.Row(
                                [
                                    date_start('Начало ввода:', type_page),
                                    date_end('Окончание ввода:', type_page),
                                ]
                            ),

                            html.Button('Получить данные', id=f'get-data-button-{type_page}'),
                            dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        card_table(f'result-table-{type_page}', "Талоны по врачам", 15)
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
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data')],
    [Input(f'date-start-{type_page}', 'date'),
     Input(f'date-end-{type_page}', 'date'),
     Input(f'status-group-radio-{type_page}', 'value')]
)
def update_table_dd(start_date, end_date, selected_status):
    if (start_date is None) or (end_date is None):
        return [], []
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    selected_status_values = status_groups[selected_status]
    selected_status_tuple = tuple(selected_status_values)
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted,
        'status_list': selected_status_tuple
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_by_doc_end_form(), bind_params)

    return columns, data
