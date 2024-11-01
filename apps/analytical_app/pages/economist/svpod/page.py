from dash import html, dcc, Output, Input, State, ALL, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.svpod.query import sql_query_rep, get_filter_conditions
from apps.analytical_app.query_executor import engine

type_page = "econ-sv-pod"


# Функция для получения опций уровня
def get_level_options(parent_id=None):
    if parent_id is None:
        query = "SELECT DISTINCT id, name FROM plan_groupindicators WHERE parent_id IS NULL"
    else:
        query = f"SELECT id, name FROM plan_groupindicators WHERE parent_id = {parent_id}"
    levels = pd.read_sql(query, engine)
    return [{'label': level['name'], 'value': level['id']} for _, level in levels.iterrows()]


# Макет с контейнером для динамических выпадающих списков
economist_sv_pod = html.Div(
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
                                    dbc.Col(filter_years(type_page), width=2),
                                    html.Div(id='dropdown-container', children=[
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id={'type': 'dynamic-dropdown', 'index': 0},
                                                options=[],
                                                placeholder="Выберите уровень 1",
                                                value=None
                                            ),
                                            width=3
                                        ),
                                    ]),
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
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "Данные", column_selectable='multi'),
        dcc.Store(id=f'selected-data-{type_page}'),
    ],
    style={"padding": "0rem"}
)


# Callback для кнопки "Суммировать"
@app.callback(
    Output(f'sum-result-result-table1-{type_page}', 'children'),
    Input(f'sum-button-result-table1-{type_page}', 'n_clicks'),
    State(f'result-table1-{type_page}', 'derived_virtual_data'),
    State(f'result-table1-{type_page}', 'selected_cells')
)
def calculate_sum_and_count(n_clicks, rows, selected_cells):
    if n_clicks is None:
        raise PreventUpdate

    # Проверка на наличие данных и выделенных ячеек
    if rows is None or not selected_cells:
        return "Нет данных или не выбраны ячейки для подсчета."

    # Инициализация суммы и счетчика
    total_sum = 0
    count = 0

    # Суммируем значения только в выделенных ячейках и считаем их количество
    for cell in selected_cells:
        row_idx = cell['row']  # Индекс строки
        col_id = cell['column_id']  # ID столбца

        # Получаем значение ячейки и добавляем к сумме, если оно является числом
        value = rows[row_idx].get(col_id, 0)
        if isinstance(value, (int, float)):  # Проверяем, что значение является числом
            total_sum += value
            count += 1  # Увеличиваем счетчик для числовых значений

    # Формируем строку с результатом
    return f"Количество выбранных ячеек: {count}, Сумма значений: {total_sum}"


# Колбэк для динамического обновления выпадающих списков
@app.callback(
    Output('dropdown-container', 'children'),
    Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
)
def display_dynamic_dropdowns(values):
    # Инициализируем список выпадающих списков
    dropdowns = []
    level = 0

    # Начальный уровень
    options = get_level_options()
    value = values[0] if values else None

    dropdown = dbc.Col(
        dcc.Dropdown(
            id={'type': 'dynamic-dropdown', 'index': level},
            options=options,
            placeholder="Выберите уровень 1",
            value=value
        ),
        width=3
    )
    dropdowns.append(dropdown)

    # Проходим по выбранным значениям и динамически создаём выпадающие списки
    while True:
        if value is None:
            break  # Если значение не выбрано, прекращаем добавлять уровни

        # Получаем опции для следующего уровня
        options = get_level_options(value)
        if not options:
            break  # Если нет дочерних элементов, прекращаем добавлять уровни

        level += 1
        value = values[level] if len(values) > level else None

        dropdown = dbc.Col(
            dcc.Dropdown(
                id={'type': 'dynamic-dropdown', 'index': level},
                options=options,
                placeholder=f"Выберите уровень {level + 1}",
                value=value
            ),
            width=3
        )
        dropdowns.append(dropdown)

    return dropdowns

# Функция для получения данных плана
def fetch_plan_data(selected_levels, year):
    # Запрашиваем данные плана для всех выбранных уровней и конкретного года
    query = text("""
        SELECT month, SUM(quantity) AS plan
        FROM plan_monthlyplan
        WHERE group_id = ANY(:selected_levels) AND month BETWEEN 1 AND 12
        GROUP BY month
        ORDER BY month
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"selected_levels": selected_levels}).mappings()
        plan_data = {row["month"]: row["plan"] for row in result}
    return plan_data


# Callback для обновления таблицы на основе всех выбранных уровней
@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'dropdown-year-{type_page}', 'value'),
    State({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
)
def update_table_with_plan(n_clicks, selected_year, selected_levels):
    if n_clicks is None:
        raise PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    # Фильтрация уровней, оставляя только выбранные значения
    selected_levels = [level for level in selected_levels if level is not None]
    if not selected_levels:
        raise PreventUpdate

    # Генерация условий для всех выбранных уровней
    filter_conditions = get_filter_conditions(selected_levels, selected_year)

    # Получаем фактические данные из основного запроса
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_rep(
            selected_year,
            group_id=selected_levels,  # передаем все выбранные уровни
            filter_conditions=filter_conditions
        )
    )

    # Получаем данные плана и добавляем их к фактическим данным
    plan_data = fetch_plan_data(selected_levels, selected_year)
    for row in data1:
        month = row.get("month")
        row["План"] = plan_data.get(month, 0)  # Используем план или 0, если данных нет

    # Добавляем колонку "План" к отображаемым колонкам
    columns1.append({"name": "План", "id": "План"})

    return columns1, data1, loading_output
