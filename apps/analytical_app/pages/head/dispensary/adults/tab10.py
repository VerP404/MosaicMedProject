# apps/analytical_app/pages/head/dispensary/adults/tab10-da.py
import io
from datetime import datetime

from dash import html, dcc, Input, Output, State, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
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
    status_groups, filter_health_group,
)

type_page = "tab10-da"

adults_dv10 = html.Div(
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
                                                    "color": "#666"
                                                },
                                            ),
                                            width=True
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
                                    dbc.Col(html.Button("Выгрузить в Excel", id=f"btn-export-{type_page}", n_clicks=0,
                                                        className="btn btn-outline-primary"), width="auto"),
                                    dcc.Download(id=f"download-{type_page}")
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_months(type_page), width=8),
                                    dbc.Col(filter_health_group(type_page), width=4),
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
    Output(f"dropdown-health-group-{type_page}", "value"),
    Input(f"dropdown-health-group-{type_page}", "value"),
)
def _enforce_single_special(vals):
    if not vals:
        return []

    if "all" in vals and len(vals) > 1:
        return ["all"]
        # Если выбрано "С группой" вместе с чем-то — только "with"
    if "with" in vals and len(vals) > 1:
        return ["with"]
    return vals


@app.callback(
    Output(f"last-updated-main-{type_page}", "children"),
    Input(f"update-button-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def _update_last_updated(n):
    # Берём максимальный updated_at из нужной таблицы
    sql = text("SELECT MAX(updated_at) FROM load_data_detailed_medical_examination")
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
    if row and row[0]:
        return "Детализация обновлена: " + row[0].strftime("%d.%m.%Y %H:%M")
    return ""


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


from dash import no_update, callback_context
from dash.dcc import send_data_frame, send_bytes
from dash.exceptions import PreventUpdate
import pandas as pd
import datetime
from sqlalchemy import text
from apps.analytical_app.query_executor import engine


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
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"dropdown-health-group-{type_page}", "value"),
    ],
    prevent_initial_call=True
)
def render_tab10_table_and_export(
        n_clicks_update, n_clicks_export,
        selected_months, year, inog, sanc, amt_null,
        start_input, end_input, start_treat, end_treat,
        report_type, status_mode, status_group, status_indiv,
        health_groups
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # --- собираем WHERE-условия ---
    conds = [f"report_year = {int(year)}", "age > 17"]
    if report_type == "month" and selected_months:
        start, end = selected_months
        conds.append(f"report_month BETWEEN {start} AND {end}")
    if report_type == "initial_input" and start_input and end_input:
        conds.append(
            f"initial_input_date BETWEEN '{start_input[:10]}' AND '{end_input[:10]}'"
        )
    if report_type == "treatment" and start_treat and end_treat:
        conds.append(
            f"treatment_end BETWEEN '{start_treat[:10]}' AND '{end_treat[:10]}'"
        )

    if inog == '1':
        conds.append("inogorodniy = FALSE")
    elif inog == '2':
        conds.append("inogorodniy = TRUE")

    if sanc == '1':
        conds.append("(sanctions = '-' OR sanctions IS NULL)")
    elif sanc == '2':
        conds.append("sanctions <> '-'")

    if amt_null == '1':
        conds.append("amount_numeric IS NOT NULL")
    elif amt_null == '2':
        conds.append("amount_numeric IS NULL")

    # статусы
    if status_mode == "group":
        sts = status_groups.get(status_group, [])
    else:
        sts = status_indiv or []
    if sts:
        q = ",".join(f"'{s}'" for s in sts)
        conds.append(f"status IN ({q})")

    # health_group
    if health_groups:
        # «all» — ничего не фильтруем (все, включая '-')
        if "all" in health_groups:
            pass
        # «with» — все, у кого есть группа (не '-')
        elif health_groups == ["with"]:
            conds.append("health_group <> '-'")
        # конкретные значения — выбираем их (возможно, включая '-')
        else:
            values = ", ".join(f"'{hg}'" for hg in health_groups)
            conds.append(f"health_group IN ({values})")

    where = " AND ".join(conds)

    # --- основной SQL (из вашего файла) ---
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

    # --- подготовка MultiIndex для отображения ---
    df = df.set_index("age")
    df.index.name = "Возраст"
    goal_map = {
        "dv4": "ДВ4", "dv2": "ДВ2", "opv": "ОПВ",
        "ud1": "УД1", "ud2": "УД2", "dr1": "ДР1", "dr2": "ДР2"
    }
    suffix_map = {"ж": "Ж", "м": "М", "итог": "Итого"}

    cols, tuples = [], []
    for p, gl in goal_map.items():
        for sk, sl in suffix_map.items():
            name = f"{p}_{sk}"
            if name in df.columns:
                cols.append(name)
                tuples.append((gl, sl))
    if "общий_итог" in df.columns:
        cols.append("общий_итог")
        tuples.append(("Общий итог", ""))

    df = df[cols]
    df.columns = pd.MultiIndex.from_tuples(tuples, names=["Цель", "Пол/Итого"])

    # --- возвращаем результат в зависимости от кнопки ---
    if trigger == f"update-button-{type_page}":
        table = dbc.Table.from_dataframe(
            df, striped=True, bordered=True, hover=True, index=True, responsive=True
        )
        return table, no_update



    elif trigger == f"btn-export-{type_page}":
        # подготавливаем табличные данные
        flat = [" ".join(col).strip() for col in df.columns]
        df.columns = flat
        df.index.name = "Возраст"
        # собираем параметры
        start, end = selected_months or (None, None)
        params = {
            "Год": year,
            "Период (месяцы)": f"{start}–{end}" if start and end else "",
            "Тип отчёта": report_type,
            "Иногородние": inog,
            "Санкции": sanc,
            "Сумма null": amt_null,
            "Статус (режим)": status_mode,
            "Статус (группа)": status_group,
            "Статус (индив)": status_indiv,
            "Группы здоровья": ", ".join(health_groups) if health_groups else "Все",
        }

        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Данные", index=True)
                pd.DataFrame({
                    "Параметр": list(params.keys()),
                    "Значение": list(params.values())
                }).to_excel(writer, sheet_name="Параметры", index=False)
            buffer.seek(0)

        filename = f"tab10_da_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx"
        return no_update, send_bytes(to_excel, filename)
    else:
        raise PreventUpdate
