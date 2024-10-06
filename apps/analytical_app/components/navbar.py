# components/navbar.py
import datetime
from email.utils import format_datetime

from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app


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
                        # Справка и дата в одном ряду
                        dbc.Col(
                            dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem("Справка", header=True),
                                    dbc.DropdownMenuItem("Статусы талонов", href="/statuses"),
                                    dbc.DropdownMenuItem("Диагнозы по 168н", href="/diagnoses-168"),
                                    dbc.DropdownMenuItem("Инструкция", href="/readme"),
                                    dbc.DropdownMenuItem("2023 год", href="http://10.136.29.166:2023/"),
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
                    className="ms-auto",  # Сдвигает элементы вправо
                ),
            ],
            fluid=True,  # Используем всю ширину страницы
            style={"padding-left": "50px", "padding-right": "20px"},  # Отступы слева и справа
        ),
        color="primary",
        dark=True,
        fixed="top",
    )

    # Callback для обновления времени в навбаре
    @app.callback(
        Output('current-time', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_time(n):
        now = datetime.datetime.now()
        formatted_time = format_datetime(now, "EEE d MMMM y H:mm:ss", locale='ru')
        return formatted_time

    return navbar
