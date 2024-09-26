from datetime import datetime

from dash import html, dcc, Output, Input, dash_table, exceptions, State
import dash_bootstrap_components as dbc
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater, get_current_reporting_month
from services.MosaicMed.callback.slider_months import get_selected_period
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import filter_years, filter_months
from services.MosaicMed.pages.dispensary.adults.query import sql_query_do_korpus_dd

type_page = "tab2-da"

tab2_layout_da = html.Div(
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
                            dbc.Row(
                                [
                                    filter_months(type_page)  # фильтр по месяцам
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
        card_table(f'result-table1-{type_page}', "Цель ДВ4 — Первый этап диспансеризации взрослых"),
        card_table(f'result-table2-{type_page}', "Цель ДВ2 — Второй этап диспансеризации взрослых"),
        card_table(f'result-table3-{type_page}', "Цель ОПВ — Профилактический осмотр взрослых"),
        card_table(f'result-table4-{type_page}', "Цель УД1 — Первый этап углубленной диспансеризации взрослых"),
        card_table(f'result-table5-{type_page}', "Цель УД2 — Второй этап углубленной диспансеризации взрослых"),
        card_table(f'result-table6-{type_page}', "Цель ДР1 — Первый этап диспансеризации репродуктивного здоровья"),
        card_table(f'result-table7-{type_page}', "Цель ДР2 — Второй этап диспансеризации репродуктивного здоровья"),
    ],
    style={"padding": "0rem"}
)


# Определяем отчетный месяц и выводим его на страницу и в переменную dcc Store
@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


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
     Output(f'result-table3-{type_page}', 'data'),
     Output(f'result-table4-{type_page}', 'columns'),
     Output(f'result-table4-{type_page}', 'data'),
     Output(f'result-table5-{type_page}', 'columns'),
     Output(f'result-table5-{type_page}', 'data'),
     Output(f'result-table6-{type_page}', 'columns'),
     Output(f'result-table6-{type_page}', 'data'),
     Output(f'result-table7-{type_page}', 'columns'),
     Output(f'result-table7-{type_page}', 'data'),
     ],
    [Input(f'selected-period-{type_page}', 'children')]
)
def update_table_dd(selected_period):
    if not selected_period:
        return [], [], [], [], [], []

    months_placeholder = ', '.join([f"'{month}'" for month in selected_period])
    bind_params = {'text_1': "ДВ4"}
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    bind_params = {'text_1': "ДВ2"}
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    bind_params = {'text_1': "ОПВ"}
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    bind_params = {'text_1': "УД1"}
    columns4, data4 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    bind_params = {'text_1': "УД2"}
    columns5, data5 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    bind_params = {'text_1': "ДР1"}
    columns6, data6 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    bind_params = {'text_1': "ДР2"}
    columns7, data7 = TableUpdater.query_to_df(engine, sql_query_do_korpus_dd(months_placeholder), bind_params)
    return columns1, data1, columns2, data2, columns3, data3, columns4, data4, columns5, data5, columns6, data6, columns7, data7
