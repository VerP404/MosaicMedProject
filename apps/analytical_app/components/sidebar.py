
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from urllib.parse import urlparse

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import execute_query


# Получаем порт основного приложения
def get_main_app_port():
    query = "SELECT main_app_port FROM home_mainsettings LIMIT 1"
    result = execute_query(query)
    if result and result[0] and result[0][0] is not None:
        return int(result[0][0])
    return 8000


def create_sidebar():
    main_app_url = "#"
    sidebar = html.Div(
        [
            # Кнопка сворачивания рядом с пунктами навигации
            html.Div(
                dbc.Button(html.I(className="bi bi-sliders"), color="secondary", id="btn_sidebar", n_clicks=0),
                style={"width": "100%", "textAlign": "left", "marginBottom": "1rem"}
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

                    # dbc.NavLink(
                    #     [html.I(className="bi bi-person-check"),
                    #      html.Span(" Главный врач", className="ms-2", id="chief-label")],
                    #     href="/chief",
                    #     active="exact",
                    #     id="chief-link"
                    # ),
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
                    # dbc.NavLink(
                    #     [html.I(className="bi bi-info-circle"),
                    #      html.Span(" ИСЗЛ", className="ms-2", id="iszl-label")],
                    #     href="/iszl",
                    #     active="exact",
                    #     id="iszl-link"
                    # ),
                    dbc.NavLink(
                        [html.I(className="bi bi-info-circle"),
                         html.Span(" WEB.ОМС", className="ms-2", id="web-talon-label")],
                        href="/web_oms",
                        active="exact",
                        id="web-talon-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-card-list"),
                         html.Span(" Реестры", className="ms-2", id="registry-label")],
                        href="/registry",
                        active="exact",
                        id="registry-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-filter-square"),
                         html.Span(" Лаборатория", className="ms-2", id="laboratory-label")],
                        href="/laboratory",
                        active="exact",
                        id="laboratory-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-list"),
                         html.Span(" Главное меню", className="ms-2", id="main-menu-label")],
                        href=main_app_url,
                        active=False,
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
         # Output("chief-label", "style"),
         Output("statistic-label", "style"),
         Output("economist-label", "style"),
         Output("admin-label", "style"),
         # Output("iszl-label", "style"),
         Output("web-talon-label", "style"),
         Output("registry-label", "style"),
         Output("laboratory-label", "style"),
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
                page_content_style["marginLeft"] = "5rem"
            return (sidebar_style, page_content_style,
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}
                    )
        else:
            # Развернутый вид
            sidebar_style["width"] = "14rem"
            page_content_style["marginLeft"] = "14rem"
            return (sidebar_style, page_content_style,
                    {"display": "inline"}, {"display": "inline"}, {"display": "inline"}, {"display": "inline"},
                    {"display": "inline"}, {"display": "inline"}, {"display": "inline"}, {"display": "inline"},
                    {"display": "inline"}, {"display": "inline"}
                    )

    @app.callback(
        [Output("main-link", "active"),
         Output("doctor-link", "active"),
         Output("head-link", "active"),
         # Output("chief-link", "active"),
         Output("statistic-link", "active"),
         Output("economist-link", "active"),
         Output("admin-link", "active"),
         # Output("iszl-link", "active"),
         Output("web-talon-link", "active"),
         Output("registry-link", "active"),
         Output("laboratory-link", "active"),
         ],
        [Input("url", "pathname")]
    )
    def update_active_links(pathname):
        return [
            pathname == "/",  # Для главной страницы Dash
            pathname.startswith("/doctor"),
            pathname.startswith("/head"),
            pathname.startswith("/statistic"),
            pathname.startswith("/economist"),
            pathname.startswith("/admin"),
            pathname.startswith("/web_oms"),
            pathname.startswith("/registry"),
            pathname.startswith("/laboratory"),
        ]

    @app.callback(
        Output("main-menu-link", "href"),
        Input("url", "href")
    )
    def update_main_menu_href(current_href):
        if not current_href:
            raise PreventUpdate
        parsed = urlparse(current_href)
        hostname = parsed.hostname or "127.0.0.1"
        scheme = parsed.scheme or "http"
        port = get_main_app_port()
        return f"{scheme}://{hostname}:{port}"

    return sidebar
