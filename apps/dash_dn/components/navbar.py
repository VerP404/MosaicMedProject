# Навбар dash_dn: бренд, организация, источник данных, пароль режима эталона, дата/время.
import os

import dash_bootstrap_components as dbc
from dash import dcc, html


def get_organization_name():
    return os.environ.get("DASH_DN_ORG", "Локальный справочник ДН")


def create_navbar():
    organization_name = get_organization_name()

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

    # Источник данных + пароль эталона + индикация режима (колбэки в dn_services_page)
    toolbar = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "Данные",
                        className="text-white-50 small fw-semibold text-uppercase",
                        style={"letterSpacing": "0.04em"},
                    ),
                    dcc.RadioItems(
                        id="dash-dn-pick-catalog",
                        options=[
                            {"label": " общий эталон", "value": "global"},
                            {"label": " локальный слой", "value": "user"},
                        ],
                        value="global",
                        className="d-flex flex-wrap gap-2 gap-sm-3 align-items-center mb-0",
                        inputClassName="form-check-input border border-2 border-light shadow-none",
                        labelStyle={
                            "fontSize": "0.78rem",
                            "color": "rgba(255,255,255,0.92)",
                            "cursor": "pointer",
                            "marginBottom": 0,
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
                        placeholder="Пароль эталона",
                        autoComplete="off",
                        size="sm",
                        className="text-dark",
                        style={"width": "min(148px, 38vw)", "minWidth": "96px"},
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-unlock-fill me-1"), "Включить"],
                        id="dash-dn-btn-global-unlock",
                        color="warning",
                        size="sm",
                        className="text-dark fw-semibold",
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-lock-fill me-1"), "Выйти"],
                        id="dash-dn-btn-global-lock",
                        outline=True,
                        color="light",
                        size="sm",
                    ),
                ],
                className="d-flex align-items-center gap-1 flex-wrap",
            ),
            html.Div(
                id="dash-dn-edit-mode-badge",
                className="d-flex align-items-center justify-content-end justify-content-lg-start",
            ),
            html.Div(
                id="dash-dn-global-unlock-msg",
                className="small text-end text-warning",
                style={"maxWidth": "240px", "lineHeight": "1.2"},
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
