from datetime import datetime

from dash import html, dcc, Output, Input, State, callback_context, no_update
from dash.exceptions import PreventUpdate
from dash.dcc import send_bytes
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import (
    filter_status,
    status_groups,
    filter_years,
    filter_report_type,
    filter_inogorod,
    filter_sanction,
    filter_amount_null,
    update_buttons,
    get_current_reporting_month,
    date_picker,
    filter_months,
    get_available_buildings,
    get_available_departments,
    filter_building,
    filter_department,
    filter_health_group,
    filter_icd_codes,
)
from apps.analytical_app.pages.head.dispensary.adults.query import (
    sql_query_dispensary_age,
    DISPENSARY_ADULT_GOALS,
)
from apps.analytical_app.query_executor import engine

type_page = "tab3-da"

GOAL_MAP = {
    "dv4": "ДВ4",
    "dv2": "ДВ2",
    "opv": "ОПВ",
    "ud1": "УД1",
    "ud2": "УД2",
    "dr1": "ДР1",
    "dr2": "ДР2",
}
SUFFIX_MAP = {"ж": "Ж", "м": "М", "итог": "Итого"}


adults_dv3 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader(
                                dbc.Row(
                                    [
                                        dbc.Col(html.H5("Фильтры", className="mb-0"), width="auto"),
                                        dbc.Col(
                                            html.Div(
                                                id=f"last-updated-main-{type_page}",
                                                style={
                                                    "textAlign": "right",
                                                    "fontSize": "0.8rem",
                                                    "color": "#666",
                                                },
                                            ),
                                            width=True,
                                        ),
                                    ],
                                    align="center",
                                    justify="between",
                                )
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                    dbc.Col(filter_report_type(type_page), width=2),
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                    dbc.Col(
                                        html.Button(
                                            "Выгрузить в Excel",
                                            id=f"btn-export-{type_page}",
                                            n_clicks=0,
                                            className="btn btn-outline-primary",
                                        ),
                                        width="auto",
                                    ),
                                    dcc.Download(id=f"download-{type_page}"),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_months(type_page), width=6),
                                    dbc.Col(filter_health_group(type_page, default=["all"]), width=6),
                                    dbc.Col(
                                        html.Label(
                                            "Выберите дату",
                                            id=f"label-date-{type_page}",
                                            style={"font-weight": "bold", "display": "none"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        date_picker(f"input-{type_page}"),
                                        width=4,
                                        id=f"col-input-{type_page}",
                                        style={"display": "none"},
                                    ),
                                    dbc.Col(
                                        date_picker(f"treatment-{type_page}"),
                                        width=4,
                                        id=f"col-treatment-{type_page}",
                                        style={"display": "none"},
                                    ),
                                ],
                                align="center",
                                style={"marginTop": "10px"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_status(type_page), width=6),
                                    dbc.Col(filter_icd_codes(type_page), width=6),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_building(type_page), width=6),
                                    dbc.Col(filter_department(type_page), width=6),
                                ],
                                className="mt-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [
                                                dbc.Label("Тип диспансеризации:"),
                                                dbc.Checklist(
                                                    options=[
                                                        {"label": g, "value": g}
                                                        for g in DISPENSARY_ADULT_GOALS
                                                    ],
                                                    value=list(DISPENSARY_ADULT_GOALS),
                                                    id=f"checklist-input-{type_page}",
                                                    inline=True,
                                                ),
                                            ]
                                        ),
                                        width=12,
                                    ),
                                ],
                                className="mt-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            id=f"selected-period-{type_page}",
                                            className="filters-label",
                                        ),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            id=f"current-month-name-{type_page}",
                                            className="filters-label",
                                        ),
                                        width=6,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px rgba(0,0,0,0.1)",
                        "border-radius": "10px",
                    },
                ),
                width=12,
            ),
            style={"marginBottom": "1rem"},
        ),
        dcc.Loading(id=f"loading-output-{type_page}", type="default"),
        dcc.Loading(
            id=f"loading-table-{type_page}",
            type="default",
            children=html.Div(id=f"table-container-{type_page}"),
        ),
    ],
    style={"padding": "0rem"},
)


def _build_age_table(df):
    if df.empty:
        return df
    df = df.set_index("age")
    df.index.name = "Возраст"
    cols, tuples = [], []
    for prefix, goal_label in GOAL_MAP.items():
        for sk, sl in SUFFIX_MAP.items():
            name = f"{prefix}_{sk}"
            if name in df.columns:
                cols.append(name)
                tuples.append((goal_label, sl))
    if "общий_итог" in df.columns:
        cols.append("общий_итог")
        tuples.append(("Общий итог", ""))
    df = df[cols]
    df.columns = pd.MultiIndex.from_tuples(tuples, names=["Цель", "Пол/Итого"])
    total_row = df.sum(numeric_only=True)
    total_row.name = "Итого"
    return pd.concat([pd.DataFrame([total_row], columns=df.columns), df])


@app.callback(
    [
        Output(f"status-group-container-{type_page}", "style"),
        Output(f"status-individual-container-{type_page}", "style"),
    ],
    [Input(f"status-selection-mode-{type_page}", "value")],
)
def toggle_status_selection_mode(mode):
    if mode == "group":
        return {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "block"}


@app.callback(
    Output(f"dropdown-health-group-{type_page}", "value"),
    Input(f"dropdown-health-group-{type_page}", "value"),
)
def _enforce_single_special(vals):
    if not vals:
        return []
    if "all" in vals and len(vals) > 1:
        return ["all"]
    if "with" in vals and len(vals) > 1:
        return ["with"]
    return vals


@app.callback(
    Output(f"last-updated-main-{type_page}", "children"),
    Input(f"update-button-{type_page}", "n_clicks"),
    prevent_initial_call=True,
)
def _update_last_updated(n):
    sql = text("SELECT MAX(updated_at) FROM load_data_oms_data")
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
    if row and row[0]:
        return "Данные ОМС обновлены: " + row[0].strftime("%d.%m.%Y %H:%M")
    return ""


@app.callback(
    [
        Output(f"label-date-{type_page}", "style"),
        Output(f"col-input-{type_page}", "style"),
        Output(f"col-treatment-{type_page}", "style"),
    ],
    [Input(f"dropdown-report-type-{type_page}", "value")],
)
def _toggle_date_filters(report_type):
    if report_type == "initial_input":
        return {"display": "block"}, {"display": "block"}, {"display": "none"}
    if report_type == "treatment":
        return {"display": "block"}, {"display": "none"}, {"display": "block"}
    return {"display": "none"}, {"display": "none"}, {"display": "none"}


@app.callback(
    Output(f"current-month-name-{type_page}", "children"),
    Input("date-interval", "n_intervals"),
)
def _update_current_month(n):
    _, name = get_current_reporting_month()
    return name


@app.callback(
    Output(f"selected-period-{type_page}", "children"),
    [
        Input(f"range-slider-month-{type_page}", "value"),
        Input(f"dropdown-year-{type_page}", "value"),
    ],
)
def _show_period(months, year):
    return f"Год: {year}, месяцы: {months}"


@app.callback(
    [
        Output(f"dropdown-building-{type_page}", "options"),
        Output(f"dropdown-department-{type_page}", "options"),
    ],
    [Input(f"dropdown-building-{type_page}", "value")],
)
def update_filters(building_id):
    buildings = get_available_buildings()
    departments = get_available_departments(building_id) if building_id else get_available_departments()
    return buildings, departments


@app.callback(
    [
        Output(f"table-container-{type_page}", "children"),
        Output(f"download-{type_page}", "data"),
    ],
    [
        Input(f"update-button-{type_page}", "n_clicks"),
        Input(f"btn-export-{type_page}", "n_clicks"),
    ],
    [
        State(f"range-slider-month-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        State(f"dropdown-inogorodniy-{type_page}", "value"),
        State(f"dropdown-sanction-{type_page}", "value"),
        State(f"dropdown-amount-null-{type_page}", "value"),
        State(f"dropdown-building-{type_page}", "value"),
        State(f"dropdown-department-{type_page}", "value"),
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"checklist-input-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"dropdown-health-group-{type_page}", "value"),
        State(f"dropdown-icd-{type_page}", "value"),
    ],
    prevent_initial_call=True,
)
def render_table_and_export(
    n_clicks_update,
    n_clicks_export,
    selected_months,
    year,
    inog,
    sanc,
    amt_null,
    building_ids,
    department_ids,
    start_input,
    end_input,
    start_treat,
    end_treat,
    report_type,
    selected_types,
    status_mode,
    status_group,
    status_indiv,
    health_groups,
    icd_codes,
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if status_mode == "group":
        statuses = status_groups.get(status_group, [])
    else:
        statuses = status_indiv or []

    sql = sql_query_dispensary_age(
        selected_year=year or datetime.now().year,
        months_range=selected_months,
        inogorod=inog,
        sanction=sanc,
        amount_null=amt_null,
        building=building_ids,
        department=department_ids,
        input_start=start_input,
        input_end=end_input,
        treatment_start=start_treat,
        treatment_end=end_treat,
        report_type=report_type,
        cel_list=selected_types,
        status_list=statuses,
        health_groups=health_groups,
        icd_codes=icd_codes,
    )
    df = pd.read_sql_query(text(sql), engine)
    df = _build_age_table(df)

    if trigger == f"update-button-{type_page}":
        if df.empty:
            return dbc.Alert("По выбранным условиям данные не найдены.", color="info", className="mt-3"), no_update
        table = dbc.Table.from_dataframe(
            df, striped=True, bordered=True, hover=True, index=True, responsive=True
        )
        return html.Div(
            [
                html.H6(
                    "Диспансеризация взрослых по возрастам, видам и полу",
                    className="mt-2 mb-2",
                ),
                table,
            ]
        ), no_update

    if trigger == f"btn-export-{type_page}":
        if df.empty:
            return dbc.Alert("Нет данных для выгрузки.", color="warning", className="mt-3"), no_update
        export_df = df.copy()
        export_df.columns = [" ".join(col).strip() for col in export_df.columns]
        export_df.index.name = "Возраст"
        start, end = selected_months or (None, None)
        params = {
            "Год": year,
            "Период (месяцы)": f"{start}–{end}" if start and end else "",
            "Тип отчёта": report_type,
            "Виды": ", ".join(selected_types or []),
            "Корпуса": building_ids,
            "Отделения": department_ids,
            "Группы здоровья": ", ".join(health_groups) if health_groups else "Все",
        }

        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                export_df.to_excel(writer, sheet_name="Данные", index=True)
                pd.DataFrame(
                    {"Параметр": list(params.keys()), "Значение": [str(v) for v in params.values()]}
                ).to_excel(writer, sheet_name="Параметры", index=False)
            buffer.seek(0)

        filename = f"dispensary_age_{datetime.now():%Y%m%d_%H%M}.xlsx"
        return no_update, send_bytes(to_excel, filename)

    raise PreventUpdate


@app.callback(
    Output(f"dropdown-icd-{type_page}", "value"),
    [Input(f"btn-apply-icd-pattern-{type_page}", "n_clicks")],
    [
        State(f"input-icd-pattern-{type_page}", "value"),
        State(f"dropdown-icd-{type_page}", "options"),
        State(f"dropdown-icd-{type_page}", "value"),
    ],
    prevent_initial_call=True,
)
def add_icd_by_pattern(n_clicks, pattern, options, current_values):
    if not pattern:
        return no_update
    pattern = pattern.upper()
    matched = [opt["value"] for opt in options if opt["value"].startswith(pattern)]
    return list(sorted(set(current_values or []) | set(matched)))
