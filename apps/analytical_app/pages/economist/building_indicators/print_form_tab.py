"""Вкладка «Печатная форма»: параметры → макет → превью/печать."""
from __future__ import annotations

import ast
import json

import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import filter_years
from apps.analytical_app.pages.economist.building_indicators.query import (
    DEFAULT_PRINT_CONFIG,
    MAX_PRINT_SECTIONS,
    MIN_PRINT_SECTIONS,
    PLAN_KIND_OPTIONS,
    delete_print_template,
    get_print_template,
    list_indicator_options,
    list_print_templates,
    normalize_print_config,
    save_print_template,
)
from apps.plan.services.print_form_engine import (
    build_print_form_data,
    render_print_form_html,
)

type_page_print = "econ-building-indicators-print"

PAYMENT_OPTIONS_OPEN = [
    {"label": "Предъявл. + оплач.", "value": "presented"},
    {"label": "Предъявленные (2, 3)", "value": "presented_2_3"},
]
PAYMENT_OPTIONS_CLOSED = [
    {"label": "Оплаченные (3)", "value": "paid"},
]

SECTION_PRESETS = [
    "Лечебно-диагностическая работа",
    "Профилактическая работа",
]


def _short_label_from_option(label: str, indicator_id) -> str:
    if not label:
        return str(indicator_id)
    return label.split("  [")[0].split(" \\ ")[-1]


def _parse_dash_id(raw: str):
    if not raw or not isinstance(raw, str) or not raw.startswith("{"):
        return raw
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw


def _count_items(config: dict) -> int:
    return sum(len(s.get("items") or []) for s in (config or {}).get("sections") or [])


def _missing_ids(missing: list | None) -> set[int]:
    out: set[int] = set()
    for m in missing or []:
        try:
            out.add(int(m.get("indicator_id")))
        except (TypeError, ValueError):
            pass
    return out


def _indicator_label_map(indicator_options) -> dict[int, str]:
    out: dict[int, str] = {}
    for opt in indicator_options or []:
        try:
            out[int(opt.get("value"))] = str(opt.get("label") or "")
        except (TypeError, ValueError):
            continue
    return out


def _render_indicator_row(
    sec_idx: int,
    i: int,
    it: dict,
    *,
    missing_ids: set[int],
    label_map: dict[int, str],
) -> html.Div:
    iid = it.get("indicator_id")
    skipped = False
    try:
        iid_int = int(iid)
        skipped = iid_int in missing_ids
    except (TypeError, ValueError):
        iid_int = iid

    full_label = (it.get("source_label") or "").strip()
    if not full_label and isinstance(iid_int, int):
        full_label = label_map.get(iid_int) or ""
    if not full_label:
        full_label = f"Индикатор #{iid}"
    tip = f"{full_label}" if str(iid) in full_label else f"{full_label}\n(id {iid})"

    return html.Div(
        [
            html.Span(f"{i + 1}.", className="pvf-ind-num text-muted"),
            dbc.Input(
                id={"type": "pvf-item-title", "sec": sec_idx, "idx": i},
                value=it.get("short_title") or "",
                placeholder="Подпись на бланке",
                debounce=True,
                size="sm",
                className="pvf-ind-title",
            ),
            html.Button(
                "i",
                type="button",
                className="pvf-ind-info",
                title=tip,
                **{"aria-label": tip},
            ),
            html.Span("нет плана", className="badge bg-warning text-dark pvf-ind-warn")
            if skipped
            else html.Span(className="pvf-ind-warn"),
            html.Div(
                dbc.Checklist(
                    id={"type": "pvf-item-year", "sec": sec_idx, "idx": i},
                    options=[{"label": "% года", "value": 1}],
                    value=[1] if it.get("show_of_year") else [],
                    switch=True,
                    inline=True,
                    className="pvf-editor-year-switch mb-0",
                ),
                className="pvf-ind-year",
            ),
            dbc.ButtonGroup(
                [
                    dbc.Button("↑", id={"type": "pvf-item-up", "sec": sec_idx, "idx": i}, color="light", size="sm", title="Выше"),
                    dbc.Button("↓", id={"type": "pvf-item-down", "sec": sec_idx, "idx": i}, color="light", size="sm", title="Ниже"),
                    dbc.Button("×", id={"type": "pvf-item-del", "sec": sec_idx, "idx": i}, color="outline-danger", size="sm", title="Убрать"),
                ],
                size="sm",
                className="pvf-ind-btns",
            ),
        ],
        className="pvf-ind-row" + (" pvf-editor-item-warn" if skipped else ""),
    )


def _render_section_card(
    sec_idx: int,
    section: dict,
    *,
    n_sections: int,
    missing_ids: set[int],
    label_map: dict[int, str],
) -> dbc.Card:
    title = section.get("title") or "Раздел"
    items = section.get("items") or []
    try:
        item_columns = max(1, min(4, int(section.get("item_columns") or 2)))
    except (TypeError, ValueError):
        item_columns = 2

    rows = [
        _render_indicator_row(sec_idx, i, it, missing_ids=missing_ids, label_map=label_map)
        for i, it in enumerate(items)
    ]
    if not rows:
        rows = [html.Div("Пока пусто — добавьте индикатор ниже", className="text-muted small py-2")]

    can_delete = n_sections > MIN_PRINT_SECTIONS
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(f"№{sec_idx + 1}", className="badge bg-primary me-2"),
                    dbc.Input(
                        id={"type": "pvf-sec-title", "sec": sec_idx},
                        value=title,
                        debounce=True,
                        className="pvf-editor-sec-title",
                        size="sm",
                    ),
                    dbc.Badge(f"{len(items)} инд.", color="secondary", className="ms-2"),
                    dbc.Button(
                        "Удалить раздел",
                        id={"type": "pvf-sec-del", "sec": sec_idx},
                        color="link",
                        size="sm",
                        className="ms-2 text-danger p-0" + ("" if can_delete else " d-none"),
                        disabled=not can_delete,
                    ),
                ],
                className="d-flex align-items-center gap-1 py-2",
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Таблиц индикаторов в ряду", className="small fw-semibold mb-1"),
                                    dcc.Dropdown(
                                        id={"type": "pvf-sec-cols", "sec": sec_idx},
                                        options=[
                                            {"label": "1 — столбиком", "value": 1},
                                            {"label": "2 рядом", "value": 2},
                                            {"label": "3 рядом", "value": 3},
                                            {"label": "4 рядом", "value": 4},
                                        ],
                                        value=item_columns,
                                        clearable=False,
                                    ),
                                ],
                                xs=12,
                                md=4,
                            ),
                            dbc.Col(
                                html.Small(
                                    "Порядок списка сверху вниз = порядок на бланке "
                                    f"(при «{item_columns} рядом» — слева направо).",
                                    className="text-muted",
                                ),
                                xs=12,
                                md=8,
                                className="d-flex align-items-end",
                            ),
                        ],
                        className="g-2 mb-3",
                    ),
                    html.Div(rows, className="pvf-ind-list mb-3"),
                    html.Hr(className="my-2"),
                    html.Div(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id={"type": "pvf-sec-add-ind", "sec": sec_idx},
                                        options=[],
                                        placeholder="Выберите индикатор…",
                                        clearable=True,
                                        className="pvf-add-ind-dd",
                                    ),
                                    xs=12,
                                    md=5,
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id={"type": "pvf-sec-add-title", "sec": sec_idx},
                                        placeholder="Короткая подпись (необяз.)",
                                        debounce=True,
                                        size="sm",
                                    ),
                                    xs=12,
                                    md=3,
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        id={"type": "pvf-sec-add-year", "sec": sec_idx},
                                        options=[{"label": "% от года", "value": 1}],
                                        value=[],
                                        switch=True,
                                        inline=True,
                                        className="mb-0",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Добавить",
                                        id={"type": "pvf-sec-add-btn", "sec": sec_idx},
                                        color="primary",
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-2 align-items-center",
                        ),
                        className="pvf-sec-add-row",
                    ),
                ],
                className="pt-2 pvf-sec-body",
            ),
        ],
        className="pvf-editor-section shadow-sm mb-3",
    )


def render_layout_editor(
    config: dict,
    missing: list | None = None,
    indicator_options=None,
) -> html.Div:
    cfg = normalize_print_config(config)
    sections = cfg.get("sections") or []
    miss = _missing_ids(missing)
    n = len(sections)
    page_cols = int(cfg.get("page_columns") or 2)
    label_map = _indicator_label_map(indicator_options)

    cards = [
        _render_section_card(
            idx, sec, n_sections=n, missing_ids=miss, label_map=label_map
        )
        for idx, sec in enumerate(sections)
    ]

    hint = dbc.Alert(
        [
            html.Div(
                [
                    html.Strong("Макет → Предпросмотр → Сохранить. "),
                    "Предпросмотр не сохраняет шаблон — только показывает бланк. ",
                    f"На печати разделы в {page_cols} столбца(ов); "
                    "внутри раздела таблицы — по «в ряду».",
                ]
            ),
        ],
        color="light",
        className="small mb-3 border",
    )

    toolbar = html.Div(
        [
            dbc.Button(
                "+ Добавить раздел",
                id=f"btn-print-add-section-{type_page_print}",
                color="primary",
                outline=True,
                size="sm",
                className="me-2",
                disabled=n >= MAX_PRINT_SECTIONS,
            ),
            html.Span(
                f"Разделов: {n}"
                + (f" (лимит {MAX_PRINT_SECTIONS})" if n >= MAX_PRINT_SECTIONS else ""),
                className="text-muted small",
            ),
        ],
        className="mb-3 d-flex align-items-center flex-wrap gap-1",
    )

    if not cards:
        return html.Div([hint, toolbar, html.Div("Нет разделов", className="text-muted")])

    return html.Div([hint, toolbar, html.Div(cards, className="pvf-editor-list")])


def _field(label, control, hint=None):
    kids = [html.Label(label, className="fw-semibold small mb-0"), control]
    if hint is not None:
        kids.append(hint)
    return html.Div(kids, className="mb-2")


def _preview_iframe(html_str: str, orientation: str) -> html.Iframe:
    """Превью через iframe — Markdown/innerHTML в Dash ненадёжны."""
    orient = orientation if orientation in ("landscape", "portrait") else "landscape"
    page = "A4 landscape" if orient == "landscape" else "A4 portrait"
    doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        "<link rel='stylesheet' href='/assets/css/print_volume_form.css'/>"
        f"<style>html,body{{margin:0;padding:10px;background:#fff;}}"
        f"@media print{{@page{{size:{page};margin:8mm;}}}}</style>"
        f"</head><body>{html_str}</body></html>"
    )
    return html.Iframe(
        srcDoc=doc,
        className="pvf-preview-iframe",
        style={
            "width": "100%",
            "minHeight": "720px",
            "height": "75vh",
            "border": "0",
            "background": "#fff",
            "borderRadius": "0.35rem",
        },
    )


def print_form_tab(indicators, month_options, month_num):
    templates = list_print_templates()
    initial_config = normalize_print_config(DEFAULT_PRINT_CONFIG)

    left = dbc.Card(
        dbc.CardBody(
            [
                html.Div("Параметры бланка", className="fw-semibold mb-2"),
                _field(
                    "Шаблон",
                    dcc.Dropdown(
                        id=f"dropdown-print-template-{type_page_print}",
                        options=templates,
                        placeholder="Не выбран",
                        clearable=True,
                    ),
                ),
                _field("Год", filter_years(type_page_print)),
                _field(
                    "Месяц",
                    dcc.Dropdown(
                        id=f"dropdown-reporting-month-{type_page_print}",
                        options=month_options,
                        value=month_num,
                        clearable=False,
                    ),
                ),
                _field(
                    "Факт",
                    dcc.Dropdown(
                        id=f"dropdown-payment-{type_page_print}",
                        options=PAYMENT_OPTIONS_OPEN,
                        value="presented",
                        clearable=False,
                    ),
                ),
                dbc.Collapse(
                    [
                        _field(
                            "Метрика",
                            dcc.Dropdown(
                                id=f"dropdown-metric-{type_page_print}",
                                options=[
                                    {"label": "Объёмы", "value": "volumes"},
                                    {"label": "Финансы", "value": "finance"},
                                ],
                                value="volumes",
                                clearable=False,
                            ),
                        ),
                        _field(
                            "Версия плана",
                            dcc.Dropdown(
                                id=f"dropdown-plan-kind-{type_page_print}",
                                options=PLAN_KIND_OPTIONS,
                                value="internal",
                                clearable=False,
                            ),
                        ),
                        dbc.Switch(
                            id=f"switch-period-closed-{type_page_print}",
                            label="Период закрыт (только оплаченные)",
                            value=False,
                            className="mb-3",
                        ),
                    ],
                    id=f"collapse-print-advanced-{type_page_print}",
                    is_open=False,
                ),
                dbc.Button(
                    "Дополнительно ▾",
                    id=f"btn-toggle-print-advanced-{type_page_print}",
                    color="link",
                    size="sm",
                    className="px-0 mb-2",
                ),
                html.Hr(className="my-2"),
                _field(
                    "Столбцов разделов на листе",
                    dcc.Dropdown(
                        id=f"dropdown-print-page-columns-{type_page_print}",
                        options=[
                            {"label": "1 — друг под другом", "value": 1},
                            {"label": "2 — два рядом", "value": 2},
                            {"label": "3 рядом", "value": 3},
                            {"label": "4 рядом", "value": 4},
                        ],
                        value=initial_config.get("page_columns") or 2,
                        clearable=False,
                    ),
                    html.Small(
                        "Сколько столбцов для разделов на печати. Не путать с таблицами внутри раздела.",
                        className="text-muted",
                    ),
                ),
                _field(
                    "Таблиц в ряду (по умолчанию)",
                    dcc.Dropdown(
                        id=f"dropdown-print-columns-{type_page_print}",
                        options=[
                            {"label": "1", "value": 1},
                            {"label": "2", "value": 2},
                            {"label": "3", "value": 3},
                            {"label": "4", "value": 4},
                        ],
                        value=initial_config.get("columns") or 2,
                        clearable=False,
                    ),
                    html.Small("Для новых разделов. У каждого раздела можно задать своё.", className="text-muted"),
                ),
                _field(
                    "Ориентация печати",
                    dcc.Dropdown(
                        id=f"dropdown-print-orientation-{type_page_print}",
                        options=[
                            {"label": "Альбомная (A4)", "value": "landscape"},
                            {"label": "Книжная (A4)", "value": "portrait"},
                        ],
                        value=initial_config.get("page_orientation") or "landscape",
                        clearable=False,
                    ),
                ),
                dbc.Button(
                    "Предпросмотр",
                    id=f"btn-generate-print-{type_page_print}",
                    color="success",
                    className="w-100 mt-1",
                ),
                html.Small(
                    "Не сохраняет шаблон — только показывает бланк внизу.",
                    className="text-muted d-block mt-1 mb-1",
                ),
                dbc.Button(
                    "Печать",
                    id=f"btn-print-{type_page_print}",
                    color="primary",
                    outline=True,
                    disabled=True,
                    className="w-100 mt-1",
                ),
                html.Div(id=f"status-{type_page_print}", className="text-muted small mt-3"),
            ],
            className="py-3 px-3",
        ),
        className="mb-3 pvf-filters-card d-print-none",
    )

    right = html.Div(
        [
            dbc.Alert(id=f"alert-{type_page_print}", is_open=False, duration=10000, className="mb-2 d-print-none"),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Макет", className="fw-semibold mb-1"),
                        html.P(
                            "Правите макет → «Предпросмотр» (не сохраняет) → при необходимости «Сохранить» шаблон. "
                            "Печать — из готового превью.",
                            className="text-muted small mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.Input(
                                                id=f"input-print-template-name-{type_page_print}",
                                                placeholder="Название шаблона",
                                                type="text",
                                            ),
                                            dbc.Button(
                                                "Сохранить",
                                                id=f"btn-save-print-tpl-{type_page_print}",
                                                color="primary",
                                            ),
                                        ],
                                        size="sm",
                                    ),
                                    xs=12,
                                    md=5,
                                ),
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Как новый",
                                                id=f"btn-save-as-print-tpl-{type_page_print}",
                                                color="outline-primary",
                                                size="sm",
                                            ),
                                            dbc.Button(
                                                "Удалить шаблон",
                                                id=f"btn-delete-print-tpl-{type_page_print}",
                                                color="outline-danger",
                                                size="sm",
                                            ),
                                        ]
                                    ),
                                    xs=12,
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Предпросмотр",
                                        id=f"btn-preview-print-{type_page_print}",
                                        color="success",
                                        size="sm",
                                        className="w-100",
                                    ),
                                    xs=12,
                                    md=3,
                                ),
                            ],
                            className="g-2 align-items-center mb-2",
                        ),
                        html.Small(
                            "Предпросмотр не сохраняет шаблон. Сохраните, когда макет устраивает.",
                            className="text-muted d-block mb-3",
                        ),
                        html.Div(
                            dbc.Button(id=f"btn-load-print-tpl-{type_page_print}", n_clicks=0, className="d-none"),
                            className="d-none",
                        ),
                        html.Div(
                            id=f"print-layout-editor-{type_page_print}",
                            children=render_layout_editor(initial_config),
                        ),
                    ]
                ),
                className="mb-3 shadow-sm d-print-none",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.Div("Превью бланка", className="fw-semibold"),
                                html.Span(
                                    id=f"preview-badge-{type_page_print}",
                                    className="badge bg-light text-muted ms-2",
                                ),
                            ],
                            className="d-flex align-items-center mb-2 d-print-none",
                        ),
                        html.Div(
                            id="print-volume-form-preview",
                            children=html.Div(
                                [
                                    html.Div("Бланк ещё не сформирован", className="fw-semibold mb-1"),
                                    html.Div(
                                        "Соберите макет и нажмите «Сформировать бланк».",
                                        className="text-muted small",
                                    ),
                                ],
                                className="pvf-empty-state text-center p-5",
                            ),
                        ),
                    ]
                ),
                className="mb-2 shadow-sm border-0",
            ),
        ]
    )

    return html.Div(
        [
            dcc.Store(id=f"store-print-template-id-{type_page_print}"),
            dcc.Store(id=f"store-print-tick-{type_page_print}"),
            dcc.Store(id=f"store-print-config-{type_page_print}", data=initial_config),
            dcc.Store(id=f"store-print-missing-{type_page_print}", data=[]),
            dcc.Store(id=f"store-print-indicator-options-{type_page_print}", data=indicators or []),
            dbc.Row(
                [
                    dbc.Col(left, xs=12, lg=3, className="mb-3"),
                    dbc.Col(right, xs=12, lg=9),
                ],
                className="g-3 align-items-start",
            ),
        ],
        className="pvf-page",
    )


# —— callbacks ——

@app.callback(
    Output(f"collapse-print-advanced-{type_page_print}", "is_open"),
    Output(f"btn-toggle-print-advanced-{type_page_print}", "children"),
    Input(f"btn-toggle-print-advanced-{type_page_print}", "n_clicks"),
    State(f"collapse-print-advanced-{type_page_print}", "is_open"),
    prevent_initial_call=True,
)
def toggle_print_advanced(n_clicks, is_open):
    opened = not bool(is_open)
    return opened, ("Дополнительно ▴" if opened else "Дополнительно ▾")


@app.callback(
    Output(f"store-print-indicator-options-{type_page_print}", "data"),
    Output({"type": "pvf-sec-add-ind", "sec": ALL}, "options"),
    Input(f"dropdown-year-{type_page_print}", "value"),
    Input(f"dropdown-plan-kind-{type_page_print}", "value"),
    Input(f"print-layout-editor-{type_page_print}", "children"),
)
def refresh_print_indicators(year, plan_kind, _editor_children):
    if not year:
        raise PreventUpdate
    options = list_indicator_options(
        int(year),
        for_editor=True,
        only_with_building_plan=True,
        plan_kind=plan_kind or "internal",
    )
    n = len(callback_context.outputs_list[1]) if callback_context.outputs_list else 0
    return options, [options] * n


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
    Output(f"print-layout-editor-{type_page_print}", "children"),
    Output(f"store-print-config-{type_page_print}", "data"),
    Output(f"dropdown-print-columns-{type_page_print}", "value"),
    Output(f"dropdown-print-page-columns-{type_page_print}", "value"),
    Output(f"dropdown-print-orientation-{type_page_print}", "value"),
    Output(f"input-print-template-name-{type_page_print}", "value"),
    Output(f"store-print-template-id-{type_page_print}", "data"),
    Output(f"dropdown-print-template-{type_page_print}", "options"),
    Output(f"dropdown-print-template-{type_page_print}", "value", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "children"),
    Output(f"alert-{type_page_print}", "color"),
    Output(f"alert-{type_page_print}", "is_open"),
    Input(f"btn-load-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-save-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-save-as-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-delete-print-tpl-{type_page_print}", "n_clicks"),
    Input(f"btn-print-add-section-{type_page_print}", "n_clicks"),
    Input({"type": "pvf-sec-add-btn", "sec": ALL}, "n_clicks"),
    Input({"type": "pvf-item-del", "sec": ALL, "idx": ALL}, "n_clicks"),
    Input({"type": "pvf-item-up", "sec": ALL, "idx": ALL}, "n_clicks"),
    Input({"type": "pvf-item-down", "sec": ALL, "idx": ALL}, "n_clicks"),
    Input({"type": "pvf-sec-del", "sec": ALL}, "n_clicks"),
    Input({"type": "pvf-sec-cols", "sec": ALL}, "value"),
    Input(f"dropdown-print-columns-{type_page_print}", "value"),
    Input(f"dropdown-print-page-columns-{type_page_print}", "value"),
    Input(f"dropdown-print-orientation-{type_page_print}", "value"),
    State(f"dropdown-print-template-{type_page_print}", "value"),
    State(f"store-print-template-id-{type_page_print}", "data"),
    State(f"input-print-template-name-{type_page_print}", "value"),
    State(f"store-print-config-{type_page_print}", "data"),
    State(f"store-print-missing-{type_page_print}", "data"),
    State(f"store-print-indicator-options-{type_page_print}", "data"),
    State({"type": "pvf-sec-add-ind", "sec": ALL}, "value"),
    State({"type": "pvf-sec-add-title", "sec": ALL}, "value"),
    State({"type": "pvf-sec-add-year", "sec": ALL}, "value"),
    State(f"dropdown-print-columns-{type_page_print}", "value"),
    State(f"dropdown-print-page-columns-{type_page_print}", "value"),
    State(f"dropdown-print-orientation-{type_page_print}", "value"),
    prevent_initial_call=True,
)
def manage_print_layout(
    n_load,
    n_save,
    n_save_as,
    n_delete,
    n_add_sec,
    n_add_btns,
    n_dels,
    n_ups,
    n_downs,
    n_sec_dels,
    n_sec_cols,
    columns_in,
    page_columns_in,
    orientation_in,
    selected_tpl,
    stored_id,
    tpl_name,
    config,
    missing,
    indicator_options,
    add_inds,
    add_titles,
    add_years,
    columns,
    page_columns,
    orientation,
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    templates = list_print_templates()
    cfg = normalize_print_config(config)
    columns = int(columns or cfg.get("columns") or 2)
    page_columns = int(page_columns or cfg.get("page_columns") or 2)
    orientation = orientation or cfg.get("page_orientation") or "landscape"

    def _ok(
        editor_cfg,
        *,
        name=no_update,
        tid=no_update,
        tpl_val=no_update,
        msg="",
        color="success",
        open_alert=False,
        cols=no_update,
        page_cols=no_update,
        orient=no_update,
        refresh_editor=True,
    ):
        editor_cfg = normalize_print_config(editor_cfg)
        if cols not in (no_update, None):
            editor_cfg["columns"] = int(cols)
        else:
            editor_cfg["columns"] = int(columns)
        if page_cols not in (no_update, None):
            editor_cfg["page_columns"] = int(page_cols)
        else:
            editor_cfg["page_columns"] = int(page_columns)
        editor_cfg["page_orientation"] = (
            orient if orient not in (no_update, None) else orientation
        )
        editor_cfg = normalize_print_config(editor_cfg)
        return (
            render_layout_editor(editor_cfg, missing, indicator_options)
            if refresh_editor
            else no_update,
            editor_cfg,
            editor_cfg["columns"],
            editor_cfg["page_columns"],
            editor_cfg["page_orientation"],
            name,
            tid,
            templates,
            tpl_val,
            msg,
            color,
            open_alert,
        )

    if trigger_id in (
        f"dropdown-print-columns-{type_page_print}",
        f"dropdown-print-page-columns-{type_page_print}",
        f"dropdown-print-orientation-{type_page_print}",
    ):
        cfg["columns"] = int(columns_in or columns or 2)
        cfg["page_columns"] = int(page_columns_in or page_columns or 2)
        cfg["page_orientation"] = orientation_in or orientation or "landscape"
        cfg = normalize_print_config(cfg)
        # page_columns меняет подсказку в редакторе
        refresh = trigger_id == f"dropdown-print-page-columns-{type_page_print}"
        return _ok(cfg, refresh_editor=refresh)

    if trigger_id == f"btn-load-print-tpl-{type_page_print}":
        if not selected_tpl:
            return _ok(cfg, msg="Выберите шаблон", color="warning", open_alert=True)
        data = get_print_template(int(selected_tpl))
        if not data:
            return _ok(cfg, msg="Шаблон не найден", color="danger", open_alert=True)
        loaded = data["config"]
        return _ok(
            loaded,
            name=data["name"],
            tid=data["id"],
            tpl_val=data["id"],
            msg=f"Загружен «{data['name']}» — нажмите «Сформировать бланк»",
            color="success",
            open_alert=True,
            cols=loaded.get("columns"),
            page_cols=loaded.get("page_columns"),
            orient=loaded.get("page_orientation"),
        )

    if trigger_id == f"btn-save-as-print-tpl-{type_page_print}":
        name = (tpl_name or "").strip()
        if not name:
            return _ok(cfg, msg="Укажите название шаблона", color="warning", open_alert=True)
        try:
            new_id = save_print_template(name, cfg)
        except Exception as exc:
            return _ok(cfg, msg=f"Ошибка: {exc}", color="danger", open_alert=True)
        templates = list_print_templates()
        return (
            no_update, cfg, no_update, no_update, no_update, name, new_id, templates, new_id,
            f"Создан «{name}»", "success", True,
        )

    if trigger_id == f"btn-save-print-tpl-{type_page_print}":
        name = (tpl_name or "").strip()
        if not name:
            return _ok(cfg, msg="Укажите название шаблона", color="warning", open_alert=True)
        pid = stored_id or selected_tpl
        try:
            new_id = save_print_template(name, cfg, template_id=int(pid) if pid else None)
        except Exception as exc:
            return _ok(cfg, msg=f"Ошибка: {exc}", color="danger", open_alert=True)
        templates = list_print_templates()
        return (
            no_update, cfg, no_update, no_update, no_update, name, new_id, templates, new_id,
            f"Сохранён «{name}»", "success", True,
        )

    if trigger_id == f"btn-delete-print-tpl-{type_page_print}":
        pid = selected_tpl or stored_id
        if not pid:
            return _ok(cfg, msg="Нечего удалять", color="warning", open_alert=True)
        try:
            delete_print_template(int(pid))
        except Exception as exc:
            return _ok(cfg, msg=f"Ошибка: {exc}", color="danger", open_alert=True)
        templates = list_print_templates()
        empty = normalize_print_config(DEFAULT_PRINT_CONFIG)
        return _ok(
            empty,
            name="",
            tid=None,
            tpl_val=None,
            msg="Шаблон удалён",
            color="success",
            open_alert=True,
            cols=empty.get("columns"),
            page_cols=empty.get("page_columns"),
            orient=empty.get("page_orientation"),
        )

    if trigger_id == f"btn-print-add-section-{type_page_print}":
        sections = list(cfg.get("sections") or [])
        if len(sections) >= MAX_PRINT_SECTIONS:
            return _ok(cfg, msg=f"Слишком много разделов (макс. {MAX_PRINT_SECTIONS})", color="warning", open_alert=True)
        preset = SECTION_PRESETS[len(sections)] if len(sections) < len(SECTION_PRESETS) else f"Раздел {len(sections) + 1}"
        sections.append(
            {
                "title": preset,
                "item_columns": int(cfg.get("columns") or 2),
                "items": [],
            }
        )
        cfg["sections"] = sections
        return _ok(cfg)

    tid = _parse_dash_id(trigger_id)
    if isinstance(tid, dict):
        t = tid.get("type")
        sec = int(tid.get("sec", 0))
        idx = tid.get("idx")
        sections = list(cfg.get("sections") or [])
        if sec < 0 or sec >= len(sections):
            raise PreventUpdate
        items = list(sections[sec].get("items") or [])

        if t == "pvf-sec-cols":
            try:
                new_cols = max(1, min(4, int(ctx.triggered[0]["value"])))
            except (TypeError, ValueError):
                raise PreventUpdate
            if int(sections[sec].get("item_columns") or 0) == new_cols:
                raise PreventUpdate
            sections[sec]["item_columns"] = new_cols
            cfg["sections"] = sections
            return _ok(cfg)

        if t == "pvf-sec-add-btn":
            ind_val = add_inds[sec] if sec < len(add_inds or []) else None
            title_val = (add_titles[sec] or "") if sec < len(add_titles or []) else ""
            year_val = (add_years[sec] or []) if sec < len(add_years or []) else []
            if not ind_val:
                return _ok(cfg, msg="Выберите индикатор", color="warning", open_alert=True)
            label = next((o.get("label") for o in (indicator_options or []) if o.get("value") == ind_val), "")
            short = (title_val or "").strip() or _short_label_from_option(label, ind_val)
            items.append(
                {
                    "indicator_id": int(ind_val),
                    "short_title": short,
                    "show_of_year": 1 in (year_val or []),
                    "source_label": (label or "").strip(),
                }
            )
            sections[sec]["items"] = items
            cfg["sections"] = sections
            return _ok(cfg)

        if t == "pvf-item-del" and idx is not None:
            idx = int(idx)
            if 0 <= idx < len(items):
                items.pop(idx)
            sections[sec]["items"] = items
            cfg["sections"] = sections
            return _ok(cfg)

        if t == "pvf-item-up" and idx is not None:
            idx = int(idx)
            if idx > 0:
                items[idx - 1], items[idx] = items[idx], items[idx - 1]
            sections[sec]["items"] = items
            cfg["sections"] = sections
            return _ok(cfg)

        if t == "pvf-item-down" and idx is not None:
            idx = int(idx)
            if idx < len(items) - 1:
                items[idx + 1], items[idx] = items[idx], items[idx + 1]
            sections[sec]["items"] = items
            cfg["sections"] = sections
            return _ok(cfg)

        if t == "pvf-sec-del":
            if len(sections) <= MIN_PRINT_SECTIONS:
                return _ok(cfg, msg="Нужен хотя бы один раздел", color="warning", open_alert=True)
            sections.pop(sec)
            cfg["sections"] = sections
            return _ok(cfg)

    raise PreventUpdate


@app.callback(
    Output(f"store-print-config-{type_page_print}", "data", allow_duplicate=True),
    Input({"type": "pvf-sec-title", "sec": ALL}, "value"),
    Input({"type": "pvf-item-title", "sec": ALL, "idx": ALL}, "value"),
    Input({"type": "pvf-item-year", "sec": ALL, "idx": ALL}, "value"),
    State(f"store-print-config-{type_page_print}", "data"),
    prevent_initial_call=True,
)
def sync_print_inline_edits(sec_titles, item_titles, item_years, config):
    """Только изменённое поле — иначе после удаления раздела старый store «возвращает» разделы."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    tid = _parse_dash_id(ctx.triggered[0]["prop_id"].split(".")[0])
    if not isinstance(tid, dict):
        raise PreventUpdate
    cfg = normalize_print_config(config)
    sections = list(cfg.get("sections") or [])
    t = tid.get("type")
    sec = int(tid.get("sec", -1))
    if sec < 0 or sec >= len(sections):
        raise PreventUpdate
    if t == "pvf-sec-title":
        sections[sec]["title"] = (ctx.triggered[0]["value"] or "").strip() or f"Раздел {sec + 1}"
    elif t in ("pvf-item-title", "pvf-item-year"):
        idx = int(tid.get("idx", -1))
        items = list(sections[sec].get("items") or [])
        if not (0 <= idx < len(items)):
            raise PreventUpdate
        if t == "pvf-item-title":
            val = ctx.triggered[0]["value"]
            items[idx]["short_title"] = (val or "").strip() or str(items[idx].get("indicator_id"))
        else:
            items[idx]["show_of_year"] = 1 in (ctx.triggered[0]["value"] or [])
        sections[sec]["items"] = items
    else:
        raise PreventUpdate
    cfg["sections"] = sections
    return cfg


@app.callback(
    Output("print-volume-form-preview", "children"),
    Output(f"btn-print-{type_page_print}", "disabled"),
    Output(f"status-{type_page_print}", "children"),
    Output(f"preview-badge-{type_page_print}", "children"),
    Output(f"store-print-missing-{type_page_print}", "data"),
    Output(f"alert-{type_page_print}", "children", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "color", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "is_open", allow_duplicate=True),
    Input(f"btn-generate-print-{type_page_print}", "n_clicks"),
    Input(f"btn-preview-print-{type_page_print}", "n_clicks"),
    State(f"dropdown-year-{type_page_print}", "value"),
    State(f"dropdown-reporting-month-{type_page_print}", "value"),
    State(f"dropdown-metric-{type_page_print}", "value"),
    State(f"dropdown-plan-kind-{type_page_print}", "value"),
    State(f"dropdown-payment-{type_page_print}", "value"),
    State(f"switch-period-closed-{type_page_print}", "value"),
    State(f"store-print-config-{type_page_print}", "data"),
    State(f"dropdown-print-columns-{type_page_print}", "value"),
    State(f"dropdown-print-page-columns-{type_page_print}", "value"),
    State(f"dropdown-print-orientation-{type_page_print}", "value"),
    prevent_initial_call=True,
)
def generate_print_form(
    n_clicks,
    n_preview,
    year,
    reporting_month,
    metric,
    plan_kind,
    payment,
    period_closed,
    config,
    columns,
    page_columns,
    orientation,
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    if not (n_clicks or n_preview):
        raise PreventUpdate
    if not year or not reporting_month:
        return no_update, True, "", "", no_update, "Укажите год и месяц", "warning", True

    cfg = normalize_print_config(config)
    cfg["columns"] = int(columns or cfg.get("columns") or 2)
    cfg["page_columns"] = int(page_columns or cfg.get("page_columns") or 2)
    cfg["page_orientation"] = orientation or cfg.get("page_orientation") or "landscape"
    cfg = normalize_print_config(cfg)

    if _count_items(cfg) == 0:
        return (
            no_update, True, "", "", no_update,
            "Добавьте хотя бы один индикатор в раздел",
            "warning", True,
        )

    try:
        data = build_print_form_data(
            year=int(year),
            reporting_month=int(reporting_month),
            config=cfg,
            payment_type=payment or "presented",
            period_closed=bool(period_closed),
            metric=metric or "volumes",
            plan_kind=plan_kind or "internal",
        )
        html_str = render_print_form_html(data)
    except Exception as exc:
        return no_update, True, "", "", no_update, f"Ошибка: {exc}", "danger", True

    n_tables = sum(len(s.get("tables") or []) for s in data.get("sections") or [])
    n_secs = len(cfg.get("sections") or [])
    missing = data.get("missing") or []
    generated = (data.get("header") or {}).get("generated_at") or ""
    orient_label = "альбом" if cfg.get("page_orientation") == "landscape" else "книга"
    page_cols = int(cfg.get("page_columns") or 2)
    status = (
        f"Превью: {n_tables} табл. · {n_secs} разд. · {page_cols} ст. · "
        f"{reporting_month}/{year} · {orient_label}"
        + (f" · {generated}" if generated else "")
        + " · макет не трогали, шаблон не сохраняли"
    )
    badge = f"{n_tables} табл. · {page_cols} ст. · {orient_label}"

    if missing:
        lines = [
            html.Div("Не попали в бланк:", className="mb-1"),
            html.Ul(
                [
                    html.Li(f"{m.get('short_title')} (id={m.get('indicator_id')}) — {m.get('reason')}")
                    for m in missing
                ],
                className="mb-0 ps-3",
            ),
        ]
        alert_msg = html.Div(lines)
        alert_color = "warning"
        if n_tables == 0:
            badge = "нет данных"
        status += f" · пропущено {len(missing)}"
    else:
        alert_msg = (
            f"Превью готово ({generated}). Сохраните шаблон, если нужно зафиксировать макет."
            if generated
            else "Превью готово."
        )
        alert_color = "success"

    # Важно: макет справа НЕ пересобираем — иначе разделы «откатываются»
    preview = _preview_iframe(html_str, cfg.get("page_orientation") or "landscape")
    return preview, n_tables == 0, status, badge, missing, alert_msg, alert_color, True


app.clientside_callback(
    """
    function(n_clicks, orientation) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }
        var iframe = document.querySelector('#print-volume-form-preview iframe');
        if (iframe && iframe.contentWindow) {
            try {
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
                return n_clicks;
            } catch (e) {}
        }
        var orient = orientation || 'landscape';
        var size = (orient === 'portrait') ? 'A4 portrait' : 'A4 landscape';
        var style = document.getElementById('pvf-print-page-style');
        if (!style) {
            style = document.createElement('style');
            style.id = 'pvf-print-page-style';
            document.head.appendChild(style);
        }
        style.textContent = '@media print { @page { size: ' + size + '; margin: 8mm; } }';
        document.body.setAttribute('data-pvf-orientation', orient);
        setTimeout(function() { window.print(); }, 50);
        return n_clicks;
    }
    """,
    Output(f"store-print-tick-{type_page_print}", "data"),
    Input(f"btn-print-{type_page_print}", "n_clicks"),
    State(f"dropdown-print-orientation-{type_page_print}", "value"),
    prevent_initial_call=True,
)


@app.callback(
    Output(f"print-layout-editor-{type_page_print}", "children", allow_duplicate=True),
    Output(f"store-print-config-{type_page_print}", "data", allow_duplicate=True),
    Output(f"dropdown-print-columns-{type_page_print}", "value", allow_duplicate=True),
    Output(f"dropdown-print-page-columns-{type_page_print}", "value", allow_duplicate=True),
    Output(f"dropdown-print-orientation-{type_page_print}", "value", allow_duplicate=True),
    Output(f"input-print-template-name-{type_page_print}", "value", allow_duplicate=True),
    Output(f"store-print-template-id-{type_page_print}", "data", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "children", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "color", allow_duplicate=True),
    Output(f"alert-{type_page_print}", "is_open", allow_duplicate=True),
    Input(f"dropdown-print-template-{type_page_print}", "value"),
    State(f"store-print-missing-{type_page_print}", "data"),
    State(f"store-print-indicator-options-{type_page_print}", "data"),
    prevent_initial_call=True,
)
def on_template_selected(selected_tpl, missing, indicator_options):
    if not selected_tpl:
        raise PreventUpdate
    data = get_print_template(int(selected_tpl))
    if not data:
        raise PreventUpdate
    loaded = normalize_print_config(data["config"])
    return (
        render_layout_editor(loaded, missing, indicator_options),
        loaded,
        loaded.get("columns") or 2,
        loaded.get("page_columns") or 2,
        loaded.get("page_orientation") or "landscape",
        data["name"],
        data["id"],
        f"Загружен «{data['name']}». Нажмите «Предпросмотр», затем при необходимости «Сохранить».",
        "info",
        True,
    )
