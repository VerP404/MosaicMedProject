"""
Конструктор отчётов WEB.ОМС — новая модель (не копия отчётов 1–5).

Три независимые оси:
  1) Строки  — по чему группировать (порядок = уровни)
  2) Показатели — какие колонки считать
  3) Фильтры  — что отбирать в выборку
+ режим значений: количество / сумма / уникальные пациенты
+ поле даты: формирование или окончание лечения
"""
from datetime import datetime, timedelta

from dash import html, dcc, Output, Input, State, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import status_groups, status_descriptions
from apps.analytical_app.pages.web_oms.status_talon.query import (
    CONSTRUCTOR_ROW_DIMS,
    CONSTRUCTOR_MEASURE_PACKS,
    DEFAULT_MEASURE_PACKS,
    build_constructor_sql,
)
from apps.analytical_app.query_executor import engine

type_page = "status-constructor"

ROW_OPTIONS = [
    {"label": meta["label"], "value": key}
    for key, meta in CONSTRUCTOR_ROW_DIMS.items()
]

SUMMARY_MEASURES = ["total", "paid", "tfoms", "in_work", "rejected", "cancelled"]
STATUS_MEASURES = [k for k in CONSTRUCTOR_MEASURE_PACKS if k.startswith("st_")]

MEASURE_OPTIONS = [
    {"label": CONSTRUCTOR_MEASURE_PACKS[k]["label"], "value": k}
    for k in SUMMARY_MEASURES + STATUS_MEASURES
]

STATUS_FILTER_OPTIONS = [
    {"label": f"{s} — {status_descriptions.get(s, '')}", "value": s}
    for s in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "12", "13", "17", "18", "19"]
]
STATUS_GROUP_OPTIONS = [{"label": g, "value": g} for g in status_groups.keys()]


def _sort_key(x):
    return (0, int(x)) if str(x).isdigit() else (1, str(x).lower())


def _options_from_sql(sql):
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        values = [
            r[0] for r in rows
            if r[0] is not None and str(r[0]).strip() not in ("", "-")
        ]
        values = sorted(set(values), key=_sort_key)
        return [{"label": v, "value": v} for v in values]
    except Exception:
        return []


def _goal_options():
    return _options_from_sql(
        "SELECT DISTINCT goal FROM data_loader_omsdata "
        "WHERE goal IS NOT NULL AND TRIM(goal) NOT IN ('', '-')"
    )


def _department_options():
    return _options_from_sql(
        "SELECT DISTINCT department FROM data_loader_omsdata "
        "WHERE department IS NOT NULL AND TRIM(department) NOT IN ('', '-')"
    )


def _specialty_options():
    return _options_from_sql(
        "SELECT DISTINCT specialty FROM data_loader_omsdata "
        "WHERE specialty IS NOT NULL AND TRIM(specialty) NOT IN ('', '-')"
    )


def _diagnosis_options():
    return _options_from_sql(
        """
        SELECT DISTINCT
            CASE
                WHEN POSITION(' ' IN main_diagnosis) > 0
                THEN SUBSTRING(main_diagnosis, 1, POSITION(' ' IN main_diagnosis) - 1)
                ELSE main_diagnosis
            END
        FROM data_loader_omsdata
        WHERE main_diagnosis IS NOT NULL AND TRIM(main_diagnosis) NOT IN ('', '-')
        """
    )


def _fill_rollup_labels(data, dim_aliases):
    if not data or not dim_aliases:
        return data
    out = []
    for row in data:
        new_row = dict(row)
        for alias in dim_aliases:
            if new_row.get(alias) is None:
                new_row[alias] = "Итого"
        out.append(new_row)
    return out


def _resolve_statuses(mode, group_name, individual):
    if mode == "individual":
        return list(individual or []) or None
    if group_name and group_name in status_groups:
        return list(status_groups[group_name])
    return None


def _section(title, children):
    return dbc.Card(
        [
            dbc.CardHeader(html.Span(title, className="fw-semibold")),
            dbc.CardBody(children, className="py-3"),
        ],
        className="mb-3 shadow-sm",
    )


web_oms_9 = html.Div(
    [
        html.H4("Конструктор отчётов", className="mb-1"),
        html.P(
            "Соберите отчёт сами: строки → показатели → фильтры. "
            "Это не замена отчётов 1–5, а отдельный инструмент.",
            className="text-muted small mb-3",
        ),
        # --- 1. Структура ---
        _section(
            "1. Структура таблицы",
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Строки (группировка, порядок важен)", className="fw-semibold small mb-1"),
                                dcc.Dropdown(
                                    id=f"rows-{type_page}",
                                    options=ROW_OPTIONS,
                                    value=["goal", "department"],
                                    multi=True,
                                    placeholder="Например: Цель, затем Подразделение…",
                                ),
                                html.Div(
                                    "Пример: Цель + Подразделение = отчёт по целям с разбивкой по корпусам.",
                                    className="text-muted small mt-1",
                                ),
                            ],
                            md=7,
                        ),
                        dbc.Col(
                            [
                                html.Label("Режим значений", className="fw-semibold small mb-1"),
                                dcc.RadioItems(
                                    id=f"value-mode-{type_page}",
                                    options=[
                                        {"label": "Количество талонов", "value": "count"},
                                        {"label": "Сумма (руб.)", "value": "sum"},
                                        {"label": "Уникальные пациенты (ЕНП)", "value": "unique"},
                                    ],
                                    value="count",
                                    className="small",
                                ),
                                dbc.Checklist(
                                    id=f"rollup-{type_page}",
                                    options=[{"label": "Строка «Итого»", "value": "rollup"}],
                                    value=["rollup"],
                                    switch=True,
                                    className="mt-2",
                                ),
                            ],
                            md=5,
                        ),
                    ],
                    className="g-3 mb-3",
                ),
                html.Label("Показатели (колонки)", className="fw-semibold small mb-1"),
                dcc.Dropdown(
                    id=f"measures-{type_page}",
                    options=MEASURE_OPTIONS,
                    value=DEFAULT_MEASURE_PACKS,
                    multi=True,
                    placeholder="Выберите, что считать…",
                ),
                html.Div(
                    [
                        dbc.Button("Только итоги", id=f"btn-measures-summary-{type_page}", size="sm", color="outline-secondary", className="me-2 mt-2"),
                        dbc.Button("Итоги + статусы", id=f"btn-measures-all-{type_page}", size="sm", color="outline-secondary", className="me-2 mt-2"),
                        dbc.Button("Только статусы", id=f"btn-measures-status-{type_page}", size="sm", color="outline-secondary", className="mt-2"),
                    ]
                ),
            ],
        ),
        # --- 2. Период ---
        _section(
            "2. Период",
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Поле даты", className="fw-semibold small mb-1"),
                                dcc.Dropdown(
                                    id=f"date-field-{type_page}",
                                    options=[
                                        {"label": "Дата формирования талона", "value": "initial_input"},
                                        {"label": "Дата окончания лечения", "value": "treatment"},
                                    ],
                                    value="initial_input",
                                    clearable=False,
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                html.Label("С", className="fw-semibold small mb-1"),
                                dcc.DatePickerSingle(
                                    id=f"date-start-{type_page}",
                                    first_day_of_week=1,
                                    date=(datetime.now().replace(day=1)).date(),
                                    display_format="DD.MM.YYYY",
                                ),
                            ],
                            width="auto",
                        ),
                        dbc.Col(
                            [
                                html.Label("По", className="fw-semibold small mb-1"),
                                dcc.DatePickerSingle(
                                    id=f"date-end-{type_page}",
                                    first_day_of_week=1,
                                    date=datetime.now().date() - timedelta(days=1),
                                    display_format="DD.MM.YYYY",
                                ),
                            ],
                            width="auto",
                        ),
                    ],
                    className="g-3 align-items-end",
                ),
            ],
        ),
        # --- 3. Фильтры ---
        _section(
            "3. Фильтры выборки (пусто = все)",
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Цели", className="fw-semibold small mb-1"),
                                dcc.Dropdown(
                                    id=f"goals-{type_page}",
                                    options=_goal_options(),
                                    multi=True,
                                    placeholder="Все цели",
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Подразделения", className="fw-semibold small mb-1"),
                                dcc.Dropdown(
                                    id=f"departments-{type_page}",
                                    options=_department_options(),
                                    multi=True,
                                    placeholder="Все подразделения",
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="g-2 mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Специальности", className="fw-semibold small mb-1"),
                                dcc.Dropdown(
                                    id=f"specialties-{type_page}",
                                    options=_specialty_options(),
                                    multi=True,
                                    placeholder="Все специальности",
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Диагнозы (код)", className="fw-semibold small mb-1"),
                                dcc.Dropdown(
                                    id=f"diagnoses-{type_page}",
                                    options=_diagnosis_options(),
                                    multi=True,
                                    placeholder="Все диагнозы",
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="g-2 mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Отбор по статусам талонов", className="fw-semibold small mb-1"),
                                dcc.RadioItems(
                                    id=f"status-mode-{type_page}",
                                    options=[
                                        {"label": "Не ограничивать", "value": "none"},
                                        {"label": "Группа", "value": "group"},
                                        {"label": "Выборочно", "value": "individual"},
                                    ],
                                    value="none",
                                    inline=True,
                                    className="small mb-2",
                                ),
                                html.Div(
                                    dcc.Dropdown(
                                        id=f"status-group-{type_page}",
                                        options=STATUS_GROUP_OPTIONS,
                                        value="Предъявленные первичные и повторные (1,2,3,4,6,8,19)",
                                        clearable=False,
                                    ),
                                    id=f"wrap-status-group-{type_page}",
                                    style={"display": "none"},
                                ),
                                html.Div(
                                    dcc.Dropdown(
                                        id=f"status-individual-{type_page}",
                                        options=STATUS_FILTER_OPTIONS,
                                        multi=True,
                                        placeholder="Выберите статусы…",
                                    ),
                                    id=f"wrap-status-individual-{type_page}",
                                    style={"display": "none"},
                                ),
                            ],
                            md=8,
                        ),
                        dbc.Col(
                            [
                                html.Label("Прочее", className="fw-semibold small mb-1"),
                                dbc.Checklist(
                                    id=f"extra-{type_page}",
                                    options=[
                                        {"label": "Исключить тариф = 0", "value": "no_zero_tariff"},
                                    ],
                                    value=["no_zero_tariff"],
                                    switch=True,
                                ),
                            ],
                            md=4,
                        ),
                    ],
                    className="g-2",
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button("Сформировать", id=f"update-button-{type_page}", color="primary", size="lg"),
                    width="auto",
                ),
                dbc.Col(html.Div(id=f"status-{type_page}", className="text-muted small mt-2")),
            ],
            className="align-items-center mb-3",
        ),
        dbc.Card(
            [
                dbc.CardHeader(html.Span(id=f"result-title-{type_page}", children="Результат", className="fw-semibold")),
                dbc.CardBody(
                    dcc.Loading(
                        dash_table.DataTable(
                            id=f"result-table-{type_page}",
                            columns=[],
                            data=[],
                            page_size=25,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            export_format="xlsx",
                            export_headers="display",
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "minWidth": "70px",
                                "maxWidth": "240px",
                                "whiteSpace": "normal",
                            },
                        ),
                        type="default",
                    )
                ),
            ],
            className="shadow-sm",
        ),
    ],
    style={"padding": "0.25rem 0 1rem"},
)


@app.callback(
    Output(f"measures-{type_page}", "value"),
    Input(f"btn-measures-summary-{type_page}", "n_clicks"),
    Input(f"btn-measures-all-{type_page}", "n_clicks"),
    Input(f"btn-measures-status-{type_page}", "n_clicks"),
    prevent_initial_call=True,
)
def quick_measures(n_sum, n_all, n_st):
    from dash import callback_context
    if not callback_context.triggered:
        raise PreventUpdate
    btn = callback_context.triggered[0]["prop_id"].split(".")[0]
    if btn == f"btn-measures-summary-{type_page}":
        return SUMMARY_MEASURES
    if btn == f"btn-measures-status-{type_page}":
        return STATUS_MEASURES
    return SUMMARY_MEASURES + STATUS_MEASURES


@app.callback(
    Output(f"wrap-status-group-{type_page}", "style"),
    Output(f"wrap-status-individual-{type_page}", "style"),
    Input(f"status-mode-{type_page}", "value"),
)
def toggle_status_filters(mode):
    hide = {"display": "none"}
    show = {"display": "block"}
    if mode == "group":
        return show, hide
    if mode == "individual":
        return hide, show
    return hide, hide


@app.callback(
    [
        Output(f"result-table-{type_page}", "columns"),
        Output(f"result-table-{type_page}", "data"),
        Output(f"result-title-{type_page}", "children"),
        Output(f"status-{type_page}", "children"),
    ],
    Input(f"update-button-{type_page}", "n_clicks"),
    State(f"rows-{type_page}", "value"),
    State(f"measures-{type_page}", "value"),
    State(f"value-mode-{type_page}", "value"),
    State(f"rollup-{type_page}", "value"),
    State(f"date-field-{type_page}", "value"),
    State(f"date-start-{type_page}", "date"),
    State(f"date-end-{type_page}", "date"),
    State(f"goals-{type_page}", "value"),
    State(f"departments-{type_page}", "value"),
    State(f"specialties-{type_page}", "value"),
    State(f"diagnoses-{type_page}", "value"),
    State(f"status-mode-{type_page}", "value"),
    State(f"status-group-{type_page}", "value"),
    State(f"status-individual-{type_page}", "value"),
    State(f"extra-{type_page}", "value"),
    prevent_initial_call=True,
)
def run_constructor(
    n_clicks,
    rows,
    measures,
    value_mode,
    rollup_value,
    date_field,
    start_date,
    end_date,
    goals,
    departments,
    specialties,
    diagnoses,
    status_mode,
    status_group,
    status_individual,
    extra,
):
    if not n_clicks:
        raise PreventUpdate
    if not start_date or not end_date:
        return [], [], "Результат", "Укажите период."
    if not rows:
        return [], [], "Результат", "Выберите хотя бы одну строку группировки."
    if not measures:
        return [], [], "Результат", "Выберите хотя бы один показатель."

    start_fmt = datetime.strptime(start_date[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
    end_fmt = datetime.strptime(end_date[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
    statuses = _resolve_statuses(status_mode, status_group, status_individual)

    sql, bind_params, dim_aliases = build_constructor_sql(
        rows=rows,
        measures=measures,
        value_mode=value_mode or "count",
        date_field=date_field or "initial_input",
        start_date=start_fmt,
        end_date=end_fmt,
        goals=goals,
        departments=departments,
        specialties=specialties,
        diagnoses=diagnoses,
        statuses=statuses,
        include_rollup=bool(rollup_value) and "rollup" in (rollup_value or []),
        exclude_zero_tariff="no_zero_tariff" in (extra or []),
    )
    columns, data = TableUpdater.query_to_df(engine, sql, bind_params)
    data = _fill_rollup_labels(data, dim_aliases)

    row_labels = [CONSTRUCTOR_ROW_DIMS[r]["label"] for r in rows if r in CONSTRUCTOR_ROW_DIMS]
    mode_label = {"count": "кол-во", "sum": "сумма", "unique": "уник. пациенты"}.get(value_mode, value_mode)
    title = f"{' → '.join(row_labels)} · {mode_label}"
    status = f"Строк: {len(data)}. {start_fmt} — {end_fmt}."
    return columns, data, title, status
