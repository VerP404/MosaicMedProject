import requests
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, Output, Input, html
import pandas as pd
import locale

from apps.chief_app.app import app
from apps.chief_app.query_executor import execute_query
from apps.chief_app.settings import COLORS

try:
    locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "")


def get_api_url(selected_year):
    query = "SELECT main_app_ip, main_app_port FROM home_mainsettings LIMIT 1"
    result = execute_query(query)
    if result:
        ip, port = result[0]
        return f"http://{ip}:{port}/api/dd_query/?year={selected_year}&months=0"
    return "#"


# Функция для получения данных через API
def fetch_dd_data(selected_year):
    url = get_api_url(selected_year)
    try:
        # Отключаем использование прокси
        response = requests.get(url, proxies={"http": None, "https": None})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка: API вернул код {response.status_code}")
            return []
    except Exception as e:
        print(f"Ошибка при вызове API: {e}")
        return []


ROWS_PER_GROUP = 3  # Количество строк в каждой странице
GROUPS = [
    ["ДВ4", "ДВ2", "ОПВ"],  # Группа 1
    ["УД1", "УД2", "ДР1", "ДР2"],  # Группа 2
    ["ПН1", "ДС2"],  # Группа 3
]

dd_table = html.Div(
    [
        dash_table.DataTable(
            id="dd-table",
            columns=[],
            data=[],
            style_header={
                "backgroundColor": COLORS["card_background"],
                "color": COLORS["text"],
                "border": "none",
            },
            style_cell={
                "backgroundColor": COLORS["card_background"],
                "color": COLORS["text"],
                "textAlign": "center",
                "border": "none",
            },
            style_table={
                "overflowX": "auto",
                "border": "none",
            },
            style_as_list_view=True,
        ),
        dcc.Store(id="dd-api-data", data=[]),  # Хранилище для данных API
        dcc.Interval(id="dd-page-interval", interval=10000, n_intervals=0),
    ]
)


@app.callback(
    Output("dd-api-data", "data"),
    Input("selected-year-store", "data"),
)
def load_dd_data(selected_year):
    return fetch_dd_data(selected_year)


@app.callback(
    [Output("dd-table", "data"), Output("dd-table", "columns")],
    [Input("dd-api-data", "data"), Input("dd-page-interval", "n_intervals")],
)
def update_dd_table(api_data, n_intervals):
    df = pd.DataFrame(api_data)
    if df.empty:
        return [], []

    # Изменяем порядок столбцов: goal, Итого, месяцы
    reordered_columns = ["goal", "Итого"] + [str(i) for i in range(1, 13)]
    df = df[reordered_columns]

    # Определяем текущую группу
    current_group_index = n_intervals % len(GROUPS)
    current_group = GROUPS[current_group_index]

    # Фильтруем строки по текущей группе
    filtered_df = df[df["goal"].isin(current_group)]
    # Переименование столбца 'goal' в 'Цель'
    filtered_df.rename(columns={"goal": "Цель"}, inplace=True)
    # Подготовка данных для таблицы
    columns = [{"name": col, "id": col} for col in filtered_df.columns]
    data = filtered_df.to_dict("records")

    return data, columns