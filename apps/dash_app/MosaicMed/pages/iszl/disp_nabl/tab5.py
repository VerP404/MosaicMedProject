from dash import html, Input, Output, dash_table, dcc, State
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import TableUpdater
from services.MosaicMed.pages.iszl.disp_nabl.query import sql_query_list_iszl_oms

# Отчет для сборки талонов
type_page = "tab5_disp_nab_cel_3"

tab4_layout_disp_nab_pr = html.Div(
    [
        html.Div(
            [
                html.H5(
                    'Список пациентов из ИСЗЛ',
                    className='label'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Hr(),
                html.Div(
                    dash_table.DataTable(id=f'result-table4-{type_page}',
                                         columns=[],
                                         editable=True,
                                         filter_action="native",
                                         sort_action="native",
                                         sort_mode='multi',
                                         export_format='xlsx',
                                         export_headers='display',
                                         style_table={'width': '600px'},
                                         style_cell={'textAlign': 'center'}
                                         )
                ),
            ],
        )
    ]
)


@app.callback(
    [Output(f'result-table4-{type_page}', 'columns'),
     Output(f'result-table4-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],  # Добавляем компонент для отображения загрузки
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > 0:
        # Показываем загрузку перед выполнением операции
        loading_output = html.Div([dcc.Loading(type="default")])
        columns4, data4 = TableUpdater.query_to_df(engine, sql_query_list_iszl_oms)
        return columns4, data4, loading_output
    else:
        columns4, data4 = [], []
        loading_output = html.Div()  # Пустой контейнер для отображения после выполнения операции
    return columns4, data4, loading_output
