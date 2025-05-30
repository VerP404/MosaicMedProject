from dash import html
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.economist.doctors.page import economist_doctors_talon_list
from apps.analytical_app.pages.head.dispensary.adults.main import head_adults_dd_main
from apps.analytical_app.pages.head.dispensary.adults.tab1 import adults_dv1
from apps.analytical_app.pages.head.dispensary.adults.tab10 import adults_dv10
from apps.analytical_app.pages.head.dispensary.adults.tab3 import adults_dv3
from apps.analytical_app.pages.head.dispensary.adults.tab8 import adults_dv8
from apps.analytical_app.pages.head.dispensary.adults.tab9 import adults_dv9
from apps.analytical_app.pages.head.dispensary.children.main import head_children_dd_main
from apps.analytical_app.pages.head.dispensary.children.tab1 import children_dn1
from apps.analytical_app.pages.head.dispensary.children.tab2 import children_dn2
from apps.analytical_app.pages.head.dispensary.children.tab3 import children_list_not_pn
from apps.analytical_app.pages.head.dispensary.children.tab4 import children_unique
from apps.analytical_app.pages.head.dispensary.reports.page import dispensary_reports
from apps.analytical_app.pages.head.dispensary.reproductive.main import head_reproductive_main
from apps.analytical_app.pages.head.dispensary.reproductive.tab1 import reproductive_dr1
from apps.analytical_app.pages.head.dispensary.reproductive.tab2 import reproductive_dr2
from apps.analytical_app.pages.head.dn_job.page import head_dn_job
from apps.analytical_app.pages.head.doctors.page import layout_doctors_goal
from apps.analytical_app.pages.head.journal.journal import layout_journal
from apps.analytical_app.pages.head.main import head_main
from apps.analytical_app.pages.statistic.sharapova.page import statistic_sharapova

routes_head = {
    "/head": head_main,
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
    "/head/dispensary-reports": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "131 форма", "active": True},
        ]),
        dispensary_reports
    ]),
    "/head/journal": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Журнал обращений", "active": True},
        ]),
        layout_journal
    ]),
    "/head/adults": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "active": True},
        ]),
        head_adults_dd_main
    ]),
    "/head/adults/dv1": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "href": "/head/adults"},
            {"label": "Отчет по видам диспансеризации", "active": True},
        ]),
        adults_dv1
    ]),
    "/head/adults/dv3": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "href": "/head/adults"},
            {"label": "Диспансеризация взрослых по возрастам", "active": True},
        ]),
        adults_dv3
    ]),
    "/head/adults/dv8": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "href": "/head/adults"},
            {"label": "Диспансеризация с группировкой по стоимости", "active": True},
        ]),
        adults_dv8
    ]),
    "/head/adults/dv9": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "href": "/head/adults"},
            {"label": "РЭМД диспансеризации", "active": True},
        ]),
        adults_dv9
    ]),
    "/head/adults/dv10": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация взрослых", "href": "/head/adults"},
            {"label": "По возрастам и группам здоровья", "active": True},
        ]),
        adults_dv10
    ]),
    "/head/children": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация детей", "active": True},
        ]),
        head_children_dd_main
    ]),
    "/head/children/pn1": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация детей", "href": "/head/children"},
            {"label": "Отчет по видам диспансеризации детей", "active": True},
        ]),
        children_dn1
    ]),
    "/head/children/pn2": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация детей", "href": "/head/children"},
            {"label": "По возрастам диспансеризация детей", "active": True},
        ]),
        children_dn2
    ]),
    "/head/children/pn3": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация детей", "href": "/head/children"},
            {"label": "Список прикрепленных детей", "active": True},
        ]),
        children_list_not_pn
    ]),
    "/head/children/pn4": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Диспансеризация детей", "href": "/head/children"},
            {"label": "Уникальные дети в ПН", "active": True},
        ]),
        children_unique
    ]),
    "/head/reproductive": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Репродуктивное здоровье", "active": True},
        ]),
        head_reproductive_main
    ]),
    "/head/reproductive/dr1": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Репродуктивное здоровье", "href": "/head/reproductive"},
            {"label": "Отчет по видам диспансеризации", "active": True},
        ]),
        reproductive_dr1
    ]),
    "/head/reproductive/dr2": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Репродуктивное здоровье", "href": "/head/reproductive"},
            {"label": "Списки пациентов репродуктивного здоровья", "active": True},
        ]),
        reproductive_dr2
    ]),
    "/head/doctors_talon": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Талоны по врачам (помесячно)", "active": True},
        ]),
        layout_doctors_goal
    ]),
    "/head/doctors_talon_goals": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Заведующий", "href": "/head"},
            {"label": "Талоны по врачам (по целям)", "active": True},
        ]),
        economist_doctors_talon_list
    ]),
}
