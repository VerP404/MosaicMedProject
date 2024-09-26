from datetime import datetime
from dash import html, Output, Input, dash_table
import dash_bootstrap_components as dbc
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import get_selected_doctors, TableUpdater, get_selected_dates
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import filter_doctors, date_start, date_end
from services.MosaicMed.pages.doctors_talon.doctor.query import sql_query_dd_date_form_def, sql_query_amb_date_form_def

type_page = "tab2-doctor-talon"

tab2_doctor_talon_layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    filter_doctors(type_page),  # фильтр по врачам
                                ]
                            ),
                            dbc.Row(
                                [
                                    date_start('Начало лечения:', type_page),
                                    date_end('Окончание лечения:', type_page),
                                ]
                            ),
                            html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
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
        card_table(f'result-table1-{type_page}', "Амбулаторная помощь"),
        card_table(f'result-table2-{type_page}', "Диспансеризация"),
        card_table(f'result-table3-{type_page}', "Стационары"),
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


# выводим нужные фильтры врача и дат
@app.callback(
    [Output(f'dropdown-doctor-{type_page}', 'options'),
     Output(f'selected-doctor-{type_page}', 'children')],
    Input(f'dropdown-doctor-{type_page}', 'value'),
)
def update_dropdown(selected_value):
    dropdown_options, selected_item_text = get_selected_doctors(selected_value)
    return dropdown_options, selected_item_text


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data')
     ],
    [Input(f'dropdown-doctor-{type_page}', 'value'),
     Input(f'date-start-{type_page}', 'date'),
     Input(f'date-end-{type_page}', 'date')]
)
def update_table_dd(value_doctor, start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], [], [], [], [], []
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'value_doctor': value_doctor,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_amb_date_form_def(), bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_dd_date_form_def(), bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_dd_date_form_def(), bind_params)

    return columns1, data1, columns2, data2, columns3, data3
