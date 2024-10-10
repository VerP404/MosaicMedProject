from dash import Output, Input, html

from apps.analytical_app.pages.administrator.delete_emd.page import admin_delete_emd
from apps.analytical_app.pages.administrator.main import admin_main
from apps.analytical_app.pages.chief.main import chief_main
from apps.analytical_app.pages.doctor.doctor.page import doctor_talon
from apps.analytical_app.pages.doctor.main import doctor_main
from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.economist.doctors.page import economist_doctors_talon_list
from apps.analytical_app.pages.economist.main import economist_main
from apps.analytical_app.pages.economist.stationary.page import economist_stationary
from apps.analytical_app.pages.economist.svpod.page import economist_sv_pod
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.head.dn_job.page import head_dn_job
from apps.analytical_app.pages.head.main import head_main
from apps.analytical_app.pages.iszl.main import iszl_main
from apps.analytical_app.pages.main.page import main_layout
from apps.analytical_app.pages.statistic.main import statistic_main
from apps.analytical_app.pages.statistic.sharapova.page import statistic_sharapova

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
    "/head/statistic-sharapova": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Отчет Шараповой по ДН", "active": True},
        ]),
        statistic_sharapova
    ]),

    "/statistic": statistic_main,
    "/statistic/statistic-sharapova": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Отчет Шараповой по ДН", "active": True},
        ]),
        statistic_sharapova
    ]),
    "/statistic/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/statistic/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Диспансерное наблюдение", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/statistic/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),

    "/doctor": doctor_main,
    "/doctor/doctor_talon": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Врач", "href": "/doctor"},
            {"label": "Талоны по врачам", "active": True},
        ]),
        doctor_talon
    ]),
    "/doctor/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Врач", "href": "/doctor"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/doctor/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Врач", "href": "/doctor"},
            {"label": "Диспансерное наблюдение", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/doctor/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Врач", "href": "/doctor"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),

    "/admin": admin_main,
    "/admin/admin_delete_emd": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Аннулирование ЭМД", "active": True},
        ]),
        admin_delete_emd
    ]),
    "/admin/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/admin/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Диспансерное наблюдение", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/admin/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),

    "/chief": chief_main,
    "/chief/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/chief"},
            {"label": "Диспансеризация взрослых", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/chief/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/chief"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/chief/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/chief"},
            {"label": "Диспансерное наблюдение", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/chief/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/chief"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),

    "/iszl": iszl_main,
    "/iszl/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/iszl"},
            {"label": "Диспансеризация взрослых", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/iszl/doctors": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/iszl"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
    "/iszl/disp_by_ages": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/iszl"},
            {"label": "Диспансерное наблюдение", "active": True},
        ]),
        economist_dispensary_age
    ]),
    "/iszl/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/iszl"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),
}


def page_not_found(pathname):
    return html.Div([
        html.H1("404: Страница не найдена", style={"textAlign": "center", "color": "red"}),
        html.P(f"Путь '{pathname}' не существует.", style={"textAlign": "center"}),
        html.A("Вернуться на главную", href="/", style={"textAlign": "center"})
    ])


# Callback для отображения страницы в зависимости от URL
def register_routes(app):
    @app.callback(
        Output('page-content', 'children'),
        [Input('url', 'pathname')]
    )
    def display_page(pathname):
        # Если путь существует, вернуть соответствующую страницу, иначе вернуть страницу 404
        return routes.get(pathname, page_not_found(pathname))
