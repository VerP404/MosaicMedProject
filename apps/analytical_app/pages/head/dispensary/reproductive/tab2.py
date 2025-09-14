from dash import html, Output, Input, State, dcc, exceptions, callback_context
import dash_bootstrap_components as dbc
import time
from functools import lru_cache

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.reproductive.query import  sql_query_reproductive_building_department
from apps.analytical_app.pages.head.dispensary.reproductive.optimized_query import sql_query_reproductive_building_department_optimized
from apps.analytical_app.query_executor import engine

type_page = "tab2-dr"

reproductive_dr2 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                ]
                            ),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        # Улучшенная индикация загрузки с прогресс-баром
        dbc.Row([
            dbc.Col([
                dbc.Progress(
                    id=f'progress-bar-{type_page}',
                    value=0,
                    striped=True,
                    animated=True,
                    style={'display': 'none'}
                ),
                html.Div(id=f'loading-status-{type_page}', style={'text-align': 'center', 'margin': '10px 0'}),
            ], width=12)
        ]),
        dcc.Loading(
            id=f'loading-output-{type_page}', 
            type='default',
            children=[card_table(f'result-table1-{type_page}', "По целям", page_size=10)]
        ),
    ],
    style={"padding": "0rem"}
)


# Кэшированная функция для SQL-запроса
@lru_cache(maxsize=32)
def get_cached_query_result(selected_year, cache_key, use_optimized=True):
    """Кэшированный результат SQL-запроса для ускорения повторных запросов"""
    if use_optimized:
        return sql_query_reproductive_building_department_optimized(
            selected_year,
            months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
            inogorod=None,
            sanction=None,
            amount_null=None,
            building=None,
            profile=None,
            doctor=None,
            input_start=None,
            input_end=None,
            treatment_start=None,
            treatment_end=None
        )
    else:
        return sql_query_reproductive_building_department(
            selected_year,
            months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
            inogorod=None,
            sanction=None,
            amount_null=None,
            building=None,
            profile=None,
            doctor=None,
            input_start=None,
            input_end=None,
            treatment_start=None,
            treatment_end=None
        )


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'progress-bar-{type_page}', 'value'),
     Output(f'progress-bar-{type_page}', 'style'),
     Output(f'loading-status-{type_page}', 'children')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value')]
)
def update_table(n_clicks, selected_year):
    # Если кнопка не была нажата, обновление не происходит
    if n_clicks is None:
        raise exceptions.PreventUpdate

    # Проверяем, что год выбран
    if not selected_year:
        return [], [], 0, {'display': 'none'}, "Ошибка: Выберите год"

    try:
        # Показываем прогресс-бар и начинаем анимацию
        progress_style = {'display': 'block'}
        status_text = "Подготовка запроса..."
        progress_value = 10
        
        # Генерируем ключ кэша на основе года и времени (для обновления кэша)
        cache_key = f"{selected_year}_{int(time.time() // 300)}"  # Обновляем кэш каждые 5 минут
        
        # Получаем SQL-запрос
        status_text = "Формирование SQL-запроса..."
        progress_value = 30
        sql_query = get_cached_query_result(selected_year, cache_key, use_optimized=True)
        
        # Выполняем запрос с индикацией прогресса
        status_text = "Выполнение запроса к базе данных..."
        progress_value = 60
        
        start_time = time.time()
        columns1, data1 = TableUpdater.query_to_df(engine, sql_query)
        execution_time = time.time() - start_time
        
        # Форматируем время выполнения
        if execution_time < 1:
            time_text = f"{execution_time*1000:.0f}мс"
        else:
            time_text = f"{execution_time:.1f}с"
        
        status_text = f"Запрос выполнен за {time_text}. Найдено записей: {len(data1)}"
        progress_value = 100
        
        # Скрываем прогресс-бар после завершения
        progress_style = {'display': 'none'}
        
        return columns1, data1, progress_value, progress_style, status_text
        
    except Exception as e:
        # Обработка ошибок
        error_msg = f"Ошибка при выполнении запроса: {str(e)}"
        return [], [], 0, {'display': 'none'}, error_msg


# Удален дублирующий callback - анимация прогресс-бара теперь в основном callback
