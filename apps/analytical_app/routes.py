from dash import Output, Input, html
from apps.analytical_app.pages.economist.main import economist_main
from apps.analytical_app.pages.economist.svpod.repotr import economist_sv_pod
from apps.analytical_app.pages.tab1 import tab1_doctor_talon_list
import dash_bootstrap_components as dbc

# Все маршруты для страниц
routes = {
    "/": html.Div([html.H1("Добро пожаловать в МозаикаМед"), html.P("Это информационно-справочная система.")]),
    "/economist": economist_main,
    "/economist/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Сверхподушевое финансирование", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/query": tab1_doctor_talon_list,
    "/about": html.H1('О нас')
}


# Callback для отображения страницы в зависимости от URL
def register_routes(app):
    @app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
    def display_page(pathname):
        return routes.get(pathname, html.Div([
            html.H1("Страница не найдена", style={"textAlign": "center"}),
            html.P(f"Путь {pathname} не существует.", style={"textAlign": "center"})
        ]))
