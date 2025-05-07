# apps/analytical_app/pages/head/dispensary/adults/tab10-da.py

from datetime import datetime

import pandas as pd
from dash import html, dcc, Input, Output, State, exceptions
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    update_buttons,
    filter_years,
    filter_report_type,
    filter_inogorod,
    filter_sanction,
    filter_amount_null,
    filter_months,
    date_picker,
    get_current_reporting_month,
    filter_status,
    status_groups,
)
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine

type_page = "tab10-da"

adults_dv10 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                    dbc.Col(filter_report_type(type_page), width=2),
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_months(type_page), width=12),
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
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(id=f"selected-period-{type_page}", className="filters-label"),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        html.Div(id=f"current-month-name-{type_page}", className="filters-label"),
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
        html.Div(id=f"table-container-{type_page}"),
    ],
    style={"padding": "0rem"},
)


@app.callback(
    [Output(f"label-date-{type_page}", "style"),
     Output(f"col-input-{type_page}", "style"),
     Output(f"col-treatment-{type_page}", "style")],
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
    [Input(f"range-slider-month-{type_page}", "value"),
     Input(f"dropdown-year-{type_page}", "value")],
)
def _show_period(months, year):
    return f"Год: {year}, месяцы: {months}"



@app.callback(
    Output(f"table-container-{type_page}", "children"),
    Input(f"update-button-{type_page}", "n_clicks"),
    [
        State(f"range-slider-month-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        State(f"dropdown-inogorodniy-{type_page}", "value"),
        State(f"dropdown-sanction-{type_page}", "value"),
        State(f"dropdown-amount-null-{type_page}", "value"),
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
    ],
)
def render_tab10_table(
    n_clicks,
    months, year, inog, sanc, amt_null,
    start_input, end_input, start_treat, end_treat, report_type,
    status_mode, status_group, status_indiv
):
    if not n_clicks:
        raise PreventUpdate

    # --- Собираем WHERE-условия ---
    conds = [f"report_year = {int(year)}", "age > 17"]
    if report_type == "month" and months:
        conds.append(f"report_month IN ({','.join(map(str,months))})")
    if report_type == "initial_input" and start_input and end_input:
        conds.append(f"initial_input_date BETWEEN '{start_input[:10]}' AND '{end_input[:10]}'")
    if report_type == "treatment" and start_treat and end_treat:
        conds.append(f"treatment_end BETWEEN '{start_treat[:10]}' AND '{end_treat[:10]}'")
    if inog=="yes":   conds.append("inogorodniy = TRUE")
    if inog=="no":    conds.append("inogorodniy = FALSE")
    if sanc=="has":   conds.append("sanctions <> '-'")
    if sanc=="none":  conds.append("(sanctions = '-' OR sanctions IS NULL)")
    if amt_null=="null":     conds.append("amount_numeric IS NULL")
    if amt_null=="not_null": conds.append("amount_numeric IS NOT NULL")

    # статусы
    if status_mode=="group":
        sts = status_groups.get(status_group, [])
    else:
        sts = status_indiv or []
    if sts:
        quoted = ",".join(f"'{s}'" for s in sts)
        conds.append(f"status IN ({quoted})")

    where = " AND ".join(conds)

    # --- Основной SQL ---
    sql = f"""
    SELECT
      age,
      COUNT(*) FILTER (WHERE goal='ДВ4' AND gender='Ж') AS dv4_ж,
      COUNT(*) FILTER (WHERE goal='ДВ4' AND gender='М') AS dv4_м,
      COUNT(*) FILTER (WHERE goal='ДВ4')                AS dv4_итог,
      COUNT(*) FILTER (WHERE goal='ДВ2' AND gender='Ж') AS dv2_ж,
      COUNT(*) FILTER (WHERE goal='ДВ2' AND gender='М') AS dv2_м,
      COUNT(*) FILTER (WHERE goal='ДВ2')                AS dv2_итог,
      COUNT(*) FILTER (WHERE goal='ОПВ' AND gender='Ж') AS opv_ж,
      COUNT(*) FILTER (WHERE goal='ОПВ' AND gender='М') AS opv_м,
      COUNT(*) FILTER (WHERE goal='ОПВ')                AS opv_итог,
      COUNT(*) FILTER (WHERE goal='УД1' AND gender='Ж') AS ud1_ж,
      COUNT(*) FILTER (WHERE goal='УД1' AND gender='М') AS ud1_м,
      COUNT(*) FILTER (WHERE goal='УД1')                AS ud1_итог,
      COUNT(*) FILTER (WHERE goal='УД2' AND gender='Ж') AS ud2_ж,
      COUNT(*) FILTER (WHERE goal='УД2' AND gender='М') AS ud2_м,
      COUNT(*) FILTER (WHERE goal='УД2')                AS ud2_итог,
      COUNT(*) FILTER (WHERE goal='ДР1' AND gender='Ж') AS dr1_ж,
      COUNT(*) FILTER (WHERE goal='ДР1' AND gender='М') AS dr1_м,
      COUNT(*) FILTER (WHERE goal='ДР1')                AS dr1_итог,
      COUNT(*) FILTER (WHERE goal='ДР2' AND gender='Ж') AS dr2_ж,
      COUNT(*) FILTER (WHERE goal='ДР2' AND gender='М') AS dr2_м,
      COUNT(*) FILTER (WHERE goal='ДР2')                AS dr2_итог,
      (
        COUNT(*) FILTER (WHERE goal='ДВ4')
      + COUNT(*) FILTER (WHERE goal='ДВ2')
      + COUNT(*) FILTER (WHERE goal='ОПВ')
      + COUNT(*) FILTER (WHERE goal='УД1')
      + COUNT(*) FILTER (WHERE goal='УД2')
      + COUNT(*) FILTER (WHERE goal='ДР1')
      + COUNT(*) FILTER (WHERE goal='ДР2')
      ) AS общий_итог
    FROM load_data_oms_data
    WHERE {where}
    GROUP BY age
    ORDER BY age;
    """

    df = pd.read_sql_query(text(sql), engine)

    # --- Подготовка для dbc.Table.from_dataframe ---
    df = df.set_index("age")
    df.index.name = "Возраст"

    goal_map = {
        "dv4":"ДВ4","dv2":"ДВ2","opv":"ОПВ",
        "ud1":"УД1","ud2":"УД2","dr1":"ДР1","dr2":"ДР2"
    }
    suffix_map = {"ж":"Ж","м":"М","итог":"Итого"}

    # порядок и заголовки
    tuples = []
    cols = []
    for p, gl in goal_map.items():
        for sk, sl in suffix_map.items():
            c = f"{p}_{sk}"
            if c in df.columns:
                tuples.append((gl, sl))
                cols.append(c)
    if "общий_итог" in df:
        tuples.append(("Общий итог",""))
        cols.append("общий_итог")

    df = df[cols]
    df.columns = pd.MultiIndex.from_tuples(tuples, names=["Цель","Пол/Итого"])

    # --- Финальный компонент ---
    table = dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        index=True,
        responsive=True
    )

    return table

