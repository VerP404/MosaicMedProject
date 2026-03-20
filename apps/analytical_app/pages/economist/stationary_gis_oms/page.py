import logging
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, exceptions, html, dash_table

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_months,
    filter_status,
    months_labels,
    months_sql_labels,
    status_groups,
    update_buttons,
)
from apps.analytical_app.pages.economist.stationary_gis_oms.query import sql_query_stationary_gis_oms
from apps.analytical_app.query_executor import engine

type_page = "econ-stationary-gis-oms"

logger = logging.getLogger(__name__)

# Те же цели, что на странице «Стационары» (economist/stationary)
STAC_GOAL_OPTIONS = [
    {"label": "В дневном стационаре", "value": "В дневном стационаре"},
    {"label": "На дому", "value": "На дому"},
    {"label": "Стационарно", "value": "Стационарно"},
]
STAC_GOALS_DEFAULT = [o["value"] for o in STAC_GOAL_OPTIONS]


def economist_stationary_gis_oms_def():
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Фильтры"),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Loading(
                                            id=f"loading-button-{type_page}",
                                            type="circle",
                                            children=html.Div(update_buttons(type_page)),
                                        ),
                                        width=1,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Год:", className="fw-bold mb-1"),
                                            dcc.Dropdown(
                                                id=f"dropdown-year-{type_page}",
                                                options=[
                                                    {"label": str(y), "value": y}
                                                    for y in range(2023, datetime.now().year + 1)
                                                ],
                                                value=datetime.now().year,
                                                clearable=False,
                                            ),
                                        ],
                                        width=1,
                                    ),
                                    dbc.Col(
                                        filter_status(
                                            type_page, default_status_group="Оплаченные (3)"
                                        ),
                                        width=10,
                                    ),
                                ],
                                align="end",
                                className="mb-3",
                            ),
                            dbc.Row(
                                [dbc.Col(filter_months(type_page), width=12)],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    dbc.Label("Цели (стационар):", className="fw-bold"),
                                    dbc.Checklist(
                                        id=f"checklist-goals-{type_page}",
                                        options=STAC_GOAL_OPTIONS,
                                        value=list(STAC_GOALS_DEFAULT),
                                        inline=True,
                                        className="mt-1",
                                    ),
                                ],
                                className="mb-2",
                            ),
                        ]
                    ),
                ],
                className="mb-3 shadow-sm",
                style={"borderRadius": "8px"},
            ),
            dcc.Loading(
                id=f"loading-table-{type_page}",
                type="default",
                children=dash_table.DataTable(
                    id=f"result-table-{type_page}",
                    columns=[],
                    data=[],
                    export_format="xlsx",
                    export_headers="display",
                    page_size=25,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    style_table={"overflowX": "auto"},
                    style_cell={"minWidth": "72px", "maxWidth": "220px", "whiteSpace": "normal"},
                ),
            ),
        ],
        style={"padding": "0rem"},
    )


@app.callback(
    Output(f"status-group-container-{type_page}", "style"),
    Output(f"status-individual-container-{type_page}", "style"),
    Input(f"status-selection-mode-{type_page}", "value"),
)
def toggle_status(mode):
    if mode == "group":
        return {"display": "block", "margin-bottom": "1rem"}, {"display": "none", "margin-bottom": "1rem"}
    return {"display": "none", "margin-bottom": "1rem"}, {"display": "block", "margin-bottom": "1rem"}


@app.callback(
    [Output(f"result-table-{type_page}", "columns"), Output(f"result-table-{type_page}", "data")],
    [Input(f"update-button-{type_page}", "n_clicks")],
    [
        State(f"dropdown-year-{type_page}", "value"),
        State(f"range-slider-month-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"checklist-goals-{type_page}", "value"),
    ],
)
def update_table(
    n_clicks,
    selected_year,
    selected_months,
    status_mode,
    selected_status_group,
    selected_individual_statuses,
    selected_goals,
):
    if not n_clicks:
        raise exceptions.PreventUpdate
    if not selected_year or not selected_months:
        return [], []

    goals = selected_goals or []
    if not goals:
        return [], []

    start_month, end_month = map(int, selected_months)
    month_names = []
    for m in range(start_month, end_month + 1):
        if m in months_sql_labels:
            month_names.append(f"{months_sql_labels[m]} {selected_year}")
        if m in months_labels:
            month_names.append(f"{months_labels[m]} {selected_year}")
    month_names = list(dict.fromkeys(month_names))
    if not month_names:
        month_names = [f"{lab} {selected_year}" for lab in months_sql_labels.values()]

    months_ph = ", ".join(f"'{mn}'" for mn in month_names)

    if status_mode == "group":
        statuses = status_groups.get(selected_status_group, ["3"])
    else:
        statuses = selected_individual_statuses or []

    if not statuses:
        return [], []

    sql = sql_query_stationary_gis_oms(months_ph, selected_year)
    bind_params = {
        "status_list": tuple(str(s) for s in statuses),
        "goals_list": tuple(goals),
    }
    try:
        columns, data = TableUpdater.query_to_df(engine, sql, bind_params)
        return columns, data
    except Exception as e:
        logger.exception("stationary_gis_oms query failed: %s", e)
        return [], []
