# components/sidebar.py
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import execute_query


# Получаем данные для главного меню
def get_main_app_url():
    query = "SELECT main_app_ip, main_app_port FROM home_mainsettings LIMIT 1"
    result = execute_query(query)
    if result:
        ip, port = result[0]
        return f"http://{ip}:{port}"
    return "#"


def create_sidebar():
    main_app_url = get_main_app_url()
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
                         html.Span(" ИСЗЛ", className="ms-2", id="iszl-label")],
                        href="/iszl",
                        active="exact",
                        id="iszl-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-info-circle"),
                         html.Span(" WEB.ОМС", className="ms-2", id="web-oms-label")],
                        href="/web_oms",
                        active="exact",
                        id="web-oms-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-list"),
                         html.Span(" Главное меню", className="ms-2", id="main-menu-label")],
                        href=main_app_url,
                        active="exact",
                        id="main-menu-link"
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
            "top": "56px",
            "left": 0,
            "bottom": 0,
            "padding": "1rem",
            "background-color": "#f8f8fa",
            "transition": "all 0.3s ease",
        },
    )

    @app.callback(
        [Output("sidebar", "style"),
         Output("page-content", "style"),
         Output("main-label", "style"),
         Output("doctor-label", "style"),
         Output("head-label", "style"),
         Output("chief-label", "style"),
         Output("statistic-label", "style"),
         Output("economist-label", "style"),
         Output("admin-label", "style"),
         Output("iszl-label", "style"),
         Output("web-oms-label", "style"),
         Output("main-menu-label", "style")],
        [Input("btn_sidebar", "n_clicks")],
        [State("sidebar-state", "data"),
         State("sidebar", "style"),
         State("page-content", "style")]
    )
    def toggle_sidebar(n_clicks, sidebar_state, sidebar_style, page_content_style):
        if n_clicks and n_clicks % 2 == 1:
            # Меняем состояние на противоположное
            if sidebar_state == "collapsed":
                sidebar_style["width"] = "5rem"
                page_content_style["margin-left"] = "5rem"
            return (sidebar_style, page_content_style,
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"},{"display": "none"},)
        else:
            # Развернутый вид
            sidebar_style["width"] = "14rem"
            page_content_style["margin-left"] = "14rem"
            return (sidebar_style, page_content_style,
                    {"display": "inline"}, {"display": "inline"}, {"display": "inline"}, {"display": "inline"},
                    {"display": "inline"}, {"display": "inline"}, {"display": "inline"}, {"display": "inline"},
                    {"display": "inline"},{"display": "inline"},)

    @app.callback(
        [Output("main-link", "active"),
         Output("doctor-link", "active"),
         Output("head-link", "active"),
         Output("chief-link", "active"),
         Output("statistic-link", "active"),
         Output("economist-link", "active"),
         Output("admin-link", "active"),
         Output("iszl-link", "active"),
         Output("web-oms-link", "active"),
         ],
        [Input("url", "pathname")]
    )
    def update_active_links(pathname):
        return [
            pathname == "/",  # Для главной страницы
            pathname.startswith("/doctor"),  # Для Врача
            pathname.startswith("/head"),  # Для Заведующего
            pathname.startswith("/chief"),  # Для Главного врача
            pathname.startswith("/statistic"),  # Для Статистика
            pathname.startswith("/economist"),  # Для Экономиста, включая вложенные страницы
            pathname.startswith("/admin"),  # Для Администратора
            pathname.startswith("/iszl"),  # Для Помощи
            pathname.startswith("/web_oms"),  # Для Помощи
        ]

    return sidebar
