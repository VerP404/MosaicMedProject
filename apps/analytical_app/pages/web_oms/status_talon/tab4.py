from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_specialist, get_selected_dates, TableUpdater
from apps.analytical_app.pages.web_oms.status_talon.query import sql_query_status_spec_korp
from apps.analytical_app.query_executor import engine

type_page = "status-spec-korp"

web_oms_4 = html.Div(
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
                                    html.Label('Корпус:'),
                                    dcc.Dropdown(id=f'dropdown-korp-{type_page}',
                                                 options=[],
                                                 placeholder='Выберите корпус...'),
                                ], className='filters'),
                            html.Div(
                                [
                                    html.Label('Специальность:'),
                                    dcc.Dropdown(id=f'dropdown-spec-{type_page}',
                                                 options=[],
                                                 placeholder='Выберите специальность...'),
                                ], className='filters'),
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
                html.Div(id=f'selected-spec-{type_page}', className='filters-label', style={'display': 'none'}),
                html.Div(id=f'selected-korp-{type_page}', className='filters-label', style={'display': 'none'}),

            ], className='filter'),
        html.Hr(),
        html.H3('Отчет по целям в специальностях и корпусах', className='label'),
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
    [Output(f'dropdown-spec-{type_page}', 'options'),
     Output(f'selected-spec-{type_page}', 'children')],
    Input(f'dropdown-spec-{type_page}', 'value'),
)
def update_dropdown(selected_value):
    sql_query_spec = """
        SELECT DISTINCT CASE
          WHEN POSITION('(' IN doctor_profile) > 0
          THEN SUBSTRING(doctor_profile FROM 1 FOR POSITION('(' IN doctor_profile) - 1)
          ELSE doctor_profile
        END
        FROM data_loader_omsdata
    """
    dropdown_options, selected_item_text = get_selected_specialist(selected_value, sql_query_spec)
    return dropdown_options, selected_item_text


@app.callback(
    [Output(f'dropdown-korp-{type_page}', 'options'),
     Output(f'selected-korp-{type_page}', 'children')],
    Input(f'dropdown-korp-{type_page}', 'value'),
)
def update_dropdown(selected_value):
    sql_query_korp = """
        SELECT DISTINCT department
        FROM data_loader_omsdata
    """
    dropdown_options, selected_item_text = get_selected_specialist(selected_value, sql_query_korp)
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
    Input(f'dropdown-spec-{type_page}', 'value'),
    Input(f'dropdown-korp-{type_page}', 'value'),
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_table_dd(value_spec, korp, start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], [], html.Div()
    loading_output = html.Div([dcc.Loading(type="default")])
    # запрос для формирования отчета
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    value_spec = f"{value_spec}%"
    bind_params = {
        'value_spec': value_spec,
        'korp': korp,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_status_spec_korp, bind_params)
    return columns, data, loading_output