from dash import html, Input, Output, dash_table, dcc, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.iszl.disp_nabl.query import sql_query_disp_nabl_list, sql_query_disp_nabl_list_svod

# Отчет для сборки талонов
type_page = "iszl-disp-nab-list"

alert_text1 = """Отобраны пациенты
- состоящие в ИСЗЛ на наблюдении с диагнозами по приказу 168н
- посещали ВГП №3 в текущем году. Проставлена последняя явка (дата, цель, тип)
"""

tab2_layout_iszl_disp_nab_list = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Список пациентов из ИСЗЛ подлежащих диспансерному наблюдению по 168н и посещавших поликлинику',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                dcc.Loading(id=f'loading2-output-{type_page}', type='default'),
                html.Hr(),
                dbc.Alert(
                    dcc.Markdown(alert_text1),
                    color="danger",
                    style={'padding': '0'},

                ),
                html.Hr(),
                html.P(id=f'filtered-data-count-{type_page}'),
                html.Div(
                    [
                        dash_table.DataTable(id=f'result-table2-{type_page}',
                                             columns=[],
                                             editable=True,
                                             export_format='xlsx',
                                             export_headers='display',
                                             ),
                    ], className='block', style={'width': '350px'}),
                html.Hr(),
                html.H5("Пофамильный список"),
                html.Div(
                    [
                        dash_table.DataTable(id=f'result-table1-{type_page}',
                                             columns=[],
                                             editable=True,
                                             filter_action="native",
                                             sort_action="native",
                                             sort_mode='multi',
                                             export_format='xlsx',
                                             export_headers='display',
                                             ),
                    ], className='block'),
            ],
        )
    ]
)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'filtered-data-count-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),
     Input(f'result-table1-{type_page}', 'filtering_settings')]
)
def update_table_dd(n_clicks, filtering_settings):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns, data = TableUpdater.query_to_df(engine, sql_query_disp_nabl_list)

        # Получаем количество отфильтрованных данных
        filtered_data_count = len(data)

        return columns, data, loading_output, f"Получено строк: {filtered_data_count}"
    else:
        columns, data = [], []
        loading_output = html.Div()  # Пустой контейнер для отображения после выполнения операции
        filtered_data_count = "Получено строк: 0"  # Изначально ноль данных
    return columns, data, loading_output, filtered_data_count

@app.callback(
    [Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading2-output-{type_page}', 'children')],  # Добавляем компонент для отображения загрузки
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns, data = TableUpdater.query_to_df(engine, sql_query_disp_nabl_list_svod)
        return columns, data, loading_output
    else:
        columns, data = [], []
        loading_output = html.Div()  # Пустой контейнер для отображения после выполнения операции
    return columns, data, loading_output
