# components/navbar.py
from dash import html, Output, Input, State, exceptions, dcc, callback_context, ALL
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine, execute_query
from sqlalchemy import text
from datetime import datetime
import time
from urllib.parse import urlparse
import pandas as pd


def get_organization_name():
    query = "SELECT name FROM organization_medicalorganization LIMIT 1"
    result = execute_query(query)
    if result:
        return result[0][0]
    return "Организация не указана"


# Создаем модальное окно
def create_modal_168n():
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Диагнозы по 168н")),
            dbc.ModalBody(
                card_table(id_table="modal-table-168", card_header="Данные по 168н", page_size=15)
            ),
            dbc.ModalFooter(
                dbc.Button("Закрыть", id="close-modal-168", className="ms-auto", n_clicks=0),
            ),
        ],
        id="modal-168",
        size="lg",  # Размер окна
        is_open=False,  # По умолчанию закрыто
    )
    return modal


def create_modal_status():
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Статусы талонов WEB-ОМС")),
            dbc.ModalBody(
                card_table(id_table="modal-table-status", card_header="Статусы талонов WEB-ОМС", page_size=15)
            ),
            dbc.ModalFooter(
                dbc.Button("Закрыть", id="close-modal-status", className="ms-auto", n_clicks=0),
            ),
        ],
        id="modal-status",
        size="lg",  # Размер окна
        is_open=False,  # По умолчанию закрыто
    )
    return modal


def create_modal_goal():
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Цели в системе ОМС")),
            dbc.ModalBody(
                card_table(id_table="modal-table-goal", card_header="Цели в системе ОМС", page_size=15)
            ),
            dbc.ModalFooter(
                dbc.Button("Закрыть", id="close-modal-goal", className="ms-auto", n_clicks=0),
            ),
        ],
        id="modal-goal",
        size="xl",
        is_open=False,
    )
    return modal


def create_navbar():
    organization_name = get_organization_name()
    
    # Создаем offcanvas для обновлений
    updates_offcanvas = create_updates_offcanvas()
    
    navbar = dbc.Navbar(
        dbc.Container(
            [
                # Логотип и название слева
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src="/assets/img/plotly-logomark.png", height="30px")),
                            dbc.Col(dbc.NavbarBrand("МозаикаМед-Аналитика", className="ms-2")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                dbc.NavLink(),
                dbc.NavLink(),
                dbc.NavLink(),
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(dbc.NavbarBrand(organization_name, className="ms-2")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                # Элементы справа: справка и дата
                dbc.Row(
                    [
                        # Кнопка Обновления
                        dbc.Col(
                            dbc.Button(
                                [
                                    "Обновления"
                                ],
                                id="open-updates-offcanvas", 
                                color="success", 
                                className="me-2",
                                size="sm"
                            ),
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem("Справка", header=True),
                                    dbc.DropdownMenuItem("Статусы талонов", id="open-modal-status", n_clicks=0),
                                    dbc.DropdownMenuItem("Диагнозы по 168н", id="open-modal-168", n_clicks=0),
                                    dbc.DropdownMenuItem("Цели в системе ОМС", id="open-modal-goal", n_clicks=0),
                                ],
                                nav=True,
                                in_navbar=True,
                                label=html.Span("Справка", className="text-white"),
                            ),
                            width="auto"
                        ),
                        # Дата
                        dbc.Col(
                            html.Div(id='current-date-output', style={"color": "white", "margin-left": "15px"}),
                            width="auto"
                        ),
                    ],
                    align="center",
                    className="ms-auto",
                ),
            ],
            fluid=True,
            style={"padding-left": "50px", "padding-right": "20px"},
        ),
        color="primary",
        dark=True,
        fixed="top",
    )

    return html.Div([navbar, updates_offcanvas])


# (удалено) Ненужный колбэк, который пытался обновлять href у кнопки


# Добавляем callback для модального окна
@app.callback(
    Output("modal-168", "is_open"),
    [Input("open-modal-168", "n_clicks"),
     Input("close-modal-168", "n_clicks")],
    [State("modal-168", "is_open")]
)
def toggle_modal(open_clicks, close_clicks, is_open):
    if open_clicks and not close_clicks:
        return True
    elif close_clicks:
        return False
    return is_open


@app.callback(
    Output("modal-status", "is_open"),
    [Input("open-modal-status", "n_clicks"),
     Input("close-modal-status", "n_clicks")],
    [State("modal-status", "is_open")]
)
def toggle_modal(open_clicks, close_clicks, is_open):
    if open_clicks and not close_clicks:
        return True
    elif close_clicks:
        return False
    return is_open


@app.callback(
    Output("modal-goal", "is_open"),
    [Input("open-modal-goal", "n_clicks"),
     Input("close-modal-goal", "n_clicks")],
    [State("modal-goal", "is_open")]
)
def toggle_modal(open_clicks, close_clicks, is_open):
    if open_clicks and not close_clicks:
        return True
    elif close_clicks:
        return False
    return is_open


@app.callback(
    [Output(f'modal-table-168', 'columns'),
     Output(f'modal-table-168', 'data'),
     ],
    [Input(f'open-modal-168', 'n_clicks')]
)
def update_table(n_clicks):
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, "SELECT * FROM data_loader_ds168n")
        return columns, data
    return [], []


@app.callback(
    [Output(f'modal-table-status', 'columns'),
     Output(f'modal-table-status', 'data'),
     ],
    [Input(f'open-modal-status', 'n_clicks')]
)
def update_table(n_clicks):
    if n_clicks > 0:
        # Импортируем status_descriptions из filters.py
        from apps.analytical_app.components.filters import status_descriptions
        
        # Создаем список данных из словаря status_descriptions
        data = []
        # Сортируем статусы: сначала числовые (как числа), потом нечисловые
        sorted_items = sorted(status_descriptions.items(), 
                            key=lambda x: (int(x[0]) if x[0].isdigit() else 999, x[0]))
        for status, description in sorted_items:
            data.append({
                'Статус': status,
                'Описание': description
            })
        
        # Создаем DataFrame и преобразуем в формат для Dash DataTable
        df = pd.DataFrame(data)
        columns = [{"name": col, "id": col} for col in df.columns]
        data = df.to_dict('records')
        
        return columns, data
    return [], []


sql_query = """
            SELECT g.code                                  as "Код",
                   g.name                                  as "Наименование",
                   CASE
                       WHEN m.is_active THEN 'Да'
                       ELSE 'Нет'
                       END                                 AS "Действует",
                   COALESCE(STRING_AGG(c.name, ', '), '-') AS "Группа"
            FROM oms_reference_generalomstarget g
                     JOIN
                 oms_reference_medicalorganizationomstarget m
                 ON
                     g.id = m.general_target_id
                     LEFT JOIN
                 oms_reference_medicalorganizationomstarget_categories l
                 ON
                     m.id = l.medicalorganizationomstarget_id
                     LEFT JOIN
                 oms_reference_omstargetcategory c
                 ON
                     l.omstargetcategory_id = c.id
            GROUP BY g.code, g.name, m.is_active, m.start_date, m.end_date
            ORDER BY CASE
                         WHEN g.code ~ '^[0-9]+$' THEN lpad(g.code, 10, '0')
                         ELSE g.code
                         END \
            """


@app.callback(
    [Output(f'modal-table-goal', 'columns'),
     Output(f'modal-table-goal', 'data'),
     ],
    [Input(f'open-modal-goal', 'n_clicks')]
)
def update_table(n_clicks):
    if n_clicks > 0:
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        return columns, data
    return [], []


# Создаем компонент offcanvas для отображения информации об обновлениях
def create_updates_offcanvas():
    # Получаем URL из модуля страницы администратора
    try:
        from apps.analytical_app.pages.administrator.update_data.page import dagster_url, filebrowser_url
    except ImportError:
        dagster_url = "http://127.0.0.1:3000"
        filebrowser_url = "http://127.0.0.1:8080"
        
    offcanvas = dbc.Offcanvas(
        [
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H5("Информация об обновлении данных", className="mb-0"),
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        html.I(className="bi bi-arrow-repeat"),  # Используем иконку Bootstrap
                                        id="refresh-updates-button",
                                        color="primary",
                                        size="sm",
                                        className="float-end"
                                    ),
                                    width="auto"
                                )
                            ],
                            align="center"
                        )
                    ),
                    dbc.CardBody(
                        [
                            html.P("Последние обновления данных в системе:", className="mb-3"),
                            html.Div(
                                id="loading-container",
                                children=[
                                    dbc.Spinner(
                                        color="primary",
                                        type="border",
                                        size="lg", 
                                        spinner_style={"width": "3rem", "height": "3rem"}
                                    ),
                                ],
                                style={"textAlign": "center", "minHeight": "200px", "paddingTop": "70px"}
                            ),
                            html.Div(
                                id="updates-table-container",
                                style={"display": "none"}
                            ),
                            html.Div(id="last-updated-time", className="text-muted mt-3 small"),
                            
                            # Добавляем секцию с кнопками управления
                            html.Hr(className="my-4"),
                            html.H6("Управление системой:", className="mb-3"),
                            
                            # Кнопки без карточек
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            [
                                                html.I(className="bi bi-robot me-2"),
                                                "Система автоматизации"
                                            ],
                                            color="primary",
                                            href=dagster_url,
                                            target="_blank",
                                            className="w-100"
                                        ),
                                        md=6,
                                        className="mb-3"
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            [
                                                html.I(className="bi bi-folder2-open me-2"),
                                                "Файловый браузер"
                                            ],
                                            color="warning",
                                            href=filebrowser_url,
                                            target="_blank",
                                            className="w-100"
                                        ),
                                        md=6,
                                        className="mb-3"
                                    ),
                                ],
                                className="mt-3"
                            ),
                            
                            # Добавляем информационный блок с подсказкой
                            dbc.Alert(
                                [
                                    html.I(className="bi bi-info-circle-fill me-2"),
                                    "Имя пользователя и пароль по умолчанию: admin"
                                ],
                                color="info",
                                className="mt-3 small py-2"
                            ),
                        ]
                    )
                ],
                className="border-0 h-100"
            )
        ],
        id="updates-offcanvas",
        title="Обновления данных",
        placement="start",
        is_open=False,
    )
    return offcanvas


# Добавляем callback для открытия/закрытия offcanvas с обновлениями
@app.callback(
    Output("updates-offcanvas", "is_open"),
    Input("open-updates-offcanvas", "n_clicks"),
    State("updates-offcanvas", "is_open"),
)
def toggle_updates_offcanvas(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


# Добавляем callback для обновления данных в таблице обновлений
@app.callback(
    [
        Output("updates-table-container", "children"),
        Output("updates-table-container", "style"),
        Output("loading-container", "style"),
        Output("last-updated-time", "children")
    ],
    [Input("updates-offcanvas", "is_open"),
     Input("refresh-updates-button", "n_clicks")]
)
def update_updates_data(is_open, n_clicks):
    # Определяем контекст вызова callback
    ctx = callback_context
    
    # Если callback вызван не открытием offcanvas и не нажатием кнопки обновления, не делаем ничего
    if not ctx.triggered or (not is_open and ctx.triggered[0]["prop_id"] == "updates-offcanvas.is_open"):
        return None, {"display": "none"}, {"display": "none"}, ""
    
    # Добавим небольшую задержку для демонстрации спиннера
    time.sleep(1)
    
    # Получаем информацию о последних обновлениях таблиц
    tables_to_check = [
        {"name": "ОМС: Талоны", "table": "load_data_talons"},
        {"name": "ОМС: Врачи", "table": "load_data_doctor"},
        {"name": "ОМС: Отказы", "table": "load_data_error_log_talon"},
        {"name": "ОМС: Диспансеризация", "table": "load_data_detailed_medical_examination"},
        {"name": "Квазар: ЭМД", "table": "load_data_emd"},
    ]
    
    rows = []
    
    try:
        with engine.connect() as conn:
            for table_info in tables_to_check:
                query = f"SELECT MAX(updated_at) FROM {table_info['table']}"
                result = conn.execute(text(query)).fetchone()
                if result and result[0]:
                    # Форматируем дату в нужный формат
                    update_time = result[0]
                    formatted_time = update_time.strftime("%d.%m.%Y %H:%M")
                    rows.append(html.Tr([
                        html.Td(table_info["name"]),
                        html.Td(formatted_time)
                    ]))
                else:
                    rows.append(html.Tr([
                        html.Td(table_info["name"]),
                        html.Td("Нет данных")
                    ]))
    except Exception as e:
        rows.append(html.Tr([
            html.Td("Ошибка получения данных"),
            html.Td(str(e))
        ]))
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Данные"),
            html.Th("Обновлено")
        ]))
    ]
    
    table_body = [html.Tbody(rows)]
    
    # Создаем таблицу
    table = dbc.Table(
        table_header + table_body,
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    last_updated_text = f"Информация актуальна на: {current_time}"
    
    # Возвращаем таблицу, стиль для контейнера таблицы (показать), 
    # стиль для контейнера спиннера (скрыть), и текст с временем
    return table, {"display": "block"}, {"display": "none"}, last_updated_text


# Добавляем callback для показа спиннера при открытии панели
@app.callback(
    [
        Output("loading-container", "style", allow_duplicate=True),
        Output("updates-table-container", "style", allow_duplicate=True)
    ],
    [Input("updates-offcanvas", "is_open")],
    prevent_initial_call=True
)
def show_spinner_on_open(is_open):
    if is_open:
        return {"textAlign": "center", "minHeight": "200px", "paddingTop": "70px", "display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "none"}
