from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import TableUpdater, get_selected_dates, get_selected_specialist
from services.MosaicMed.pages.WO_coupons.status_talon.query import sql_query_status_korpus

type_page = "status-korp"

tab3_layout_other_status = html.Div(
    [
        # Блок 1: Выбор элемента из списка
        html.Div(
            [
                html.H3('Фильтры', className='label'),
                html.Div(
                    [
                        html.Div([
                            html.Div(
                                [
                                    html.Label('Цель:'),
                                    dcc.Dropdown(id=f'dropdown-cel-{type_page}',
                                                 options=[],
                                                 placeholder='Выберите цель...'),
                                ], className='filters'),
                            # html.Div(
                            #     [
                            #         html.Label('Иногородний'),
                            #         dcc.Dropdown(
                            #             id=f'dropdown-type_t-{type_page}',
                            #             options=[{'label': type_t, 'value': type_t} for type_t in ['да', 'нет', 'все']],
                            #             value='все',
                            #             multi=False,
                            #             placeholder='Выберите тип талона...'),
                            #
                            #     ], className='filters'),
                            html.Hr(),
                            html.Label('По дате формирования талона в Web OMS'),
                            html.P(),
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
                html.Div(id=f'selected-cel-{type_page}', className='filters-label', style={'display': 'none'}),
            ], className='filter'),
        html.Hr(),
        html.H3('Отчет по корпусам в цели', className='label'),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        html.Div(
            [
                dash_table.DataTable(id=f'result-table-{type_page}',
                                     columns=[],
                                     page_size=15,
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     export_format='xlsx',
                                     export_headers='display',
                                     ),
            ], className='block'),
    ]
)

# выводим нужные фильтры специальности и месяца
@app.callback(
    [Output(f'dropdown-cel-{type_page}', 'options'),
     Output(f'selected-cel-{type_page}', 'children')],
    Input(f'dropdown-cel-{type_page}', 'value'),
)
def update_dropdown(selected_value):
    sql_query_cel = """
        SELECT DISTINCT "Цель"
        FROM oms.oms_data
    """
    dropdown_options, selected_item_text = get_selected_specialist(selected_value, sql_query_cel)
    return dropdown_options, selected_item_text


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
    Input(f'dropdown-cel-{type_page}', 'value'),
    # Input(f'dropdown-type_t-{type_page}', 'value'),
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_table_dd(cel, start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], [], html.Div()
    loading_output = html.Div([dcc.Loading(type="default")])
    # запрос для формирования отчета
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    # type_tal = ''
    # match  type_t:
    #     case 'да':
    #         type_tal = "like \'360%\'"
    #     case 'нет':
    #         type_tal = "not like \'360%\'"
    #     case 'все':
    #         type_tal = "is not null"
    bind_params = {
        'cel': cel,
        # 'type_tal': type_tal,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_status_korpus, bind_params)
    return columns, data, loading_output
