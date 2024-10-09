from dash import Output, Input, exceptions, State

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import *
from apps.analytical_app.components.toast import toast
from apps.analytical_app.elements import card_table
from apps.analytical_app.app import app
from apps.analytical_app.pages.head.dn_job.query import sql_head_dn_job, sql_head_dn_job2
from apps.analytical_app.query_executor import engine

type_page = "head-dn-job"

head_dn_job = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            html.Button('Получить данные', id=f'get-data-button-{type_page}'),
                            dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        card_table(f'result-table1-{type_page}', "Анализ внесенных записей в ИСЗЛ", 15),
        card_table(f'result-table2-{type_page}', "Список пациентов из ИСЗЛ \"Диспансерное наблюдение работающих\"", 15),
        toast(type_page)

    ],
    style={"padding": "0rem"}

)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'result-table2-{type_page}', 'columns'),
     Output(f'result-table2-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'no-data-toast-{type_page}', 'is_open')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table(n_clicks):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    sql_query1 = sql_head_dn_job()
    sql_query2 = sql_head_dn_job2()

    columns1, data1 = TableUpdater.query_to_df(engine, sql_query1)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query2)

    if len(data1) == 0 or len(data2) == 0:
        return columns1, data1, columns2, data2, loading_output, True

    return columns1, data1, columns2, data2, loading_output, False
