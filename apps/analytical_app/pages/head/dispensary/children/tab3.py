import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State, dash_table
from time import time
import logging

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.children.query import (
    query_download_children_list_not_pn1,
    query_children_list_not_pn1_summary_by_uchastok,
    sql_query_children_list_not_pn1_details_by_uchastok_age,
    get_diagnostic_stats,
)
from apps.analytical_app.query_executor import engine
from apps.analytical_app.app import app

logger = logging.getLogger(__name__)

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
                dbc.Button(id=f'diagnostic-button-{type_page}', n_clicks=0, children='Диагностика (если пустая таблица)', 
                          color='warning', outline=True, className='ms-2'),
                dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                html.Div(id=f'diagnostic-info-{type_page}', className='mt-3'),
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
            columns1, data1 = TableUpdater.query_to_df(engine, query_download_children_list_not_pn1, debug=True)
            _cache_set(cache_key1, columns1, data1)
        if cached2 is not None:
            columns2, data2 = cached2
        else:
            columns2, data2 = TableUpdater.query_to_df(engine, query_children_list_not_pn1_summary_by_uchastok, debug=True)
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


@app.callback(
    Output(f'diagnostic-info-{type_page}', 'children'),
    [Input(f'diagnostic-button-{type_page}', 'n_clicks')]
)
def run_diagnostic(n_clicks):
    """Выполняет диагностические запросы для выявления причины пустых результатов."""
    if n_clicks is None or n_clicks == 0:
        return None
    
    try:
        stats = get_diagnostic_stats()
        results = {}
        
        for key, query in stats.items():
            try:
                columns, data = TableUpdater.query_to_df(engine, query)
                if data:
                    results[key] = data[0]  # Первая строка результата
                else:
                    results[key] = {'error': 'Запрос вернул пустой результат'}
            except Exception as e:
                logger.error(f"Ошибка при выполнении диагностического запроса {key}: {str(e)}", exc_info=True)
                results[key] = {'error': str(e)}
        
        # Формируем информативное сообщение
        info_items = []
        
        # Проверка таблицы OMS data
        oms = results.get('check_omsdata', {})
        if 'error' not in oms:
            info_items.append(html.H5("1. Проверка таблицы data_loader_omsdata:"))
            info_items.append(html.P(f"Всего строк: {oms.get('total_rows', 'N/A')}"))
            info_items.append(html.P(f"Уникальных ENP: {oms.get('unique_enp', 'N/A')}"))
            info_items.append(html.P(f"ENP с целями ПН1/ДС1/ДС2: {oms.get('enp_with_goals', 'N/A')}"))
            info_items.append(html.P(f"ENP с ПН1: {oms.get('enp_with_pn1', 'N/A')}"))
            info_items.append(html.Hr())
        
        # Проверка таблицы населения
        iszl = results.get('check_iszlpeople', {})
        info_items.append(html.H5("2. Проверка таблицы data_loader_iszlpeople:"))
        if 'error' in iszl:
            info_items.append(html.P(f"❌ ОШИБКА: {iszl.get('error', 'Неизвестная ошибка')}", className='text-danger'))
        else:
            info_items.append(html.P(f"Всего строк: {iszl.get('total_rows', 'N/A')}"))
            info_items.append(html.P(f"Уникальных ENP: {iszl.get('unique_enp', 'N/A')}"))
            info_items.append(html.P(f"С валидными датами: {iszl.get('valid_dates', 'N/A')}"))
            info_items.append(html.P(f"Детей (<18 лет): {iszl.get('children_count', 'N/A')}"))
            if iszl.get('children_count', 0) == 0:
                info_items.append(html.P("⚠️ ВНИМАНИЕ: Нет детей в таблице! Нужно загрузить данные из CSV.", 
                                        className='text-danger fw-bold'))
        info_items.append(html.Hr())
        
        # Проверка CTE talon
        talon = results.get('check_talon_cte', {})
        if 'error' not in talon:
            info_items.append(html.H5("3. CTE 'talon' (обработанные данные OMS):"))
            info_items.append(html.P(f"Всего ENP: {talon.get('unique_enp', 'N/A')}"))
            info_items.append(html.P(f"С ПН1: {talon.get('with_pn1', 'N/A')}"))
            info_items.append(html.Hr())
        
        # Проверка CTE naselenie
        naselenie = results.get('check_naselenie_cte', {})
        info_items.append(html.H5("4. CTE 'naselenie' (обработанное население):"))
        if 'error' in naselenie:
            info_items.append(html.P(f"❌ ОШИБКА: {naselenie.get('error', 'Неизвестная ошибка')}", className='text-danger'))
        else:
            info_items.append(html.P(f"Всего ENP: {naselenie.get('unique_enp', 'N/A')}"))
            info_items.append(html.P(f"Возраст: {naselenie.get('min_age', 'N/A')} - {naselenie.get('max_age', 'N/A')} лет"))
            if naselenie.get('unique_enp', 0) == 0:
                info_items.append(html.P("⚠️ ВНИМАНИЕ: CTE naselenie пустое! Проблема с данными в data_loader_iszlpeople.", 
                                        className='text-danger fw-bold'))
        info_items.append(html.Hr())
        
        # Проверка результата JOIN
        join_result = results.get('check_join_result', {})
        info_items.append(html.H5("5. Результат JOIN naselenie + talon:"))
        if 'error' in join_result:
            info_items.append(html.P(f"❌ ОШИБКА: {join_result.get('error', 'Неизвестная ошибка')}", className='text-danger'))
        else:
            total_after_join = join_result.get('total_after_join', 0)
            without_talon = join_result.get('without_talon_data', 0)
            without_pn1 = join_result.get('without_pn1', 0)
            with_pn1 = join_result.get('with_pn1', 0)
            info_items.append(html.P(f"Всего после JOIN: {total_after_join}"))
            info_items.append(html.P(f"Без данных talon (has_pn1 IS NULL): {without_talon}"))
            info_items.append(html.P(f"Без ПН1 (has_pn1 = 0): {without_pn1}"))
            info_items.append(html.P(f"С ПН1 (has_pn1 = 1): {with_pn1}"))
            if total_after_join == 0:
                info_items.append(html.P("⚠️ ВНИМАНИЕ: JOIN не дал результатов - нет совпадений по ENP между таблицами!", 
                                        className='text-danger fw-bold'))
            elif with_pn1 == total_after_join:
                info_items.append(html.P("⚠️ ВНИМАНИЕ: Все дети имеют ПН1, поэтому нет детей без ПН1 (это нормально если так в базе).", 
                                        className='text-warning fw-bold'))
            elif without_pn1 == 0 and without_talon == 0:
                info_items.append(html.P("⚠️ ПРОБЛЕМА: Все записи после JOIN имеют has_pn1=1, но JOIN дал результат. Проверьте логику фильтрации.", 
                                        className='text-danger fw-bold'))
        info_items.append(html.Hr())
        
        # Проверка совпадения ENP между таблицами
        enp_match = results.get('check_enp_match', {})
        info_items.append(html.H5("5.1. Проверка совпадения ENP между таблицами:"))
        if 'error' in enp_match:
            info_items.append(html.P(f"❌ ОШИБКА: {enp_match.get('error', 'Неизвестная ошибка')}", className='text-danger'))
        else:
            iszl_count = enp_match.get('iszl_enp_count', 0)
            oms_count = enp_match.get('oms_enp_count', 0)
            matching = enp_match.get('matching_enp', 0)
            iszl_only = enp_match.get('iszl_only_enp', 0)
            oms_only = enp_match.get('oms_only_enp', 0)
            info_items.append(html.P(f"ENP в iszlpeople (дети): {iszl_count}"))
            info_items.append(html.P(f"ENP в omsdata (с целями ПН1/ДС1/ДС2): {oms_count}"))
            info_items.append(html.P(f"Совпадающие ENP: {matching}"))
            info_items.append(html.P(f"Только в iszlpeople: {iszl_only}"))
            info_items.append(html.P(f"Только в omsdata: {oms_only}"))
            if matching == 0 and iszl_count > 0 and oms_count > 0:
                info_items.append(html.P("⚠️ КРИТИЧНО: Нет совпадений по ENP между таблицами! Возможные причины:", 
                                        className='text-danger fw-bold'))
                info_items.append(html.Ul([
                    html.Li("Разные форматы ENP (например, с пробелами или без)"),
                    html.Li("ENP в разных регистрах"),
                    html.Li("ENP содержат лишние символы"),
                ], className='list-unstyled'))
                info_items.append(html.P("Проверьте примеры ENP из обеих таблиц вручную."))
        info_items.append(html.Hr())
        
        # Финальный результат
        final = results.get('check_final_filter', {})
        info_items.append(html.H5("6. Финальный результат (после фильтра COALESCE(o.has_pn1, 0) = 0):"))
        if 'error' in final:
            info_items.append(html.P(f"❌ ОШИБКА: {final.get('error', 'Неизвестная ошибка')}", className='text-danger'))
        else:
            final_count = final.get('final_count', 0)
            info_items.append(html.P(f"Должно быть записей: {final_count}"))
            
            # Диагностика
            if final_count == 0:
                info_items.append(html.Div([
                    html.H5("🔍 Возможные причины пустого результата:", className='text-danger'),
                    html.Ul([
                        html.Li("Если children_count = 0 → нет детей в таблице data_loader_iszlpeople (нужно обновить данные из CSV)"),
                        html.Li("Если with_pn1 = total_after_join → все дети имеют ПН1, значит нет детей без ПН1 (это нормально)"),
                        html.Li("Если matching_enp = 0 → нет совпадений по ENP между таблицами (проверьте форматы ENP)"),
                        html.Li("Проверьте формат даты рождения (dr) - должен быть валидной датой"),
                        html.Li("Проверьте, что все дети действительно младше 18 лет"),
                    ])
                ], className='alert alert-warning'))
            else:
                info_items.append(html.Div([
                    html.P(f"✅ Найдено {final_count} записей. Данные должны отображаться в таблице.", 
                          className='text-success fw-bold')
                ], className='alert alert-success'))
        
        return dbc.Card([
            dbc.CardHeader(html.H4("Результаты диагностики", className='mb-0')),
            dbc.CardBody(info_items)
        ], className='mt-3')
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении диагностики: {str(e)}", exc_info=True)
        return dbc.Alert(f"Ошибка при выполнении диагностики: {str(e)}", color="danger")
