import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State, dash_table
from time import time

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.children.query import (
    query_download_children_list_not_pn1,
    query_children_list_not_pn1_summary_by_uchastok,
    sql_query_children_list_not_pn1_details_by_uchastok_age,
)
from apps.analytical_app.query_executor import engine
from apps.analytical_app.app import app

type_page = "children-list-not-pn"

# Простейшее TTL-кэширование результата выборки для разгрузки БД
CACHE_TTL_SECONDS = 600
_cache_storage = {}


def _cache_get(cache_key):
    entry = _cache_storage.get(cache_key)
    if entry is None:
        return None
    if time() - entry["ts"] > CACHE_TTL_SECONDS:
        return None
    return entry["columns"], entry["data"]


def _cache_set(cache_key, columns, data):
    _cache_storage[cache_key] = {"ts": time(), "columns": columns, "data": data}

children_list_not_pn = html.Div(
    [
        html.Div(
            [
                html.H3('Список прикрепленных детей без профилактического осмотра (ПН1)', className='label'),
                dbc.Accordion([
                    dbc.AccordionItem([
                        dcc.Markdown(
                            """
                            Инструкция по обновлению населения (ISZLPeople):

                            1. Положить CSV в папку: `mosaic_conductor/etl/data/iszl/people/`
                            2. Запустить команду синхронизации:
                               
                               `python3 manage.py sync_iszl_people --file="mosaic_conductor/etl/data/iszl/people/Att_MO_36002520251009.csv" --encoding=utf-8-sig --delimiter=";" --chunk=5000 --db_mode`

                            3. Альтернатива: через Dagster запустить asset `iszl_people_sync` (он возьмет последний CSV из папки).
                            """
                        )
                    ], title="Как обновить данные населения из CSV")
                ], start_collapsed=True, always_open=False, className='mb-2'),
                dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                dbc.Tabs([
                    dbc.Tab(
                        card_table(
                            f'result-table-{type_page}',
                            "Отчет по всем видам диспансеризации детей с разбивкой по возрастам",
                            page_size=10
                        ),
                        label="Отчет"
                    ),
                    dbc.Tab(
                        html.Div([
                            card_table(
                                f'result-table-summary-{type_page}',
                                "Свод по участкам: без ПН1 (колонки 0..17 лет)",
                                page_size=20
                            ),
                            html.Div(
                                [
                                    html.Hr(),
                                    html.H5("Детализация по выбранной ячейке"),
                                    dcc.Loading(id=f'loading-details-{type_page}', type='default'),
                                    card_table(
                                        f'result-table-details-{type_page}',
                                        "Пациенты по участку и возрасту",
                                        page_size=10
                                    ),
                                ]
                            )
                        ]),
                        label="Свод по участку"
                    ),
                ])
            ], className='block',),
    ]
)


@app.callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'result-table-summary-{type_page}', 'columns'),
        Output(f'result-table-summary-{type_page}', 'data'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [Input(f'get-data-button-{type_page}', 'n_clicks')]
)
def update_table_dd(n_clicks):
    if n_clicks is None:
        n_clicks = 0
    loading_output = html.Div([dcc.Loading(type="default")])
    if n_clicks > 0:
        cache_key1 = f"{type_page}__list_v1"
        cache_key2 = f"{type_page}__summary_v1"
        cached1 = _cache_get(cache_key1)
        cached2 = _cache_get(cache_key2)
        if cached1 is not None:
            columns1, data1 = cached1
        else:
            columns1, data1 = TableUpdater.query_to_df(engine, query_download_children_list_not_pn1)
            _cache_set(cache_key1, columns1, data1)
        if cached2 is not None:
            columns2, data2 = cached2
        else:
            columns2, data2 = TableUpdater.query_to_df(engine, query_children_list_not_pn1_summary_by_uchastok)
            _cache_set(cache_key2, columns2, data2)
    else:
        columns1, data1, columns2, data2 = [], [], [], []

    return columns1, data1, columns2, data2, loading_output


@app.callback(
    [
        Output(f'result-table-details-{type_page}', 'columns'),
        Output(f'result-table-details-{type_page}', 'data'),
        Output(f'loading-details-{type_page}', 'children')
    ],
    [Input(f'result-table-summary-{type_page}', 'active_cell')],
    [State(f'result-table-summary-{type_page}', 'derived_viewport_data')]
)
def update_table_details(active_cell, viewport_data):
    loading_output = html.Div([dcc.Loading(type="default")])
    columns3, data3 = [], []
    if active_cell and viewport_data:
        r = active_cell.get('row')
        c = active_cell.get('column_id')
        try:
            if r is not None and isinstance(r, int) and 0 <= r < len(viewport_data):
                row = viewport_data[r]
                uchastok = row.get('Участок')
                if c is not None and isinstance(c, str):
                    if c == 'Всего':
                        query_details = sql_query_children_list_not_pn1_details_by_uchastok_age(uchastok, None)
                        columns3, data3 = TableUpdater.query_to_df(engine, query_details)
                    elif c not in ('Участок',) and c.isdigit():
                        age = int(c)
                        query_details = sql_query_children_list_not_pn1_details_by_uchastok_age(uchastok, age)
                        columns3, data3 = TableUpdater.query_to_df(engine, query_details)
        except Exception:
            columns3, data3 = [], []
    return columns3, data3, loading_output
