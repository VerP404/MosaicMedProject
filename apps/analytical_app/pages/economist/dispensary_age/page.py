# -*- coding: utf-8 -*-
"""
Страница «Анализ вторых этапов диспансеризации»: данные из load_data_detailed_medical_examination,
цели ДВ4/ДВ2, ДР1/ДР2, УД1/УД2, номенклатура B*.
"""
import base64
from datetime import datetime

from dash import html, dcc, Input, Output, State, exceptions
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import (
    filter_years,
    filter_months,
    update_buttons,
    filter_status,
    filter_report_type,
    date_picker,
    status_groups,
)
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.dispensary_age.query import (
    get_dr_analysis_data,
    build_summary_dr1_pivot,
    build_summary_dr2_pivot,
    build_summary_combined_pivot,
    GOAL_TYPE_PAIRS,
)
from apps.analytical_app.pages.economist.dispensary_age.excel_export import build_dr_excel

type_page = "econ-dispensary-age"

# Вкладка: Стоимость по пациентам
tab_patients = html.Div(
    [
        html.Div(id=f"loading-status-patients-{type_page}", style={"text-align": "center", "margin": "10px 0"}),
        dcc.Loading(
            id=f"loading-patients-{type_page}",
            type="default",
            children=card_table(
                f"table-patients-{type_page}",
                "Стоимость по пациентам",
                page_size=25,
            ),
        ),
    ],
    style={"padding": "0rem"},
)

# Вкладка: Сводная по обоим этапам (rowspan и стили)
tab_summary = html.Div(
    [
        html.Div(id=f"loading-status-summary-{type_page}", style={"text-align": "center", "margin": "10px 0"}),
        dcc.Loading(
            id=f"loading-summary-{type_page}",
            type="default",
            children=dbc.Card(
                [
                    dbc.CardHeader("Сводная по полу и группам здоровья (оба этапа)"),
                    dbc.CardBody(html.Div(id=f"pivot-summary-{type_page}"), style={"overflowX": "auto"}),
                ],
                className="shadow-sm",
                style={"borderRadius": "10px"},
            ),
        ),
    ],
    style={"padding": "0rem"},
)

# Контейнеры для сводных ДР1/ДР2 — заполняются HTML-таблицей с rowspan и стилями
tab_dr1 = html.Div(
    [
        html.Div(id=f"loading-status-dr1-{type_page}", style={"text-align": "center", "margin": "10px 0"}),
        dcc.Loading(
            id=f"loading-dr1-{type_page}",
            type="default",
            children=dbc.Card(
                [
                    dbc.CardHeader("Сводная (1-й этап) — количество по группе здоровья и стоимости"),
                    dbc.CardBody(html.Div(id=f"pivot-dr1-{type_page}"), style={"overflowX": "auto"}),
                ],
                className="shadow-sm",
                style={"borderRadius": "10px"},
            ),
        ),
    ],
    style={"padding": "0rem"},
)

tab_dr2 = html.Div(
    [
        html.Div(id=f"loading-status-dr2-{type_page}", style={"text-align": "center", "margin": "10px 0"}),
        dcc.Loading(
            id=f"loading-dr2-{type_page}",
            type="default",
            children=dbc.Card(
                [
                    dbc.CardHeader("Сводная (2-й этап) — количество по группе здоровья и стоимости"),
                    dbc.CardBody(html.Div(id=f"pivot-dr2-{type_page}"), style={"overflowX": "auto"}),
                ],
                className="shadow-sm",
                style={"borderRadius": "10px"},
            ),
        ),
    ],
    style={"padding": "0rem"},
)


def _build_pivot_sheet(rows):
    """
    Строит сводную таблицу как HTML: объединённые ячейки по группе здоровья,
    подытоги по группе и общий итог с визуальным выделением.
    """
    if not rows:
        return html.Div("Нет данных", className="text-muted p-3")

    # Разбиваем на блоки: (group_name, [detail rows + subtotal row])
    blocks = []
    current_group = None
    current_block = []
    grand_total = None

    for r in rows:
        rt = r.get("_row_type")
        if rt == "detail":
            if r["Группа здоровья"] != current_group:
                if current_group is not None:
                    blocks.append((current_group, current_block))
                current_group = r["Группа здоровья"]
                current_block = []
            current_block.append(r)
        elif rt == "subtotal":
            current_block.append(r)
            blocks.append((current_group, current_block))
            current_group = None
            current_block = []
        elif rt == "grand_total":
            grand_total = r
            if current_group is not None:
                blocks.append((current_group, current_block))
            break

    # Стили
    style_group_cell = {
        "verticalAlign": "top",
        "fontWeight": "600",
        "backgroundColor": "rgba(13, 110, 253, 0.06)",
        "borderRight": "2px solid rgba(13, 110, 253, 0.3)",
        "minWidth": "200px",
    }
    style_subtotal = {"fontWeight": "bold", "backgroundColor": "rgba(0, 0, 0, 0.06)"}
    style_grand = {"fontWeight": "bold", "backgroundColor": "rgba(13, 110, 253, 0.12)"}
    style_header = {"backgroundColor": "#0d6efd", "color": "white", "fontWeight": "600"}

    thead = html.Thead(
        html.Tr(
            [
                html.Th("Группа здоровья", style={**style_header, "width": "30%"}),
                html.Th("Стоимость", style={**style_header, "width": "12%"}),
                html.Th("Ж", style={**style_header, "width": "12%"}),
                html.Th("М", style={**style_header, "width": "12%"}),
                html.Th("Общий итог", style={**style_header, "width": "14%"}),
            ]
        )
    )

    tbody_rows = []
    for group_name, block_rows in blocks:
        rowspan = len(block_rows)
        for j, row in enumerate(block_rows):
            is_subtotal = row.get("_row_type") == "subtotal"
            cell_style = style_subtotal if is_subtotal else {}
            cells = []
            if j == 0:
                cells.append(
                    html.Td(
                        group_name,
                        rowSpan=rowspan,
                        style=style_group_cell,
                    )
                )
            cells.extend([
                html.Td(row["Стоимость"], style=cell_style),
                html.Td(row["Ж"], style=cell_style),
                html.Td(row["М"], style=cell_style),
                html.Td(row["Общий итог"], style=cell_style),
            ])
            tr = html.Tr(cells, style=cell_style)
            tbody_rows.append(tr)

    if grand_total:
        tbody_rows.append(
            html.Tr(
                [
                    html.Td("Общий итог", colSpan=2, style={**style_grand, "fontWeight": "bold"}),
                    html.Td(grand_total["Ж"], style=style_grand),
                    html.Td(grand_total["М"], style=style_grand),
                    html.Td(grand_total["Общий итог"], style=style_grand),
                ],
                style=style_grand,
            )
        )

    table = dbc.Table(
        [thead, html.Tbody(tbody_rows)],
        bordered=True,
        hover=True,
        size="sm",
        style={"marginBottom": 0},
        className="table-responsive",
    )
    return table


def _fmt_cost(x):
    """Формат числа для стоимости (запятая как десятичный разделитель)."""
    if isinstance(x, (int, float)):
        return f"{x:,.2f}".replace(",", " ").replace(".", ",")
    return str(x)


def _build_pivot_sheet_combined(rows, type1: str, type2: str):
    """
    Сводная по двум этапам: объединённые ячейки по Группе здоровья type1,
    в строках — Группа здоровья type2, Ж, М, Общий итог, стоимости.
    """
    if not rows:
        return html.Div("Нет данных", className="text-muted p-3")

    k_grp1 = f"Группа здоровья {type1}"
    k_grp2 = f"Группа здоровья {type2}"
    k_cost1 = f"Стоимость {type1}"
    k_cost2 = f"Стоимость {type2}"

    blocks = []
    current_group = None
    current_block = []
    grand_total = None

    for r in rows:
        rt = r.get("_row_type")
        if rt == "detail":
            if r.get(k_grp1) != current_group:
                if current_group is not None:
                    blocks.append((current_group, current_block))
                current_group = r.get(k_grp1)
                current_block = []
            current_block.append(r)
        elif rt == "subtotal":
            current_block.append(r)
            blocks.append((current_group, current_block))
            current_group = None
            current_block = []
        elif rt == "grand_total":
            grand_total = r
            if current_group is not None:
                blocks.append((current_group, current_block))
            break

    style_group_cell = {
        "verticalAlign": "top",
        "fontWeight": "600",
        "backgroundColor": "rgba(13, 110, 253, 0.06)",
        "borderRight": "2px solid rgba(13, 110, 253, 0.3)",
        "minWidth": "180px",
    }
    style_subtotal = {"fontWeight": "bold", "backgroundColor": "rgba(0, 0, 0, 0.06)"}
    style_grand = {"fontWeight": "bold", "backgroundColor": "rgba(13, 110, 253, 0.12)"}
    style_header = {"backgroundColor": "#0d6efd", "color": "white", "fontWeight": "600"}

    thead = html.Thead(
        html.Tr(
            [
                html.Th(k_grp1, style={**style_header, "width": "22%"}),
                html.Th(k_grp2, style={**style_header, "width": "22%"}),
                html.Th("Ж", style={**style_header, "width": "8%"}),
                html.Th("М", style={**style_header, "width": "8%"}),
                html.Th("Общий итог", style={**style_header, "width": "10%"}),
                html.Th(k_cost1, style={**style_header, "width": "10%"}),
                html.Th(k_cost2, style={**style_header, "width": "10%"}),
                html.Th("Общая стоимость", style={**style_header, "width": "10%"}),
            ]
        )
    )

    tbody_rows = []
    for group_name, block_rows in blocks:
        rowspan = len(block_rows)
        for j, row in enumerate(block_rows):
            is_subtotal = row.get("_row_type") == "subtotal"
            cell_style = style_subtotal if is_subtotal else {}
            cells = []
            if j == 0:
                cells.append(html.Td(group_name, rowSpan=rowspan, style=style_group_cell))
            cells.extend([
                html.Td(row.get(k_grp2, ""), style=cell_style),
                html.Td(row.get("Ж", ""), style=cell_style),
                html.Td(row.get("М", ""), style=cell_style),
                html.Td(row.get("Общий итог", ""), style=cell_style),
                html.Td(_fmt_cost(row.get(k_cost1, 0)), style=cell_style),
                html.Td(_fmt_cost(row.get(k_cost2, 0)), style=cell_style),
                html.Td(_fmt_cost(row.get("Общая стоимость", 0)), style=cell_style),
            ])
            tbody_rows.append(html.Tr(cells, style=cell_style))

    if grand_total:
        tbody_rows.append(
            html.Tr(
                [
                    html.Td("Общий итог", colSpan=2, style={**style_grand, "fontWeight": "bold"}),
                    html.Td(grand_total.get("Ж", ""), style=style_grand),
                    html.Td(grand_total.get("М", ""), style=style_grand),
                    html.Td(grand_total.get("Общий итог", ""), style=style_grand),
                    html.Td(_fmt_cost(grand_total.get(k_cost1, 0)), style=style_grand),
                    html.Td(_fmt_cost(grand_total.get(k_cost2, 0)), style=style_grand),
                    html.Td(_fmt_cost(grand_total.get("Общая стоимость", 0)), style=style_grand),
                ],
                style=style_grand,
            )
        )

    return dbc.Table(
        [thead, html.Tbody(tbody_rows)],
        bordered=True,
        hover=True,
        size="sm",
        style={"marginBottom": 0},
        className="table-responsive",
    )


layout_dispensary_age = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=1),
                                    dbc.Col(
                                        dbc.Button(
                                            "Скачать Excel",
                                            id=f"download-excel-{type_page}",
                                            color="success",
                                            className="mt-3",
                                        ),
                                        width=1,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Цель:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                            dcc.Dropdown(
                                                id=f"dropdown-goal-type-{type_page}",
                                                options=[
                                                    {"label": "ДВ4 и ДВ2", "value": "ДВ4"},
                                                    {"label": "ДР1 и ДР2", "value": "ДР1"},
                                                    {"label": "УД1 и УД2", "value": "УД1"},
                                                ],
                                                value="ДР1",
                                                clearable=False,
                                                style={"width": "100%"},
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(filter_years(type_page), width=1),
                                    dbc.Col(
                                        [
                                            html.Label("Тип периода:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                            filter_report_type(type_page),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Отчетный месяц:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                            filter_months(type_page),
                                        ],
                                        width=5,
                                        id=f"col-months-{type_page}",
                                    ),
                                ],
                                align="center",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Label("Выберите дату", id=f"label-date-{type_page}", style={"font-weight": "bold", "display": "none"}),
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
                                style={"display": "flex", "align-items": "center", "margin-bottom": "10px"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Статус талона:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                                            filter_status(type_page, default_status_group="Оплаченные (3)"),
                                        ],
                                        width=12,
                                    ),
                                ],
                                align="center",
                            ),
                            dbc.Row(
                                dbc.Col(
                                    dbc.Alert(
                                        "Анализ вторых этапов диспансеризации. Данные из реестра детализации (номенклатура B*).",
                                        color="info",
                                    ),
                                    width=12,
                                )
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                        "border-radius": "10px",
                    },
                ),
                width=12,
            ),
            style={"margin": "0 auto", "padding": "0rem"},
        ),
        dbc.Tabs(
            [
                dbc.Tab(label="Стоимость по пациентам", tab_id=f"tab-patients-{type_page}", children=tab_patients),
                dbc.Tab(label="Сводная (оба этапа)", tab_id=f"tab-summary-{type_page}", children=tab_summary),
                dbc.Tab(label="Сводная (1-й этап)", tab_id=f"tab-dr1-{type_page}", children=tab_dr1),
                dbc.Tab(label="Сводная (2-й этап)", tab_id=f"tab-dr2-{type_page}", children=tab_dr2),
            ],
            active_tab=f"tab-patients-{type_page}",
            id=f"tabs-{type_page}",
        ),
        dcc.Download(id=f"download-xlsx-{type_page}"),
        dbc.Toast(
            id=f"toast-excel-{type_page}",
            header="Экспорт в Excel",
            icon="info",
            duration=4000,
            is_open=False,
            dismissable=True,
            style={"position": "fixed", "top": 60, "right": 50, "width": 350},
        ),
    ],
    style={"padding": "0rem"},
)


def _patient_columns(type1: str, type2: str):
    """Колонки таблицы «Стоимость по пациентам» в зависимости от выбранной цели (type1, type2)."""
    return [
        {"name": "ЕНП", "id": "ЕНП"},
        {"name": "Номер полиса", "id": "Номер полиса"},
        {"name": "Фамилия", "id": "Фамилия"},
        {"name": "Имя", "id": "Имя"},
        {"name": "Отчество", "id": "Отчество"},
        {"name": "Пол", "id": "Пол"},
        {"name": "Дата рождения", "id": "Дата рождения"},
        {"name": f"Маршрут {type1}", "id": f"Маршрут {type1}"},
        {"name": f"Группа здоровья {type1}", "id": f"Группа здоровья {type1}"},
        {"name": f"Группа здоровья {type2}", "id": f"Группа здоровья {type2}"},
        {"name": "Направлен на II этап", "id": "Направлен на II этап"},
        {"name": f"Стоимость {type1}", "id": f"Стоимость {type1}"},
        {"name": f"Стоимость {type2}", "id": f"Стоимость {type2}"},
        {"name": "Общая стоимость", "id": "Общая стоимость"},
        {"name": f"Количество талонов {type1}", "id": f"Количество талонов {type1}"},
        {"name": f"Статус {type1}", "id": f"Статус {type1}"},
        {"name": f"Количество талонов {type2}", "id": f"Количество талонов {type2}"},
        {"name": f"Статус {type2}", "id": f"Статус {type2}"},
        {"name": f"Номер талона {type1}", "id": f"Номер талона {type1}"},
        {"name": f"Номер талона {type2}", "id": f"Номер талона {type2}"},
        {"name": f"Доктор {type1}", "id": f"Доктор {type1}"},
        {"name": f"Доктор {type2}", "id": f"Доктор {type2}"},
        {"name": f"Подразделение {type1}", "id": f"Подразделение {type1}"},
        {"name": f"Подразделение {type2}", "id": f"Подразделение {type2}"},
    ]


def _summary_columns(type1: str, type2: str):
    return [
        {"name": "Пол", "id": "Пол"},
        {"name": f"Группа здоровья {type1}", "id": f"Группа здоровья {type1}"},
        {"name": f"Группа здоровья {type2}", "id": f"Группа здоровья {type2}"},
        {"name": "Количество пациентов", "id": "Количество пациентов"},
        {"name": f"Стоимость {type1}", "id": f"Стоимость {type1}"},
        {"name": f"Стоимость {type2}", "id": f"Стоимость {type2}"},
        {"name": "Общая стоимость", "id": "Общая стоимость"},
    ]




@app.callback(
    Output(f"status-group-container-{type_page}", "style"),
    Output(f"status-individual-container-{type_page}", "style"),
    Input(f"status-selection-mode-{type_page}", "value"),
)
def toggle_status_selection(mode):
    if mode == "group":
        return {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "block"}


@app.callback(
    [
        Output(f"col-months-{type_page}", "style"),
        Output(f"col-input-{type_page}", "style"),
        Output(f"col-treatment-{type_page}", "style"),
        Output(f"label-date-{type_page}", "style"),
    ],
    Input(f"dropdown-report-type-{type_page}", "value"),
)
def toggle_period_filters(report_type):
    """Показываем отчётный месяц или поля выбора дат в зависимости от типа периода."""
    if report_type == "month":
        return {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "none"}
    if report_type == "initial_input":
        return {"display": "none"}, {"display": "block"}, {"display": "none"}, {"display": "block"}
    if report_type == "treatment":
        return {"display": "none"}, {"display": "none"}, {"display": "block"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "none"}


@app.callback(
    [
        Output(f"table-patients-{type_page}", "columns"),
        Output(f"table-patients-{type_page}", "data"),
        Output(f"loading-status-patients-{type_page}", "children"),
        Output(f"pivot-summary-{type_page}", "children"),
        Output(f"loading-status-summary-{type_page}", "children"),
        Output(f"pivot-dr1-{type_page}", "children"),
        Output(f"loading-status-dr1-{type_page}", "children"),
        Output(f"pivot-dr2-{type_page}", "children"),
        Output(f"loading-status-dr2-{type_page}", "children"),
    ],
    Input(f"update-button-{type_page}", "n_clicks"),
    [
        State(f"dropdown-year-{type_page}", "value"),
        State(f"range-slider-month-{type_page}", "value"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"dropdown-goal-type-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
    ],
)
def update_dr_tables(
    n_clicks,
    selected_year,
    month_range,
    report_type,
    goal_type,
    status_mode,
    status_group,
    status_individual,
    date_input_start,
    date_input_end,
    date_treatment_start,
    date_treatment_end,
):
    if n_clicks is None:
        raise PreventUpdate

    talon_types = GOAL_TYPE_PAIRS.get(goal_type, ("ДР1", "ДР2"))
    type1, type2 = talon_types
    report_type = report_type or "month"

    if not selected_year:
        msg = "Выберите год."
        empty_sheet = _build_pivot_sheet([])
        empty_combined = _build_pivot_sheet_combined([], type1, type2)
        return (
            _patient_columns(type1, type2), [], msg,
            empty_combined, msg,
            empty_sheet, msg,
            empty_sheet, msg,
        )
    if report_type in ("initial_input", "treatment"):
        if report_type == "initial_input" and (not date_input_start or not date_input_end):
            msg = "Укажите период (дата формирования)."
        elif report_type == "treatment" and (not date_treatment_start or not date_treatment_end):
            msg = "Укажите период (дата окончания лечения)."
        else:
            msg = None
        if msg:
            empty_sheet = _build_pivot_sheet([])
            empty_combined = _build_pivot_sheet_combined([], type1, type2)
            return (
                _patient_columns(type1, type2), [], msg,
                empty_combined, msg,
                empty_sheet, msg,
                empty_sheet, msg,
            )

    months = None
    if month_range is not None:
        if isinstance(month_range, (list, tuple)) and len(month_range) >= 1:
            m1, m2 = month_range[0], month_range[-1]
            months = list(range(m1, m2 + 1))
        else:
            months = [int(month_range)]

    status_list = None
    if status_mode == "group" and status_group:
        status_list = status_groups.get(status_group)
    elif status_mode == "individual" and status_individual:
        status_list = status_individual if isinstance(status_individual, list) else [status_individual]

    def _date_str(d):
        if d is None:
            return None
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        return str(d)[:10] if d else None

    start_date, end_date = None, None
    if report_type == "initial_input" and date_input_start and date_input_end:
        start_date, end_date = _date_str(date_input_start), _date_str(date_input_end)
    elif report_type == "treatment" and date_treatment_start and date_treatment_end:
        start_date, end_date = _date_str(date_treatment_start), _date_str(date_treatment_end)

    try:
        patient_costs, summary = get_dr_analysis_data(
            selected_year=selected_year,
            selected_months=months,
            talon_types=talon_types,
            report_type=report_type,
            status_list=status_list,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        err_msg = f"Ошибка загрузки: {e!s}"
        err_sheet = _build_pivot_sheet([])
        err_combined = _build_pivot_sheet_combined([], type1, type2)
        return (
            _patient_columns(type1, type2), [], err_msg,
            err_combined, err_msg,
            err_sheet, err_msg,
            err_sheet, err_msg,
        )

    status_text = f"Загружено пациентов: {len(patient_costs)}, строк сводной: {len(summary)}."
    combined_pivot = build_summary_combined_pivot(summary, type1, type2)
    pivot_dr1 = build_summary_dr1_pivot(patient_costs, type1)
    pivot_dr2 = build_summary_dr2_pivot(patient_costs, type2)
    return (
        _patient_columns(type1, type2),
        patient_costs,
        status_text,
        _build_pivot_sheet_combined(combined_pivot, type1, type2),
        status_text,
        _build_pivot_sheet(pivot_dr1),
        status_text,
        _build_pivot_sheet(pivot_dr2),
        status_text,
    )


@app.callback(
    [
        Output(f"download-xlsx-{type_page}", "data"),
        Output(f"toast-excel-{type_page}", "is_open"),
        Output(f"toast-excel-{type_page}", "children"),
        Output(f"toast-excel-{type_page}", "icon"),
    ],
    Input(f"download-excel-{type_page}", "n_clicks"),
    [
        State(f"dropdown-year-{type_page}", "value"),
        State(f"range-slider-month-{type_page}", "value"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"dropdown-goal-type-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
    ],
    prevent_initial_call=True,
)
def export_dr_to_excel(
    n_clicks,
    selected_year,
    month_range,
    report_type,
    goal_type,
    status_mode,
    status_group,
    status_individual,
    date_input_start,
    date_input_end,
    date_treatment_start,
    date_treatment_end,
):
    if n_clicks is None:
        raise PreventUpdate
    if not selected_year:
        return (
            None,
            True,
            "Выберите год и период для экспорта.",
            "warning",
        )
    talon_types = GOAL_TYPE_PAIRS.get(goal_type, ("ДР1", "ДР2"))
    type1, type2 = talon_types
    report_type = report_type or "month"
    if report_type == "initial_input" and (not date_input_start or not date_input_end):
        return (None, True, "Укажите период (дата формирования).", "warning")
    if report_type == "treatment" and (not date_treatment_start or not date_treatment_end):
        return (None, True, "Укажите период (дата окончания лечения).", "warning")

    months = None
    if month_range is not None:
        if isinstance(month_range, (list, tuple)) and len(month_range) >= 1:
            m1, m2 = month_range[0], month_range[-1]
            months = list(range(m1, m2 + 1))
        else:
            months = [int(month_range)]
    status_list = None
    if status_mode == "group" and status_group:
        status_list = status_groups.get(status_group)
    elif status_mode == "individual" and status_individual:
        status_list = status_individual if isinstance(status_individual, list) else [status_individual]
    def _date_str(d):
        if d is None:
            return None
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        return str(d)[:10] if d else None

    start_date, end_date = None, None
    if report_type == "initial_input":
        start_date, end_date = _date_str(date_input_start), _date_str(date_input_end)
    elif report_type == "treatment":
        start_date, end_date = _date_str(date_treatment_start), _date_str(date_treatment_end)

    try:
        patient_costs, summary = get_dr_analysis_data(
            selected_year=selected_year,
            selected_months=months,
            talon_types=talon_types,
            report_type=report_type,
            status_list=status_list,
            start_date=start_date,
            end_date=end_date,
        )
        combined_pivot = build_summary_combined_pivot(summary, type1, type2)
        pivot_dr1 = build_summary_dr1_pivot(patient_costs, type1)
        pivot_dr2 = build_summary_dr2_pivot(patient_costs, type2)
        buffer = build_dr_excel(
            patient_costs, summary, combined_pivot, pivot_dr1, pivot_dr2, type1, type2,
        )
        filename = f"Анализ_вторых_этапов_{selected_year}_{datetime.now():%Y%m%d_%H%M}.xlsx"
        b64 = base64.b64encode(buffer.getvalue()).decode()
        return (
            {
                "content": b64,
                "base64": True,
                "filename": filename,
                "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            True,
            f"Файл «{filename}» готов к скачиванию.",
            "success",
        )
    except Exception as e:
        return (
            None,
            True,
            f"Ошибка при формировании Excel: {e!s}"[:200],
            "danger",
        )
