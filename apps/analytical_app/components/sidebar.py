# components/sidebar.py
from dash import html
import dash_bootstrap_components as dbc


def create_sidebar():
    sidebar = html.Div(
        [
            # Кнопка сворачивания рядом с пунктами навигации
            html.Div(
                dbc.Button(html.I(className="bi bi-chevron-left"), color="secondary", id="btn_sidebar", n_clicks=0),
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
                        [html.I(className="bi bi-info-circle"),
                         html.Span(" О нас", className="ms-2", id="about-label")],
                        href="/about",
                        active="exact",
                        id="about-link"
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
            "width": "18rem",
            "padding": "1rem",
            "background-color": "#f8f8fa",
            "transition": "all 0.3s ease",
        },
    )
    return sidebar
