# Талоны по датам: фильтр по дате окончания лечения / дате формирования, таблица Дата | Итого | цели
from datetime import datetime

from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
from dash import dash_table
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, date_picker, update_buttons
from apps.analytical_app.pages.web_oms.status_talon.query import sql_query_talons_by_dates
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
                                html.Div(
                                    date_picker(f"input-{type_page}"),
                                    id=f"col-input-{type_page}",
                                    style={"width": "100%"},
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                html.Div(
                                    date_picker(f"treatment-{type_page}"),
                                    id=f"col-treatment-{type_page}",
                                    style={"display": "none", "width": "100%"},
                                ),
                                width=4,
                            ),
                        ],
                        align="center",
                        className="mb-3",
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
    Input(f"dropdown-report-type-{type_page}", "value"),
)
def toggle_period_inputs(report_type):
    if report_type == "initial_input":
        return {"width": "100%"}, {"display": "none", "width": "100%"}
    else:
        return {"display": "none", "width": "100%"}, {"width": "100%"}


@app.callback(
    Output(f"result-table-container-{type_page}", "children"),
    Input(f"update-button-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"dropdown-report-type-{type_page}", "value"),
    State(f"date-picker-range-input-{type_page}", "start_date"),
    State(f"date-picker-range-input-{type_page}", "end_date"),
    State(f"date-picker-range-treatment-{type_page}", "start_date"),
    State(f"date-picker-range-treatment-{type_page}", "end_date"),
)
def update_table_talons_by_dates(
    n_clicks, year, report_type, start_in, end_in, start_tr, end_tr
):
    if not n_clicks:
        raise exceptions.PreventUpdate

    if not year:
        year = datetime.now().year

    months_placeholder = ", ".join(str(m) for m in range(1, 13))
    si = ei = st = et = None
    if report_type == "initial_input" and start_in and end_in:
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

    goals = _load_goals()
    if not goals:
        return dbc.Alert(
            "В базе не найдено ни одной цели (goal).",
            color="info",
        )

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
    )
    cols, data = TableUpdater.query_to_df(engine, sql)

    if not data:
        return dbc.Alert(
            "По выбранным условиям данные не найдены.",
            color="info",
        )

    # Количество дат = количество строк с датами (без служебных строк)
    dates_count = len(data)

    # Первая строка — Итого по выбранному периоду
    total_row = {"Дата": "Итого"}
    for c in cols:
        cid = c["id"] if isinstance(c, dict) else c
        if cid == "Дата":
            continue
        total_row[cid] = sum(
            (row.get(cid) or 0) if isinstance(row.get(cid), (int, float)) else 0
            for row in data
        )

    # Вторая строка — Среднее по выгрузившимся датам
    avg_row = {"Дата": "Среднее"}
    for c in cols:
        cid = c["id"] if isinstance(c, dict) else c
        if cid == "Дата":
            continue
        total_val = total_row.get(cid, 0) if isinstance(total_row.get(cid), (int, float)) else 0
        avg_row[cid] = round(total_val / dates_count) if dates_count else 0

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
