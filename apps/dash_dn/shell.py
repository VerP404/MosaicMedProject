from dash import dcc, html
import dash_bootstrap_components as dbc

from apps.dash_dn.app import dash_dn_app
from apps.dash_dn.components.navbar import create_navbar
from apps.dash_dn.dn_services_page import layout_body as dn_pick_layout
from apps.dash_dn.reference_pages import layout_body as ref_layout
from apps.dash_dn.analysis_page import layout_body as analysis_layout


def build_layout():
    return html.Div(
        [
            dcc.Store(id="dash-dn-active-catalog", data="global"),
            dcc.Store(id="dash-dn-global-unlocked", data=False),
            create_navbar(),
            html.Main(
                dbc.Container(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    label="Подбор услуг",
                                    tab_id="tab-pick",
                                    tab_class_name="fw-semibold",
                                    children=html.Div(
                                        dn_pick_layout(),
                                        className="pt-3",
                                    ),
                                ),
                                dbc.Tab(
                                    label="Справочники",
                                    tab_id="tab-ref",
                                    tab_class_name="fw-semibold",
                                    children=html.Div(
                                        ref_layout(),
                                        className="pt-3",
                                    ),
                                ),
                                dbc.Tab(
                                    label="Анализ",
                                    tab_id="tab-analysis",
                                    tab_class_name="fw-semibold",
                                    children=html.Div(
                                        analysis_layout(),
                                        className="pt-3",
                                    ),
                                ),
                            ],
                            id="dash-dn-tabs",
                            active_tab="tab-pick",
                            className="nav-tabs-card mt-2",
                        ),
                    ],
                    fluid=True,
                    className="py-4 px-3 px-lg-4",
                ),
                style={
                    "paddingTop": "5.75rem",
                    "minHeight": "calc(100vh - 4rem)",
                    "background": "linear-gradient(165deg, #e2e8f0 0%, #f1f5f9 38%, #f8fafc 100%)",
                    "paddingBottom": "2.5rem",
                },
            ),
        ],
        className="dash-dn-app-root",
        style={"minHeight": "100vh"},
    )


def init_layout():
    dash_dn_app.layout = build_layout()
