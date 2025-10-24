from dash import Output, Input, html

from apps.analytical_app.pages.administrator.delete_emd.page import admin_delete_emd
from apps.analytical_app.pages.administrator.main import admin_main
from apps.analytical_app.pages.administrator.routes import routes_administrator
from apps.analytical_app.pages.chief.main import chief_main
from apps.analytical_app.pages.doctor.routes import routes_doctors
from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.economist.doctor_stac.tab1 import economist_doctor_stac
from apps.analytical_app.pages.economist.doctors.page import economist_doctors_talon_list_def
from apps.analytical_app.pages.economist.indicators.page import econ_indicators
from apps.analytical_app.pages.economist.main import economist_main
from apps.analytical_app.pages.economist.stationary.page import economist_stationary
from apps.analytical_app.pages.economist.svpod.page import economist_sv_pod
from apps.analytical_app.pages.economist.dispensary.page import economist_dispensary_analysis
from apps.analytical_app.pages.economist.financial_indicators.page import layout
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.head.dn_job.page import head_dn_job
from apps.analytical_app.pages.head.doctors.page import layout_doctors_goal
from apps.analytical_app.pages.head.routes import routes_head
from apps.analytical_app.pages.iszl.main import iszl_main
from apps.analytical_app.pages.laboratory.routes import routes_laboratory
from apps.analytical_app.pages.main.page import main_layout
from apps.analytical_app.pages.registry.routes import routes_registry
from apps.analytical_app.pages.statistic.cardiology_report.cardiology_report import statistic_cardiology
from apps.analytical_app.pages.statistic.dispensary_visits.dispensary_visits import statistic_dd_visits
from apps.analytical_app.pages.statistic.eln.eln import eln_layout
from apps.analytical_app.pages.statistic.main import statistic_main
from apps.analytical_app.pages.statistic.remd500.remd500_report import layout_remd500
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
from apps.analytical_app.pages.web_oms.status_talon.tab7 import adults_dv10 as web_oms_7

# Все маршруты для страниц
routes = {
    "/": main_layout,
    "/economist": economist_main,
    "/economist/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Показатели: выполнение по месяцам", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/economist/doctors": lambda: html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "По врачам", "active": True},
        ]),
        economist_doctors_talon_list_def()
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
    "/economist/indicators": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Индикаторы", "active": True},
        ]),
        econ_indicators
    ]),
    "/economist/doctor-stac": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Стационары по врачам", "active": True},
        ]),
        economist_doctor_stac
    ]),
    "/economist/doctors_talon": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "По врачам", "active": True},
        ]),
        layout_doctors_goal
    ]),
    "/economist/dispensary": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Диспансеризация", "active": True},
        ]),
        economist_dispensary_analysis()
    ]),
    "/economist/financial_indicators": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Экономист", "href": "/economist"},
            {"label": "Финансовые показатели", "active": True},
        ]),
        layout()
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
    "/statistic/eln": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "ЭЛН", "active": True},
        ]),
        eln_layout
    ]),
    "/statistic/remd500": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Статистик", "href": "/statistic"},
            {"label": "РЭМД500", "active": True},
        ]),
        layout_remd500
    ]),

    # Удаление ЭМД доступно в разделе Заведующий
    "/head/delete-emd": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Удаление ЭМД", "active": True},
        ]),
        admin_delete_emd
    ]),

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
    "/web_oms/web_oms_rep7": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "WEB.ОМС", "href": "/web_oms"},
            {"label": "Отчет 7 - Уникальные талоны по диагнозам", "active": True},
        ]),
        web_oms_7
    ]),

    "/iszl": iszl_main,
    "/iszl/svpod": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/iszl"},
            {"label": "Диспансеризация взрослых", "active": True},
        ]),
        economist_sv_pod
    ]),
    "/iszl/doctors": lambda: html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Главный врач", "href": "/iszl"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        economist_doctors_talon_list_def()
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
routes.update(routes_registry)
routes.update(routes_laboratory)


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
        view = routes.get(pathname)
        if view is None:
            return page_not_found(pathname)
        # Если маршрут — функция, вызываем её для динамической генерации layout
        return view() if callable(view) else view
