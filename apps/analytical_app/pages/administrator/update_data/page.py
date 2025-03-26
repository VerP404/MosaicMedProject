from dash import dcc, html, Output, Input, exceptions
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from datetime import datetime
import pandas as pd

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.query_executor import engine
from apps.analytical_app.elements import card_table

type_page = "admin-update-data"

# Словарь для отображения table_name
table_name_map = {
    "load_data_talons": "Талоны из web-ОМС",
    "some_other_table": "Другая таблица",
}

admin_update_data = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Button("Получить данные", id=f'update-button-{type_page}', n_clicks=0)
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                        "border-radius": "10px"
                    }
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "Данные load_data_loadlog", page_size=10),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    [
        Output(f'result-table1-{type_page}', 'columns'),
        Output(f'result-table1-{type_page}', 'data'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')]
)
def update_table(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    query = """
        SELECT 
            id, 
            table_name, 
            start_time, 
            end_time, 
            count_before, 
            count_after, 
            duration, 
            error_occurred, 
            error_code, 
            run_url
        FROM load_data_loadlog
    """
    # columns и data - это структуры для DataTable (из TableUpdater)
    columns, data = TableUpdater.query_to_df(engine, query)

    # Настраиваем столбцы вручную, чтобы run_url стал markdown-ссылкой
    # Берем исходные колонки из columns, и при необходимости дополняем/меняем
    for col in columns:
        if col['id'] == 'run_url':
            # Позволяем в ячейках использовать Markdown
            col['presentation'] = 'markdown'

    # Обрабатываем каждую строку
    for row in data:
        # 1. Сопоставляем table_name со словарём
        row["table_name"] = table_name_map.get(row["table_name"], row["table_name"])

        # 2. Форматируем start_time
        if row.get("start_time"):
            if isinstance(row["start_time"], (datetime, pd.Timestamp)):
                row["start_time"] = row["start_time"].strftime("%d.%m.%Y %H:%M:%S")
            elif isinstance(row["start_time"], str):
                # Если всё же строка
                dt_start = datetime.fromisoformat(row["start_time"])
                row["start_time"] = dt_start.strftime("%d.%m.%Y %H:%M:%S")

        # 3. Форматируем end_time
        if row.get("end_time"):
            if isinstance(row["end_time"], (datetime, pd.Timestamp)):
                row["end_time"] = row["end_time"].strftime("%d.%m.%Y %H:%M:%S")
            elif isinstance(row["end_time"], str):
                dt_end = datetime.fromisoformat(row["end_time"])
                row["end_time"] = dt_end.strftime("%d.%m.%Y %H:%M:%S")

        # 4. Преобразуем duration (только минуты и секунды)
        if row.get("duration") is not None:
            total_seconds = float(row["duration"])
            minutes = int(total_seconds // 60)
            seconds_float = total_seconds % 60
            row["duration"] = f"{minutes}м {seconds_float:.2f}с"

        # 5. run_url -> Markdown-ссылка
        if row.get("run_url"):
            url_text = row["run_url"]
            row["run_url"] = f"[открыть]({url_text})"

    return columns, data, loading_output
