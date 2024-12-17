from dash import html
import dash_bootstrap_components as dbc


from apps.analytical_app.pages.registry.main import registry_main
from apps.analytical_app.pages.registry.not_hospitalized.page import not_hospitalized_page

routes_registry = {
    "/registry": registry_main,
    "/registry/not_hospitalized": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Реестры", "href": "/registry"},
            {"label": "Не госпитализированные", "active": True},
        ]),
        not_hospitalized_page
    ]),
}