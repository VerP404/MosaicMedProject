from datetime import datetime

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
def fetch_plan_data(selected_level, year):
    # Запрашиваем данные плана для одного выбранного уровня и конкретного года
    query = text("""
        SELECT month, SUM(quantity) AS plan
        FROM plan_monthlyplan
        WHERE group_id = :selected_level AND month BETWEEN 1 AND 12
        GROUP BY month
        ORDER BY month
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"selected_level": selected_level}).mappings()
        plan_data = {row["month"]: row["plan"] for row in result}
    return plan_data


# Callback для обновления таблицы с добавлением процента выполнения
@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data')],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'dropdown-year-{type_page}', 'value'),
    State({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
)
def update_table_with_plan_and_balance(n_clicks, selected_year, selected_levels):
    if n_clicks is None:
        raise PreventUpdate

    selected_levels = [level for level in selected_levels if level is not None]
    if not selected_levels:
        raise PreventUpdate

    # Получаем фактические данные и план для одного выбранного уровня
    selected_level = selected_levels[-1]
    filter_conditions = get_filter_conditions([selected_level], selected_year)
    fact_columns, fact_data = TableUpdater.query_to_df(
        engine,
        sql_query_rep(selected_year, group_id=[selected_level], filter_conditions=filter_conditions)
    )
    plan_data = fetch_plan_data(selected_level, selected_year)

    # Получаем текущую дату и месяц
    today = datetime.today()
    current_month = today.month
    current_day = today.day

    # Добавляем "План 1/12", "Входящий остаток" и вычисляем "План" и "Факт"
    incoming_balance = 0
    for row in fact_data:
        month = row.get("month")
        row["План 1/12"] = plan_data.get(month, 0)  # Извлеченное значение из базы
        row["Входящий остаток"] = incoming_balance
        row["План"] = row["План 1/12"] + row["Входящий остаток"]  # Сумма "План 1/12" и "Входящий остаток"

        # Условие для расчета Итогового "Факт"
        if month < current_month - 1:
            # Для месяцев до предыдущего текущего месяца используем только "оплачено"
            row["Факт"] = row.get("оплачено", 0)
        elif month == current_month - 1:
            # Для предыдущего месяца используем "оплачено" после 10-го числа, иначе суммируем "новые", "в_тфомс", "оплачено", "исправлено"
            if current_day <= 10:
                row["Факт"] = sum(row.get(col, 0) for col in ["новые", "в_тфомс", "оплачено", "исправлено"])
            else:
                row["Факт"] = row.get("оплачено", 0)
        elif month == current_month:
            # Для текущего месяца суммируем "новые", "в_тфомс", "оплачено", "исправлено"
            row["Факт"] = sum(row.get(col, 0) for col in ["новые", "в_тфомс", "оплачено", "исправлено"])

        # Рассчитываем процент выполнения (если План не равен нулю) и форматируем до одного знака после запятой
        row["%"] = round((row["Факт"] / row["План"] * 100), 1) if row["План"] != 0 else 0

        # Обновляем входящий остаток для следующего месяца
        incoming_balance = row["План 1/12"] - row.get("оплачено", 0)

    # Структура заголовков с учетом всех требований
    columns = [
        {"name": ["", "Месяц"], "id": "month"},
        {"name": ["Итог", "План"], "id": "План"},
        {"name": ["Итог", "Факт"], "id": "Факт"},
        {"name": ["Итог", "%"], "id": "%"},
        {"name": ["Факт", "Новые"], "id": "новые"},
        {"name": ["Факт", "В ТФОМС"], "id": "в_тфомс"},
        {"name": ["Факт", "Оплачено"], "id": "оплачено"},
        {"name": ["Факт", "Отказано"], "id": "отказано"},
        {"name": ["Факт", "Исправлено"], "id": "исправлено"},
        {"name": ["Факт", "Отменено"], "id": "отменено"},
        {"name": ["План 1/12", "План 1/12"], "id": "План 1/12"},  # Значение плана из базы
        {"name": ["План 1/12", "Входящий остаток"], "id": "Входящий остаток"},
    ]

    return columns, fact_data

