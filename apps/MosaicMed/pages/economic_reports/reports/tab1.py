from dash import html, dcc, Output, Input, exceptions, State
import dash_bootstrap_components as dbc
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater, get_current_reporting_month
from services.MosaicMed.callback.slider_months import get_selected_period
from services.MosaicMed.generate_pages.elements import card_table
from services.MosaicMed.generate_pages.filters import filter_years, filter_months, filter_status
from services.MosaicMed.generate_pages.constants import status_groups, months_labels
from services.MosaicMed.pages.economic_reports.reports.query import sql_query_econ_1, sql_query_econ_4, \
    sql_query_econ_3, sql_query_econ_2

type_page = "ec-rep"
alert_text_amb = """- Посещения - 1, 5, 7, 9, 10, 14, 140, 640
- Обращения - 30
- Неотложка - 22
- Диспансерное наблюдение - 3
"""

alert_text = """ЦАХ:
- 11136001 Сорокина Татьяна Валентиновна
- 11136005 Карандеев Максим Анатольевич
- 11112018 Шадрин Илья Сергеевич

Гинекология:
- 11136007 Столярова Тамара Владимировна
- 11136014 Войтко Валерия Александровна

"""
tab1_layout_ec_report = html.Div(
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
                                    filter_years(type_page)  # фильтр по годам
                                ]
                            ),
                            dbc.Row(
                                [
                                    filter_months(type_page)  # фильтр по месяцам
                                ]
                            ),
                            html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                            html.Div(id=f'selected-month-{type_page}', className='filters-label'),
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
        dbc.Row(
            [
                dbc.Alert(dcc.Markdown(alert_text_amb), color="danger", style={'padding': '0 0 0 10px'}),
                card_table(f'result-table1-{type_page}', "Амбулаторная помощь"),
                dbc.Alert(dcc.Markdown(alert_text), color="danger", style={'padding': '0 0 0 10px'}),
                card_table(f'result-table2-{type_page}', "Стационары"),
                card_table(f'result-table3-{type_page}', "Диспансеризация детей"),
                card_table(f'result-table4-{type_page}', "Диспансеризация взрослых"),
            ]
        ),
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
    Output(f'selected-month-{type_page}', 'children'),
    Input(f'range-slider-month-{type_page}', 'value')
)
def update_selected_month(selected_months):
    if selected_months is None:
        return "Выбранный месяц: Не выбран"

    start_month, end_month = selected_months
    start_month_name = months_labels.get(start_month, 'Неизвестно')
    end_month_name = months_labels.get(end_month, 'Неизвестно')
    if start_month_name == end_month_name:
        return f'Выбранный месяц: {start_month_name}'
    else:
        return f'Выбранный месяц: с {start_month_name} по {end_month_name}'


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
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),
     State(f'selected-period-{type_page}', 'children'),
     State(f'status-group-radio-{type_page}', 'value')]
)
def update_table(n_clicks, selected_period, selected_status):
    if n_clicks is None or not selected_period or not selected_status:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    selected_status_values = status_groups[selected_status]
    selected_status_tuple = tuple(selected_status_values)

    sql_cond = ', '.join([f"'{period}'" for period in selected_period])

    bind_params = {
        'status_list': selected_status_tuple
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_econ_1(sql_cond), bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_econ_2(sql_cond), bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_econ_3(sql_cond), bind_params)
    columns4, data4 = TableUpdater.query_to_df(engine, sql_query_econ_4(sql_cond), bind_params)

    return columns1, data1, columns2, data2, columns3, data3, columns4, data4, loading_output
