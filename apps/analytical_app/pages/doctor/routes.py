from dash import Output, Input, html
import dash_bootstrap_components as dbc


from apps.analytical_app.pages.doctor.doctor.page import doctor_talon
from apps.analytical_app.pages.doctor.main import doctor_main
from apps.analytical_app.pages.head.dn_job.page import head_dn_job

routes_doctors = {
    "/doctor": doctor_main,
    "/doctor/doctor_talon": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Врач", "href": "/doctor"},
            {"label": "Талоны по типу и цели", "active": True},
        ]),
        doctor_talon
    ]),
    "/doctor/dn_job": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Врач", "href": "/doctor"},
            {"label": "Диспансерное наблюдение работающих", "active": True},
        ]),
        head_dn_job
    ]),
}