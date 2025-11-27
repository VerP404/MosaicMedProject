from dash import html
import dash_bootstrap_components as dbc


from apps.analytical_app.pages.registry.main import registry_main
from apps.analytical_app.pages.registry.not_hospitalized.page import not_hospitalized_page
from apps.analytical_app.pages.registry.appointment_analysis.page import appointment_analysis_page
from apps.analytical_app.pages.registry.health_schools.page import health_schools_page
from apps.analytical_app.pages.registry.analysis_orders.page import analysis_orders_page

routes_registry = {
    "/registry": registry_main,
    "/registry/not_hospitalized": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Реестры", "href": "/registry"},
            {"label": "Не госпитализированные", "active": True},
        ]),
        not_hospitalized_page
    ]),
    "/registry/appointment_analysis": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Реестры", "href": "/registry"},
            {"label": "Анализ записанных на прием", "active": True},
        ]),
        appointment_analysis_page
    ]),
    "/registry/health_schools": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Реестры", "href": "/registry"},
            {"label": "Анализ школ здоровья", "active": True},
        ]),
        health_schools_page
    ]),
    "/registry/analysis_orders": html.Div([
        dbc.Breadcrumb(items=[
            {"label": "Реестры", "href": "/registry"},
            {"label": "Журнал заказов анализов", "active": True},
        ]),
        analysis_orders_page
    ]),
}