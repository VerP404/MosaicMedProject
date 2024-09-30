from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.eln.query import sql_query_eln_often, sql_query_eln_often_list

type_page = "eln-tab1"

tab1_eln = html.Div(
    [
        # Блок 1: Выбор элемента из списка
        html.Div(
            [
                # html.H3('Фильтры', className='label'),
                html.Div(
                    [
                        html.Label('Укажите дату приема'),
                        html.Div([
                            html.Label('Дата приема:', style={'width': '120px', 'display': 'inline-block'}),
                            dcc.DatePickerSingle(
                                id=f'date-picker-{type_page}',
                                first_day_of_week=1,
                                date=datetime.now().date() - timedelta(days=1),  # Устанавливаем начальную дату
                                display_format='DD.MM.YYYY'
                            ),
                        ], className='filters'),
                    ], className='filters-line'),
            ], className='filter'),
        html.Hr(),
        html.H3('Записи на выбранную дату пациентов открывавших ЛН более 3х раз за последние 6 месяцев',
                className='label'),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        html.Div(
            [
                dash_table.DataTable(id=f'result-table1-{type_page}',
                                     columns=[],
                                     page_size=31,
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
        html.Hr(),
        html.H3('Список пациентов открывавших ЛН более 3х раз за последние 6 месяцев',
                className='label'),
        html.Div(
            [
                dash_table.DataTable(id=f'result-table2-{type_page}',
                                     columns=[],
                                     page_size=31,
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     style_table={'width': '800px'}
                                     ),
            ], className='block'),
    ]
)


# дата по умолчанию
@app.callback(
    Output(f'date-picker-{type_page}', 'date'),
    Input(f'interval-component-{type_page}', 'n_intervals')
)
def update_date_picker(n_intervals):
    new_date = datetime.now().date() - timedelta(days=1)
    return new_date


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     ],
    Input(f'date-picker-{type_page}', 'date'),
)
def update_table_dd(date):
    if date is None:
        return [], [], [], [], html.Div()
    loading_output = html.Div([dcc.Loading(type="default")])
    # запрос для формирования отчета
    start_date_formatted = datetime.strptime(date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'date_in': start_date_formatted,
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_eln_often, bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_eln_often_list, bind_params)
    return columns1, data1, columns2, data2, loading_output
