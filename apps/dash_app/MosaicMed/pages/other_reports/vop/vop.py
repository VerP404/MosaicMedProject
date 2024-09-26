from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, dash_table, State
from services.MosaicMed.app import app
from database.db_conn import engine
from services.MosaicMed.callback.callback import TableUpdater, get_selected_dates
from services.MosaicMed.pages.other_reports.vop.query import sql_query_vop
import dash_bootstrap_components as dbc

type_page = "vop"
alert_text = """Внутренние болезни:
- Группа диагнозов I00-I99: Болезни системы сердечно-сосудистого.
- Группа диагнозов E00-E90: Заболевания щитовидной железы.
- Группа диагнозов K00-K93: Болезни органов пищеварения.
- Группа диагнозов N00-N99: Болезни мочеполовой системы.
- Группа диагнозов J00-J99: Болезни органов дыхания.
- Группа диагнозов D50-D89: Другие болезни крови и кроветворных органов.  

Неврология:
- Группа диагнозов G00-G99: Болезни нервной системы.
- Группа диагнозов F00-F99: Психические и поведенческие расстройства.
- Группа диагнозов H80-H89: Болезни слухового и равновесия.  

Отоларингология (оториноларингология):
- Группа диагнозов H60-H95: Болезни уха и височной кости.  

Офтальмология:
- Группа диагнозов S05: Травмы, относящиеся к глазу и его придаточным органам.
- Группа диагнозов H00-H59: Болезни глаза и его придаточного аппарата.  

Хирургия:
- Группа диагнозов C00-D49: Злокачественные новообразования.
- Группа диагнозов S00-T98: Травмы, включая ожоги и множественные травмы.
- Группа диагнозов M00-M99: Болезни опорно-двигательного аппарата.  

Акушерство и гинекология:
- Группа диагнозов O00-O99: Беременность, роды и послеродовой период.  

Педиатрия:
- Группа диагнозов P00-P96: Новорожденные дети.
- Группа диагнозов Q00-Q99: Врожденные малформации, деформации и хромосомные нарушения.
"""

tab_layout_other_vop = html.Div(
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
        html.Hr(),
        html.Div(
            [
                dbc.Button(
                    "Названия счетов", id=f"alert-toggle-auto-{type_page}", className="me-1", n_clicks=0
                ),
                html.Hr(),
                dbc.Alert(dcc.Markdown(alert_text), id=f"alert-auto-{type_page}", color="warning", is_open=False,
                          style={'padding': '0 0 0 10px'}),
            ]
        ),
        # Блок 2: Диспансеризация
        html.Div(
            [
                dbc.Alert('Отчет по ВОП', className='label',color="info"),
                dash_table.DataTable(id=f'result-table-{type_page}',
                                     columns=[],
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


@app.callback(
    Output(f"alert-auto-{type_page}", "is_open"),
    [Input(f"alert-toggle-auto-{type_page}", "n_clicks")],
    [State(f"alert-auto-{type_page}", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open


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
     Output(f'result-table-{type_page}', 'data')],
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
    columns, data = TableUpdater.query_to_df(engine, sql_query_vop, bind_params)
    return columns, data
