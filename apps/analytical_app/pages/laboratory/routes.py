from dash import html
import dash_bootstrap_components as dbc

from apps.analytical_app.pages.laboratory.journal.page import laboratory_journal
from apps.analytical_app.pages.laboratory.main import laboratory_main

routes_laboratory = {
    "/laboratory": laboratory_main,
    "/laboratory/journal": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Лаборатория", "href": "/laboratory"},
            {"label": "Журнал для процедурных м/с", "active": True},
        ]),
        laboratory_journal
    ]),
} 