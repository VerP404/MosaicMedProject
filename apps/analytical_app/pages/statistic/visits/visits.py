from datetime import datetime, timedelta

from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_dates, TableUpdater
from apps.analytical_app.components.filters import (
    filter_years, filter_inogorod, filter_sanction, filter_amount_null,
    filter_report_type, filter_months, date_picker, update_buttons,
    filter_building, filter_department, filter_profile, filter_doctor,
    get_available_buildings, get_available_departments, get_available_profiles,
    get_available_doctors, get_departments_by_doctor, parse_doctor_ids,
)
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.pages.statistic.visits.query import (
    sql_query_visits, sql_query_visits_korpus, sql_query_visits_korpus_spec,
    sql_query_visits_pos_home, sql_query_visits_by_group, sql_query_visits_by_goal,
    sql_query_visits_by_goal_status,
)
from apps.analytical_app.query_executor import engine

alert_text1 = """**Сводка по дате окончания лечения**

Учёт посещений:
- амбулатория — цели `1, 3, 5, 7, 9, 10, 13, 14, 140, 22, 30, 301, 305, 307, 64, 640, 32` (сумма поля visits)
- диспансеризация — взрослые `ДВ4, ДВ2, ОПВ, УД1, УД2`; дети `ПН1, ДС2` (1 посещение на талон)
- дневной стационар вычитается, стационары в сводку не входят
"""

alert_text_goals = """**По целям** — те же фильтры, что на странице врача (год, тип отчёта, корпус, отделение, профиль, врач).

- **Талонов** — число талонов ОМС
- **Посещений** — как в сводке: амбулаторные цели — сумма `visits`, ДД/ПН/ДС — 1 на талон, дневной стационар — 0
- **Посещений в талоне** — сумма поля `visits` как есть
- таблица статусов — как «По целям» у врача
"""

type_page = "visits"
type_page_goal = "visits-goal"

summary_tab = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader("Фильтры"),
                dbc.CardBody(
                    [
                        html.H6("По дате окончания лечения", className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Label("Дата начала:", className="me-2"),
                                            dcc.DatePickerSingle(
                                                id=f"date-picker-start-{type_page}",
                                                first_day_of_week=1,
                                                date=datetime.now().date() - timedelta(days=1),
                                                display_format="DD.MM.YYYY",
                                            ),
                                        ]
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Label("Дата окончания:", className="me-2"),
                                            dcc.DatePickerSingle(
                                                id=f"date-picker-end-{type_page}",
                                                first_day_of_week=1,
                                                date=datetime.now().date() - timedelta(days=1),
                                                display_format="DD.MM.YYYY",
                                            ),
                                        ]
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-3 align-items-center",
                        ),
                        html.Div(id=f"selected-doctor-{type_page}", className="filters-label", style={"display": "none"}),
                        dcc.Loading(id=f"loading-output-{type_page}", type="default"),
                    ]
                ),
            ],
            className="mb-3",
        ),
        dbc.Alert(dcc.Markdown(alert_text1), color="light", className="mb-3"),
        html.Div(id=f"selected-date1-{type_page}", className="filters-label mb-2"),
        card_table(f"result-table1-{type_page}", "Посещения взрослых и детей", 15),
        html.Div(id=f"selected-date2-{type_page}", className="filters-label mt-3 mb-2"),
        card_table(f"result-table2-{type_page}", "Посещения по корпусам", 15),
        html.Div(id=f"selected-date3-{type_page}", className="filters-label mt-3 mb-2"),
        card_table(f"result-table3-{type_page}", "Посещения по корпусам и специальностям", 15),
        html.Div(id=f"selected-date4-{type_page}", className="filters-label mt-3 mb-2"),
        card_table(f"result-table4-{type_page}", "Посещения на дому", 15),
    ]
)

goals_tab = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader("Фильтры ОМС"),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(update_buttons(type_page_goal), width=2),
                                dbc.Col(filter_years(type_page_goal), width=1),
                                dbc.Col(filter_report_type(type_page_goal), width=2),
                                dbc.Col(filter_inogorod(type_page_goal), width=2),
                                dbc.Col(filter_sanction(type_page_goal), width=2),
                                dbc.Col(filter_amount_null(type_page_goal), width=2),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(filter_months(type_page_goal), width=12),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Label(
                                                "Выберите дату",
                                                id=f"label-date-{type_page_goal}",
                                                style={"font-weight": "bold", "display": "none"},
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            date_picker(f"input-{type_page_goal}"),
                                            width=4,
                                            id=f"col-input-{type_page_goal}",
                                            style={"display": "none"},
                                        ),
                                        dbc.Col(
                                            date_picker(f"treatment-{type_page_goal}"),
                                            width=4,
                                            id=f"col-treatment-{type_page_goal}",
                                            style={"display": "none"},
                                        ),
                                    ],
                                    align="center",
                                    className="mb-2",
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(filter_building(type_page_goal), width=6),
                                dbc.Col(filter_department(type_page_goal), width=6),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(filter_profile(type_page_goal), width=6),
                                dbc.Col(filter_doctor(type_page_goal), width=6),
                            ]
                        ),
                        html.Div(id=f"selected-period-{type_page_goal}", className="filters-label mt-2"),
                    ]
                ),
            ],
            className="mb-3",
        ),
        dbc.Alert(dcc.Markdown(alert_text_goals), color="light", className="mb-3"),
        dcc.Loading(
            [
                card_table(f"result-table-group-{type_page_goal}", "По группам", 20),
                html.Div(className="mt-3"),
                card_table(f"result-table-goal-{type_page_goal}", "Посещения и талоны по целям", 40),
                html.Div(className="mt-3"),
                card_table(f"result-table-status-{type_page_goal}", "Талоны по целям и статусам", 40),
            ],
            type="default",
        ),
    ]
)

statistic_visits = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(summary_tab, label="Сводка по дате лечения", tab_id="summary"),
                dbc.Tab(goals_tab, label="По целям", tab_id="goals"),
            ],
            id=f"tabs-{type_page}",
            active_tab="summary",
            className="mb-3",
        )
    ]
)


@app.callback(
    Output(f"selected-date1-{type_page}", "children"),
    Output(f"selected-date2-{type_page}", "children"),
    Output(f"selected-date3-{type_page}", "children"),
    Output(f"selected-date4-{type_page}", "children"),
    Input(f"date-picker-start-{type_page}", "date"),
    Input(f"date-picker-end-{type_page}", "date"),
)
def update_selected_dates(start_date, end_date):
    sel_date = get_selected_dates(start_date, end_date)
    return sel_date, sel_date, sel_date, sel_date


@app.callback(
    [
        Output(f"result-table1-{type_page}", "columns"),
        Output(f"result-table1-{type_page}", "data"),
        Output(f"result-table2-{type_page}", "columns"),
        Output(f"result-table2-{type_page}", "data"),
        Output(f"result-table3-{type_page}", "columns"),
        Output(f"result-table3-{type_page}", "data"),
        Output(f"result-table4-{type_page}", "columns"),
        Output(f"result-table4-{type_page}", "data"),
        Output(f"loading-output-{type_page}", "children"),
    ],
    Input(f"date-picker-start-{type_page}", "date"),
    Input(f"date-picker-end-{type_page}", "date"),
)
def update_table_dd(start_date, end_date):
    if (start_date is None) or (end_date is None):
        return [], [], [], [], [], [], [], [], html.Div()
    loading_output = html.Div([dcc.Loading(type="default")])
    start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    bind_params = {
        "start_date": start_date_formatted,
        "end_date": end_date_formatted,
    }
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_visits, bind_params)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_visits_korpus, bind_params)
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_visits_korpus_spec, bind_params)
    columns4, data4 = TableUpdater.query_to_df(engine, sql_query_visits_pos_home, bind_params)
    return columns1, data1, columns2, data2, columns3, data3, columns4, data4, loading_output


@app.callback(
    [
        Output(f"range-slider-month-{type_page_goal}", "style"),
        Output(f"date-picker-range-input-{type_page_goal}", "style"),
        Output(f"date-picker-range-treatment-{type_page_goal}", "style"),
    ],
    [Input(f"dropdown-report-type-{type_page_goal}", "value")],
)
def toggle_filters_goal(report_type):
    if report_type == "month":
        return {"display": "block"}, {"display": "none"}, {"display": "none"}
    if report_type == "initial_input":
        return {"display": "none"}, {"display": "block"}, {"display": "none"}
    if report_type == "treatment":
        return {"display": "none"}, {"display": "none"}, {"display": "block"}
    return {"display": "none"}, {"display": "none"}, {"display": "none"}


@app.callback(
    [
        Output(f"col-input-{type_page_goal}", "style"),
        Output(f"col-treatment-{type_page_goal}", "style"),
    ],
    [Input(f"dropdown-report-type-{type_page_goal}", "value")],
)
def toggle_datepickers_goal(report_type):
    if report_type == "initial_input":
        return {"display": "block"}, {"display": "none"}
    if report_type == "treatment":
        return {"display": "none"}, {"display": "block"}
    return {"display": "none"}, {"display": "none"}


@app.callback(
    Output(f"label-date-{type_page_goal}", "style"),
    [
        Input(f"dropdown-report-type-{type_page_goal}", "value"),
        Input(f"date-picker-range-input-{type_page_goal}", "start_date"),
        Input(f"date-picker-range-input-{type_page_goal}", "end_date"),
        Input(f"date-picker-range-treatment-{type_page_goal}", "start_date"),
        Input(f"date-picker-range-treatment-{type_page_goal}", "end_date"),
    ],
)
def toggle_label_visibility_goal(report_type, start_date_input, end_date_input, start_date_treatment, end_date_treatment):
    if report_type in ["initial_input", "treatment"] and (
        start_date_input or end_date_input or start_date_treatment or end_date_treatment
    ):
        return {"display": "block"}
    return {"display": "none"}


@app.callback(
    [
        Output(f"dropdown-building-{type_page_goal}", "options"),
        Output(f"dropdown-department-{type_page_goal}", "options"),
        Output(f"dropdown-profile-{type_page_goal}", "options"),
        Output(f"dropdown-doctor-{type_page_goal}", "options"),
    ],
    [
        Input(f"dropdown-building-{type_page_goal}", "value"),
        Input(f"dropdown-department-{type_page_goal}", "value"),
        Input(f"dropdown-profile-{type_page_goal}", "value"),
        Input(f"dropdown-doctor-{type_page_goal}", "value"),
        Input(f"dropdown-year-{type_page_goal}", "value"),
    ],
)
def update_filters_goal(building_id, department_id, profile_id, doctor_id, selected_year):
    if not selected_year:
        selected_year = datetime.now().year

    buildings = get_available_buildings()

    if doctor_id:
        departments_by_doctor = get_departments_by_doctor(doctor_id)
        if department_id:
            selected_departments = department_id if isinstance(department_id, list) else [department_id]
            valid = all(
                any(item["value"] == d for item in departments_by_doctor)
                for d in selected_departments
            )
            if not valid:
                departments_by_building = (
                    get_available_departments(building_id) if building_id else get_available_departments()
                )
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
    Output(f"selected-period-{type_page_goal}", "children"),
    [
        Input(f"range-slider-month-{type_page_goal}", "value"),
        Input(f"dropdown-year-{type_page_goal}", "value"),
    ],
)
def update_selected_period_goal(selected_months_range, selected_year):
    period = get_selected_period(selected_months_range, selected_year, None)
    return ", ".join(str(p) for p in period) if period else ""


def _fmt_iso_date(value):
    if not value:
        return None
    return datetime.strptime(str(value).split("T")[0], "%Y-%m-%d").strftime("%d-%m-%Y")


@app.callback(
    [
        Output(f"result-table-group-{type_page_goal}", "columns"),
        Output(f"result-table-group-{type_page_goal}", "data"),
        Output(f"result-table-goal-{type_page_goal}", "columns"),
        Output(f"result-table-goal-{type_page_goal}", "data"),
        Output(f"result-table-status-{type_page_goal}", "columns"),
        Output(f"result-table-status-{type_page_goal}", "data"),
    ],
    [Input(f"update-button-{type_page_goal}", "n_clicks")],
    [
        State(f"dropdown-year-{type_page_goal}", "value"),
        State(f"range-slider-month-{type_page_goal}", "value"),
        State(f"dropdown-inogorodniy-{type_page_goal}", "value"),
        State(f"dropdown-sanction-{type_page_goal}", "value"),
        State(f"dropdown-amount-null-{type_page_goal}", "value"),
        State(f"dropdown-building-{type_page_goal}", "value"),
        State(f"dropdown-department-{type_page_goal}", "value"),
        State(f"dropdown-profile-{type_page_goal}", "value"),
        State(f"dropdown-doctor-{type_page_goal}", "value"),
        State(f"date-picker-range-input-{type_page_goal}", "start_date"),
        State(f"date-picker-range-input-{type_page_goal}", "end_date"),
        State(f"date-picker-range-treatment-{type_page_goal}", "start_date"),
        State(f"date-picker-range-treatment-{type_page_goal}", "end_date"),
        State(f"dropdown-report-type-{type_page_goal}", "value"),
    ],
)
def update_table_visits_goal(
    n_clicks,
    selected_year,
    selected_period,
    inogorodniy,
    sanction,
    amount_null,
    building_ids,
    department_ids,
    profile_ids,
    doctor_ids,
    start_date_input,
    end_date_input,
    start_date_treatment,
    end_date_treatment,
    report_type,
):
    if not n_clicks:
        raise exceptions.PreventUpdate
    if not selected_year:
        raise exceptions.PreventUpdate

    months_placeholder = "1"
    if selected_period and len(selected_period) == 2:
        months_placeholder = ",".join(str(m) for m in range(selected_period[0], selected_period[1] + 1))

    start_date_input_formatted, end_date_input_formatted = None, None
    start_date_treatment_formatted, end_date_treatment_formatted = None, None

    if report_type == "initial_input":
        months_placeholder = "1,2,3,4,5,6,7,8,9,10,11,12"
        start_date_input_formatted = _fmt_iso_date(start_date_input)
        end_date_input_formatted = _fmt_iso_date(end_date_input)
        if not start_date_input_formatted or not end_date_input_formatted:
            raise exceptions.PreventUpdate
    elif report_type == "treatment":
        months_placeholder = "1,2,3,4,5,6,7,8,9,10,11,12"
        start_date_treatment_formatted = _fmt_iso_date(start_date_treatment)
        end_date_treatment_formatted = _fmt_iso_date(end_date_treatment)
        if not start_date_treatment_formatted or not end_date_treatment_formatted:
            raise exceptions.PreventUpdate

    kwargs = dict(
        selected_year=selected_year,
        months_placeholder=months_placeholder,
        inogorod=inogorodniy,
        sanction=sanction,
        amount_null=amount_null,
        building=building_ids or None,
        department=department_ids or None,
        profile=profile_ids or None,
        doctor=parse_doctor_ids(doctor_ids) or None,
        input_start=start_date_input_formatted,
        input_end=end_date_input_formatted,
        treatment_start=start_date_treatment_formatted,
        treatment_end=end_date_treatment_formatted,
    )

    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_visits_by_group(**kwargs))
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_visits_by_goal(**kwargs))
    columns3, data3 = TableUpdater.query_to_df(engine, sql_query_visits_by_goal_status(**kwargs))
    return columns1, data1, columns2, data2, columns3, data3
