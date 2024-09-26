from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table
from services.MosaicMed.app import app
from database.db_conn import engine
from services.MosaicMed.callback.callback import TableUpdater, get_selected_dates

from services.MosaicMed.pages.other_reports.sharapova.query import sql_query_sharapova

type_page = "sharapova"

tab_layout_other_sharapova = html.Div(
    [
        # Блок 1: Выбор элемента из списка
        html.Div(
            [
                html.H3('Фильтры', className='label'),
                html.Div(
                    [
                        html.Div([
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
                html.Div(id=f'selected-date-{type_page}', className='filters-label'),

            ], className='filter'),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        html.Div(
            [
                html.H3('Отчет по диспансерному наблюдению для Шараповой', className='label'),
                dash_table.DataTable(id=f'result-table-{type_page}',
                                     columns=[],
                                     export_format='xlsx',
                                     export_headers='display',
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     ),
            ], className='block'),
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
    Output(f'selected-date-{type_page}', 'children'),
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_selected_dates(start_date, end_date):
    return get_selected_dates(start_date, end_date)



@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_table_dd(start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], []
    loading_output = html.Div([dcc.Loading(type="default")])
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_sharapova, bind_params)
    return columns, data, loading_output
