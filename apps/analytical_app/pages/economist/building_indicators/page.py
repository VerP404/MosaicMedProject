"""Конструктор отчёта и ввод планов: индикаторы по корпусам."""
from __future__ import annotations

import io
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback_context, dash_table, dcc, html, no_update
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import (
    filter_years,
    get_available_buildings,
    get_current_reporting_month,
)
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.building_indicators.query import (
    DEFAULT_PRINT_CONFIG,
    LAYOUT_OPTIONS,
    PLAN_KIND_OPTIONS,
    delete_preset,
    delete_print_template,
    get_preset,
    get_print_template,
    list_indicator_options,
    list_presets,
    list_print_templates,
    normalize_print_config,
    run_building_report,
    save_preset,
    save_print_template,
)
from apps.plan.services.building_report_engine import LAYOUT_INDICATOR_BUILDING
from apps.plan.services.print_form_engine import (
    build_print_form_data,
    render_print_form_html,
)
from apps.analytical_app.pages.economist.building_indicators.plans_entry import (
    plans_entry_tab,
)

type_page = "econ-building-indicators"
type_page_print = "econ-building-indicators-print"
PRINT_ITEMS_TABLE = "bie-print-items"


def _current_year() -> int:
    return datetime.now().year


def _report_tab(presets, indicators, buildings, month_options, month_num):
    return html.Div(
        [
            dcc.Store(id=f"store-result-{type_page}"),
            dcc.Store(id=f"store-preset-id-{type_page}"),
            dcc.Store(id=f"store-pending-payment-{type_page}"),
            dcc.Download(id=f"download-excel-{type_page}"),
            dbc.Alert(id=f"alert-{type_page}", is_open=False, duration=6000, className="mb-2"),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Шаблон набора (пресет)", className="mb-2"),
                        html.P(
                            "Это не ввод планов. Здесь собираете набор индикаторов (+ корпуса, вид таблицы) "
                            "и сохраняете шаблон, чтобы каждый раз быстро смотреть план/факт по этому набору.",
                            className="text-muted mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=f"dropdown-preset-{type_page}",
                                        options=presets,
                                        placeholder="Выберите сохранённый шаблон",
                                        clearable=True,
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"input-preset-name-{type_page}",
                                        placeholder="Название шаблона, напр. Неотложка+ДВ4",
                                        type="text",
                                    ),
                                    width=3,
                                ),
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button("Загрузить", id=f"btn-load-preset-{type_page}", color="secondary"),
                                            dbc.Button("Сохранить", id=f"btn-save-preset-{type_page}", color="primary"),
                                            dbc.Button(
                                                "Сохранить как",
                                                id=f"btn-save-as-preset-{type_page}",
                                                color="outline-primary",
                                            ),
                                            dbc.Button("Удалить", id=f"btn-delete-preset-{type_page}", color="danger"),
                                        ]
                                    ),
                                    width=5,
                                ),
                            ],
                            className="g-2 align-items-center",
                        ),
                    ]
                ),
                className="mb-3 shadow-sm",
            ),
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.P(
                                "1) Отметьте нужные индикаторы  2) при необходимости корпуса  "
                                "3) вид таблицы / метрику  4) «Сформировать». "
                                "Цифры плана берутся из вкладки «Ввод планов», факт — из оказанных услуг.",
                                className="text-muted mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Какие индикаторы в отчёт", className="fw-bold"),
                                            dcc.Dropdown(
                                                id=f"dropdown-indicators-{type_page}",
                                                options=indicators,
                                                multi=True,
                                                placeholder="Пусто = все, у которых есть план по корпусам",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Какие корпуса показать", className="fw-bold"),
                                            dcc.Dropdown(
                                                id=f"dropdown-buildings-{type_page}",
                                                options=buildings,
                                                multi=True,
                                                placeholder="Пусто = все корпуса",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Как разложить таблицу", className="fw-bold"),
                                            dbc.RadioItems(
                                                id=f"radio-layout-{type_page}",
                                                options=LAYOUT_OPTIONS,
                                                value=LAYOUT_INDICATOR_BUILDING,
                                                inline=False,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Метрика", className="fw-bold"),
                                            dcc.Dropdown(
                                                id=f"dropdown-metric-{type_page}",
                                                options=[
                                                    {"label": "Объёмы", "value": "volumes"},
                                                    {"label": "Финансы", "value": "finance"},
                                                ],
                                                value="volumes",
                                                clearable=False,
                                            ),
                                            html.Label("Версия плана", className="fw-bold mt-2"),
                                            dcc.Dropdown(
                                                id=f"dropdown-plan-kind-{type_page}",
                                                options=PLAN_KIND_OPTIONS,
                                                value="internal",
                                                clearable=False,
                                            ),
                                            dbc.Switch(
                                                id=f"switch-period-closed-{type_page}",
                                                label="Период закрыт (факт = только оплаченные)",
                                                value=False,
                                                className="mt-3",
                                            ),
                                            html.Label("Факт за отчётный месяц", className="fw-bold mt-2"),
                                            dcc.Dropdown(
                                                id=f"dropdown-payment-{type_page}",
                                                options=[
                                                    {
                                                        "label": "Предъявленные и оплаченные (1,2,3,4,6,8,19)",
                                                        "value": "presented",
                                                    },
                                                    {
                                                        "label": "Предъявленные (2,3)",
                                                        "value": "presented_2_3",
                                                    },
                                                ],
                                                value="presented",
                                                clearable=False,
                                            ),
                                            html.P(
                                                "Режим выше — только для выбранного месяца отчёта. "
                                                "За остальные месяцы в нарастающем итоге всегда статус 3 (оплаченные).",
                                                className="text-muted small mt-1 mb-0",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Switch(
                                                id=f"switch-unique-{type_page}",
                                                label="Уникальные пациенты",
                                                value=False,
                                                className="mt-4",
                                            ),
                                            dbc.Switch(
                                                id=f"switch-require-plan-{type_page}",
                                                label="Только где есть план корпуса",
                                                value=True,
                                                className="mt-2",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ]
                            ),
                        ],
                        title="Состав отчёта (набор индикаторов)",
                    )
                ],
                start_collapsed=False,
                className="mb-3",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Год", className="fw-bold"),
                                        filter_years(type_page),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Отчётный месяц", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-reporting-month-{type_page}",
                                            options=month_options,
                                            value=month_num,
                                            clearable=False,
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Сформировать",
                                        id=f"btn-generate-{type_page}",
                                        color="success",
                                        className="mt-4",
                                    ),
                                    width=2,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Excel",
                                        id=f"btn-excel-{type_page}",
                                        color="outline-success",
                                        className="mt-4",
                                        disabled=True,
                                    ),
                                    width=2,
                                ),
                            ],
                            className="align-items-start",
                        ),
                        html.Div(id=f"status-{type_page}", className="mt-2 text-muted"),
                    ]
                ),
                className="mb-3 shadow-sm",
            ),
            dcc.Loading(
                id=f"loading-{type_page}",
                type="default",
                children=card_table(f"result-table-{type_page}", "Отчёт по корпусам", page_size=40),
            ),
        ]
    )


def _print_items_from_config(config: dict) -> list[dict]:
    rows = []
    for sec in (config or {}).get("sections") or []:
        section_title = sec.get("title") or "Раздел"
        for it in sec.get("items") or []:
            rows.append(
                {
                    "section": section_title,
                    "indicator_id": it.get("indicator_id"),
                    "short_title": it.get("short_title") or "",
                    "show_of_year": bool(it.get("show_of_year")),
                }
            )
    return rows


def _config_from_print_items(
    rows: list[dict],
    columns: int = 3,
    page_orientation: str = "landscape",
) -> dict:
    sections_map: dict[str, list] = {}
    order: list[str] = []
    for row in rows or []:
        section = (row.get("section") or "Раздел").strip() or "Раздел"
        try:
            iid = int(row.get("indicator_id"))
        except (TypeError, ValueError):
            continue
        if section not in sections_map:
            sections_map[section] = []
            order.append(section)
        show = row.get("show_of_year")
        if isinstance(show, str):
            show = show.strip().lower() in {"1", "true", "yes", "да", "y"}
        sections_map[section].append(
            {
                "indicator_id": iid,
                "short_title": (row.get("short_title") or "").strip() or str(iid),
                "show_of_year": bool(show),
            }
        )
    sections = [{"title": title, "items": sections_map[title]} for title in order]
    if not sections:
        sections = list(DEFAULT_PRINT_CONFIG["sections"])
    return normalize_print_config(
        {
            "columns": columns or 3,
            "page_orientation": page_orientation or "landscape",
            "sections": sections,
        }
    )


def _print_form_tab(indicators, month_options, month_num):
    templates = list_print_templates()
    return html.Div(
        [
            dcc.Store(id=f"store-print-template-id-{type_page_print}"),
            dcc.Store(id=f"store-print-tick-{type_page_print}"),
            dcc.Store(
                id=f"store-print-config-{type_page_print}",
                data=DEFAULT_PRINT_CONFIG,
            ),
            dbc.Alert(
                id=f"alert-{type_page_print}",
                is_open=False,
                duration=8000,
                className="mb-2 d-print-none",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Шаблон бланка", className="mb-2"),
                        html.P(
                            "Соберите набор индикаторов с короткими подписями для печати. "
                            "В списке — только индикаторы, у которых уже есть план по корпусам. "
                            "Секции задаются в колонке «Раздел» таблицы.",
                            className="text-muted mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=f"dropdown-print-template-{type_page_print}",
                                        options=templates,
                                        placeholder="Выберите шаблон",
                                        clearable=True,
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"input-print-template-name-{type_page_print}",
                                        placeholder="Название шаблона",
                                        type="text",
                                    ),
                                    width=3,
                                ),
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Загрузить",
                                                id=f"btn-load-print-tpl-{type_page_print}",
                                                color="secondary",
                                            ),
                                            dbc.Button(
                                                "Сохранить",
                                                id=f"btn-save-print-tpl-{type_page_print}",
                                                color="primary",
                                            ),
                                            dbc.Button(
                                                "Сохранить как",
                                                id=f"btn-save-as-print-tpl-{type_page_print}",
                                                color="outline-primary",
                                            ),
                                            dbc.Button(
                                                "Удалить",
                                                id=f"btn-delete-print-tpl-{type_page_print}",
                                                color="danger",
                                            ),
                                        ]
                                    ),
                                    width=5,
                                ),
                            ],
                            className="g-2 align-items-center mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Колонок на бланке", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-print-columns-{type_page_print}",
                                            options=[
                                                {"label": "2", "value": 2},
                                                {"label": "3", "value": 3},
                                                {"label": "4", "value": 4},
                                            ],
                                            value=3,
                                            clearable=False,
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Ориентация", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-print-orientation-{type_page_print}",
                                            options=[
                                                {"label": "Альбомная", "value": "landscape"},
                                                {"label": "Книжная", "value": "portrait"},
                                            ],
                                            value="landscape",
                                            clearable=False,
                                        ),
                                    ],
                                    width=2,
                                ),
                            ],
                            className="g-2 mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Раздел", className="fw-bold"),
                                        dbc.Input(
                                            id=f"input-print-section-{type_page_print}",
                                            value="Лечебно-диагностическая работа",
                                            type="text",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Индикатор", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-print-add-indicator-{type_page_print}",
                                            options=indicators,
                                            placeholder="Выберите индикатор",
                                            clearable=True,
                                        ),
                                    ],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Подпись на бланке", className="fw-bold"),
                                        dbc.Input(
                                            id=f"input-print-short-title-{type_page_print}",
                                            placeholder="Короткое название",
                                            type="text",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Checkbox(
                                            id=f"check-print-of-year-{type_page_print}",
                                            label="от года",
                                            value=False,
                                            className="mt-4",
                                        ),
                                    ],
                                    width=1,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Добавить",
                                        id=f"btn-print-add-item-{type_page_print}",
                                        color="primary",
                                        className="mt-4",
                                    ),
                                    width=1,
                                ),
                            ],
                            className="g-2 mb-2",
                        ),
                        dash_table.DataTable(
                            id=f"table-print-items-{type_page_print}",
                            columns=[
                                {"name": "Раздел", "id": "section", "editable": True},
                                {"name": "ID", "id": "indicator_id", "editable": False},
                                {"name": "Подпись", "id": "short_title", "editable": True},
                                {
                                    "name": "от года",
                                    "id": "show_of_year",
                                    "editable": True,
                                    "type": "text",
                                },
                            ],
                            data=[],
                            row_deletable=True,
                            page_size=15,
                            style_table={"overflowX": "auto"},
                            style_cell={"padding": "4px", "fontSize": "13px"},
                            style_header={"fontWeight": "bold"},
                        ),
                    ]
                ),
                className="mb-3 shadow-sm d-print-none",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Параметры периода и факта", className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Год", className="fw-bold"),
                                        filter_years(type_page_print),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Отчётный месяц", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-reporting-month-{type_page_print}",
                                            options=month_options,
                                            value=month_num,
                                            clearable=False,
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Метрика", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-metric-{type_page_print}",
                                            options=[
                                                {"label": "Объёмы", "value": "volumes"},
                                                {"label": "Финансы", "value": "finance"},
                                            ],
                                            value="volumes",
                                            clearable=False,
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Версия плана", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-plan-kind-{type_page_print}",
                                            options=PLAN_KIND_OPTIONS,
                                            value="internal",
                                            clearable=False,
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Switch(
                                            id=f"switch-period-closed-{type_page_print}",
                                            label="Период закрыт",
                                            value=False,
                                            className="mt-4",
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Факт за отчётный месяц", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-payment-{type_page_print}",
                                            options=PAYMENT_OPTIONS_OPEN,
                                            value="presented",
                                            clearable=False,
                                        ),
                                    ],
                                    width=4,
                                ),
                            ],
                            className="g-2 mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "Сформировать бланк",
                                        id=f"btn-generate-print-{type_page_print}",
                                        color="success",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Печать / PDF",
                                        id=f"btn-print-{type_page_print}",
                                        color="primary",
                                        outline=True,
                                        disabled=True,
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    html.Div(
                                        id=f"status-{type_page_print}",
                                        className="text-muted mt-2",
                                    ),
                                    width=True,
                                ),
                            ],
                            className="g-2 align-items-center",
                        ),
                    ]
                ),
                className="mb-3 shadow-sm d-print-none",
            ),
            html.Div(
                id=f"print-volume-form-preview",
                children=html.Div(
                    "Сформируйте бланк — здесь появится превью для печати.",
                    className="text-muted p-3",
                ),
            ),
        ]
    )


def economist_building_indicators_def():
    year = _current_year()
    month_num, _month_name = get_current_reporting_month()
    presets = list_presets()
    indicators = list_indicator_options(year)
    indicators_print = list_indicator_options(
        year, for_editor=True, only_with_building_plan=True
    )
    buildings = get_available_buildings()

    month_options = [
        {"label": name, "value": i}
        for i, name in enumerate(
            [
                "Январь",
                "Февраль",
                "Март",
                "Апрель",
                "Май",
                "Июнь",
                "Июль",
                "Август",
                "Сентябрь",
                "Октябрь",
                "Ноябрь",
                "Декабрь",
            ],
            start=1,
        )
    ]

    return html.Div(
        [
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="Отчёт",
                        tab_id=f"tab-report-{type_page}",
                        children=_report_tab(presets, indicators, buildings, month_options, month_num),
                    ),
                    dbc.Tab(
                        label="Ввод планов",
                        tab_id=f"tab-plans-{type_page}",
                        children=plans_entry_tab(),
                    ),
                    dbc.Tab(
                        label="Печатная форма",
                        tab_id=f"tab-print-{type_page}",
                        children=_print_form_tab(indicators_print, month_options, month_num),
                    ),
                ],
                active_tab=f"tab-report-{type_page}",
                id=f"tabs-{type_page}",
                className="mb-2 d-print-none",
            )
        ],
        style={"padding": "0.5rem"},
    )


def _collect_config(
    indicators,
    buildings,
    layout,
    metric,
    payment,
    unique_flag,
    require_plan,
    period_closed=False,
) -> dict:
    return {
        "indicator_ids": indicators or [],
        "building_ids": buildings or [],
        "layout": layout or LAYOUT_INDICATOR_BUILDING,
        "metric": metric or "volumes",
        "payment_type": payment or "presented",
        "period_closed": bool(period_closed),
        "unique_flag": bool(unique_flag),
        "require_building_plan": bool(require_plan),
        "columns": ["plan", "fact", "pct", "balance"],
    }


PAYMENT_OPTIONS_OPEN = [
    {"label": "Предъявленные и оплаченные (1,2,3,4,6,8,19)", "value": "presented"},
    {"label": "Предъявленные (2,3)", "value": "presented_2_3"},
]
PAYMENT_OPTIONS_CLOSED = [
    {"label": "Оплаченные (3) — период закрыт", "value": "paid"},
]


@app.callback(
    Output(f"dropdown-payment-{type_page}", "options"),
    Output(f"dropdown-payment-{type_page}", "value"),
    Output(f"dropdown-payment-{type_page}", "disabled"),
    Output(f"store-pending-payment-{type_page}", "data", allow_duplicate=True),
    Input(f"switch-period-closed-{type_page}", "value"),
    Input(f"store-pending-payment-{type_page}", "data"),
    State(f"dropdown-payment-{type_page}", "value"),
    prevent_initial_call=True,
)
def toggle_period_closed_payment(period_closed, pending_payment, current_payment):
    if period_closed:
        return PAYMENT_OPTIONS_CLOSED, "paid", True, None
    preferred = pending_payment if pending_payment in ("presented", "presented_2_3") else None
    value = preferred or (
        current_payment if current_payment in ("presented", "presented_2_3") else "presented"
    )
    return PAYMENT_OPTIONS_OPEN, value, False, None


@app.callback(
    Output(f"dropdown-indicators-{type_page}", "options"),
    Input(f"dropdown-year-{type_page}", "value"),
    Input(f"dropdown-plan-kind-{type_page}", "value"),
)
def refresh_indicators(year, plan_kind):
    if not year:
        raise PreventUpdate
    return list_indicator_options(int(year), plan_kind=plan_kind or "internal")


@app.callback(
    Output(f"dropdown-indicators-{type_page}", "value"),
    Output(f"dropdown-buildings-{type_page}", "value"),
    Output(f"radio-layout-{type_page}", "value"),
    Output(f"dropdown-metric-{type_page}", "value"),
    Output(f"switch-unique-{type_page}", "value"),
    Output(f"switch-require-plan-{type_page}", "value"),
    Output(f"switch-period-closed-{type_page}", "value"),
    Output(f"store-pending-payment-{type_page}", "data"),
    Output(f"input-preset-name-{type_page}", "value"),
    Output(f"store-preset-id-{type_page}", "data"),
    Output(f"alert-{type_page}", "children"),
    Output(f"alert-{type_page}", "color"),
    Output(f"alert-{type_page}", "is_open"),
    Output(f"dropdown-preset-{type_page}", "options"),
    Input(f"btn-load-preset-{type_page}", "n_clicks"),
    Input(f"btn-save-preset-{type_page}", "n_clicks"),
    Input(f"btn-save-as-preset-{type_page}", "n_clicks"),
    Input(f"btn-delete-preset-{type_page}", "n_clicks"),
    State(f"dropdown-preset-{type_page}", "value"),
    State(f"store-preset-id-{type_page}", "data"),
    State(f"input-preset-name-{type_page}", "value"),
    State(f"dropdown-indicators-{type_page}", "value"),
    State(f"dropdown-buildings-{type_page}", "value"),
    State(f"radio-layout-{type_page}", "value"),
    State(f"dropdown-metric-{type_page}", "value"),
    State(f"dropdown-payment-{type_page}", "value"),
    State(f"switch-unique-{type_page}", "value"),
    State(f"switch-require-plan-{type_page}", "value"),
    State(f"switch-period-closed-{type_page}", "value"),
    prevent_initial_call=True,
)
def manage_presets(
    n_load,
    n_save,
    n_save_as,
    n_delete,
    selected_preset,
    stored_preset_id,
    preset_name,
    indicators,
    buildings,
    layout,
    metric,
    payment,
    unique_flag,
    require_plan,
    period_closed,
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    presets = list_presets()

    noop_fields = (no_update,) * 10

    if trigger == f"btn-load-preset-{type_page}":
        if not selected_preset:
            return (*noop_fields, "Выберите пресет", "warning", True, presets)
        data = get_preset(int(selected_preset))
        if not data:
            return (*noop_fields, "Пресет не найден", "danger", True, presets)
        cfg = data["config"] or {}
        closed = bool(cfg.get("period_closed", False))
        pay = cfg.get("payment_type") or "presented"
        if closed:
            pay = "paid"
        elif pay not in ("presented", "presented_2_3"):
            pay = "presented"
        return (
            cfg.get("indicator_ids") or [],
            cfg.get("building_ids") or [],
            cfg.get("layout") or LAYOUT_INDICATOR_BUILDING,
            cfg.get("metric") or "volumes",
            bool(cfg.get("unique_flag", False)),
            bool(cfg.get("require_building_plan", True)),
            closed,
            pay,
            data["name"],
            data["id"],
            f"Загружен пресет «{data['name']}»",
            "success",
            True,
            presets,
        )

    config = _collect_config(
        indicators, buildings, layout, metric, payment, unique_flag, require_plan, period_closed
    )

    if trigger == f"btn-save-as-preset-{type_page}":
        name = (preset_name or "").strip()
        if not name:
            return (*noop_fields, "Укажите название пресета", "warning", True, presets)
        try:
            new_id = save_preset(name, config, preset_id=None)
        except Exception as exc:
            return (*noop_fields, f"Ошибка сохранения: {exc}", "danger", True, presets)
        presets = list_presets()
        return (
            *(no_update,) * 8,
            name,
            new_id,
            f"Создан пресет «{name}»",
            "success",
            True,
            presets,
        )

    if trigger == f"btn-save-preset-{type_page}":
        name = (preset_name or "").strip()
        if not name:
            return (*noop_fields, "Укажите название пресета", "warning", True, presets)
        pid = stored_preset_id or selected_preset
        try:
            new_id = save_preset(name, config, preset_id=int(pid) if pid else None)
        except Exception as exc:
            return (*noop_fields, f"Ошибка сохранения: {exc}", "danger", True, presets)
        presets = list_presets()
        return (
            *(no_update,) * 8,
            name,
            new_id,
            f"Сохранён пресет «{name}»",
            "success",
            True,
            presets,
        )

    if trigger == f"btn-delete-preset-{type_page}":
        pid = selected_preset or stored_preset_id
        if not pid:
            return (*noop_fields, "Нечего удалять", "warning", True, presets)
        try:
            delete_preset(int(pid))
        except Exception as exc:
            return (*noop_fields, f"Ошибка удаления: {exc}", "danger", True, presets)
        presets = list_presets()
        return (
            *(no_update,) * 8,
            "",
            None,
            "Пресет удалён",
            "success",
            True,
            presets,
        )

    raise PreventUpdate


@app.callback(
    Output(f"result-table-{type_page}", "columns"),
    Output(f"result-table-{type_page}", "data"),
    Output(f"store-result-{type_page}", "data"),
    Output(f"btn-excel-{type_page}", "disabled"),
    Output(f"status-{type_page}", "children"),
    Input(f"btn-generate-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"dropdown-reporting-month-{type_page}", "value"),
    State(f"dropdown-indicators-{type_page}", "value"),
    State(f"dropdown-buildings-{type_page}", "value"),
    State(f"radio-layout-{type_page}", "value"),
    State(f"dropdown-metric-{type_page}", "value"),
    State(f"dropdown-plan-kind-{type_page}", "value"),
    State(f"dropdown-payment-{type_page}", "value"),
    State(f"switch-unique-{type_page}", "value"),
    State(f"switch-require-plan-{type_page}", "value"),
    State(f"switch-period-closed-{type_page}", "value"),
    prevent_initial_call=True,
)
def generate_report(
    n_clicks,
    year,
    reporting_month,
    indicators,
    buildings,
    layout,
    metric,
    plan_kind,
    payment,
    unique_flag,
    require_plan,
    period_closed,
):
    if not n_clicks:
        raise PreventUpdate
    if not year or not reporting_month:
        return [], [], None, True, "Укажите год и месяц отчёта"

    try:
        _long_df, pivoted = run_building_report(
            year=int(year),
            reporting_month=int(reporting_month),
            indicator_ids=indicators,
            building_ids=buildings,
            layout=layout or LAYOUT_INDICATOR_BUILDING,
            metric=metric or "volumes",
            payment_type=payment or "presented",
            unique_flag=bool(unique_flag),
            require_building_plan=bool(require_plan),
            period_closed=bool(period_closed),
            plan_kind=plan_kind or "internal",
        )
    except Exception as exc:
        return [], [], None, True, f"Ошибка: {exc}"

    if pivoted is None or pivoted.empty:
        return [], [], None, True, "Нет данных (проверьте планы корпусов и выбранные индикаторы)"

    columns = [{"name": c, "id": c} for c in pivoted.columns]
    records = pivoted.to_dict("records")
    mode_label = (
        "оплаченные (3)"
        if period_closed or payment == "paid"
        else (
            "предъявленные 2,3"
            if payment == "presented_2_3"
            else "предъявленные+оплаченные 1,2,3,4,6,8,19"
        )
    )
    return (
        columns,
        records,
        {"columns": list(pivoted.columns), "records": records},
        False,
        (
            f"Строк: {len(records)}. Год {year}, отчётный месяц {reporting_month}. "
            f"Факт за месяц: {mode_label}; остальные месяцы: оплаченные (3)."
        ),
    )

@app.callback(
    Output(f"download-excel-{type_page}", "data"),
    Input(f"btn-excel-{type_page}", "n_clicks"),
    State(f"store-result-{type_page}", "data"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"dropdown-reporting-month-{type_page}", "value"),
    prevent_initial_call=True,
)
def download_excel(n_clicks, stored, year, month):
    if not n_clicks or not stored:
        raise PreventUpdate
    df = pd.DataFrame(stored.get("records") or [])
    if df.empty:
        raise PreventUpdate
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Отчёт", index=False)
    buffer.seek(0)
    filename = f"building_indicators_{year}_{month}.xlsx"
    return dcc.send_bytes(buffer.getvalue(), filename)


# ========== Печатная форма ==========

@app.callback(
    Output(f"dropdown-print-add-indicator-{type_page_print}", "options"),
    Input(f"dropdown-year-{type_page_print}", "value"),
    Input(f"dropdown-plan-kind-{type_page_print}", "value"),
)
def refresh_print_indicators(year, plan_kind):
    if not year:
        raise PreventUpdate
    return list_indicator_options(
        int(year),
        for_editor=True,
        only_with_building_plan=True,
        plan_kind=plan_kind or "internal",
    )


@app.callback(
    Output(f"dropdown-payment-{type_page_print}", "options"),
    Output(f"dropdown-payment-{type_page_print}", "value"),
    Output(f"dropdown-payment-{type_page_print}", "disabled"),
    Input(f"switch-period-closed-{type_page_print}", "value"),
    State(f"dropdown-payment-{type_page_print}", "value"),
)
def toggle_print_period_closed(period_closed, current_payment):
    if period_closed:
        return PAYMENT_OPTIONS_CLOSED, "paid", True
    value = current_payment if current_payment in ("presented", "presented_2_3") else "presented"
    return PAYMENT_OPTIONS_OPEN, value, False


@app.callback(
    Output(f"table-print-items-{type_page_print}", "data"),
    Output(f"input-print-short-title-{type_page_print}", "value"),
    Output(f"dropdown-print-add-indicator-{type_page_print}", "value"),
    Input(f"btn-print-add-item-{type_page_print}", "n_clicks"),
    State(f"table-print-items-{type_page_print}", "data"),
    State(f"input-print-section-{type_page_print}", "value"),
    State(f"dropdown-print-add-indicator-{type_page_print}", "value"),
    State(f"dropdown-print-add-indicator-{type_page_print}", "options"),
    State(f"input-print-short-title-{type_page_print}", "value"),
    State(f"check-print-of-year-{type_page_print}", "value"),
    prevent_initial_call=True,
)
def add_print_item(n_clicks, rows, section, indicator_id, indicator_options, short_title, of_year):
    if not n_clicks:
        raise PreventUpdate
    if not indicator_id:
        raise PreventUpdate
    rows = list(rows or [])
    label = ""
    for opt in indicator_options or []:
        if opt.get("value") == indicator_id:
            label = opt.get("label") or ""
            break
    # убрать суффикс [МО: ...] из подписи по умолчанию
    default_title = label.split("  [")[0].split(" \\ ")[-1] if label else str(indicator_id)
    title = (short_title or "").strip() or default_title
    rows.append(
        {
            "section": (section or "Раздел").strip() or "Раздел",
            "indicator_id": int(indicator_id),
            "short_title": title,
            "show_of_year": bool(of_year),
        }
    )
    return rows, "", None


@app.callback(
    Output(f"table-print-items-{type_page_print}", "data", allow_duplicate=True),
    Output(f"dropdown-print-columns-{type_page_print}", "value"),
    Output(f"dropdown-print-orientation-{type_page_print}", "value"),
    Output(f"input-print-template-name-{type_page_print}", "value"),
    Output(f"store-print-template-id-{type_page_print}", "data"),
    Output(f"dropdown-print-template-{type_page_print}", "options"),
    Output(f"alert-{type_page_print}", "children"),
    Output(f"alert-{type_page_print}", "color"),
    Output(f"alert-{type_page_print}", "is_open"),
    Input(f"btn-load-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-save-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-save-as-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-delete-print-tpl-{type_page_print}", "n_clicks"),
    State(f"dropdown-print-template-{type_page_print}", "value"),
    State(f"store-print-template-id-{type_page_print}", "data"),
    State(f"input-print-template-name-{type_page_print}", "value"),
    State(f"table-print-items-{type_page_print}", "data"),
    State(f"dropdown-print-columns-{type_page_print}", "value"),
    State(f"dropdown-print-orientation-{type_page_print}", "value"),
    prevent_initial_call=True,
)
def manage_print_templates(
    n_load,
    n_save,
    n_save_as,
    n_delete,
    selected_tpl,
    stored_id,
    tpl_name,
    items,
    columns,
    orientation,
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    templates = list_print_templates()
    noop = (no_update, no_update, no_update, no_update, no_update, templates)

    if trigger == f"btn-load-print-tpl-{type_page_print}":
        if not selected_tpl:
            return (*noop[:5], templates, "Выберите шаблон", "warning", True)
        data = get_print_template(int(selected_tpl))
        if not data:
            return (*noop[:5], templates, "Шаблон не найден", "danger", True)
        cfg = data["config"]
        return (
            _print_items_from_config(cfg),
            cfg.get("columns") or 3,
            cfg.get("page_orientation") or "landscape",
            data["name"],
            data["id"],
            templates,
            f"Загружен шаблон «{data['name']}»",
            "success",
            True,
        )

    config = _config_from_print_items(items, columns, orientation)

    if trigger == f"btn-save-as-print-tpl-{type_page_print}":
        name = (tpl_name or "").strip()
        if not name:
            return (*noop[:5], templates, "Укажите название шаблона", "warning", True)
        try:
            new_id = save_print_template(name, config)
        except Exception as exc:
            return (*noop[:5], templates, f"Ошибка: {exc}", "danger", True)
        templates = list_print_templates()
        return (
            no_update,
            no_update,
            no_update,
            name,
            new_id,
            templates,
            f"Создан шаблон «{name}»",
            "success",
            True,
        )

    if trigger == f"btn-save-print-tpl-{type_page_print}":
        name = (tpl_name or "").strip()
        if not name:
            return (*noop[:5], templates, "Укажите название шаблона", "warning", True)
        pid = stored_id or selected_tpl
        try:
            new_id = save_print_template(name, config, template_id=int(pid) if pid else None)
        except Exception as exc:
            return (*noop[:5], templates, f"Ошибка: {exc}", "danger", True)
        templates = list_print_templates()
        return (
            no_update,
            no_update,
            no_update,
            name,
            new_id,
            templates,
            f"Сохранён шаблон «{name}»",
            "success",
            True,
        )

    if trigger == f"btn-delete-print-tpl-{type_page_print}":
        pid = selected_tpl or stored_id
        if not pid:
            return (*noop[:5], templates, "Нечего удалять", "warning", True)
        try:
            delete_print_template(int(pid))
        except Exception as exc:
            return (*noop[:5], templates, f"Ошибка: {exc}", "danger", True)
        templates = list_print_templates()
        return (
            [],
            3,
            "landscape",
            "",
            None,
            templates,
            "Шаблон удалён",
            "success",
            True,
        )

    raise PreventUpdate


@app.callback(
    Output("print-volume-form-preview", "children"),
    Output(f"btn-print-{type_page_print}", "disabled"),
    Output(f"status-{type_page_print}", "children"),
    Output(f"alert-{type_page_print}", "children", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "color", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "is_open", allow_duplicate=True),
    Input(f"btn-generate-print-{type_page_print}", "n_clicks"),
    State(f"dropdown-year-{type_page_print}", "value"),
    State(f"dropdown-reporting-month-{type_page_print}", "value"),
    State(f"dropdown-metric-{type_page_print}", "value"),
    State(f"dropdown-plan-kind-{type_page_print}", "value"),
    State(f"dropdown-payment-{type_page_print}", "value"),
    State(f"switch-period-closed-{type_page_print}", "value"),
    State(f"table-print-items-{type_page_print}", "data"),
    State(f"dropdown-print-columns-{type_page_print}", "value"),
    State(f"dropdown-print-orientation-{type_page_print}", "value"),
    prevent_initial_call=True,
)
def generate_print_form(
    n_clicks,
    year,
    reporting_month,
    metric,
    plan_kind,
    payment,
    period_closed,
    items,
    columns,
    orientation,
):
    if not n_clicks:
        raise PreventUpdate
    if not year or not reporting_month:
        return no_update, True, "", "Укажите год и отчётный месяц", "warning", True
    if not items:
        return (
            no_update,
            True,
            "",
            "Добавьте хотя бы один индикатор в бланк",
            "warning",
            True,
        )

    config = _config_from_print_items(items, columns, orientation)
    try:
        data = build_print_form_data(
            year=int(year),
            reporting_month=int(reporting_month),
            config=config,
            payment_type=payment or "presented",
            period_closed=bool(period_closed),
            metric=metric or "volumes",
            plan_kind=plan_kind or "internal",
        )
        html_str = render_print_form_html(data)
    except Exception as exc:
        return no_update, True, "", f"Ошибка формирования: {exc}", "danger", True

    n_tables = sum(len(s.get("tables") or []) for s in data.get("sections") or [])
    missing = data.get("missing") or []
    status = (
        f"Бланк готов: разделов {len(data.get('sections') or [])}, "
        f"таблиц {n_tables}. Год {year}, месяц {reporting_month}."
    )
    alert_msg = "Бланк сформирован"
    alert_color = "success"
    if missing:
        miss_txt = "; ".join(
            f"{m.get('short_title')} (id={m.get('indicator_id')})" for m in missing
        )
        status += f" Пропущены без плана корпусов: {miss_txt}."
        if n_tables == 0:
            alert_msg = (
                f"Нет данных. Выбранные индикаторы без плана по корпусам: {miss_txt}. "
                "Удалите строку и добавьте индикатор с пометкой «есть корпуса» "
                "(для Неотложки это id=4, не «на дому»)."
            )
            alert_color = "warning"
        else:
            alert_msg = f"Бланк сформирован, но часть индикаторов пропущена: {miss_txt}"
            alert_color = "warning"
    preview = html.Div(
        dcc.Markdown(html_str, dangerously_allow_html=True),
        className="pvf-preview-inner",
    )
    return preview, n_tables == 0, status, alert_msg, alert_color, True


app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }
        window.print();
        return n_clicks;
    }
    """,
    Output(f"store-print-tick-{type_page_print}", "data"),
    Input(f"btn-print-{type_page_print}", "n_clicks"),
    prevent_initial_call=True,
)
