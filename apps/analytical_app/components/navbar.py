# components/navbar.py
from dash import html, Output, Input, State, exceptions, dcc
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine


# Создаем модальное окно
def create_modal():
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


def create_navbar():
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
                            dbc.Col(dbc.NavbarBrand("БУЗ ВО \"ВГП №3\"", className="ms-2")),
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
                        dbc.Col(
                            dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem("Справка", header=True),
                                    dbc.DropdownMenuItem("Статусы талонов", id="open-modal-status", n_clicks=0),
                                    dbc.DropdownMenuItem("Диагнозы по 168н", id="open-modal-168", n_clicks=0),
                                    # Открытие модального окна
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

    return navbar


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
        columns, data = TableUpdater.query_to_df(engine,
                                                 f"SELECT status::integer as \"Цель\", "
                                                 "name as \"Название\" FROM oms_reference_statusweboms "
                                                 "ORDER BY status::integer")
        return columns, data
    return [], []
