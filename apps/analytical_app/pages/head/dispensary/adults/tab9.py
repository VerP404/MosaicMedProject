# файл: apps/analytical_app/pages/head/dispensary/adults/tab9-da.py
from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.adults.query import sql_query_dispensary_remd
from apps.analytical_app.query_executor import engine

type_page = "tab9-da"

# Лэйаут страницы
adults_dv9 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            # Заголовок фильтров
                            dbc.CardHeader(
                                dbc.Row(
                                    [
                                        dbc.Col(html.H5("Фильтры", className="mb-0"), width="auto"),
                                        dbc.Col(
                                            html.Div(
                                                id=f'last-updated-{type_page}',
                                                style={"fontWeight": "bold", "textAlign": "right"}
                                            ),
                                            width=True
                                        )
                                    ],
                                    align="center",
                                    justify="between"
                                )
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=2),
                                    dbc.Col(dbc.Alert(
                                        [
                                            html.Span("Данные из Журнала ЭМД."), html.Br(),
                                            html.Span("Тип: Диспансеризация взрослого населения"), html.Br(),
                                            html.Span("- да: статус \"Документ успешно зарегистрирован\"."), html.Br(),
                                            html.Span(
                                                "- нет: документ сформирован, но не зарегистрирован. Все прочие статусы."),
                                            html.Br(),
                                        ],
                                        color="success"
                                    )),
                                ],
                                align="center",
                                className="g-2"
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px rgba(0,0,0,0.1)",
                        "border-radius": "10px"
                    }
                ),
                width=12
            )
        ),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        # сама таблица с merge_duplicate_headers=True
        card_table(
            f'result-table1-{type_page}',
            "РЭМД диспансеризации (ДВ4, ОПВ) по врачам и месяцам документа",
            merge_duplicate_headers=True
        )
    ],
    style={"padding": "0rem"}
)


# Колбэк: строим колонки, данные и дату последнего обновления
@app.callback(
    [
        Output(f'result-table1-{type_page}', 'columns'),
        Output(f'result-table1-{type_page}', 'data'),
        Output(f'loading-output-{type_page}', 'children'),
        Output(f'last-updated-{type_page}', 'children'),
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value')]
)
def update_table_tab9(n_clicks, selected_year):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    # индикатор загрузки
    loading = html.Div([dcc.Loading(type="default")])

    # SQL и данные
    sql = sql_query_dispensary_remd(selected_year)
    orig_columns, data = TableUpdater.query_to_df(engine, sql)

    # Собираем колонки с merge_duplicate_headers
    month_map = {
        'янв': 'Январь', 'фев': 'Февраль', 'мар': 'Март',
        'апр': 'Апрель', 'май': 'Май', 'июн': 'Июнь',
        'июл': 'Июль', 'авг': 'Август', 'сен': 'Сентябрь',
        'окт': 'Октябрь', 'ноя': 'Ноябрь', 'дек': 'Декабрь'
    }
    metrics = ['да', 'нет', 'итого']

    dash_columns = []
    for col in orig_columns:
        cid = col['id']
        if cid == 'doctor':
            dash_columns.append({'name': ['', 'Врач'], 'id': 'doctor'})
        elif cid == 'branch':
            dash_columns.append({'name': ['', 'Корпус'], 'id': 'branch'})
        else:
            short_m, met = cid.split('_', 1)
            if short_m in month_map and met in metrics:
                dash_columns.append({
                    'name': [month_map[short_m], met],
                    'id': cid
                })
            else:
                dash_columns.append(col)

    # Получаем дату последнего обновления из load_data_emd
    with engine.connect() as conn:
        row = conn.execute(text("SELECT MAX(updated_at) FROM load_data_emd")).fetchone()
    last_updated = (row[0].strftime('%d.%m.%Y %H:%M')
                    if row and row[0] else "Нет данных")

    # Возвращаем всё, включая дату
    return dash_columns, data, loading, f"Последнее обновление: {last_updated}"
