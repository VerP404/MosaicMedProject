from dash import html, Input, Output, dash_table, dcc
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.it_department.cel_3.query import sql_query_list_patients, sql_query_list_patients_svod

# Отчет для сборки талонов
type_page = "tab1_cel_3"

alert_text1 = """Уникальные по пациенту (ЕНП) и диагнозу.  
Нарастающий итог.
"""

tab1_layout_cel_3 = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Список талонов по БСК для блокировки по причине "Проведено ДН по БСК более 1 раза в году"',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                dbc.Alert(
                    dcc.Markdown(alert_text1),
                    color="danger",
                    style={'padding': '0'},

                ),
                html.Div(
                    [
                        html.Label('Свод для блокировки повторной цели 3 по БСК'),
                        dash_table.DataTable(id=f'result-table2-{type_page}',
                                             columns=[],
                                             editable=True,
                                             filter_action="native",
                                             sort_action="native",
                                             sort_mode='multi',
                                             export_format='xlsx',
                                             export_headers='display',
                                             style_table={'width': '350px'}
                                             ),
                    ], className='block'),
                html.Hr(),
                html.Div(
                    [
                        html.Label('Список для блокировки цели 3 по БСК'),
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
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],  # Добавляем компонент для отображения загрузки
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns1, data1 = TableUpdater.query_to_df(engine, sql_query_list_patients)
        columns2, data2 = TableUpdater.query_to_df(engine, sql_query_list_patients_svod)
        return columns1, data1, columns2, data2, loading_output
    return [], [], [], [], html.Div()
