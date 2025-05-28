from dash import html
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.administrator.delete_emd.page import admin_delete_emd
from apps.analytical_app.pages.administrator.generation_invoices.page import admin_gen_inv
from apps.analytical_app.pages.administrator.main import admin_main
from apps.analytical_app.pages.administrator.update_data.page import admin_update_data
from apps.analytical_app.pages.administrator.sql_editor import sql_editor_layout
from apps.analytical_app.pages.economist.disp_by_ages.page import economist_dispensary_age
from apps.analytical_app.pages.head.dn_job.page import head_dn_job

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
    "/admin/admin_update_data": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Администратор", "href": "/admin"},
            {"label": "Обновление данных", "active": True},
        ]),
        admin_update_data
    ]),
    "/admin/sql_editor": sql_editor_layout,

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
