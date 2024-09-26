from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table
from services.MosaicMed.app import app
from database.db_conn import engine
from services.MosaicMed.callback.callback import TableUpdater, get_selected_dates
from services.MosaicMed.pages.other_reports.cardiology_report.query import sql_query_cardiology_report
import dash_bootstrap_components as dbc


type_page = "cardiology"

alert_text1 = """Условия:
- Цель 30
- Характер заболевания 2 - Впервые установленное
- Отчет строится по дате окончания лечения в талонах ОМС
"""

tab_layout_other_cardiology = html.Div(
    [
        html.Div(
            [
                html.H3('Фильтры', className='label'),
                html.Div(
                    [
                        html.H5('По дате окончания лечения'),
                        html.Div([
                            html.Label('Дата начала :', style={'width': '120px', 'display': 'inline-block'}),
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

                html.Div(id=f'selected-date-{type_page}', className='filters-label'),

            ], className='filter'),
        html.Div(
            [
                html.H3('Кардиологический отчет по талонам ОМС', className='label'),
                dbc.Alert(dcc.Markdown(alert_text1), color="danger", style={'padding': '0 0 0 10px'}),
            ], className='block'),
        html.Hr(),
        html.Div(
            [
                dash_table.DataTable(id=f'result-table-{type_page}',
                                     columns=[],
                                     export_format='xlsx',
                                     export_headers='display',
                                     editable=True,
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode='multi',
                                     style_data={'width': '800px', "text-align": "left"},
                                     style_table={'width': '800px'}
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
     Output(f'result-table-{type_page}', 'data')
     ],
    Input(f'date-picker-start-{type_page}', 'date'),
    Input(f'date-picker-end-{type_page}', 'date')
)
def update_table_dd(start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], []
    # запрос для формирования отчета
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    bind_params = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query_cardiology_report, bind_params)
    return columns, data
