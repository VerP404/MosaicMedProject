from dash import Output, Input, html

from apps.analytical_app.pages.administrator.delete_emd.page import admin_delete_emd
from apps.analytical_app.pages.administrator.main import admin_main
from apps.analytical_app.pages.administrator.routes import routes_administrator
from apps.analytical_app.pages.chief.main import chief_main
from apps.analytical_app.pages.doctor.routes import routes_doctors
from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.economist.doctors.page import economist_doctors_talon_list
from apps.analytical_app.pages.economist.main import economist_main
from apps.analytical_app.pages.economist.stationary.page import economist_stationary
from apps.analytical_app.pages.economist.svpod.page import economist_sv_pod
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.head.dn_job.page import head_dn_job
from apps.analytical_app.pages.head.routes import routes_head
from apps.analytical_app.pages.iszl.main import iszl_main
from apps.analytical_app.pages.main.page import main_layout
from apps.analytical_app.pages.statistic.cardiology_report.cardiology_report import statistic_cardiology
from apps.analytical_app.pages.statistic.dispensary_visits.dispensary_visits import statistic_dd_visits
from apps.analytical_app.pages.statistic.main import statistic_main
from apps.analytical_app.pages.statistic.result_pneumonia.result_pneumonia import statistic_pneumonia
from apps.analytical_app.pages.statistic.sharapova.page import statistic_sharapova
from apps.analytical_app.pages.statistic.visits.visits import statistic_visits
from apps.analytical_app.pages.statistic.vop.vop import statistic_vop
from apps.analytical_app.pages.web_oms.main import web_oms_main
from apps.analytical_app.pages.web_oms.status_talon.tab1 import web_oms_1
from apps.analytical_app.pages.web_oms.status_talon.tab2 import web_oms_2
from apps.analytical_app.pages.web_oms.status_talon.tab3 import web_oms_3
from apps.analytical_app.pages.web_oms.status_talon.tab4 import web_oms_4
from apps.analytical_app.pages.web_oms.status_talon.tab5 import web_oms_5
from apps.analytical_app.pages.web_oms.status_talon.tab6 import web_oms_6

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





    "/statistic": statistic_main,
    "/statistic/statistic-sharapova": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Отчет Шараповой по ДН", "active": True},
        ]),
        statistic_sharapova
    ]),
    "/statistic/cardiology": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Кардиологический отчет", "active": True},
        ]),
        statistic_cardiology
    ]),
    "/statistic/pneumonia": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Пневмонии по возрастам", "active": True},
        ]),
        statistic_pneumonia
    ]),
    "/statistic/dd-visits": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Посещения в диспансеризации", "active": True},
        ]),
        statistic_dd_visits
    ]),
    "/statistic/visits": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Посещения в талонах", "active": True},
        ]),
        statistic_visits
    ]),
    "/statistic/vop": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "Отчет по ВОП", "active": True},
        ]),
        statistic_vop
    ]),





    # "/chief": chief_main,
    # "/chief/svpod": html.Div([
    #     dbc.Breadcrumb(items=[
    #         {"label": "Главный врач", "href": "/chief"},
    #         {"label": "Диспансеризация взрослых", "active": True},
    #     ]),
    #     economist_sv_pod
    # ]),
    # "/chief/doctors": html.Div([
    #     dbc.Breadcrumb(items=[
    #         {"label": "Главный врач", "href": "/chief"},
    #         {"label": "Диспансеризация детей", "active": True},
    #     ]),
    #     economist_doctors_talon_list
    # ]),
    # "/chief/disp_by_ages": html.Div([
    #     dbc.Breadcrumb(items=[
    #         {"label": "Главный врач", "href": "/chief"},
    #         {"label": "Диспансерное наблюдение", "active": True},
    #     ]),
    #     economist_dispensary_age
    # ]),
    # "/chief/dn_job": html.Div([
    #     dbc.Breadcrumb(items=[
    #         {"label": "Главный врач", "href": "/chief"},
    #         {"label": "Диспансерное наблюдение работающих", "active": True},
    #     ]),
    #     head_dn_job
    # ]),


    "/web_oms": web_oms_main,
    "/web_oms/web_oms_rep1": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 1 - По целям", "active": True},
        ]),
        web_oms_1
    ]),
    "/web_oms/web_oms_rep2": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 2 - Специальность по целям", "active": True},
        ]),
        web_oms_2
    ]),
    "/web_oms/web_oms_rep3": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 3 - Цель по корпусам", "active": True},
        ]),
        web_oms_3
    ]),
    "/web_oms/web_oms_rep4": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 4 - Корпус и специальность по целям", "active": True},
        ]),
        web_oms_4
    ]),
    "/web_oms/web_oms_rep5": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 5 - Цели и диагнозы по корпусам", "active": True},
        ]),
        web_oms_5
    ]),
    "/web_oms/web_oms_rep6": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 6 - Список пациентов и их диагнозы в текущем году", "active": True},
        ]),
        web_oms_6
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

routes.update(routes_doctors)
routes.update(routes_head)
routes.update(routes_administrator)


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
        return routes.get(pathname, page_not_found(pathname))
