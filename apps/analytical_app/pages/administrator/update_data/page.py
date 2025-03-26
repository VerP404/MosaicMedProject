from dash import dcc, html, Output, Input, exceptions, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from datetime import datetime
import pandas as pd
from datetime import datetime, date

from sqlalchemy import text

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
col_rename = {
    "table_name": "Название таблицы",
    "start_time": "Время начала",
    "end_time": "Время окончания",
    "count_before": "Количество до",
    "count_after": "Количество после",
    "duration": "Длительность",
    "error_occurred": "Ошибка",
    "error_code": "Код ошибки",
    "run_url": "Ссылка"
}

with engine.connect() as connection:
    result = connection.execute(text("SELECT dagster_ip, dagster_port FROM home_mainsettings LIMIT 1"))
    row = result.fetchone()
    if row:
        dagster_url = f"http://{row[0]}:{row[1]}"
    else:
        dagster_url = "http://127.0.0.1:3000"
    result2 = connection.execute(text("SELECT filebrowser_ip, filebrowser_port FROM home_mainsettings LIMIT 1"))
    row = result2.fetchone()
    if row:
        filebrowser_url = f"http://{row[0]}:{row[1]}"
    else:
        filebrowser_url = "http://127.0.0.1:8080"

admin_update_data = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H5("Обновить данные лога загрузки", className="card-title"),
                                                    dcc.DatePickerRange(
                                                        id=f"date-picker-{type_page}",
                                                        min_date_allowed=date(2000, 1, 1),
                                                        max_date_allowed=date(2100, 12, 31),
                                                        initial_visible_month=date.today(),
                                                        start_date=date.today().isoformat(),
                                                        end_date=date.today().isoformat(),
                                                        display_format="DD.MM.YYYY",
                                                    ),
                                                    dbc.Button("Выполнить", id=f'update-button-{type_page}',
                                                               n_clicks=0),
                                                ]
                                            )
                                        ),
                                        md=4,
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H5("Система автоматизации", className="card-title"),
                                                    html.P(
                                                        "Система для контроля работы автоматизации и уведомлений о проблемах"),
                                                    dbc.Button("Открыть", color="success", href=dagster_url,
                                                               target="_blank"),
                                                ]
                                            )
                                        ),
                                        md=4,
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H5("Файловый браузер", className="card-title"),
                                                    html.P("Пользователь и пароль: admin"),
                                                    dbc.Button("Открыть", color="warning", href=filebrowser_url,
                                                               target="_blank"),
                                                ]
                                            )
                                        ),
                                        md=4,
                                    ),
                                ],
                                justify="start",
                                align="center",
                                style={
                                    "padding": "10px",
                                    "background-color": "#f8f9fa",
                                    "border-radius": "5px",
                                    "margin-top": "10px"
                                }
                            ),
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
        card_table(f'result-table1-{type_page}', "Данные", page_size=10),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    [
        Output(f'result-table1-{type_page}', 'columns'),
        Output(f'result-table1-{type_page}', 'data'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [
        Input(f'update-button-{type_page}', 'n_clicks')
    ],
    [
        State(f"date-picker-{type_page}", "start_date"),
        State(f"date-picker-{type_page}", "end_date"),
    ]
)
def update_table(n_clicks, start_date, end_date):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate

    # Если даты не заданы, используем сегодняшний день по умолчанию
    if not start_date or not end_date:
        today_str = date.today().isoformat()
        start_date = today_str
        end_date = today_str

    loading_output = html.Div([dcc.Loading(type="default")])

    # Формируем запрос с фильтром по start_time
    query = f"""
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
        WHERE DATE(start_time) BETWEEN '{start_date}' AND '{end_date}'
    """
    columns, data = TableUpdater.query_to_df(engine, query)

    # Убираем колонку id из списка столбцов
    columns = [col for col in columns if col['id'] != 'id']

    # Переименовываем заголовки столбцов на русский и настраиваем отображение ссылки
    for col in columns:
        if col['id'] in col_rename:
            col['name'] = col_rename[col['id']]
        if col['id'] == 'run_url':
            col['presentation'] = 'markdown'

    # Обрабатываем каждую строку данных
    for row in data:
        # Удаляем поле id
        row.pop("id", None)

        # Преобразуем table_name через словарь
        row["table_name"] = table_name_map.get(row["table_name"], row["table_name"])

        # Форматируем start_time
        if row.get("start_time"):
            if isinstance(row["start_time"], (datetime, pd.Timestamp)):
                row["start_time"] = row["start_time"].strftime("%d.%m.%Y %H:%M:%S")
            elif isinstance(row["start_time"], str):
                dt_start = datetime.fromisoformat(row["start_time"])
                row["start_time"] = dt_start.strftime("%d.%m.%Y %H:%M:%S")

        # Форматируем end_time
        if row.get("end_time"):
            if isinstance(row["end_time"], (datetime, pd.Timestamp)):
                row["end_time"] = row["end_time"].strftime("%d.%m.%Y %H:%M:%S")
            elif isinstance(row["end_time"], str):
                dt_end = datetime.fromisoformat(row["end_time"])
                row["end_time"] = dt_end.strftime("%d.%m.%Y %H:%M:%S")

        # Преобразуем duration (только минуты и секунды)
        if row.get("duration") is not None:
            total_seconds = float(row["duration"])
            minutes = int(total_seconds // 60)
            seconds_float = total_seconds % 60
            row["duration"] = f"{minutes}м {seconds_float:.2f}с"

        # Преобразуем run_url в Markdown-ссылку с текстом "открыть"
        if row.get("run_url"):
            url_text = row["run_url"]
            row["run_url"] = f"[открыть]({url_text})"

    return columns, data, loading_output
