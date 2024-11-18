import requests
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, Output, Input, html
import pandas as pd
import locale

from apps.chief_app.app import app
from apps.chief_app.settings import COLORS

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")


# Функция для получения данных через API
def fetch_api_data():
    url = "http://127.0.0.1:8000/api/base_query/?year=2024&months=0"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []  # Возвращаем пустой список, если API недоступен
    except Exception as e:
        print(f"Ошибка при вызове API: {e}")
        return []


table_data = fetch_api_data()

# Преобразование в DataFrame
df = pd.DataFrame(table_data)

# Переименование столбцов
df.rename(
    columns={
        "report_month_number": "Месяц",
        "Количество пациентов": "Талоны",
        "Сумма": "Сумма",
    },
    inplace=True,
)
# Вычисление итоговых значений
total_sum = locale.format_string("%.2f", df["Сумма"].sum(), grouping=True)
# Форматирование суммы по разрядам
df["Сумма"] = df["Сумма"].apply(lambda x: locale.format_string("%.2f", x, grouping=True))

# Количество строк на странице
ROWS_PER_PAGE = 4

# Генерация компонента DataTable
report_months = dbc.Container(
    [
        html.Div(
            [
                html.P(f"Сумма нарастающе: {total_sum}", style={"color": COLORS["text"]}),
            ],
            style={"marginTop": "10px", "textAlign": "center"},
        ),
        dash_table.DataTable(
            id="table-card5",
            columns=[{"name": col, "id": col} for col in df.columns],
            data=df[:ROWS_PER_PAGE].to_dict("records"),  # Отображение первых строк
            style_header={"backgroundColor": COLORS["card_background"], "color": COLORS["text"]},
            style_cell={"backgroundColor": COLORS["card_background"], "color": COLORS["text"], "textAlign": "center"},
            style_table={"overflowX": "auto"},
        ),
        dcc.Interval(id="page-interval", interval=5000, n_intervals=0),  # Интервал для переключения страниц

    ]
)


# Callback для переключения страниц
@app.callback(
    Output("table-card5", "data"),
    Input("page-interval", "n_intervals"),
)
def update_table_data(n_intervals):
    current_page = (n_intervals % ((len(df) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE))
    start_index = current_page * ROWS_PER_PAGE
    end_index = start_index + ROWS_PER_PAGE
    return df[start_index:end_index].to_dict("records")
