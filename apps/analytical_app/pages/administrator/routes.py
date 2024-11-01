from dash import html
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.administrator.delete_emd.page import admin_delete_emd
from apps.analytical_app.pages.administrator.generation_invoices.page import admin_gen_inv
from apps.analytical_app.pages.administrator.main import admin_main
from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.economist.doctors.page import economist_doctors_talon_list
from apps.analytical_app.pages.head.dispensary.adults.main import head_adults_dd_main
from apps.analytical_app.pages.head.dispensary.adults.tab1 import adults_dv1
from apps.analytical_app.pages.head.dispensary.adults.tab3 import adults_dv3
from apps.analytical_app.pages.head.dispensary.adults.tab8 import adults_dv8
from apps.analytical_app.pages.head.dispensary.children.main import head_children_dd_main
from apps.analytical_app.pages.head.dispensary.children.tab1 import children_dn1
from apps.analytical_app.pages.head.dispensary.children.tab2 import children_dn2
from apps.analytical_app.pages.head.dispensary.reports.page import dispensary_reports
from apps.analytical_app.pages.head.dispensary.reproductive.main import head_reproductive_main
from apps.analytical_app.pages.head.dispensary.reproductive.tab1 import reproductive_dr1
from apps.analytical_app.pages.head.dispensary.reproductive.tab2 import reproductive_dr2
from apps.analytical_app.pages.head.dn_job.page import head_dn_job
from apps.analytical_app.pages.head.main import head_main
from apps.analytical_app.pages.statistic.sharapova.page import statistic_sharapova

routes_administrator = {
    "/admin": admin_main,
    "/admin/admin_delete_emd": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Аннулирование ЭМД", "active": True},
        ]),
        admin_delete_emd
    ]),
    "/admin/gen_invoices": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Сборка счетов", "active": True},
        ]),
        admin_gen_inv
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
}
