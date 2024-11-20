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
        return f"http://{ip}:{port}/api/base_query/?year={selected_year}&months=0"
    return "#"

# Функция для получения данных через API
def fetch_api_data(selected_year):
    url = get_api_url(selected_year)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка: API вернул код {response.status_code}")
            return []
    except Exception as e:
        print(f"Ошибка при вызове API: {e}")
        return []

ROWS_PER_PAGE = 3

report_months = dbc.Container(
    [
        # Новая таблица для отображения сводной информации
        dash_table.DataTable(
            id="summary-table",
            columns=[
                {"name": "Отчетный месяц", "id": "Отчетный месяц"},
                {"name": "Среднемесячно", "id": "Среднемесячно"},
                {"name": "Нарастающе", "id": "Нарастающе"},
            ],
            data=[],
            style_header={
                "backgroundColor": COLORS["card_background"],
                "color": COLORS["text"],
                "border": "none",  # Убираем границы в заголовке
            },
            style_cell={
                "backgroundColor": COLORS["card_background"],
                "color": COLORS["text"],
                "textAlign": "center",
                "border": "none",  # Убираем границы ячеек
            },
            style_table={
                "overflowX": "auto",
                "border": "none",  # Убираем границы всей таблицы
            },
            style_as_list_view=True,
        ),
        dash_table.DataTable(
            id="table-card5",
            columns=[],
            data=[],
            style_header={
                "backgroundColor": COLORS["card_background"],
                "color": COLORS["text"],
            },
            style_cell={
                "backgroundColor": COLORS["card_background"],
                "color": COLORS["text"],
                "textAlign": "center",
            },
            style_table={
                "overflowX": "auto",
            },
            style_data_conditional=[],
            style_as_list_view=True,
        ),
        dcc.Interval(
            id="page-interval", interval=5000, n_intervals=0
        ),
        dcc.Store(id="table-data", data=[]),
    ]
)

@app.callback(
    [
        Output("summary-table", "data"),
        Output("table-card5", "columns"),
        Output("table-data", "data"),
    ],
    Input("selected-year-store", "data"),
)
def update_data(selected_year):
    table_data = fetch_api_data(selected_year)
    df = pd.DataFrame(table_data)

    if df.empty:
        return [], [], []

    # Переименование столбцов
    df.rename(
        columns={
            "report_month_number": "Месяц",
            "Количество пациентов": "Талоны",
            "Сумма": "Сумма",
        },
        inplace=True,
    )

    # Преобразование данных без форматирования для таблицы
    df["Сумма"] = df["Сумма"].astype(float)

    # Расчёты для отображения в summary-table
    total_sum = locale.format_string("%.2f", float(df["Сумма"].sum()), grouping=True)
    average_sum = locale.format_string("%.2f", float(df["Сумма"].mean()), grouping=True)
    last_month_value = df.loc[df["Месяц"].idxmax(), "Сумма"]
    last_month_sum = locale.format_string("%.2f", float(last_month_value), grouping=True)

    # Данные для summary-table
    summary_data = [
        {
            "Отчетный месяц": last_month_sum,
            "Среднемесячно": average_sum,
            "Нарастающе": total_sum,
        }
    ]

    # Колонки основной таблицы
    columns = [{"name": col, "id": col} for col in df.columns]

    return summary_data, columns, df.to_dict("records")

@app.callback(
    [
        Output("table-card5", "data"),
        Output("table-card5", "style_data_conditional"),
    ],
    [Input("page-interval", "n_intervals")],
    [Input("table-data", "data")],
)
def update_table_page(n_intervals, table_data):
    df = pd.DataFrame(table_data)
    if df.empty:
        return [], []

    current_page = (n_intervals % ((len(df) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE))
    start_index = current_page * ROWS_PER_PAGE
    end_index = start_index + ROWS_PER_PAGE
    page_data = df[start_index:end_index].to_dict("records")

    # Вычисление среднего
    avg_value = df["Сумма"].mean()

    # Условия форматирования
    style_data_conditional = [
        {
            "if": {"filter_query": f"{{Сумма}} > {avg_value}"},
            "color": "green",
            "fontWeight": "bold",
        },
        {
            "if": {"filter_query": f"{{Сумма}} < {avg_value}"},
            "color": "red",
            "fontWeight": "bold",
        },
    ]

    return page_data, style_data_conditional
