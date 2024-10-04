# components/sidebar.py
from dash import html
import dash_bootstrap_components as dbc


def create_sidebar():
    sidebar = html.Div(
        [
            # Кнопка сворачивания рядом с пунктами навигации
            html.Div(
                dbc.Button(html.I(className="bi bi-sliders"), color="secondary", id="btn_sidebar", n_clicks=0),
                style={"width": "100%", "text-align": "left", "margin-bottom": "1rem"}
            ),
            # Навигация
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="bi bi-house"), html.Span(" Главная", className="ms-2", id="main-label")],
                        href="/",
                        active="exact",
                        id="main-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-person"),
                         html.Span(" Врач", className="ms-2", id="doctor-label")],
                        href="/doctor",
                        active="exact",
                        id="doctor-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-person-plus"),
                         html.Span(" Заведующий", className="ms-2", id="head-label")],
                        href="/head",
                        active="exact",
                        id="head-link"
                    ),

                    dbc.NavLink(
                        [html.I(className="bi bi-person-check"),
                         html.Span(" Главный врач", className="ms-2", id="chief-label")],
                        href="/chief",
                        active="exact",
                        id="chief-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-bar-chart"),
                         html.Span(" Статистик", className="ms-2", id="statistic-label")],
                        href="/statistic",
                        active="exact",
                        id="statistic-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-currency-dollar"),
                         html.Span(" Экономист", className="ms-2", id="economist-label")],
                        href="/economist",
                        active="exact",
                        id="economist-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-person-circle"),
                         html.Span(" Администратор", className="ms-2", id="admin-label")],
                        href="/admin",
                        active="exact",
                        id="admin-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-info-circle"),
                         html.Span(" Помощь", className="ms-2", id="help-label")],
                        href="/help",
                        active="exact",
                        id="help-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-info-circle"),
                         html.Span(" Запросы", className="ms-2", id="query-label")],
                        href="/query",
                        active="exact",
                        id="query-link"
                    ),

                ],
                vertical=True,
                pills=True,
                className="sidebar-nav"
            ),
        ],
        id="sidebar",
        style={
            "position": "fixed",
            "top": "56px",  # высота навбара
            "left": 0,
            "bottom": 0,
            "width": "5rem",
            "padding": "1rem",
            "background-color": "#f8f8fa",
            "transition": "all 0.3s ease",
        },
    )
    return sidebar
