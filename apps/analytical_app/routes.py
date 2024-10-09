from dash import Output, Input, html

from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.economist.doctors.page import economist_doctors_talon_list
from apps.analytical_app.pages.economist.main import economist_main
from apps.analytical_app.pages.economist.stationary.page import economist_stationary
from apps.analytical_app.pages.economist.svpod.page import economist_sv_pod
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.head.dn_job.page import head_dn_job
from apps.analytical_app.pages.head.main import head_main
from apps.analytical_app.pages.main.page import main_layout

# Все маршруты для страниц
routes = {
    "/": main_layout,
    "/economist": economist_main,
    "/economist/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Сверхподушевое финансирование", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/economist/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "По врачам", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/economist/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Диспансеризация по возрастам", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/economist/stationary": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Стационары", "active": True},
        ]),
        economist_stationary
    ]),

    "/head": head_main,
    "/head/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/head/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/head/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансерное наблюдение", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/head/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),
    "/about": html.H1('О нас')
}


# Callback для отображения страницы в зависимости от URL
def register_routes(app):
    @app.callback(
        Output('page-content', 'children'),
        [Input('url', 'pathname')]
    )
    def display_page(pathname):
        return routes.get(pathname, html.Div([
            html.H1("Страница не найдена", style={"textAlign": "center"}),
            html.P(f"Путь {pathname} не существует.", style={"textAlign": "center"})
        ]))
