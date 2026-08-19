# Талоны по датам: фильтр по дате окончания лечения / дате формирования, таблица Дата | Итого | цели
import re
from datetime import date, datetime

from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
from dash import dash_table
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, date_picker, update_buttons
from apps.analytical_app.pages.web_oms.status_talon.query import (
    sql_query_talons_by_dates,
    GROUP_COL_NAMES,
)
from apps.analytical_app.query_executor import engine

type_page = "web_oms_talons_dates"


def _sort_key(x):
    return (0, int(x)) if str(x).isdigit() else (1, str(x).lower())


def _load_goals():
    """Все доступные цели из БД (как в economist/doctors)."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT DISTINCT goal FROM data_loader_omsdata "
                "WHERE goal IS NOT NULL AND TRIM(goal) <> '' AND goal <> '-'"
            )
        ).fetchall()
    return sorted([r[0] for r in rows], key=_sort_key)


def _goal_options():
    try:
        return [{"label": g, "value": g} for g in _load_goals()]
    except Exception:
        return []


def _col_id(c):
    return c["id"] if isinstance(c, dict) else c


def parse_specific_dates(text, year):
    """
    Разбор ввода «день.месяц»: 05.08 06.09 10.11 → 5 августа, 6 сентября, 10 ноября.
    Также принимает полную дату ДД.ММ.ГГГГ.
    """
    if not text or not str(text).strip():
        return [], []

    tokens = [t for t in re.split(r"[\s,;]+", str(text).strip()) if t]
    parsed = []
    errors = []
    year = int(year)
    for tok in tokens:
        parts = [p for p in re.split(r"[.\-/]", tok) if p]
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            errors.append(tok)
            continue
        try:
            if len(nums) == 3:
                a, b, c = nums
                if c >= 100:
                    d, m, y = a, b, c
                elif a >= 100:
                    y, m, d = a, b, c
                else:
                    errors.append(tok)
                    continue
            elif len(nums) == 2:
                d, m = nums
                y = year
            else:
                errors.append(tok)
                continue
            parsed.append(date(y, m, d))
        except ValueError:
            errors.append(tok)

    return sorted(set(parsed)), errors


web_oms_8 = html.Div(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.CardHeader("Фильтры"),
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
                            dbc.Col(filter_years(type_page), width=1),
                            dbc.Col(
                                [
                                    dbc.Label("Период по:", className="me-2"),
                                    dcc.Dropdown(
                                        id=f"dropdown-report-type-{type_page}",
                                        options=[
                                            {"label": "По дате формирования", "value": "initial_input"},
                                            {"label": "По дате окончания лечения", "value": "treatment"},
                                        ],
                                        value="initial_input",
                                        clearable=False,
                                        style={"width": "100%"},
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Режим дат:", className="me-2"),
                                    dcc.Dropdown(
                                        id=f"dropdown-date-mode-{type_page}",
                                        options=[
                                            {"label": "Период", "value": "period"},
                                            {"label": "Конкретные даты", "value": "days"},
                                        ],
                                        value="period",
                                        clearable=False,
                                        style={"width": "100%"},
                                    ),
                                ],
                                width=2,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        date_picker(f"input-{type_page}"),
                                        id=f"col-input-{type_page}",
                                        style={"width": "100%"},
                                    ),
                                    html.Div(
                                        date_picker(f"treatment-{type_page}"),
                                        id=f"col-treatment-{type_page}",
                                        style={"display": "none", "width": "100%"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Label("Даты (дд.мм):", className="me-2"),
                                            dcc.Input(
                                                id=f"input-specific-dates-{type_page}",
                                                type="text",
                                                placeholder="05.08 06.09 10.11",
                                                debounce=True,
                                                style={"width": "100%"},
                                            ),
                                            html.Small(
                                                "День.месяц выбранного года. Пример: 05.08 06.09 10.11 "
                                                "→ 05-08-2026, 06-09-2026, 10-11-2026",
                                                className="text-muted",
                                            ),
                                        ],
                                        id=f"col-days-{type_page}",
                                        style={"display": "none", "width": "100%"},
                                    ),
                                ],
                                width=5,
                            ),
                        ],
                        align="center",
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Группировка:", className="me-2"),
                                    dcc.Dropdown(
                                        id=f"dropdown-group-mode-{type_page}",
                                        options=[
                                            {"label": "По датам", "value": "date"},
                                            {"label": "По врачам", "value": "doctors"},
                                            {"label": "По корпусам", "value": "buildings"},
                                            {"label": "По отделениям", "value": "departments"},
                                            {"label": "По специальностям", "value": "specialty"},
                                        ],
                                        value="date",
                                        clearable=False,
                                        style={"width": "100%"},
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                html.Div(
                                    dbc.Switch(
                                        id=f"switch-split-date-{type_page}",
                                        label="Разбивка по датам",
                                        value=False,
                                        style={"marginTop": "28px"},
                                    ),
                                    id=f"col-split-date-{type_page}",
                                    style={"display": "none"},
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Скрытие нулей:", className="me-2"),
                                    dbc.Checklist(
                                        id=f"checklist-hide-zeros-{type_page}",
                                        options=[
                                            {"label": "Строки с Итого = 0", "value": "rows"},
                                            {"label": "Цели с Итого = 0", "value": "cols"},
                                        ],
                                        value=["rows"],
                                        inline=True,
                                        switch=True,
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        align="center",
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Цели:", className="me-2"),
                                    dcc.Dropdown(
                                        id=f"dropdown-goals-{type_page}",
                                        options=_goal_options(),
                                        value=[],
                                        multi=True,
                                        clearable=True,
                                        searchable=True,
                                        placeholder="Все цели",
                                        style={"width": "100%"},
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        align="center",
                    ),
                ]
            ),
            className="mb-3 shadow-sm",
            style={"borderRadius": "8px"},
        ),
        dcc.Loading(
            id=f"loading-table-{type_page}",
            type="default",
            children=html.Div(id=f"result-table-container-{type_page}"),
        ),
    ],
    style={"padding": "0rem"},
)


@app.callback(
    Output(f"col-input-{type_page}", "style"),
    Output(f"col-treatment-{type_page}", "style"),
    Output(f"col-days-{type_page}", "style"),
    Output(f"col-split-date-{type_page}", "style"),
    Input(f"dropdown-report-type-{type_page}", "value"),
    Input(f"dropdown-date-mode-{type_page}", "value"),
    Input(f"dropdown-group-mode-{type_page}", "value"),
)
def toggle_period_inputs(report_type, date_mode, group_mode):
    hidden = {"display": "none", "width": "100%"}
    shown = {"width": "100%"}
    split_style = {"display": "none"} if (group_mode or "date") == "date" else {}
    if date_mode == "days":
        return hidden, hidden, shown, split_style
    if report_type == "initial_input":
        return shown, hidden, hidden, split_style
    return hidden, shown, hidden, split_style


@app.callback(
    Output(f"result-table-container-{type_page}", "children"),
    Input(f"update-button-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"dropdown-report-type-{type_page}", "value"),
    State(f"dropdown-date-mode-{type_page}", "value"),
    State(f"input-specific-dates-{type_page}", "value"),
    State(f"dropdown-goals-{type_page}", "value"),
    State(f"dropdown-group-mode-{type_page}", "value"),
    State(f"switch-split-date-{type_page}", "value"),
    State(f"checklist-hide-zeros-{type_page}", "value"),
    State(f"date-picker-range-input-{type_page}", "start_date"),
    State(f"date-picker-range-input-{type_page}", "end_date"),
    State(f"date-picker-range-treatment-{type_page}", "start_date"),
    State(f"date-picker-range-treatment-{type_page}", "end_date"),
)
def update_table_talons_by_dates(
    n_clicks,
    year,
    report_type,
    date_mode,
    specific_dates_text,
    selected_goals,
    group_mode,
    split_by_date,
    hide_zeros,
    start_in,
    end_in,
    start_tr,
    end_tr,
):
    if not n_clicks:
        raise exceptions.PreventUpdate

    if not year:
        year = datetime.now().year

    hide_zeros = hide_zeros or []
    hide_zero_rows = "rows" in hide_zeros
    hide_zero_cols = "cols" in hide_zeros
    date_mode = date_mode or "period"
    group_mode = group_mode or "date"
    split_by_date = bool(split_by_date) and group_mode != "date"

    months_placeholder = ", ".join(str(m) for m in range(1, 13))
    si = ei = st = et = None
    specific_dates = None

    if date_mode == "days":
        specific_dates, bad_tokens = parse_specific_dates(specific_dates_text, year)
        if bad_tokens:
            return dbc.Alert(
                "Не разобраны даты: "
                + ", ".join(bad_tokens)
                + ". Формат: дд.мм (05.08 = 5 августа) или ДД.ММ.ГГГГ.",
                color="warning",
            )
        if not specific_dates:
            return dbc.Alert(
                "Введите даты, например: 05.08 06.09 10.11",
                color="warning",
            )
    elif report_type == "initial_input" and start_in and end_in:
        si = datetime.fromisoformat(start_in.split("T")[0]).strftime("%d-%m-%Y")
        ei = datetime.fromisoformat(end_in.split("T")[0]).strftime("%d-%m-%Y")
    elif report_type == "treatment" and start_tr and end_tr:
        st = datetime.fromisoformat(start_tr.split("T")[0]).strftime("%d-%m-%Y")
        et = datetime.fromisoformat(end_tr.split("T")[0]).strftime("%d-%m-%Y")
    else:
        return dbc.Alert(
            "Выберите период (даты начала и окончания) для выбранного типа отчёта.",
            color="warning",
        )

    all_goals = _load_goals()
    if not all_goals:
        return dbc.Alert(
            "В базе не найдено ни одной цели (goal).",
            color="info",
        )

    if selected_goals:
        selected_set = set(selected_goals)
        goals = [g for g in all_goals if g in selected_set]
        if not goals:
            return dbc.Alert(
                "Выбранные цели не найдены в базе.",
                color="warning",
            )
    else:
        goals = all_goals

    sql = sql_query_talons_by_dates(
        selected_year=year,
        months_placeholder=months_placeholder,
        inogorod=None,
        sanction=None,
        amount_null=None,
        report_type=report_type,
        goals=goals,
        input_start=si,
        input_end=ei,
        treatment_start=st,
        treatment_end=et,
        status_list=None,
        specific_dates=specific_dates,
        hide_zero_rows=hide_zero_rows,
        group_mode=group_mode,
        split_by_date=split_by_date,
    )
    cols, data = TableUpdater.query_to_df(engine, sql)

    if not data:
        return dbc.Alert(
            "По выбранным условиям данные не найдены.",
            color="info",
        )

    rows_count = len(data)

    total_row = {}
    avg_row = {}
    first_group = True
    for c in cols:
        cid = _col_id(c)
        if cid in GROUP_COL_NAMES:
            total_row[cid] = "Итого" if first_group else ""
            avg_row[cid] = "Среднее" if first_group else ""
            first_group = False
            continue
        total_val = sum(
            (row.get(cid) or 0) if isinstance(row.get(cid), (int, float)) else 0
            for row in data
        )
        total_row[cid] = total_val
        avg_row[cid] = round(total_val / rows_count) if rows_count else 0

    if hide_zero_cols:
        keep_cols = []
        for c in cols:
            cid = _col_id(c)
            if cid in GROUP_COL_NAMES or cid == "Итого":
                keep_cols.append(c)
                continue
            if (total_row.get(cid) or 0) != 0:
                keep_cols.append(c)
        keep_ids = {_col_id(c) for c in keep_cols}
        cols = keep_cols

        def _trim(row):
            return {k: v for k, v in row.items() if k in keep_ids}

        data = [_trim(r) for r in data]
        total_row = _trim(total_row)
        avg_row = _trim(avg_row)

    data_with_total = [total_row, avg_row] + data

    return html.Div(
        [
            dash_table.DataTable(
                id=f"table-{type_page}",
                columns=[
                    {"name": c["name"] if isinstance(c, dict) else c, "id": c["id"] if isinstance(c, dict) else c}
                    for c in cols
                ],
                data=data_with_total,
                page_size=25,
                sort_action="native",
                filter_action="native",
                export_format="xlsx",
                style_table={"overflowX": "auto"},
                style_data_conditional=[
                    {
                        "if": {"row_index": 0},
                        "fontWeight": "bold",
                        "backgroundColor": "rgba(0, 0, 0, 0.05)",
                    },
                    {
                        "if": {"row_index": 1},
                        "fontWeight": "bold",
                        "backgroundColor": "rgba(0, 0, 0, 0.03)",
                    },
                ],
            )
        ]
    )
