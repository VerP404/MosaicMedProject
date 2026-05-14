# Навбар dash_dn: бренд, период матрицы (до/после 01.04.2026 + копия правок), пароль админа.
import os

import dash_bootstrap_components as dbc
from dash import dcc, html

from apps.dash_dn.catalog_periods import default_active_catalog, main_nav_catalog_options


def get_organization_name():
    return os.environ.get("DASH_DN_ORG", "Локальный справочник ДН")


def create_navbar():
    organization_name = get_organization_name()
    _nav_opts = main_nav_catalog_options()
    _nav_val = default_active_catalog()

    logo_block = html.A(
        dbc.Row(
            [
                dbc.Col(html.I(className="bi bi-heart-pulse-fill text-white fs-3")),
                dbc.Col(
                    html.Div(
                        [
                            dbc.NavbarBrand(
                                "МозаикаМед",
                                className="text-white p-0 d-block lh-sm",
                            ),
                            html.Small(
                                "Подбор услуг ДН",
                                className="text-white-50 d-block",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        className="ms-2",
                    )
                ),
            ],
            align="center",
            className="g-0",
        ),
        href="/",
        style={"textDecoration": "none"},
    )

    org_block = html.Div(
        dbc.NavbarBrand(
            organization_name,
            className="text-white text-truncate mb-0 w-100",
            style={"maxWidth": "min(42vw, 480px)", "fontSize": "0.95rem"},
        ),
        className="text-center px-2",
    )

    toolbar = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "Период матрицы",
                        className="text-white small fw-semibold text-nowrap me-sm-2",
                    ),
                    dcc.Dropdown(
                        id="dash-dn-pick-catalog",
                        options=_nav_opts,
                        value=_nav_val,
                        clearable=False,
                        searchable=False,
                        className="dash-dn-catalog-dd",
                        style={
                            "minWidth": "min(220px, 88vw)",
                            "maxWidth": "360px",
                            "fontSize": "0.85rem",
                            "backgroundColor": "#fff",
                            "color": "#212529",
                            "borderRadius": "0.375rem",
                        },
                    ),
                ],
                className="d-flex flex-column flex-sm-row align-items-start align-items-sm-center gap-1 gap-sm-2",
            ),
            html.Div(
                className="vr d-none d-lg-block bg-white opacity-25 align-self-stretch mx-lg-1",
                style={"minHeight": "28px", "width": "1px"},
            ),
            html.Div(
                [
                    dbc.Input(
                        id="dash-dn-inp-global-pwd",
                        type="password",
                        placeholder="Пароль",
                        autoComplete="off",
                        size="sm",
                        className="text-dark",
                        style={"width": "min(100px, 26vw)", "minWidth": "72px"},
                    ),
                    dbc.Button(
                        html.I(className="bi bi-unlock-fill"),
                        id="dash-dn-btn-global-unlock",
                        color="warning",
                        size="sm",
                        className="text-dark",
                        title="Разрешить правку общего справочника",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-lock-fill"),
                        id="dash-dn-btn-global-lock",
                        outline=True,
                        color="light",
                        size="sm",
                        title="Обычный режим",
                    ),
                ],
                className="d-flex align-items-center gap-1 flex-wrap",
                title="Пароль администратора — для правки общего справочника (вкладка «Справочники»)",
            ),
            html.Div(
                id="dash-dn-edit-mode-badge",
                className="d-flex align-items-center justify-content-end justify-content-lg-start",
            ),
            html.Div(
                id="dash-dn-global-unlock-msg",
                className="small text-end text-warning",
                style={"maxWidth": "200px", "lineHeight": "1.2"},
            ),
        ],
        className=(
            "d-flex flex-column flex-xl-row align-items-stretch align-items-xl-center "
            "gap-2 gap-xl-3 py-1 py-xl-0"
        ),
    )

    date_block = html.Div(
        id="current-date-output",
        style={
            "color": "white",
            "whiteSpace": "nowrap",
            "fontSize": "0.85rem",
        },
        className="ms-lg-2 ps-lg-3 border-start border-white border-opacity-25",
    )

    navbar = dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(logo_block, width="auto", className="pe-0"),
                        dbc.Col(
                            org_block,
                            className="d-none d-md-flex justify-content-center px-1 min-w-0",
                            md=4,
                            lg=3,
                        ),
                        dbc.Col(
                            toolbar,
                            xs=12,
                            lg=True,
                            className="mt-2 mt-lg-0 d-flex justify-content-lg-end",
                        ),
                        dbc.Col(
                            date_block,
                            width="auto",
                            className="d-flex align-items-center justify-content-end mt-2 mt-lg-0",
                        ),
                    ],
                    className="align-items-lg-center g-2 w-100 flex-wrap",
                ),
            ],
            fluid=True,
            className="px-2 px-sm-3",
        ),
        color="primary",
        dark=True,
        fixed="top",
        className="shadow-sm py-2 border-bottom border-white border-opacity-10",
        style={"zIndex": 1030},
    )

    return html.Div([navbar], className="dash-dn-navbar-wrap")
