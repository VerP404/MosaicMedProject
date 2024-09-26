from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table
from services.MosaicMed.app import app
from database.db_conn import engine
from services.MosaicMed.callback.callback import TableUpdater, get_selected_dates
import dash_bootstrap_components as dbc
from services.MosaicMed.pages.other_reports.visits.query import sql_query_visits, sql_query_visits_korpus, sql_query_visits_korpus_spec, \
    sql_query_visits_pos_home

alert_text1 = """Условия:
- амбулатория - ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305', '307', '64', '640', '32')
- диспансеризация - ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ПН1', 'ДС2')
- Стационары не входят!
"""

type_page = "visits"

tab_layout_other_visits = html.Div(
    [
        # Блок 1: Выбор элемента из списка
        html.Div(
            [
                html.H3('Фильтры', className='label'),
                html.Div(
                    [
                        html.Div([
                            html.H5('По дате окончания лечения'),
                            html.Label('Дата начала:', style={'width': '120px', 'display': 'inline-block'}),
                            dcc.DatePickerSingle(
                                id=f'date-picker-start-{type_page}',
                                first_day_of_week=1,
                                date=datetime.now().date() - timedelta(days=1),  # Устанавливаем начальную дату
                                display_format='DD.MM.YYYY'
                            ),
                        ], className='filters'),
                        html.Div([
                            html.Label('Дата окончания:', style={'width': '120px', 'display': 'inline-block'}),
                            dcc.DatePickerSingle(
                                id=f'date-picker-end-{type_page}',
                                first_day_of_week=1,
                                date=datetime.now().date() - timedelta(days=1),  # Устанавливаем конечную дату
                                display_format='DD.MM.YYYY'
                            ),
                        ], className='filters'),
                    ], className='filters-line'),

                html.Div(id=f'selected-doctor-{type_page}', className='filters-label', style={'display': 'none'}),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
            ], className='filter'),
        html.Hr(),
        html.Div(
            [
                html.H3('Отчет по количеству посещений пациентами взрослыми и детьми', className='label'),
                dbc.Alert(dcc.Markdown(alert_text1), color="danger", style={'padding': '0 0 0 10px'}),
                html.Div(id=f'selected-date1-{type_page}', className='filters-label'),
                dash_table.DataTable(id=f'result-table1-{type_page}',
                                     columns=[],
                                     export_format='xlsx',
                                     export_headers='display',
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     ),
            ], className='block', style={'width': '800px'}),
        html.Hr(),
        html.Div(
            [
                html.H3('Отчет по количеству посещений пациентами по корпусам', className='label'),
                html.Div(id=f'selected-date2-{type_page}', className='filters-label'),
                dash_table.DataTable(id=f'result-table2-{type_page}',
                                     columns=[],
                                     export_format='xlsx',
                                     export_headers='display',
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     ),
            ], className='block', style={'width': '800px'}),
        html.Hr(),
        html.Div(
            [
                html.H3('Отчет по количеству посещений пациентами по корпусам и специальностям', className='label'),
                html.Div(id=f'selected-date3-{type_page}', className='filters-label'),
                dash_table.DataTable(id=f'result-table3-{type_page}',
                                     columns=[],
                                     export_format='xlsx',
                                     export_headers='display',
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     ),
            ], className='block', style={'width': '1000px'}),
        html.Hr(),
        html.Div(
            [
                html.H3('Отчет по количеству посещений на дому', className='label'),
                html.Div(id=f'selected-date4-{type_page}', className='filters-label'),
                dash_table.DataTable(id=f'result-table4-{type_page}',
                                     columns=[],
                                     export_format='xlsx',
                                     export_headers='display',
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     ),
            ], className='block', style={'width': '350px'}),
    ]
)


# дата по умолчанию
@app.callback(
    Output(f'date-picker-end-{type_page}', 'date'),
    Input(f'interval-component-{type_page}', 'n_intervals')
)
def update_date_picker(n_intervals):
    # Вычислите новую дату, например, на один день вперед от текущей даты
    new_date = datetime.now().date() - timedelta(days=1)
    return new_date


# строка с выбранными датами
@app.callback(
    Output(f'selected-date1-{type_page}', 'children'),
    Output(f'selected-date2-{type_page}', 'children'),
    Output(f'selected-date3-{type_page}', 'children'),
    Output(f'selected-date4-{type_page}', 'children'),
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_selected_dates(start_date, end_date):
    sel_date = get_selected_dates(start_date, end_date)
    return sel_date, sel_date, sel_date, sel_date


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'result-table3-{type_page}', 'columns'),
     Output(f'result-table3-{type_page}', 'data'),
     Output(f'result-table4-{type_page}', 'columns'),
     Output(f'result-table4-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')
     ],
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_table_dd(start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], [], [], [], [], [], [], [], html.Div()
    loading_output = html.Div([dcc.Loading(type="default")])
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_visits, bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_visits_korpus, bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_visits_korpus_spec, bind_params)
    columns4, data4 = TableUpdater.query_to_df(engine, sql_query_visits_pos_home, bind_params)
    return columns1, data1, columns2, data2, columns3, data3, columns4, data4, loading_output
