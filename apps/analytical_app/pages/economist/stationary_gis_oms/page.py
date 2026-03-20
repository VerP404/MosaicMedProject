import logging
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, exceptions, html, dash_table

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_amount_null,
    filter_building,
    filter_department,
    filter_doctor,
    filter_inogorod,
    filter_months,
    filter_profile,
    filter_sanction,
    filter_status,
    get_available_buildings,
    get_available_departments,
    get_available_doctors,
    get_available_profiles,
    get_departments_by_doctor,
    get_doctor_details,
    months_labels,
    months_sql_labels,
    parse_doctor_ids,
    status_groups,
    update_buttons,
)
from apps.analytical_app.pages.economist.stationary_gis_oms.query import sql_query_stationary_gis_oms
from apps.analytical_app.query_executor import engine

type_page = "econ-stationary-gis-oms"

logger = logging.getLogger(__name__)

STAC_GOAL_OPTIONS = [
    {"label": "В дневном стационаре", "value": "В дневном стационаре"},
    {"label": "На дому", "value": "На дому"},
    {"label": "Стационарно", "value": "Стационарно"},
]
STAC_GOALS_DEFAULT = [o["value"] for o in STAC_GOAL_OPTIONS]


def _clean_org_ids(val):
    """Убирает «Все»/нечисловые значения из мультивыбора корпус/отделение/профиль."""
    if not val:
        return None
    lst = val if isinstance(val, list) else [val]
    nums = []
    for x in lst:
        if x in (None, "all", "ALL"):
            continue
        if isinstance(x, int):
            nums.append(x)
        elif isinstance(x, str) and x.isdigit():
            nums.append(int(x))
    return nums if nums else None


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
                                [
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                ],
                                className="mb-3",
                            ),
                            dbc.Row(
                                [dbc.Col(filter_months(type_page), width=12)],
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_building(type_page), width=6),
                                    dbc.Col(filter_department(type_page), width=6),
                                ],
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_profile(type_page), width=6),
                                    dbc.Col(filter_doctor(type_page), width=6),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                id=f"selected-filters-{type_page}",
                                className="selected-filters-block",
                                style={
                                    "margin": "10px 0",
                                    "padding": "10px",
                                    "border": "1px solid #ccc",
                                    "border-radius": "5px",
                                },
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
    [
        Output(f"dropdown-building-{type_page}", "options"),
        Output(f"dropdown-department-{type_page}", "options"),
        Output(f"dropdown-profile-{type_page}", "options"),
        Output(f"dropdown-doctor-{type_page}", "options"),
    ],
    [
        Input(f"dropdown-building-{type_page}", "value"),
        Input(f"dropdown-department-{type_page}", "value"),
        Input(f"dropdown-profile-{type_page}", "value"),
        Input(f"dropdown-doctor-{type_page}", "value"),
        Input(f"dropdown-year-{type_page}", "value"),
    ],
)
def update_filters(building_id, department_id, profile_id, doctor_id, selected_year):
    if not selected_year:
        selected_year = datetime.now().year

    buildings = get_available_buildings()

    if doctor_id:
        departments_by_doctor = get_departments_by_doctor(doctor_id)
        if department_id:
            if isinstance(department_id, list):
                selected_departments = department_id
            else:
                selected_departments = [department_id]
            valid = all(
                any(item["value"] == d for item in departments_by_doctor)
                for d in selected_departments
            )
            if not valid:
                if building_id:
                    departments_by_building = get_available_departments(building_id)
                else:
                    departments_by_building = get_available_departments()
                merged = {item["value"]: item for item in departments_by_doctor}
                for item in departments_by_building:
                    merged.setdefault(item["value"], item)
                departments = list(merged.values())
            else:
                departments = departments_by_doctor
        else:
            departments = departments_by_doctor
    elif building_id:
        departments = get_available_departments(building_id)
    else:
        departments = get_available_departments()

    if building_id or department_id:
        profiles = get_available_profiles(building_id, department_id)
    else:
        profiles = get_available_profiles()

    doctors = get_available_doctors(building_id, department_id, profile_id, selected_year)

    return buildings, departments, profiles, doctors


@app.callback(
    Output(f"selected-filters-{type_page}", "children"),
    Input(f"dropdown-doctor-{type_page}", "value"),
)
def update_selected_filters(doctor_ids):
    parsed_ids = parse_doctor_ids(doctor_ids)
    if not parsed_ids:
        return html.Span("Врачи не выбраны — учитываются все, остальные фильтры по корпусу/отделению/профилю активны.", className="text-muted small")

    details_list = get_doctor_details(parsed_ids)
    items = []
    for details in details_list:
        items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong(details["doctor_name"]),
                            dbc.Badge(details["code"], color="info", pill=True, className="ms-2"),
                        ],
                        className="mb-1",
                    ),
                    html.Ul(
                        [
                            html.Li([html.Strong("Специальность: "), details["specialty"]]),
                            html.Li([html.Strong("Отделение: "), details["department"]]),
                            html.Li([html.Strong("Корпус: "), details["building"]]),
                        ],
                        style={"list-style-type": "none", "margin": 0, "padding": 0},
                    ),
                ],
                className="p-2 mb-2",
                style={"border": "1px solid #f1f3f5", "borderRadius": "0.375rem"},
            )
        )

    header = html.Span(
        [
            html.Span("Выбранные врачи"),
            dbc.Badge(str(len(details_list)), color="secondary", pill=True, className="ms-2"),
        ]
    )

    return dbc.Accordion(
        [
            dbc.AccordionItem(
                html.Div(items),
                title=header,
            )
        ],
        start_collapsed=True,
        always_open=False,
        className="mb-0",
        style={"border": "1px solid #e9ecef", "borderRadius": "0.5rem"},
    )


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
        State(f"dropdown-inogorodniy-{type_page}", "value"),
        State(f"dropdown-sanction-{type_page}", "value"),
        State(f"dropdown-amount-null-{type_page}", "value"),
        State(f"dropdown-building-{type_page}", "value"),
        State(f"dropdown-department-{type_page}", "value"),
        State(f"dropdown-profile-{type_page}", "value"),
        State(f"dropdown-doctor-{type_page}", "value"),
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
    inogorodniy,
    sanction,
    amount_null,
    building_ids,
    department_ids,
    profile_ids,
    doctor_value,
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

    doctor_ids = parse_doctor_ids(doctor_value)
    b = _clean_org_ids(building_ids)
    d = _clean_org_ids(department_ids)
    p = _clean_org_ids(profile_ids)

    sql = sql_query_stationary_gis_oms(
        months_ph,
        selected_year,
        inogorodniy=inogorodniy or "3",
        sanction=sanction or "3",
        amount_null=amount_null or "3",
        building_ids=b,
        department_ids=d,
        profile_ids=p,
        doctor_ids=doctor_ids if doctor_ids else None,
    )
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
