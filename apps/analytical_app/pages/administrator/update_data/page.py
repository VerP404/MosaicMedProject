from dash import dcc, html, Output, Input, State, no_update, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from datetime import datetime, date
import pandas as pd
from sqlalchemy import text
import time

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.query_executor import engine
from apps.analytical_app.elements import card_table

type_page = "admin-update-data"

# Словари для отображения и переименования
table_name_map = {
    "load_data_talons": "Талоны из web-ОМС",
    "data_loader_omsdata": "Талоны из web-ОМС. старая версия",
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
    dagster_url = f"http://{row[0]}:{row[1]}" if row else "http://127.0.0.1:3000"
    result2 = connection.execute(text("SELECT filebrowser_ip, filebrowser_port FROM home_mainsettings LIMIT 1"))
    row = result2.fetchone()
    filebrowser_url = f"http://{row[0]}:{row[1]}" if row else "http://127.0.0.1:8080"

# Основной layout страницы
admin_update_data = html.Div(
    [
        # Скрытый Store для обновления таблицы после удаления
        dcc.Store(id=f"table-refresh-store-{type_page}"),
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
                                                    dbc.Button("Выполнить", id=f"update-button-{type_page}", n_clicks=0),
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
                                                    html.P("Система для контроля работы автоматизации и уведомлений о проблемах"),
                                                    dbc.Button("Открыть", color="success", href=dagster_url, target="_blank"),
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
                                                    dbc.Button("Открыть", color="warning", href=filebrowser_url, target="_blank"),
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
        dcc.Loading(id=f"loading-output-{type_page}", type='default'),
        # Элементы для управления выбором и удалением (с использованием type_page в id)
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    html.Div(
                        [
                            dcc.Input(id=f"pin-input-{type_page}", type="password", placeholder="Введите PIN"),
                            dbc.Button("Выбрать все", id=f"select-all-button-{type_page}", color="info"),
                            dbc.Button("Снять выделение", id=f"clear-selection-button-{type_page}", color="secondary"),
                            dbc.Button("Удалить выбранные", id=f"delete-button-{type_page}", n_clicks=0, color="danger")
                        ],
                        style={"display": "flex", "gap": "10px", "alignItems": "center", "marginBottom": "10px"}
                    ),
                    title="Удаление записей из истории"
                )
            ],
            active_item=None  # по умолчанию все элементы свернуты
        ),
        dbc.Alert(id=f"delete-alert-{type_page}", is_open=False, duration=4000, style={"marginBottom": "10px"}),
        # Таблица с множественным выбором строк
        card_table(f"result-table1-{type_page}", "Данные", page_size=10, row_selectable="multi", hidden_columns=["id"]),
        # Модальное окно для подтверждения удаления
        dbc.Modal(
            [
                dbc.ModalHeader("Подтверждение удаления"),
                dbc.ModalBody("Вы уверены, что хотите удалить выбранные записи?"),
                dbc.ModalFooter(
                    dbc.Button("Подтвердить", id=f"confirm-delete-{type_page}", n_clicks=0, className="ml-auto")
                ),
            ],
            id=f"delete-modal-{type_page}",
            is_open=False,
        )
    ],
    style={"padding": "0rem"}
)

# Callback обновления таблицы, с учетом dcc.Store для обновления после удаления
@app.callback(
    [
        Output(f"result-table1-{type_page}", 'columns'),
        Output(f"result-table1-{type_page}", 'data'),
        Output(f"loading-output-{type_page}", 'children')
    ],
    [
        Input(f"update-button-{type_page}", 'n_clicks'),
        Input(f"table-refresh-store-{type_page}", "data")
    ],
    [
        State(f"date-picker-{type_page}", "start_date"),
        State(f"date-picker-{type_page}", "end_date"),
    ]
)
def update_table(n_clicks, refresh_trigger, start_date, end_date):
    if (n_clicks is None or n_clicks == 0) and refresh_trigger is None:
        raise PreventUpdate

    if not start_date or not end_date:
        today_str = date.today().isoformat()
        start_date = today_str
        end_date = today_str

    loading_output = html.Div([dcc.Loading(type="default")])
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
        ORDER BY start_time DESC
    """
    columns, data = TableUpdater.query_to_df(engine, query)

    for col in columns:
        if col['id'] in col_rename:
            col['name'] = col_rename[col['id']]
        if col['id'] == 'run_url':
            col['presentation'] = 'markdown'

    for row in data:
        row["table_name"] = table_name_map.get(row["table_name"], row["table_name"])
        for key in ["start_time", "end_time"]:
            if row.get(key):
                dt_val = row[key]
                if isinstance(dt_val, (datetime, pd.Timestamp)):
                    row[key] = dt_val.strftime("%d.%m.%Y %H:%M:%S")
                elif isinstance(dt_val, str):
                    dt_obj = datetime.fromisoformat(dt_val)
                    row[key] = dt_obj.strftime("%d.%m.%Y %H:%M:%S")
        if row.get("duration") is not None:
            total_seconds = float(row["duration"])
            minutes = int(total_seconds // 60)
            seconds_float = total_seconds % 60
            row["duration"] = f"{minutes}м {seconds_float:.2f}с"
        if row.get("run_url"):
            url_text = row["run_url"]
            row["run_url"] = f"[открыть]({url_text})"

    return columns, data, loading_output

# Callback для открытия/закрытия модального окна
@app.callback(
    Output(f"delete-modal-{type_page}", "is_open"),
    [Input(f"delete-button-{type_page}", "n_clicks"), Input(f"confirm-delete-{type_page}", "n_clicks")],
    [State(f"delete-modal-{type_page}", "is_open")]
)
def toggle_modal(delete_click, confirm_click, is_open):
    if delete_click or confirm_click:
        return not is_open
    return is_open

# Единый callback для управления выбранными строками (selected_rows)
@app.callback(
    Output(f"result-table1-{type_page}", "selected_rows"),
    [
        Input(f"table-refresh-store-{type_page}", "data"),
        Input(f"select-all-button-{type_page}", "n_clicks"),
        Input(f"clear-selection-button-{type_page}", "n_clicks")
    ],
    [
        State(f"result-table1-{type_page}", "derived_virtual_data"),
        State(f"result-table1-{type_page}", "data")
    ]
)
def update_selected_rows(refresh_data, select_all_clicks, clear_clicks, derived_virtual_data, full_data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    # Используем только видимые строки, если они заданы, иначе полные данные.
    visible_data = derived_virtual_data if derived_virtual_data is not None else full_data
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == f"select-all-button-{type_page}":
        # Выбираем индексы только для видимых строк
        return list(range(len(visible_data)))
    elif trigger_id in [f"clear-selection-button-{type_page}", f"table-refresh-store-{type_page}"]:
        return []
    else:
        return no_update


# Callback для удаления выбранных записей и обновления таблицы (без обновления selected_rows)
@app.callback(
    [
        Output(f"delete-alert-{type_page}", "children"),
        Output(f"delete-alert-{type_page}", "color"),
        Output(f"delete-alert-{type_page}", "is_open"),
        Output(f"table-refresh-store-{type_page}", "data")
    ],
    Input(f"confirm-delete-{type_page}", "n_clicks"),
    [
        State(f"result-table1-{type_page}", "selected_rows"),
        State(f"result-table1-{type_page}", "data"),
        State(f"pin-input-{type_page}", "value")
    ]
)
def delete_records(n_clicks, selected_rows, table_data, pin):
    if not n_clicks:
        raise PreventUpdate

    STORED_PIN = "1234"  # Пин-код
    if pin != STORED_PIN:
        return "Неверный PIN", "danger", True, no_update

    if not selected_rows:
        return "Нет выбранных записей для удаления", "warning", True, no_update

    delete_ids = []
    for i in selected_rows:
        if "id" in table_data[i]:
            delete_ids.append(table_data[i]["id"])

    if not delete_ids:
        return "Невозможно определить записи для удаления", "warning", True, no_update

    try:
        with engine.connect() as connection:
            query = text("DELETE FROM load_data_loadlog WHERE id IN :ids")
            connection.execute(query, {"ids": tuple(delete_ids)})
            connection.commit()
        refresh_val = time.time()  # генерируем новое значение для обновления таблицы
        return "Записи успешно удалены", "success", True, refresh_val
    except Exception as e:
        return f"Ошибка при удалении: {e}", "danger", True, no_update
