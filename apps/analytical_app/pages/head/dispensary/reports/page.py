import datetime

from dash import html, dcc, Output, Input, dash_table, exceptions, State
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import status_groups, get_current_reporting_month
from apps.analytical_app.pages.head.dispensary.reports.query import sql_query_disp_rep_f1000, sql_query_disp_rep_f1001, \
    sql_query_disp_rep_f2000, sql_query_disp_rep_f3000, sql_query_disp_rep_f2001, sql_query_disp_rep_f3001_3003
from apps.analytical_app.query_executor import engine

type_page = "dispensary-reports"


def date_r():
    date_start = datetime.datetime.now()
    day_list = ['01', '02', '03', '04', '05']

    date = date_start
    day_str = date.strftime("%d")
    if day_str in day_list:
        date = (date_start - datetime.timedelta(days=10))
        mon = date.strftime("%m")
    else:
        mon = date.strftime("%m")
    return mon


# Определяем текущий месяц
month = date_r()

dispensary_reports = html.Div(
    [
        dcc.Store(id=f'current-month-number-{type_page}'),
        dcc.Store(id=f'select-month-number-start-{type_page}'),
        dcc.Store(id=f'select-month-number-end-{type_page}'),
        # Блок 1: Выбор элемента из списка
        html.Div(
            [
                html.H3('Фильтры', className='label'),
                dcc.RangeSlider(
                    id=f'month-slider-{type_page}',
                    min=1,
                    max=12,
                    step=1,
                    marks={
                        1: 'Январь',
                        2: 'Февраль',
                        3: 'Март',
                        4: 'Апрель',
                        5: 'Май',
                        6: 'Июнь',
                        7: 'Июль',
                        8: 'Август',
                        9: 'Сентябрь',
                        10: 'Октябрь',
                        11: 'Ноябрь',
                        12: 'Декабрь'
                    },
                    value=[int(month), int(month)],
                    updatemode='mouseup'
                ),
                dcc.RadioItems(
                    id=f'status-group-radio-{type_page}',
                    options=[{'label': group, 'value': group} for group in status_groups.keys()],
                    value='Оплаченные (3)',
                    labelStyle={'display': 'block'}
                ),
                html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                html.Div(id=f'selected-month-{type_page}', className='filters-label'),
                html.Button('Получить данные', id=f'get-data-button-{type_page}'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
            ], className='filter'),
        # Блок 2: Таблица
        html.Div(
            [
                html.H3('1000', className='label'),
                dash_table.DataTable(id=f'result-table1-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('1001', className='label'),
                dash_table.DataTable(id=f'result-table2-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('2000', className='label'),
                dash_table.DataTable(id=f'result-table3-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('2001', className='label'),
                dash_table.DataTable(id=f'result-table4-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('3000', className='label'),
                dash_table.DataTable(id=f'result-table5-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('3001 - 3003', className='label'),
                dash_table.DataTable(id=f'result-table6-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('4000', className='label'),
                dash_table.DataTable(id=f'result-table7-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Div(
            [
                html.H3('4001', className='label'),
                dash_table.DataTable(id=f'result-table8-{type_page}', columns=[],
                                     editable=False,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
    ]
)


# Определяем отчетный месяц и выводим его на страницу и в переменную dcc Store
@app.callback(
    Output(f'current-month-number-{type_page}', 'data'),
    Output(f'current-month-name-{type_page}', 'children'),
    [Input('date-interval', 'n_intervals')]
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_num, current_month_name


@app.callback(
    Output(f'selected-month-{type_page}', 'children'),
    Input(f'month-slider-{type_page}', 'value')
)
def update_selected_month(selected_months):
    start_month, end_month = selected_months
    start_month_name = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь'
    }.get(start_month, 'Неизвестно')
    end_month_name = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь'
    }.get(end_month, 'Неизвестно')
    if start_month_name == end_month_name:
        return f'Выбранный месяц: {start_month_name}'
    else:
        return f'Выбранный месяц: с {start_month_name} по {end_month_name}'


@app.callback(
    Output(f'select-month-number-start-{type_page}', 'data'),
    Output(f'select-month-number-end-{type_page}', 'data'),
    Input(f'month-slider-{type_page}', 'value')
)
def update_selected_months_in_store(selected_months):
    return selected_months[0], selected_months[1]


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
     Output(f'result-table8-{type_page}', 'columns'),
     Output(f'result-table8-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),  # Срабатывание по нажатию кнопки "получить данные"
     Input(f'select-month-number-start-{type_page}', 'data'),
     Input(f'select-month-number-end-{type_page}', 'data'),
     Input(f'current-month-number-{type_page}', 'data')],
    [State(f'status-group-radio-{type_page}', 'value')]
)
def update_table(n_clicks, month_start, month_end, current_month, selected_status):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    loading_output = html.Div([dcc.Loading(type="default")])
    selected_status_values = status_groups[selected_status]
    selected_status_tuple = tuple(selected_status_values)
    sql_conditions = ''
    if month_end == current_month:
        sql_conditions = 'or ("Номер счёта" is null) or ("Статус" in (\'6\', \'8\'))'
    sql_query1 = sql_query_disp_rep_f1000(sql_conditions)
    sql_query2 = sql_query_disp_rep_f1001(sql_conditions)

    sql_conditions_dd = ''
    if month_end == current_month:
        sql_conditions_dd = 'or ("Счет" is null) or ("Статус" in (\'6\', \'8\'))'
    sql_query3 = sql_query_disp_rep_f2000(sql_conditions_dd)
    sql_query4 = sql_query_disp_rep_f2001(sql_conditions_dd)
    sql_query5 = sql_query_disp_rep_f3000(sql_conditions_dd)
    sql_query6 = sql_query_disp_rep_f3001_3003(sql_conditions_dd)
    # sql_query7 = sql_query_disp_rep_f4000(sql_conditions_dd)
    sql_query7 = sql_query_disp_rep_f3001_3003(sql_conditions_dd)
    # sql_query8 = sql_query_disp_rep_f4001(sql_conditions_dd)
    sql_query8 = sql_query_disp_rep_f3001_3003(sql_conditions_dd)

    list_months = []
    for i in range(month_start, month_end + 1):
        list_months.append(TableUpdater.get_sql_month(str(i)))
    bind_params = {
        'list_months': list_months,
        'status_list': selected_status_tuple
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query1, bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query2, bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query3, bind_params)
    columns4, data4 = TableUpdater.query_to_df(engine, sql_query4, bind_params)
    columns5, data5 = TableUpdater.query_to_df(engine, sql_query5, bind_params)
    columns6, data6 = TableUpdater.query_to_df(engine, sql_query6, bind_params)
    columns7, data7 = TableUpdater.query_to_df(engine, sql_query7, bind_params)
    columns8, data8 = TableUpdater.query_to_df(engine, sql_query8, bind_params)
    return columns1, data1, columns2, data2, columns3, data3, columns4, data4, columns5, data5, columns6, data6, columns7, data7, columns8, data8, loading_output
