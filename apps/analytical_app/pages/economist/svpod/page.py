from dash import html, dcc, Output, Input, State, ALL, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate

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
                                        # Начальный выпадающий список уровня 0
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id={'type': 'dynamic-dropdown', 'index': 0},
                                                options=get_level_options(),
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
        card_table(f'result-table1-{type_page}', "Данные"),
    ],
    style={"padding": "0rem"}
)

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

# Колбэк для обновления таблицы на основе последнего выбранного уровня
@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'dropdown-year-{type_page}', 'value'),
    State({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
)
def update_table(n_clicks, selected_year, selected_levels):
    if n_clicks is None:
        raise PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    # Оставляем только выбранные значения
    selected_levels = [level for level in selected_levels if level is not None]
    if not selected_levels:
        raise PreventUpdate

    final_level = selected_levels[-1]

    # Получаем условия для последнего выбранного уровня
    filter_conditions = get_filter_conditions([final_level], selected_year)

    # Генерация SQL-запроса с учетом только условий последнего уровня
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_rep(
            selected_year,
            group_id=[final_level],
            filter_conditions=filter_conditions
        )
    )

    return columns1, data1, loading_output