from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.flaskapp.flask_app import flask_app
from services.MosaicMed.app import app
from database.db_conn import engine
from services.MosaicMed.callback.callback import get_selected_doctors, get_current_reporting_month, TableUpdater
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import filter_doctors, filter_years, filter_months
from services.MosaicMed.callback.slider_months import get_selected_period
from services.MosaicMed.pages.doctors_talon.doctor.query import sql_query_amb_def, sql_query_dd_def, sql_query_stac_def

type_page = "tab1-doctor-talon"

tab1_doctor_talon_layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(filter_doctors(type_page), width=9),  # фильтр по врачам
                                    dbc.Col(filter_years(type_page), width=3)  # фильтр по годам
                                ]
                            ),
                            dbc.Row(
                                [
                                    filter_months(type_page)  # фильтр по месяцам
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=9),
                                    dbc.Col(html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=3)
                                ]
                            ),
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
        card_table(f'result-table1-{type_page}', "Амбулаторная помощь"),
        card_table(f'result-table2-{type_page}', "Диспансеризация"),
        card_table(f'result-table3-{type_page}', "Стационары"),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


@app.callback(
    [Output(f'dropdown-doctor-{type_page}', 'options'),
     Output(f'selected-doctor-{type_page}', 'children')],
    [Input(f'dropdown-doctor-{type_page}', 'value')]
)
def update_dropdown_layout(selected_doctor):
    dropdown_options, selected_item_text = get_selected_doctors(selected_doctor)
    if isinstance(dropdown_options, list) and all(isinstance(option, dict) for option in dropdown_options):
        return dropdown_options, selected_item_text
    return [], selected_item_text



@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [Input(f'range-slider-month-{type_page}', 'value'),
     Input(f'dropdown-year-{type_page}', 'value'),
     Input(f'current-month-name-{type_page}', 'children')]
)
def update_selected_period_list(selected_months_range, selected_year, current_month_name):
    return get_selected_period(selected_months_range, selected_year, current_month_name)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data')],
    [Input(f'dropdown-doctor-{type_page}', 'value'),
     Input(f'selected-period-{type_page}', 'children')]
)
def update_table_dd(value_doctor, selected_period):
    if value_doctor is None or not selected_period:
        return [], [], [], [], [], []

    months_placeholder = ', '.join([f"'{month}'" for month in selected_period])
    bind_params = {'value_doctor': value_doctor}
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_amb_def(months_placeholder), bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_dd_def(months_placeholder), bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_stac_def(months_placeholder), bind_params)

    return columns1, data1, columns2, data2, columns3, data3
