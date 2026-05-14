"""
Вкладка «Анализ» — загрузка detail_services CSV и те же отчёты, что в report_detail_services.py.
"""
from __future__ import annotations

import base64
import csv
import io
import os
from datetime import datetime
import re
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, dcc, html, dash_table, no_update
from dash.exceptions import PreventUpdate

from apps.dash_dn.app import dash_dn_app as app
from apps.dash_dn.bot_tasks import db as bot_db
from apps.dash_dn.detail_services_report import (
    build_report,
    load_required_services_for_icd_codes_by_specialty,
    load_specialties_from_db,
    load_allowed_service_codes_from_db,
    load_diagnosis_lookup_from_db,
    read_detail_csv_from_bytes,
)
from apps.dash_dn.catalog_periods import (
    default_active_catalog,
    main_nav_catalog_options,
    matrix_catalog_after,
    matrix_catalog_before,
)
from apps.dash_dn.sqlite_catalog.paths import get_db_path

PREFIX = "dash-dn-analysis"

_BOT_STATUS_RU: dict[str, str] = {
    "queued": "в очереди (ожидает воркер)",
    "running": "выполняется (воркер работает)",
    "succeeded": "успешно (готово)",
    "failed": "ошибка (см. error / artifacts)",
    "cancelled": "отменено (не будет выполнено)",
}


def _bot_status_ru(s: str | None) -> str:
    key = str(s or "").strip().lower()
    return _BOT_STATUS_RU.get(key, key or "")


_SPECIALTY_OPTS_CACHE: dict[str, list[dict]] = {}


def _specialty_options(catalog: str | None = None) -> list[dict]:
    """Dropdown options for dn_specialty; cached per process per catalog slug."""
    cat = (catalog or default_active_catalog()).strip() or default_active_catalog()
    if cat in _SPECIALTY_OPTS_CACHE:
        return _SPECIALTY_OPTS_CACHE[cat]
    items = load_specialties_from_db(catalog=cat)
    opts = [{"label": name, "value": int(sid)} for sid, name in items]
    _SPECIALTY_OPTS_CACHE[cat] = opts
    return opts


def _default_claim_ambulatory_base() -> str:
    raw = (os.environ.get("DASH_DN_CLAIM_AMBULATORY_BASE_URL") or "").strip()
    if not raw:
        raw = "http://10.36.0.142:9000/claim/ambulatory/"
    return raw.rstrip("/") + "/"


def _dt_style():
    return {
        "overflowX": "auto",
        "maxHeight": "420px",
        "border": "1px solid #dee2e6",
        "borderRadius": "0.375rem",
    }


def _table(
    id_suffix: str,
    page_size: int = 25,
    *,
    wrap_long_text: bool = False,
    selectable_ticket: bool = False,
):
    cell_style = {
        "fontSize": "0.85rem",
        "padding": "6px 8px",
        "textAlign": "left",
    }
    if wrap_long_text:
        cell_style["whiteSpace"] = "normal"
        cell_style["height"] = "auto"
        cell_style["minWidth"] = "200px"
    kw: dict = dict(
        id=f"{PREFIX}-{id_suffix}",
        columns=[],
        data=[],
        page_size=page_size,
        page_action="native",
        filter_action="native",
        sort_action="native",
        export_format="xlsx",
        export_headers="display",
        markdown_options={"link_target": "_blank"},
        # Use Russian-like separators in numeric formatting:
        # grouping with spaces, decimals with comma.
        locale_format={"decimal": ",", "group": " ", "grouping": [3]},
        # fixed_rows отключён: при columns=[] / data=[] Dash DataTable падает в JS (getWeight / undefined).
        style_table=_dt_style(),
        style_cell=cell_style,
        style_header={"fontWeight": "600", "backgroundColor": "#f1f5f9"},
    )
    if selectable_ticket:
        kw["row_selectable"] = "single"
        kw["selected_rows"] = []
    return dash_table.DataTable(**kw)


def layout_body():
    _cat_opts = main_nav_catalog_options()
    _work_default = default_active_catalog()
    _cmp_a_default = matrix_catalog_before()
    _cmp_b_default = matrix_catalog_after()

    return html.Div(
        [
            html.P(
                "Загрузите Детализацию талонов по услугам из web.ОМС (csv-файл). "
                "Сначала исключаются строки, где в «Код услуги» прочерк «-» или пусто (как в Квазар для части строк). "
                "Далее своды по оставшимся строкам; замечания — на вкладке «Ошибки».",
                className="text-muted small",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Upload(
                                id=f"{PREFIX}-upload",
                                children=html.Div(
                                    [
                                        html.I(className="bi bi-cloud-upload me-2"),
                                        "1) Загрузите detail_services CSV",
                                    ],
                                    className="small",
                                ),
                                className="border rounded-3 p-4 text-center bg-white mb-2",
                                style={"cursor": "pointer"},
                                multiple=False,
                            ),
                            html.Div(
                                id=f"{PREFIX}-upload-status-detail",
                                className="small text-muted mb-2",
                                children="Файл detail_services: не выбран",
                            ),
                        ],
                        md=12,
                        lg=6,
                    ),
                    dbc.Col(
                        [
                            dcc.Upload(
                                id=f"{PREFIX}-upload-journal",
                                children=html.Div(
                                    [
                                        html.I(className="bi bi-journal-text me-2"),
                                        "2) Загрузите journal CSV",
                                    ],
                                    className="small",
                                ),
                                className="border rounded-3 p-4 text-center bg-white mb-2",
                                style={"cursor": "pointer"},
                                multiple=False,
                            ),
                            html.Div(
                                id=f"{PREFIX}-upload-status-journal",
                                className="small text-muted mb-2",
                                children="Файл journal: не выбран",
                            ),
                        ],
                        md=12,
                        lg=6,
                    ),
                ],
                className="g-2",
            ),
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.Strong("С какого справочника считать ожидаемые услуги", className="d-block mb-1 small"),
                            dcc.Dropdown(
                                id=f"{PREFIX}-work-catalog",
                                options=_cat_opts,
                                value=_work_default,
                                clearable=False,
                                className="mb-2",
                            ),
                            html.Small(
                                "Как в шапке: период матрицы. После смены перезапустите «Анализ journal».",
                                className="text-muted d-block mb-3",
                            ),
                            html.Strong("Сравнить два периода (коды услуг в правилах)", className="d-block mb-1 small"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Span("A", className="small text-muted d-block"),
                                            dcc.Dropdown(
                                                id=f"{PREFIX}-cmp-catalog-a",
                                                options=_cat_opts,
                                                value=_cmp_a_default,
                                                clearable=False,
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Span("B", className="small text-muted d-block"),
                                            dcc.Dropdown(
                                                id=f"{PREFIX}-cmp-catalog-b",
                                                options=_cat_opts,
                                                value=_cmp_b_default,
                                                clearable=False,
                                            ),
                                        ],
                                        md=6,
                                    ),
                                ],
                                className="g-2 mb-2",
                            ),
                            dbc.Button(
                                "Сравнить коды услуг в требованиях",
                                id=f"{PREFIX}-cmp-matrix-btn",
                                color="secondary",
                                size="sm",
                                className="mb-2",
                            ),
                            html.Div(id=f"{PREFIX}-cmp-matrix-out", className="small"),
                        ]
                    )
                ],
                className="mb-3 border-0 shadow-sm",
            ),
            dbc.Button(
                "3) Обработать",
                id=f"{PREFIX}-run",
                color="primary",
                size="sm",
                className="mb-3",
            ),
            html.Div(id=f"{PREFIX}-msg", className="mb-2"),
            dcc.Store(id=f"{PREFIX}-report-store", data=None),
            dcc.Store(id=f"{PREFIX}-cat-sum-applied", data=None),
            dcc.Store(id=f"{PREFIX}-block-applied", data=None),
            dcc.Store(id=f"{PREFIX}-claim-base-url", data=_default_claim_ambulatory_base()),
            dcc.Store(id=f"{PREFIX}-bot-doctor-overrides", data=None),
            dcc.Store(id=f"{PREFIX}-bot-specialty-overrides", data=None),
            # Persist uploaded files across page refresh (localStorage).
            # We store file paths under apps/dash_dn/data/uploads/ and keep metadata here.
            dcc.Store(id=f"{PREFIX}-upload-cache", data=None, storage_type="local"),
            html.Div(id=f"{PREFIX}-dummy-clientside", style={"display": "none"}),
            dcc.Loading(
                [
                    html.Div(id=f"{PREFIX}-summary", className="mb-3"),
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                [
                                                    html.I(className="bi bi-box-arrow-up-right me-2"),
                                                    "Открыть талон во внешней системе",
                                                ],
                                                id=f"{PREFIX}-btn-open-claim",
                                                color="info",
                                                outline=True,
                                                size="sm",
                                            ),
                                            html.Span(
                                                " На вкладках с колонкой «Талон» выделите строку и нажмите — "
                                                "страница талона откроется в новой вкладке.",
                                                className="small text-muted ms-lg-2 d-inline-block mt-2 mt-lg-0",
                                            ),
                                        ],
                                        className="d-flex flex-wrap align-items-center gap-2",
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    "Базовый URL: ",
                                    html.Code(id=f"{PREFIX}-claim-base-hint", children=_default_claim_ambulatory_base()),
                                    " (переменная ",
                                    html.Code("DASH_DN_CLAIM_AMBULATORY_BASE_URL"),
                                    ")",
                                ],
                                className="small text-muted mb-2",
                            ),
                        ]
                    ),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                label="Свод по диагнозам",
                                tab_id="a-diag",
                                children=html.Div(_table("tbl-diag"), className="pt-3"),
                            ),
                            dbc.Tab(
                                label="Талоны с одной услугой",
                                tab_id="a-one",
                                children=html.Div(
                                    _table("tbl-one", wrap_long_text=True, selectable_ticket=True),
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Талоны 2+ услуг",
                                tab_id="a-multi",
                                children=html.Div(
                                    _table("tbl-multi", wrap_long_text=True, selectable_ticket=True),
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Свод по категориям",
                                tab_id="a-cat",
                                children=html.Div(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Статусы талонов (мультивыбор)",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-cat-statuses",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все статусы",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=5,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Показать", className="small fw-semibold"),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-cat-axis",
                                                            options=[
                                                                {"label": " DS1 (основной)", "value": "ds1"},
                                                                {
                                                                    "label": " DS2 (сопутствующие)",
                                                                    "value": "ds2",
                                                                },
                                                            ],
                                                            value="ds1",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "inline-block", "marginRight": "1rem"},
                                                        ),
                                                    ],
                                                    md=6,
                                                    lg=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Разбивка по подразделению (только DS1)",
                                                            className="small fw-semibold",
                                                        ),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-cat-unit",
                                                            options=[
                                                                {"label": " Нет", "value": "no"},
                                                                {"label": " Да", "value": "yes"},
                                                            ],
                                                            value="no",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "inline-block", "marginRight": "1rem"},
                                                        ),
                                                    ],
                                                    md=6,
                                                    lg=4,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Отчетный период", className="small fw-semibold mb-1"),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-cat-report-periods",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все периоды",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Дата формирования", className="small fw-semibold mb-1"),
                                                        dcc.DatePickerRange(
                                                            id=f"{PREFIX}-cat-formed-range",
                                                            display_format="DD-MM-YYYY",
                                                            minimum_nights=0,
                                                        ),
                                                    ],
                                                    md=6,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Дата окончания лечения",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dcc.DatePickerRange(
                                                            id=f"{PREFIX}-cat-end-range",
                                                            display_format="DD-MM-YYYY",
                                                            minimum_nights=0,
                                                        ),
                                                    ],
                                                    md=6,
                                                    lg=4,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Checkbox(
                                                            id=f"{PREFIX}-cat-include-notref",
                                                            value=True,
                                                            className="me-2",
                                                        ),
                                                        dbc.Label(
                                                            "Включать категорию «Нет в справочнике»",
                                                            html_for=f"{PREFIX}-cat-include-notref",
                                                            className="small fw-semibold mb-0",
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",
                                                    md=12,
                                                    lg=6,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Checkbox(
                                                            id=f"{PREFIX}-cat-sum-enabled",
                                                            value=False,
                                                            className="me-2",
                                                        ),
                                                        dbc.Label(
                                                            "Фильтр по стоимости талона",
                                                            html_for=f"{PREFIX}-cat-sum-enabled",
                                                            className="small fw-semibold mb-0",
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",
                                                    md=6,
                                                    lg=5,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.InputGroupText("Режим"),
                                                                    dbc.Select(
                                                                        id=f"{PREFIX}-cat-sum-op",
                                                                        options=[
                                                                            {
                                                                                "label": "Больше (>)",
                                                                                "value": "gt",
                                                                            },
                                                                            {
                                                                                "label": "Меньше (<)",
                                                                                "value": "lt",
                                                                            },
                                                                            {
                                                                                "label": "Равно (=)",
                                                                                "value": "eq",
                                                                            },
                                                                        ],
                                                                        value="gt",
                                                                        size="sm",
                                                                        style={"maxWidth": "200px"},
                                                                    ),
                                                                    dbc.InputGroupText("Сумма"),
                                                                    dbc.Input(
                                                                        id=f"{PREFIX}-cat-sum-value",
                                                                        type="number",
                                                                        min=0,
                                                                        step="0.01",
                                                                        placeholder="Введите сумму талона",
                                                                        size="sm",
                                                                    ),
                                                                ],
                                                                size="sm",
                                                                className="mb-2",
                                                            ),
                                                            dbc.Button(
                                                                "Обновить таблицу",
                                                                id=f"{PREFIX}-cat-sum-apply",
                                                                color="primary",
                                                                size="sm",
                                                                className="mt-2",
                                                            ),
                                                        ],
                                                        id=f"{PREFIX}-cat-sum-controls",
                                                        style={"display": "none"},
                                                    ),
                                                    md=6,
                                                    lg=7,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        _table("tbl-cat", page_size=40),
                                        dbc.Card(
                                            [
                                                dbc.CardHeader("Детализация по выбранной ячейке"),
                                                dbc.CardBody(
                                                    [
                                                        html.Div(
                                                            id=f"{PREFIX}-cat-details-title",
                                                            className="small fw-semibold mb-2",
                                                        ),
                                                        _table(
                                                            "tbl-cat-details",
                                                            page_size=30,
                                                            selectable_ticket=True,
                                                        ),
                                                    ]
                                                ),
                                            ],
                                            className="mt-3",
                                        ),
                                    ],
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Матрица цен",
                                tab_id="a-price-matrix",
                                children=html.Div(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Статусы талонов (мультивыбор)",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-pm-statuses",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все статусы",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Режим", className="small fw-semibold"),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-pm-mode",
                                                            options=[
                                                                {"label": " По статусам", "value": "status"},
                                                                {
                                                                    "label": " По ценовым диапазонам",
                                                                    "value": "price",
                                                                },
                                                            ],
                                                            value="status",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "inline-block", "marginRight": "1rem"},
                                                        ),
                                                    ],
                                                    md=6,
                                                    lg=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Категории", className="small fw-semibold"),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-pm-axis",
                                                            options=[
                                                                {"label": " DS1 (основной)", "value": "ds1"},
                                                                {"label": " DS2 (сопутствующие)", "value": "ds2"},
                                                            ],
                                                            value="ds1",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "inline-block", "marginRight": "1rem"},
                                                        ),
                                                    ],
                                                    md=6,
                                                    lg=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Метрика", className="small fw-semibold"),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-pm-metric",
                                                            options=[
                                                                {"label": " Количество", "value": "count"},
                                                                {"label": " Сумма талонов", "value": "sum"},
                                                            ],
                                                            value="count",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "inline-block", "marginRight": "1rem"},
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=2,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        id=f"{PREFIX}-pm-note",
                                                        className="small text-muted mt-4",
                                                    ),
                                                    md=12,
                                                    lg=12,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        _table("tbl-price-matrix", page_size=50),
                                    ],
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Блокировка выгрузки талонов",
                                tab_id="a-block",
                                children=html.Div(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Статусы талонов (мультивыбор)",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-block-statuses",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Выберите статусы",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=7,
                                                    lg=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Дополнительно",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dcc.Checklist(
                                                            id=f"{PREFIX}-block-only-errors",
                                                            options=[
                                                                {
                                                                    "label": " Только талоны с ошибками",
                                                                    "value": "yes",
                                                                }
                                                            ],
                                                            value=["yes"],
                                                            className="small",
                                                            inputStyle={"marginRight": "0.35rem"},
                                                        ),
                                                    ],
                                                    md=5,
                                                    lg=6,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Checkbox(
                                                            id=f"{PREFIX}-block-sum-enabled",
                                                            value=False,
                                                            className="me-2",
                                                        ),
                                                        dbc.Label(
                                                            "Фильтр по стоимости талона",
                                                            html_for=f"{PREFIX}-block-sum-enabled",
                                                            className="small fw-semibold mb-0",
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",
                                                    md=5,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.InputGroupText("Режим"),
                                                                    dbc.Select(
                                                                        id=f"{PREFIX}-block-sum-op",
                                                                        options=[
                                                                            {"label": "Больше (>)", "value": "gt"},
                                                                            {"label": "Меньше (<)", "value": "lt"},
                                                                            {"label": "Равно (=)", "value": "eq"},
                                                                        ],
                                                                        value="gt",
                                                                        size="sm",
                                                                        style={"maxWidth": "200px"},
                                                                    ),
                                                                    dbc.InputGroupText("Сумма"),
                                                                    dbc.Input(
                                                                        id=f"{PREFIX}-block-sum-value",
                                                                        type="number",
                                                                        min=0,
                                                                        step="0.01",
                                                                        placeholder="Введите сумму талона",
                                                                        size="sm",
                                                                    ),
                                                                ],
                                                                size="sm",
                                                            ),
                                                        ],
                                                        id=f"{PREFIX}-block-sum-controls",
                                                        style={"display": "none"},
                                                    ),
                                                    md=7,
                                                    lg=8,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Логика между ошибками и стоимостью",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-block-logic",
                                                            options=[
                                                                {"label": " И", "value": "and"},
                                                                {"label": " ИЛИ", "value": "or"},
                                                            ],
                                                            value="and",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "inline-block", "marginRight": "1rem"},
                                                        ),
                                                    ],
                                                    md=8,
                                                    lg=7,
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Обновить список",
                                                        id=f"{PREFIX}-block-apply",
                                                        color="primary",
                                                        size="sm",
                                                        className="mt-4",
                                                    ),
                                                    md=4,
                                                    lg=5,
                                                    className="d-flex align-items-start",
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        html.Div(id=f"{PREFIX}-block-summary", className="small text-muted mb-2"),
                                        _table("tbl-block", page_size=40, selectable_ticket=True),
                                    ],
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Ошибки",
                                tab_id="a-errors",
                                children=html.Div(
                                    [
                                        dbc.Label("Что показывать", className="small fw-semibold"),
                                        dcc.RadioItems(
                                            id=f"{PREFIX}-errors-filter",
                                            options=[
                                                {"label": " Все", "value": "all"},
                                                {"label": " По услугам", "value": "svc"},
                                                {"label": " По диагнозам", "value": "dx"},
                                            ],
                                            value="all",
                                            className="small mb-3",
                                            inputClassName="me-1",
                                            labelStyle={"display": "inline-block", "marginRight": "1.25rem"},
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "Замечания по услугам (код/формат и обязательные услуги по диагнозам)",
                                                    className="small text-muted mb-1",
                                                ),
                                                _table(
                                                    "tbl-errors-svc",
                                                    page_size=25,
                                                    wrap_long_text=True,
                                                    selectable_ticket=True,
                                                ),
                                            ],
                                            id=f"{PREFIX}-errors-svc-wrap",
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "Несоответствия диагнозов справочнику dn_diagnosis",
                                                    className="small text-muted mb-1",
                                                ),
                                                _table("tbl-errors-dx", selectable_ticket=True),
                                            ],
                                            id=f"{PREFIX}-errors-dx-wrap",
                                        ),
                                    ],
                                    className="pt-3",
                                ),
                            ),
                        dbc.Tab(
                            label="Потери",
                            tab_id="a-loss",
                            children=html.Div(
                                [
                                    html.P(
                                        "Свод по потерям (как «Свод по категориям»): статусы, суммы по талонам и детализация.",
                                        className="small text-muted",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Статусы (мультивыбор)", className="small fw-semibold mb-1"),
                                                    dcc.Dropdown(
                                                        id=f"{PREFIX}-loss-status",
                                                        options=[],
                                                        value=[],
                                                        multi=True,
                                                        placeholder="Все статусы",
                                                        className="small",
                                                    ),
                                                ],
                                                md=12,
                                                lg=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Подразделение", className="small fw-semibold mb-1"),
                                                    dcc.Dropdown(
                                                        id=f"{PREFIX}-loss-unit",
                                                        options=[],
                                                        value=[],
                                                        multi=True,
                                                        placeholder="все",
                                                        className="small",
                                                    ),
                                                ],
                                                md=12,
                                                lg=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Checklist(
                                                        id=f"{PREFIX}-loss-by-unit",
                                                        options=[{"label": " Разбивка по подразделению", "value": "on"}],
                                                        value=["on"],
                                                        className="small mt-4",
                                                        inputClassName="me-1",
                                                    )
                                                ],
                                                md=12,
                                                lg=4,
                                            ),
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Checklist(
                                                    id=f"{PREFIX}-loss-show-status",
                                                    options=[{"label": " Показывать статусы в своде", "value": "on"}],
                                                    value=["on"],
                                                    className="small",
                                                    inputClassName="me-1",
                                                ),
                                                md=12,
                                            )
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Button(
                                                        "Посчитать",
                                                        id=f"{PREFIX}-loss-run",
                                                        color="primary",
                                                        size="sm",
                                                    ),
                                                    dbc.Button(
                                                        "Скачать (CSV)",
                                                        id=f"{PREFIX}-loss-download-btn",
                                                        color="success",
                                                        outline=True,
                                                        size="sm",
                                                        className="ms-2",
                                                    ),
                                                ],
                                                md=12,
                                            )
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    html.Div(id=f"{PREFIX}-loss-msg", className="mb-2"),
                                    dcc.Store(id=f"{PREFIX}-loss-store", data=None),
                                    dcc.Download(id=f"{PREFIX}-loss-download"),
                                    html.H6("Свод", className="mt-2"),
                                    _table("tbl-loss-sum", page_size=25, wrap_long_text=False, selectable_ticket=True),
                                    html.H6("Детализация", className="mt-3"),
                                    _table("tbl-loss-details", page_size=25, wrap_long_text=True),
                                ],
                                className="pt-3",
                            ),
                        ),
                        dbc.Tab(
                                label="Автоисправление",
                                tab_id="a-bot",
                                children=html.Div(
                                    [
                                        html.P(
                                            "Сформируйте задачи на исправление и запустите воркер Playwright отдельным процессом. "
                                            "MVP: добавление/правка услуг (без удаления лишних).",
                                            className="small text-muted",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Button(
                                                            "Сформировать задачи из «проблем по услугам»",
                                                            id=f"{PREFIX}-bot-enqueue",
                                                            color="primary",
                                                            size="sm",
                                                        ),
                                                        dbc.Button(
                                                            "Обновить",
                                                            id=f"{PREFIX}-bot-refresh",
                                                            color="secondary",
                                                            outline=True,
                                                            size="sm",
                                                            className="ms-2",
                                                        ),
                                                        dbc.Checklist(
                                                            id=f"{PREFIX}-bot-autorefresh",
                                                            options=[{"label": " Авто‑обновление (10с)", "value": "on"}],
                                                            value=[],
                                                            className="small mt-2",
                                                            inputClassName="me-1",
                                                        ),
                                                        html.Div(
                                                            id=f"{PREFIX}-bot-enqueue-msg",
                                                            className="small text-muted mt-2",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Команда запуска воркера", className="small fw-semibold mb-1"),
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    dbc.Checklist(
                                                                        id=f"{PREFIX}-bot-worker-headful",
                                                                        options=[{"label": " Показать браузер (headful)", "value": "on"}],
                                                                        value=[],
                                                                        className="small",
                                                                        inputClassName="me-1",
                                                                    ),
                                                                    md=12,
                                                                    lg=7,
                                                                ),
                                                                dbc.Col(
                                                                    dbc.InputGroup(
                                                                        [
                                                                            dbc.InputGroupText("slowmo"),
                                                                            dbc.Input(
                                                                                id=f"{PREFIX}-bot-worker-slowmo",
                                                                                type="number",
                                                                                min=0,
                                                                                step=50,
                                                                                value=200,
                                                                                size="sm",
                                                                            ),
                                                                            dbc.InputGroupText("ms"),
                                                                        ],
                                                                        size="sm",
                                                                    ),
                                                                    md=12,
                                                                    lg=5,
                                                                ),
                                                            ],
                                                            className="g-2 mb-2",
                                                        ),
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    dbc.InputGroup(
                                                                        [
                                                                            dbc.InputGroupText("воркеров"),
                                                                            dbc.Input(
                                                                                id=f"{PREFIX}-bot-worker-n",
                                                                                type="number",
                                                                                min=1,
                                                                                step=1,
                                                                                value=5,
                                                                                size="sm",
                                                                            ),
                                                                        ],
                                                                        size="sm",
                                                                    ),
                                                                    md=12,
                                                                    lg=5,
                                                                ),
                                                                dbc.Col(
                                                                    dbc.Checklist(
                                                                        id=f"{PREFIX}-bot-worker-one-headful",
                                                                        options=[
                                                                            {
                                                                                "label": " Только worker-1 в браузере (остальные headless)",
                                                                                "value": "on",
                                                                            }
                                                                        ],
                                                                        value=["on"],
                                                                        className="small mt-1",
                                                                        inputClassName="me-1",
                                                                    ),
                                                                    md=12,
                                                                    lg=7,
                                                                ),
                                                            ],
                                                            className="g-2 mb-2",
                                                        ),
                                                        html.Code(
                                                            id=f"{PREFIX}-bot-worker-cmd",
                                                            className="small",
                                                        ),
                                                        dbc.Textarea(
                                                            id=f"{PREFIX}-bot-worker-cmds",
                                                            value="",
                                                            rows=8,
                                                            className="small font-monospace mt-2",
                                                            style={"whiteSpace": "pre"},
                                                            readOnly=True,
                                                        ),
                                                        html.Div(
                                                            "Статусы выполнения смотрите ниже в таблице очереди (status/error/artifacts).",
                                                            className="small text-muted mt-2",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=6,
                                                ),
                                            ],
                                            className="g-2 mb-3",
                                        ),
                                        html.Hr(),
                                        html.H6("Постановка задач (фильтры + выбор талонов)", className="mb-2"),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Статусы (мультивыбор)", className="small fw-semibold mb-1"),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-bot-cand-status",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все статусы",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Врач (мультивыбор)", className="small fw-semibold mb-1"),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-bot-cand-doctor",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все врачи",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Подразделение (мультивыбор)", className="small fw-semibold mb-1"),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-bot-cand-unit",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все подразделения",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Специальность", className="small fw-semibold mb-1"),
                                                        dcc.Dropdown(
                                                            id=f"{PREFIX}-bot-cand-specialty-id",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            placeholder="Все специальности",
                                                            className="small",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=3,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Диагнозы: включить префиксы (через запятую, напр. N,E)",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dbc.Input(
                                                            id=f"{PREFIX}-bot-cand-diag-include",
                                                            placeholder="пусто = все",
                                                            size="sm",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label(
                                                            "Диагнозы: исключить префиксы (через запятую, напр. C,D)",
                                                            className="small fw-semibold mb-1",
                                                        ),
                                                        dbc.Input(
                                                            id=f"{PREFIX}-bot-cand-diag-exclude",
                                                            placeholder="например: C",
                                                            size="sm",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Окончание лечения (диапазон)", className="small fw-semibold mb-1"),
                                                        dcc.DatePickerRange(
                                                            id=f"{PREFIX}-bot-cand-end-date",
                                                            display_format="DD.MM.YYYY",
                                                            start_date=None,
                                                            end_date=None,
                                                            minimum_nights=0,
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Checklist(
                                                            id=f"{PREFIX}-bot-cand-only-allowed-status",
                                                            options=[
                                                                {
                                                                    "label": " Только статусы 1/6/8/19 (система позволяет править)",
                                                                    "value": "on",
                                                                }
                                                            ],
                                                            value=["on"],
                                                            className="small mt-4",
                                                            inputClassName="me-1",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Checklist(
                                                            id=f"{PREFIX}-bot-cand-hide-in-queue",
                                                            options=[
                                                                {
                                                                    "label": " Убрать талоны, уже в очереди (queued/running)",
                                                                    "value": "on",
                                                                }
                                                            ],
                                                            value=["on"],
                                                            className="small mt-4",
                                                            inputClassName="me-1",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Label("Режим", className="small fw-semibold mb-1"),
                                                        dcc.RadioItems(
                                                            id=f"{PREFIX}-bot-mode",
                                                            options=[
                                                                {"label": " add_update (добавить/обновить)", "value": "add_update"},
                                                                {"label": " sync (точное соответствие, без дублей)", "value": "sync"},
                                                            ],
                                                            value="sync",
                                                            className="small",
                                                            inputClassName="me-1",
                                                            labelStyle={"display": "block"},
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Label("doctor_id для задач", className="small fw-semibold mb-1"),
                                                        dbc.Input(
                                                            id=f"{PREFIX}-bot-doctor-id",
                                                            value="",
                                                            placeholder="например: 00136001",
                                                            size="sm",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    dbc.Button(
                                                                        "Выбрать все (на странице)",
                                                                        id=f"{PREFIX}-bot-cand-select-all",
                                                                        color="secondary",
                                                                        outline=True,
                                                                        size="sm",
                                                                        className="mt-4 me-2",
                                                                    ),
                                                                    width="auto",
                                                                ),
                                                                dbc.Col(
                                                                    dbc.Button(
                                                                        "Выбрать все (по фильтру)",
                                                                        id=f"{PREFIX}-bot-cand-select-all-filtered",
                                                                        color="secondary",
                                                                        outline=True,
                                                                        size="sm",
                                                                        className="mt-4 me-2",
                                                                    ),
                                                                    width="auto",
                                                                ),
                                                                dbc.Col(
                                                                    dbc.Button(
                                                                        "Снять выделение",
                                                                        id=f"{PREFIX}-bot-cand-clear",
                                                                        color="secondary",
                                                                        outline=True,
                                                                        size="sm",
                                                                        className="mt-4",
                                                                    ),
                                                                    width="auto",
                                                                ),
                                                            ],
                                                            className="g-1",
                                                        ),
                                                        dbc.Button(
                                                            "Создать задачи по выбранным талонам",
                                                            id=f"{PREFIX}-bot-enqueue-selected",
                                                            color="success",
                                                            size="sm",
                                                            className="mt-4",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    "Массовая замена doctor_id и специальности (пересчитает svc_dx)",
                                                                    className="small fw-semibold mt-3",
                                                                ),
                                                                dbc.Row(
                                                                    [
                                                                        dbc.Col(
                                                                            dbc.Input(
                                                                                id=f"{PREFIX}-bot-bulk-doctor-id",
                                                                                value="",
                                                                                placeholder="новый doctor_id (например 00136001)",
                                                                                size="sm",
                                                                            ),
                                                                            md=12,
                                                                            lg=5,
                                                                        ),
                                                                        dbc.Col(
                                                                            dcc.Dropdown(
                                                                                id=f"{PREFIX}-bot-bulk-specialty-id",
                                                                                options=[],
                                                                                value=None,
                                                                                placeholder="новый specialty_id (из списка)",
                                                                                clearable=True,
                                                                            ),
                                                                            md=12,
                                                                            lg=7,
                                                                        ),
                                                                    ],
                                                                    className="g-2 mt-1",
                                                                ),
                                                                dbc.Row(
                                                                    [
                                                                        dbc.Col(
                                                                            dbc.InputGroup(
                                                                                [
                                                                                    dbc.InputGroupText("N"),
                                                                                    dbc.Input(
                                                                                        id=f"{PREFIX}-bot-bulk-n",
                                                                                        type="number",
                                                                                        min=1,
                                                                                        step=1,
                                                                                        value=200,
                                                                                        size="sm",
                                                                                    ),
                                                                                ],
                                                                                size="sm",
                                                                            ),
                                                                            width="auto",
                                                                        ),
                                                                        dbc.Col(
                                                                            dbc.Button(
                                                                                "Применить к выбранным",
                                                                                id=f"{PREFIX}-bot-bulk-apply-selected",
                                                                                color="primary",
                                                                                outline=True,
                                                                                size="sm",
                                                                            ),
                                                                            width="auto",
                                                                        ),
                                                                        dbc.Col(
                                                                            dbc.Button(
                                                                                "Применить к первым N (по фильтру)",
                                                                                id=f"{PREFIX}-bot-bulk-apply-firstn",
                                                                                color="primary",
                                                                                outline=True,
                                                                                size="sm",
                                                                            ),
                                                                            width="auto",
                                                                        ),
                                                                        dbc.Col(
                                                                            dbc.Button(
                                                                                "Сбросить оверрайды (выбранные)",
                                                                                id=f"{PREFIX}-bot-bulk-reset-selected",
                                                                                color="secondary",
                                                                                outline=True,
                                                                                size="sm",
                                                                            ),
                                                                            width="auto",
                                                                        ),
                                                                    ],
                                                                    className="g-1 mt-2",
                                                                ),
                                                            ],
                                                            className="mt-2",
                                                        ),
                                                        html.Div(
                                                            id=f"{PREFIX}-bot-enqueue-selected-msg",
                                                            className="small text-muted mt-2",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=4,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        dash_table.DataTable(
                                            id=f"{PREFIX}-bot-candidates",
                                            columns=[],
                                            data=[],
                                            page_size=15,
                                            page_action="native",
                                            filter_action="native",
                                            sort_action="native",
                                            editable=True,
                                            row_selectable="multi",
                                            selected_rows=[],
                                            style_table=_dt_style(),
                                            style_cell={"fontSize": "0.85rem", "padding": "6px 8px", "whiteSpace": "normal"},
                                            style_header={"fontWeight": "600", "backgroundColor": "#f1f5f9"},
                                        ),
                                        html.Div(
                                            id=f"{PREFIX}-bot-last-updated",
                                            className="small text-muted mb-2",
                                        ),
                                        dcc.Interval(
                                            id=f"{PREFIX}-bot-poll",
                                            interval=10_000,
                                            n_intervals=0,
                                        ),
                                        html.Div(id=f"{PREFIX}-bot-queue-stats", className="small mb-2"),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Button(
                                                            "Отменить все queued",
                                                            id=f"{PREFIX}-bot-cancel-queued",
                                                            color="warning",
                                                            outline=True,
                                                            size="sm",
                                                            className="me-2",
                                                        ),
                                                        dbc.Button(
                                                            "Сбросить зависшие running",
                                                            id=f"{PREFIX}-bot-requeue-running",
                                                            color="secondary",
                                                            outline=True,
                                                            size="sm",
                                                            className="me-2",
                                                        ),
                                                        dbc.Button(
                                                            "Очистить всю очередь",
                                                            id=f"{PREFIX}-bot-purge-all",
                                                            color="danger",
                                                            outline=True,
                                                            size="sm",
                                                        ),
                                                    ],
                                                    md=12,
                                                    lg=6,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        id=f"{PREFIX}-bot-queue-msg",
                                                        className="small text-muted",
                                                    ),
                                                    md=12,
                                                    lg=6,
                                                ),
                                            ],
                                            className="g-2 mb-2",
                                        ),
                                        _table("tbl-bot-tasks", page_size=30),
                                    ],
                                    className="pt-3",
                                ),
                            ),
                        dbc.Tab(
                            label="Анализ файлов",
                            tab_id="a-files",
                            children=html.Div(
                                [
                                    html.P(
                                        "Использует уже загруженные сверху файлы: detail_services CSV + journal CSV. "
                                        "Добавляет в journal 3 поля (статус / услуги в карте / правильные услуги) и даёт скачать назад.",
                                        className="small text-muted",
                                    ),
                                    dbc.Button(
                                        "Проанализировать journal",
                                        id=f"{PREFIX}-run-journal-analyze",
                                        color="primary",
                                        size="sm",
                                        className="mb-2",
                                    ),
                                    dbc.Button(
                                        "Скачать journal с полями",
                                        id=f"{PREFIX}-download-journal-enriched-btn",
                                        color="success",
                                        outline=True,
                                        size="sm",
                                        className="mb-2 ms-2",
                                    ),
                                    html.Div(id=f"{PREFIX}-journal-analyze-msg", className="mb-2"),
                                    dcc.Store(id=f"{PREFIX}-journal-analyze-store", data=None),
                                    dcc.Download(id=f"{PREFIX}-download-journal-enriched"),
                                    _table("tbl-journal-analyze", page_size=25, wrap_long_text=True),
                                ],
                                className="pt-3",
                            ),
                        ),
                        ],
                        id=f"{PREFIX}-inner-tabs",
                        active_tab="a-diag",
                        className="nav-tabs-card",
                    ),
                ],
                type="default",
                className="dash-dn-loading",
            ),
        ],
    )


def _summary_cards(report: dict, ref_line: str, dx_line: str) -> html.Div:
    raw_n = report.get("rows_raw_total", report["total_rows"])
    total_tickets = int(report.get("unique_tickets", 0))
    per_ticket = report.get("per_ticket") or []
    tickets_ok = sum(1 for t in per_ticket if bool(t.get("svc_ok")))
    tickets_err = int(len(report.get("tickets_service_mismatch") or []))
    return html.Div(
        [
            html.P(ref_line, className="small text-muted mb-2"),
            html.P(dx_line, className="small text-muted mb-2"),
            dbc.Row(
                [
                    _card("Талоны / правильные / с ошибками", f"{total_tickets} / {tickets_ok} / {tickets_err}"),
                    _card("Строк в файле", str(raw_n)),
                ],
                className="g-2",
            ),
        ],
    )


def _card(title: str, value: str):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.P(title, className="small text-muted mb-1"),
                    html.H4(value, className="mb-0"),
                ]
            ),
            className="shadow-sm border-0",
        ),
        xs=12,
        sm=6,
        lg=3,
    )


def _rows_diagnosis(report: dict) -> list[dict]:
    out = []
    for diag, agg in sorted(
        report["by_diagnosis"].items(),
        key=lambda x: (-x[1]["талонов"], x[0]),
    ):
        out.append(
            {
                "diagnosis": diag,
                "tickets": agg["талонов"],
                "sum": round(float(agg["сумма_талонов"]), 2),
            }
        )
    return out


def _rows_single(report: dict) -> list[dict]:
    return [
        {
            "tal": t["талон"],
            "enp": t.get("енп", ""),
            "status": t.get("статус", ""),
            "unit": t.get("подразделение", ""),
            "doctor": t.get("врач", ""),
            "diag": t["диагноз"],
            "ds1_code": t.get("ds1_code", ""),
            "ds1_cat": t.get("ds1_category", ""),
            "ds2": t.get("ds2_raw", ""),
            "ds2_codes": t.get("ds2_codes", ""),
            "ds2_cat": t.get("ds2_categories_line", ""),
            "dx_note": t.get("diagnosis_note", ""),
            "services": t.get("услуги", ""),
            "sum": round(float(t["сумма_талона"]), 2),
        }
        for t in sorted(report["single_service"], key=lambda x: x["талон"])
    ]


def _rows_multi(report: dict) -> list[dict]:
    return [
        {
            "tal": t["талон"],
            "enp": t.get("енп", ""),
            "status": t.get("статус", ""),
            "unit": t.get("подразделение", ""),
            "doctor": t.get("врач", ""),
            "diag": t["диагноз"],
            "ds1_code": t.get("ds1_code", ""),
            "ds1_cat": t.get("ds1_category", ""),
            "ds2": t.get("ds2_raw", ""),
            "ds2_codes": t.get("ds2_codes", ""),
            "ds2_cat": t.get("ds2_categories_line", ""),
            "dx_note": t.get("diagnosis_note", ""),
            "services": t.get("услуги", ""),
            "sum": round(float(t["сумма_талона"]), 2),
            "n": t["число_строк_услуг"],
        }
        for t in sorted(
            report["multi_service"],
            key=lambda x: (-x["число_строк_услуг"], x["талон"]),
        )
    ]


def _report_store_payload(report: dict) -> dict:
    """Кэш для вкладок «Свод по категориям» и «Ошибки» (после загрузки CSV)."""
    return {
        "svc_ticket": _rows_svc_ticket(report),
        # all tickets (not only mismatches) for losses
        "tickets_all": report.get("per_ticket") or [],
        "dx_mismatch": _rows_dx_mismatch(report),
        "block_tickets": _rows_block_tickets(report),
        "cat_ds1": _rows_cat_ds1(report),
        "cat_ds1_unit": _rows_cat_ds1_unit(report),
        "cat_ds2": _rows_cat_ds2(report),
        "cat_ticket_rows": _rows_cat_ticket_filter(report),
    }


def _rows_cat_ds1(report: dict) -> list[dict]:
    bc = report.get("by_category_ds1") or {}
    out = []
    for cat, agg in sorted(
        bc.items(),
        key=lambda x: (-x[1]["талонов"], x[0]),
    ):
        n = int(agg["талонов"])
        n_ok = int(agg.get("талонов_услуги_ок", 0))
        s = round(float(agg["сумма_талонов"]), 2)
        s_ok = round(float(agg.get("сумма_услуги_ок", 0.0)), 2)
        out.append(
            {
                "cat": cat,
                "n": n,
                "sum": s,
                "n_ok": n_ok,
                "sum_ok": s_ok,
                "n_bad": n - n_ok,
                "sum_bad": round(s - s_ok, 2),
            }
        )
    return out


def _rows_cat_ds1_unit(report: dict) -> list[dict]:
    rows = report.get("by_category_ds1_by_unit") or []
    out = []
    for r in rows:
        n = int(r["талонов"])
        n_ok = int(r["талонов_услуги_ок"])
        s = float(r["сумма_талонов"])
        s_ok = float(r["сумма_услуги_ок"])
        out.append(
            {
                "cat": r["категория"],
                "unit": r["подразделение"],
                "n": n,
                "sum": round(s, 2),
                "n_ok": n_ok,
                "sum_ok": round(s_ok, 2),
                "n_bad": n - n_ok,
                "sum_bad": round(s - s_ok, 2),
            }
        )
    return out


def _rows_cat_ds2(report: dict) -> list[dict]:
    bc = report.get("by_category_ds2") or {}
    items = bc.items() if isinstance(bc, dict) else []
    out = [{"cat": k, "n": n} for k, n in items]
    return sorted(out, key=lambda x: (-x["n"], x["cat"]))


def _rows_dx_mismatch(report: dict) -> list[dict]:
    return [
        {
            "tal": m["талон"],
            "enp": m.get("енп", ""),
            "status": m.get("статус", ""),
            "unit": m.get("подразделение", ""),
            "doctor": m.get("врач", ""),
            "kind": m["тип"],
            "code": m["код_мкб"],
            "note": m["комментарий"],
        }
        for m in report.get("diagnosis_mismatches") or []
    ]


def _rows_svc_ticket(report: dict) -> list[dict]:
    return [
        {
            "tal": t["талон"],
            "enp": t.get("енп", ""),
            "status": t.get("статус", ""),
            "unit": t.get("подразделение", ""),
            "doctor": t.get("врач", ""),
            "specialty": t.get("специальность", ""),
            "position": t.get("должность", ""),
            "specialty_id": t.get("specialty_id", None),
            "diag": t.get("диагноз", ""),
            "ds2_mkb": t.get("сопутствующие_мкб", ""),
            "svc_dx": t.get("услуги_по_диагнозам", ""),
            "n_lines": t["число_строк_услуг"],
            "sum": round(float(t["сумма_талона"]), 2),
            "reasons": t["причины"],
        }
        for t in sorted(
            report.get("tickets_service_mismatch") or [],
            key=lambda x: x["талон"],
        )
    ]


def _rows_block_tickets(report: dict) -> list[dict]:
    per_ticket = report.get("per_ticket") or []
    mismatch_rows = report.get("tickets_service_mismatch") or []
    reasons_by_tal = {
        str(t.get("талон")): str(t.get("причины", "")).strip()
        for t in mismatch_rows
        if t.get("талон") is not None
    }
    out = []
    for t in per_ticket:
        tal = str(t.get("талон", "")).strip()
        reasons = reasons_by_tal.get(tal, "")
        has_error = bool(reasons)
        out.append(
            {
                "tal": tal,
                "status": t.get("статус", ""),
                "sum": round(float(t.get("сумма_талона", 0.0) or 0.0), 2),
                "error": "Да" if has_error else "Нет",
                "reasons": reasons,
                "unit": t.get("подразделение", ""),
                "doctor": t.get("врач", ""),
                "diag": t.get("диагноз", ""),
            }
        )
    return sorted(out, key=lambda x: (str(x.get("status", "")), str(x.get("tal", ""))))


COLS_DIAG = [
    {"name": "Диагноз основной (DS1)", "id": "diagnosis"},
    {"name": "Талонов", "id": "tickets", "type": "numeric"},
    {"name": "Сумма талонов", "id": "sum", "type": "numeric"},
]
COLS_ONE = [
    {"name": "Талон", "id": "tal"},
    {"name": "ЕНП", "id": "enp"},
    {"name": "Статус", "id": "status"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "МКБ основной", "id": "ds1_code"},
    {"name": "Категория (основной)", "id": "ds1_cat"},
    {"name": "Сопутствующий (DS2)", "id": "ds2"},
    {"name": "МКБ сопутствующие", "id": "ds2_codes"},
    {"name": "Категории сопутствующих", "id": "ds2_cat"},
    {"name": "Замечания по диагнозам", "id": "dx_note"},
    {"name": "Услуги (код — сумма)", "id": "services"},
    {"name": "Сумма талона", "id": "sum", "type": "numeric"},
]
COLS_MULTI = [
    {"name": "Талон", "id": "tal"},
    {"name": "ЕНП", "id": "enp"},
    {"name": "Статус", "id": "status"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "МКБ основной", "id": "ds1_code"},
    {"name": "Категория (основной)", "id": "ds1_cat"},
    {"name": "Сопутствующий (DS2)", "id": "ds2"},
    {"name": "МКБ сопутствующие", "id": "ds2_codes"},
    {"name": "Категории сопутствующих", "id": "ds2_cat"},
    {"name": "Замечания по диагнозам", "id": "dx_note"},
    {"name": "Услуги (код — сумма)", "id": "services"},
    {"name": "Сумма талона", "id": "sum", "type": "numeric"},
    {"name": "Число строк услуг", "id": "n", "type": "numeric"},
]
COLS_CAT_DS1 = [
    {"name": "Категория / статус (основной DS1)", "id": "cat"},
    {
        "name": "Талонов (услуги по справочнику)",
        "id": "n_ok",
        "type": "numeric",
    },
    {
        "name": "Сумма (услуги по справочнику)",
        "id": "sum_ok",
        "type": "numeric",
    },
    {
        "name": "Талонов (услуги не по справочнику)",
        "id": "n_bad",
        "type": "numeric",
    },
    {
        "name": "Сумма (услуги не по справочнику)",
        "id": "sum_bad",
        "type": "numeric",
    },
    {"name": "Талонов", "id": "n", "type": "numeric"},
    {"name": "Сумма талонов", "id": "sum", "type": "numeric"},
]
COLS_CAT_DS1_UNIT = [
    {"name": "Категория (DS1)", "id": "cat"},
    {"name": "Подразделение", "id": "unit"},
    {
        "name": "Талонов (услуги по справочнику)",
        "id": "n_ok",
        "type": "numeric",
    },
    {
        "name": "Сумма (услуги по справочнику)",
        "id": "sum_ok",
        "type": "numeric",
    },
    {
        "name": "Талонов (услуги не по справочнику)",
        "id": "n_bad",
        "type": "numeric",
    },
    {
        "name": "Сумма (услуги не по справочнику)",
        "id": "sum_bad",
        "type": "numeric",
    },
    {"name": "Талонов", "id": "n", "type": "numeric"},
    {"name": "Сумма талонов", "id": "sum", "type": "numeric"},
]
COLS_CAT_DS2 = [
    {"name": "Категория / статус (сопутствующие DS2)", "id": "cat"},
    {"name": "Упоминаний кодов", "id": "n", "type": "numeric"},
]
COLS_DX_MISMATCH = [
    {"name": "Талон", "id": "tal"},
    {"name": "ЕНП", "id": "enp"},
    {"name": "Статус", "id": "status"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "Тип", "id": "kind"},
    {"name": "Код МКБ", "id": "code"},
    {"name": "Комментарий", "id": "note"},
]
COLS_SVC_TICKET = [
    {"name": "Талон", "id": "tal"},
    {"name": "ЕНП", "id": "enp"},
    {"name": "Статус", "id": "status"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "МКБ (DS1)", "id": "diag"},
    {"name": "МКБ сопутствующие (DS2)", "id": "ds2_mkb"},
    {
        "name": "Услуги по диагнозам (справочник ДН)",
        "id": "svc_dx",
    },
    {"name": "Строк услуг", "id": "n_lines", "type": "numeric"},
    {"name": "Сумма талона", "id": "sum", "type": "numeric"},
    {"name": "Причины", "id": "reasons"},
]
COLS_BLOCK = [
    {"name": "Талон", "id": "tal"},
    {"name": "Статус", "id": "status"},
    {"name": "Сумма талона", "id": "sum", "type": "numeric"},
    {"name": "С ошибкой", "id": "error"},
    {"name": "Причины ошибок", "id": "reasons"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "Диагноз (DS1)", "id": "diag"},
]
COLS_CAT_DETAILS = [
    {"name": "Талон", "id": "tal"},
    {"name": "Статус", "id": "status"},
    {"name": "Отчетный период", "id": "report_period"},
    {"name": "Дата формирования", "id": "formed_date_raw"},
    {"name": "Дата окончания лечения", "id": "end_date_raw"},
    {"name": "Категория DS1", "id": "cat"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Сумма талона", "id": "ticket_sum", "type": "numeric"},
    {"name": "Услуги по справочнику", "id": "svc_ok"},
    {"name": "Категории DS2", "id": "ds2_categories_line"},
]


@app.callback(
    Output(f"{PREFIX}-msg", "children"),
    Output(f"{PREFIX}-summary", "children"),
    Output(f"{PREFIX}-tbl-diag", "data"),
    Output(f"{PREFIX}-tbl-diag", "columns"),
    Output(f"{PREFIX}-tbl-one", "data"),
    Output(f"{PREFIX}-tbl-one", "columns"),
    Output(f"{PREFIX}-tbl-multi", "data"),
    Output(f"{PREFIX}-tbl-multi", "columns"),
    Output(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-run", "n_clicks"),
    State(f"{PREFIX}-upload", "contents"),
    State(f"{PREFIX}-upload", "filename"),
    State(f"{PREFIX}-upload-journal", "contents"),
    State(f"{PREFIX}-upload-journal", "filename"),
    State(f"{PREFIX}-upload-cache", "data"),
    State(f"{PREFIX}-work-catalog", "value"),
    prevent_initial_call=True,
)
def run_analysis(
    n_clicks,
    contents,
    upload_filename,
    journal_contents,
    journal_filename,
    upload_cache,
    work_catalog,
):
    _ = n_clicks
    wc = str(work_catalog or default_active_catalog()).strip() or default_active_catalog()
    cache = upload_cache or {}
    # After page refresh dcc.Upload loses contents; fall back to cached files on disk.
    cached_raw: bytes | None = None
    if not contents:
        detail_path = str(cache.get("detail_path") or "")
        if detail_path and Path(detail_path).exists():
            cached_raw = Path(detail_path).read_bytes()
            upload_filename = upload_filename or str(cache.get("detail_name") or Path(detail_path).name)
        else:
            raise PreventUpdate

    try:
        if cached_raw is not None:
            raw = cached_raw
        else:
            _meta, content_string = contents.split(",", 1)
            raw = base64.b64decode(content_string)
    except Exception:
        return (
            dbc.Alert("Не удалось прочитать файл.", color="danger", className="py-2 mb-0"),
            None,
            *_empty_tables(),
        )

    if not raw:
        raise PreventUpdate

    journal_note = ""
    try:
        allowed = load_allowed_service_codes_from_db(wc)
        dx_lookup = load_diagnosis_lookup_from_db(wc)
        _fn, rows = read_detail_csv_from_bytes(raw)
        if rows and not _has_report_period_in_detail(rows):
            journal_rows: list[dict[str, str]] = []
            if journal_contents:
                try:
                    _meta_j, content_j = journal_contents.split(",", 1)
                    raw_j = base64.b64decode(content_j)
                    journal_rows = _read_semicolon_csv_rows_from_bytes(raw_j)
                    journal_note = f"journal: {journal_filename or 'загружен вручную'}"
                except Exception:
                    journal_rows = []
            else:
                jpath = str(cache.get("journal_path") or "")
                if jpath and Path(jpath).exists():
                    try:
                        raw_j = Path(jpath).read_bytes()
                        journal_rows = _read_semicolon_csv_rows_from_bytes(raw_j)
                        journal_filename = journal_filename or str(cache.get("journal_name") or Path(jpath).name)
                        journal_note = f"journal: {journal_filename or 'из кеша'}"
                    except Exception:
                        journal_rows = []
            if journal_rows:
                rows, filled = _inject_fields_from_journal(rows, journal_rows)
                journal_note = (
                    f"{journal_note}; заполнено периодов: {filled.get('period', 0)}, "
                    f"дат формирования: {filled.get('formed', 0)}"
                )
            else:
                journal_note = "journal: не загружен/не разобран, поля периода/даты не подмешаны"
        report = build_report(rows, allowed, dx_lookup)
    except Exception as e:
        return (
            dbc.Alert(f"Ошибка разбора: {e}", color="danger", className="py-2 mb-0"),
            None,
            *_empty_tables(),
        )

    db_path = get_db_path()
    ref_line = (
        f"Справочник услуг: SQLite · dn_service (catalog={wc}) · {db_path} — {len(allowed)} кодов"
    )
    dx_line = (
        f"Справочник диагнозов: dn_diagnosis + dn_diagnosis_category (catalog={wc}) · "
        f"{db_path} — {len(dx_lookup)} кодов МКБ"
    )
    summary = _summary_cards(report, ref_line, dx_line)
    shown_name = upload_filename or "файл"
    sk_m = report.get("skipped_service_missing", 0)
    sk_r = report.get("skipped_service_rejected", 0)
    msg = dbc.Alert(
        f"Обработан файл: {shown_name}. "
        f"Уникальных талонов: {report['unique_tickets']}; строк: {report['total_rows']}. "
        f"Строк услуг без кода / не из справочника: {sk_m} / {sk_r}. "
        f"{journal_note + '. ' if journal_note else ''}"
        f"Своды по категориям и диагнозам — по всем талонам; замечания по услугам и диагнозам — вкладка «Ошибки».",
        color="success",
        className="py-2 mb-0",
    )

    return (
        msg,
        summary,
        _rows_diagnosis(report),
        COLS_DIAG,
        _rows_single(report),
        COLS_ONE,
        _rows_multi(report),
        COLS_MULTI,
        _report_store_payload(report),
    )


@app.callback(
    Output(f"{PREFIX}-upload-status-detail", "children"),
    Input(f"{PREFIX}-upload", "filename"),
    Input(f"{PREFIX}-upload-cache", "data"),
)
def update_detail_upload_status(filename, cache):
    if filename:
        return f"Файл detail_services: {filename} (загружен)"
    cache = cache or {}
    if cache.get("detail_name"):
        return f"Файл detail_services: {cache.get('detail_name')} (из кеша)"
    return "Файл detail_services: не выбран"


@app.callback(
    Output(f"{PREFIX}-upload-status-journal", "children"),
    Input(f"{PREFIX}-upload-journal", "filename"),
    Input(f"{PREFIX}-upload-cache", "data"),
)
def update_journal_upload_status(filename, cache):
    if filename:
        return f"Файл journal: {filename} (загружен)"
    cache = cache or {}
    if cache.get("journal_name"):
        return f"Файл journal: {cache.get('journal_name')} (из кеша)"
    return "Файл journal: не выбран"


@app.callback(
    Output(f"{PREFIX}-work-catalog", "options"),
    Output(f"{PREFIX}-cmp-catalog-a", "options"),
    Output(f"{PREFIX}-cmp-catalog-b", "options"),
    Input("dash-dn-tabs", "active_tab"),
)
def analysis_refresh_catalog_dropdown_opts(_tab):
    opts = main_nav_catalog_options()
    return opts, opts, opts


@app.callback(
    Output(f"{PREFIX}-cmp-matrix-out", "children"),
    Input(f"{PREFIX}-cmp-matrix-btn", "n_clicks"),
    State(f"{PREFIX}-cmp-catalog-a", "value"),
    State(f"{PREFIX}-cmp-catalog-b", "value"),
    prevent_initial_call=True,
)
def analysis_compare_matrix_requirement_codes(_n, ca, cb):
    from sqlalchemy import text

    from apps.dash_dn.sqlite_catalog.db import get_engine

    a = str(ca or matrix_catalog_before()).strip() or matrix_catalog_before()
    b = str(cb or matrix_catalog_after()).strip() or matrix_catalog_after()
    if a == b:
        return dbc.Alert("Выберите два разных каталога.", color="warning", className="py-2 mb-0")
    eng = get_engine()
    q = text(
        """
        SELECT DISTINCT UPPER(TRIM(s.code))
        FROM dn_service_requirement sr
        JOIN dn_service s ON s.id = sr.service_id AND s.catalog = :cat
        WHERE sr.catalog = :cat AND s.is_active = 1
          AND s.code IS NOT NULL AND TRIM(s.code) != ''
        """
    )
    with eng.connect() as conn:
        sa = {str(r[0]).upper() for r in conn.execute(q, {"cat": a}).fetchall() if r[0]}
        sb = {str(r[0]).upper() for r in conn.execute(q, {"cat": b}).fetchall() if r[0]}
    only_a = sorted(sa - sb)
    only_b = sorted(sb - sa)
    both = len(sa & sb)
    return html.Div(
        [
            html.Div(
                f"Каталог A={a}: {len(sa)} кодов; B={b}: {len(sb)} кодов; общих: {both}. "
                f"Только в A: {len(only_a)}; только в B: {len(only_b)}.",
                className="mb-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Strong("Только в A", className="small d-block mb-1"),
                            html.Pre(
                                "\n".join(only_a[:400]) + ("\n…" if len(only_a) > 400 else ""),
                                className="small bg-light p-2 rounded",
                                style={"maxHeight": "220px", "overflow": "auto"},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Strong("Только в B", className="small d-block mb-1"),
                            html.Pre(
                                "\n".join(only_b[:400]) + ("\n…" if len(only_b) > 400 else ""),
                                className="small bg-light p-2 rounded",
                                style={"maxHeight": "220px", "overflow": "auto"},
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="g-2",
            ),
        ]
    )


@app.callback(
    Output(f"{PREFIX}-journal-analyze-msg", "children"),
    Output(f"{PREFIX}-tbl-journal-analyze", "data"),
    Output(f"{PREFIX}-tbl-journal-analyze", "columns"),
    Output(f"{PREFIX}-journal-analyze-store", "data"),
    Input(f"{PREFIX}-run-journal-analyze", "n_clicks"),
    State(f"{PREFIX}-upload-cache", "data"),
    State(f"{PREFIX}-work-catalog", "value"),
    prevent_initial_call=True,
)
def run_journal_analyze(_n, upload_cache, work_catalog):
    def _svc_base(code: str) -> str:
        m = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", str(code or "").upper())
        return m.group(1) if m else str(code or "").upper()

    # Взаимозаменяемые услуги (канонизация перед сравнением).
    # Здесь перечисляем base-коды (Axx.xx.xxx / Bxx.xx.xxx), которые считаем эквивалентными.
    _EQUIV_GROUPS: list[set[str]] = [
        {"B04.047.001", "B04.047.003"},
    ]
    _equiv_map: dict[str, str] = {}
    for g in _EQUIV_GROUPS:
        canon = sorted(g)[0]
        for x in g:
            _equiv_map[x] = canon

    def _canon(code_base: str) -> str:
        b = _svc_base(code_base)
        return _equiv_map.get(b, b)

    wc = str(work_catalog or default_active_catalog()).strip() or default_active_catalog()
    cache = upload_cache or {}
    jpath = str(cache.get("journal_path") or "").strip()
    dpath = str(cache.get("detail_path") or "").strip()
    jname = str(cache.get("journal_name") or "").strip()
    dname = str(cache.get("detail_name") or "").strip()
    if not jpath or not dpath or not Path(jpath).exists() or not Path(dpath).exists():
        return (
            dbc.Alert(
                "Сначала загрузите сверху оба файла: detail_services CSV и journal CSV (они должны быть «из кеша/загружены»).",
                color="warning",
                className="py-2 mb-0",
            ),
            [],
            [],
            None,
        )
    raw = Path(jpath).read_bytes()
    raw_detail = Path(dpath).read_bytes()

    dx_lookup = load_diagnosis_lookup_from_db(wc)

    # Generic semicolon CSV parse (utf-8-sig/cp1251 best-effort)
    try:
        try:
            text = raw.decode("utf-8-sig")
            if "\ufffd" in text:
                raise ValueError("bad utf8")
        except Exception:
            text = raw.decode("cp1251", errors="replace")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        rows = [dict(r) for r in reader]
    except Exception as e:
        return dbc.Alert(f"Ошибка разбора journal: {e}", color="danger", className="py-2 mb-0"), [], [], None

    if not rows:
        return dbc.Alert("journal пустой.", color="warning", className="py-2 mb-0"), [], [], None

    # detail_services rows -> talon -> list of service codes (what was actually in card / claim)
    try:
        _fn_detail, detail_rows = read_detail_csv_from_bytes(raw_detail)
    except Exception as e:
        return dbc.Alert(f"Ошибка разбора detail_services: {e}", color="danger", className="py-2 mb-0"), [], [], None
    svc_re = re.compile(r"\b([AB]\d{2}\.\d{2,3}\.\d{3}(?:\.\d{3})?)\b", re.IGNORECASE)
    svc_by_tal: dict[str, list[str]] = {}
    for dr in detail_rows:
        tal = str(dr.get("Талон") or "").strip()
        code = str(dr.get("Код услуги") or "").strip()
        if not tal:
            continue
        m = svc_re.search(code)
        if not m:
            continue
        c = m.group(1).upper()
        svc_by_tal.setdefault(tal, [])
        if c not in svc_by_tal[tal]:
            svc_by_tal[tal].append(c)

    # Heuristics: find columns
    headers = list(rows[0].keys())
    hl = {h: str(h).lower() for h in headers}

    def _find_any(*needles: str) -> str | None:
        for h in headers:
            s = hl.get(h, "")
            if all(n in s for n in needles):
                return h
        return None

    col_tal = _find_any("талон") or _find_any("talon") or headers[0]
    col_diag = _find_any("диагноз") or _find_any("ds1")
    col_spec = _find_any("спец") or _find_any("special")
    col_pos = _find_any("долж") or _find_any("post") or _find_any("position")
    col_services = _find_any("услуг") or _find_any("service")

    # Build specialty match if possible
    spec_items = load_specialties_from_db(catalog=wc)

    def _norm_text(s: str) -> str:
        t = str(s or "").strip().lower().replace("ё", "е")
        t = re.sub(r"[^0-9a-zа-я]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t.replace("врач ", "").replace("врач", "").strip()

    def _match_specialty_id(spec_text: str, pos_text: str) -> int | None:
        src = " ".join([_norm_text(spec_text), _norm_text(pos_text)]).strip()
        if not src:
            return None
        src_tokens = set(src.split())
        best: tuple[float, int] | None = None
        for sid, name in spec_items:
            n = _norm_text(name)
            if not n:
                continue
            if n in src or src in n:
                score = 10.0
            else:
                toks = set(n.split())
                inter = len(src_tokens & toks)
                if inter == 0:
                    continue
                score = inter / max(len(toks), 1)
            if best is None or score > best[0]:
                best = (score, int(sid))
        if best is None:
            return None
        return best[1] if best[0] >= 0.34 else None

    def _diag_code(x: str) -> str:
        m = re.search(r"\b([A-Z]\d{2}(?:\.\d+)?)\b", str(x or "").upper())
        return m.group(1) if m else ""

    # Precompute expected services map for (diag, sid)
    pairs: set[tuple[str, int]] = set()
    for r in rows:
        d = _diag_code(r.get(col_diag, "") if col_diag else "")
        sid = _match_specialty_id(r.get(col_spec, "") if col_spec else "", r.get(col_pos, "") if col_pos else "")
        if d and sid:
            pairs.add((d, sid))
    exp_map: dict[tuple[str, int], list[str]] = {}
    if pairs:
        diag_codes = {d for d, _ in pairs}
        spec_ids = {sid for _, sid in pairs}
        req = load_required_services_for_icd_codes_by_specialty(diag_codes, spec_ids, catalog=wc)
        for (dcode, sid), items in (req or {}).items():
            codes = []
            seen = set()
            for sc, _nm in items or []:
                m = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", str(sc or "").upper())
                base = m.group(1) if m else str(sc or "").upper()
                if base and base not in seen:
                    seen.add(base)
                    codes.append(base)
            exp_map[(str(dcode).upper(), int(sid))] = codes

    out = []
    for r in rows:
        tal = str(r.get(col_tal) or "").strip()
        diag = str(r.get(col_diag) or "").strip() if col_diag else ""
        dcode = _diag_code(diag)
        grp = ""
        if dcode:
            if dcode not in dx_lookup:
                grp = "нет в справочнике (dn_diagnosis)"
            else:
                v = dx_lookup.get(dcode)
                grp = v if v else "(без категории)"
        have = svc_by_tal.get(tal, [])
        services_raw = "; ".join(have)
        sid = _match_specialty_id(r.get(col_spec, "") if col_spec else "", r.get(col_pos, "") if col_pos else "")
        need = exp_map.get((dcode, int(sid))) if (dcode and sid) else []
        # status: strict enough for контроля качества
        # ok только если ВСЕ обязательные услуги (need) присутствуют в карте (по base-кодам).
        if need:
            have_b = {_canon(x) for x in have if x}
            need_b = {_canon(x) for x in need if x}
            missing = sorted([x for x in need_b if x not in have_b])
            extra = sorted([x for x in have_b if x and x not in need_b])
            status = "ok" if not missing else "error"
            # правильные услуги показываем только если ошибка (как вы просили)
            need_str = "; ".join(sorted(need_b)) if missing else ""
        else:
            missing = []
            extra = []
            status = "n/a"
            need_str = ""
        out.append(
            {
                "талон": tal,
                "диагноз": diag,
                "группа_диагноза": grp,
                "specialty_id": sid,
                "услуги_в_карте": services_raw,
                "статус": status,
                "правильные_услуги": need_str,
                "missing": "; ".join(missing) if missing else "",
                "extra": "; ".join(extra) if extra else "",
            }
        )

    cols = [
        {"name": "Талон", "id": "талон"},
        {"name": "Диагноз", "id": "диагноз"},
        {"name": "Группа диагноза", "id": "группа_диагноза"},
        {"name": "specialty_id", "id": "specialty_id"},
        {"name": "Услуги в карте", "id": "услуги_в_карте"},
        {"name": "Статус", "id": "статус"},
        {"name": "Правильные услуги (если ошибка)", "id": "правильные_услуги"},
        {"name": "missing", "id": "missing"},
        {"name": "extra", "id": "extra"},
    ]
    msg = dbc.Alert(
        f"journal обработан: {jname or Path(jpath).name} (+ detail_services: {dname or Path(dpath).name}). "
        f"Строк: {len(out)}. Каталог справочника: {wc}.",
        color="success",
        className="py-2 mb-0",
    )
    # Store full enriched journal (original rows + new fields) for download
    enriched = []
    for base_row, extra in zip(rows, out):
        merged = dict(base_row)
        merged["статус"] = extra["статус"]
        merged["услуги_в_карте"] = extra["услуги_в_карте"]
        merged["правильные_услуги"] = extra["правильные_услуги"]
        merged["группа_диагноза"] = extra["группа_диагноза"]
        merged["missing"] = extra.get("missing", "")
        merged["extra"] = extra.get("extra", "")
        enriched.append(merged)
    return msg, out, cols, {"filename": (jname or "journal.csv"), "rows": enriched}


@app.callback(
    Output(f"{PREFIX}-download-journal-enriched", "data"),
    Input(f"{PREFIX}-download-journal-enriched-btn", "n_clicks"),
    State(f"{PREFIX}-journal-analyze-store", "data"),
    prevent_initial_call=True,
)
def download_journal_enriched(_n, store):
    if not store or not store.get("rows"):
        raise PreventUpdate
    rows = store["rows"]
    fname0 = str(store.get("filename") or "journal.csv")
    stem = re.sub(r"\.csv$", "", fname0, flags=re.IGNORECASE)
    out_name = f"{stem}_enriched.csv"

    # write as semicolon CSV (utf-8-sig) with all original columns + 3 new fields
    # ensure new columns exist in header
    extra_cols = ["статус", "услуги_в_карте", "правильные_услуги"]
    header = list(rows[0].keys())
    for c in extra_cols:
        if c not in header:
            header.append(c)

    def _writer(bytes_io):
        import io as _io

        buf = _io.TextIOWrapper(bytes_io, encoding="utf-8-sig", newline="")
        w = csv.DictWriter(buf, fieldnames=header, delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
        buf.flush()

    return dcc.send_bytes(_writer, out_name)


def _empty_tables():
    return (
        [],
        COLS_DIAG,
        [],
        COLS_ONE,
        [],
        COLS_MULTI,
        None,
    )


def _cat_ticket_rows_for_filter(store: dict | None) -> list[dict]:
    if not store:
        return []
    return store.get("cat_ticket_rows") or []


def _normalize_statuses(values) -> set[str]:
    return {str(v).strip() for v in (values or []) if str(v).strip()}


def _read_semicolon_csv_rows_from_bytes(raw: bytes) -> list[dict[str, str]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    return [dict(r) for r in reader]


def _uploads_dir() -> Path:
    # apps/dash_dn/data/uploads/
    base = Path(__file__).resolve().parent / "data" / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _safe_name(name: str) -> str:
    n = re.sub(r"[^0-9A-Za-zА-Яа-я._-]+", "_", str(name or "").strip())
    return n[:120] or "upload.csv"


def _save_upload(kind: str, filename: str, raw: bytes) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = _uploads_dir() / f"{kind}_{ts}_{_safe_name(filename)}"
    out.write_bytes(raw)
    return out


@app.callback(
    Output(f"{PREFIX}-upload-cache", "data"),
    Input(f"{PREFIX}-upload", "contents"),
    State(f"{PREFIX}-upload", "filename"),
    Input(f"{PREFIX}-upload-journal", "contents"),
    State(f"{PREFIX}-upload-journal", "filename"),
    State(f"{PREFIX}-upload-cache", "data"),
    prevent_initial_call=True,
)
def cache_upload_files(detail_contents, detail_name, journal_contents, journal_name, prev):
    prev = prev or {}
    out = dict(prev)
    if detail_contents:
        try:
            _m, s = detail_contents.split(",", 1)
            raw = base64.b64decode(s)
            p = _save_upload("detail", detail_name or "detail.csv", raw)
            out.update({"detail_path": str(p), "detail_name": str(detail_name or p.name)})
        except Exception:
            pass
    if journal_contents:
        try:
            _m, s = journal_contents.split(",", 1)
            raw = base64.b64decode(s)
            p = _save_upload("journal", journal_name or "journal.csv", raw)
            out.update({"journal_path": str(p), "journal_name": str(journal_name or p.name)})
        except Exception:
            pass
    return out


def _norm_text(v) -> str:
    return str(v or "").strip()


def _has_report_period_in_detail(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and "Отчетный период" in rows[0]


def _inject_fields_from_journal(
    detail_rows: list[dict[str, str]],
    journal_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    if not detail_rows:
        return detail_rows, {"period": 0, "formed": 0}

    tal_col = "Талон"
    period_target_col = "Отчетный период"
    period_journal_col = "Отчетный период выгрузки"
    formed_target_col = "Дата формирования"
    formed_journal_col = "Дата выгрузки"

    journal_by_tal: dict[str, tuple[str, str]] = {}
    for jr in journal_rows:
        tal = _norm_text(jr.get(tal_col))
        per = _norm_text(jr.get(period_journal_col) or jr.get(period_target_col))
        formed = _norm_text(jr.get(formed_journal_col) or jr.get(formed_target_col))
        if tal and per and tal not in journal_by_tal:
            journal_by_tal[tal] = (per, formed)
        elif tal and tal not in journal_by_tal and formed:
            journal_by_tal[tal] = ("", formed)

    out: list[dict[str, str]] = []
    filled_period = 0
    filled_formed = 0
    for dr in detail_rows:
        row = dict(dr)
        tal = _norm_text(row.get(tal_col))
        if tal in journal_by_tal:
            per, formed = journal_by_tal[tal]
            if not _norm_text(row.get(period_target_col)) and per:
                row[period_target_col] = per
                filled_period += 1
            if not _norm_text(row.get(formed_target_col)) and formed:
                row[formed_target_col] = formed
                filled_formed += 1
        out.append(row)
    return out, {"period": filled_period, "formed": filled_formed}


def _ticket_filter_match(ticket_sum: float, op: str, threshold: float) -> bool:
    if op == "lt":
        return ticket_sum < threshold
    if op == "eq":
        return ticket_sum == threshold
    return ticket_sum > threshold


def _filtered_ok_metrics(
    ticket_rows: list[dict],
    op: str,
    threshold: float,
    *,
    statuses: set[str] | None = None,
    by_unit: bool,
) -> dict:
    out: dict = {}
    for row in ticket_rows:
        if statuses and str(row.get("status", "")).strip() not in statuses:
            continue
        if not row.get("svc_ok"):
            continue
        ticket_sum = float(row.get("ticket_sum", 0.0))
        if not _ticket_filter_match(ticket_sum, op, threshold):
            continue
        key = (row.get("cat"), row.get("unit")) if by_unit else row.get("cat")
        if key not in out:
            out[key] = {"n": 0, "sum": 0.0}
        out[key]["n"] += 1
        out[key]["sum"] += ticket_sum
    return out


def _append_cat_filtered_columns(
    data: list[dict],
    cols: list[dict],
    ticket_rows: list[dict],
    statuses: set[str] | None,
    op: str | None,
    threshold: float | None,
    *,
    by_unit: bool,
) -> tuple[list[dict], list[dict]]:
    cols_ext = cols + [
        {
            "name": "Талонов отфильтровано (услуги по справочнику)",
            "id": "n_ok_filtered",
            "type": "numeric",
        },
        {
            "name": "Сумма отфильтровано (услуги по справочнику)",
            "id": "sum_ok_filtered",
            "type": "numeric",
        },
    ]
    if op is None or threshold is None:
        data_ext = [{**row, "n_ok_filtered": 0, "sum_ok_filtered": 0.0} for row in data]
        return data_ext, cols_ext

    metrics = _filtered_ok_metrics(
        ticket_rows,
        op,
        threshold,
        statuses=statuses,
        by_unit=by_unit,
    )
    out = []
    for row in data:
        key = (row.get("cat"), row.get("unit")) if by_unit else row.get("cat")
        agg = metrics.get(key) or {"n": 0, "sum": 0.0}
        out.append(
            {
                **row,
                "n_ok_filtered": int(agg["n"]),
                "sum_ok_filtered": round(float(agg["sum"]), 2),
            }
        )
    return out, cols_ext


def _cat_sum_filter_from_applied(applied: dict | None) -> tuple[str | None, float | None]:
    if not applied:
        return None, None
    op = (applied.get("op") or "gt").strip()
    try:
        threshold = float(applied.get("value"))
    except (TypeError, ValueError):
        return None, None
    if op not in {"gt", "lt", "eq"}:
        op = "gt"
    return op, threshold


def _rows_cat_ticket_filter(report: dict) -> list[dict]:
    tickets = report.get("per_ticket") or []
    mismatch_ids = {
        str(t.get("талон"))
        for t in (report.get("tickets_service_mismatch") or [])
        if t.get("талон") is not None
    }
    out: list[dict] = []
    for t in tickets:
        diagnosis = str(t.get("диагноз", ""))
        ds1_code = str(t.get("ds1_code", "")).strip()
        ds1_cat = str(t.get("ds1_category", "")).strip()
        if ds1_code:
            if ds1_cat:
                cat = ds1_cat
            elif "DS1: нет в справочнике" in str(t.get("diagnosis_note", "")):
                cat = "нет в справочнике (основной)"
            else:
                cat = "(без категории в справочнике)"
        else:
            cat = "(нет диагноза DS1)" if diagnosis == "(без диагноза)" else "(нет извлечённого кода МКБ в DS1)"
        unit = str(t.get("подразделение", "")).strip() or "(не указано)"
        tal = str(t.get("талон", "")).strip()
        out.append(
            {
                "tal": tal,
                "cat": cat,
                "unit": unit,
                "ticket_sum": float(t.get("сумма_талона", 0.0) or 0.0),
                "svc_ok": tal not in mismatch_ids,
                "status": str(t.get("статус", "")).strip(),
                "ds2_categories": list(t.get("ds2_categories") or []),
                "report_period": str(t.get("отчетный_период", "")).strip(),
                "formed_date_raw": str(t.get("дата_формирования", "")).strip(),
                "end_date_raw": str(t.get("дата_окончания_лечения", "")).strip(),
            }
        )
    return out


def _date_to_iso(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _ticket_rows_with_dates(ticket_rows: list[dict]) -> list[dict]:
    out = []
    for r in ticket_rows:
        out.append(
            {
                **r,
                "formed_date": _date_to_iso(r.get("formed_date_raw", "")),
                "end_date": _date_to_iso(r.get("end_date_raw", "")),
            }
        )
    return out


def _iso_today_fallback(end_date_iso: str, formed_iso: str) -> str:
    return end_date_iso or formed_iso or ""


def _safe_bool(v) -> bool:
    return bool(v) and str(v).lower() not in {"false", "0", "none", ""}


def _ts_to_dt_str(ts: int | float | str | None) -> str:
    try:
        v = int(float(ts)) if ts is not None and str(ts).strip() else 0
    except Exception:
        v = 0
    if v <= 0:
        return ""
    return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")


def _date_in_range(value_iso: str, start_iso: str | None, end_iso: str | None) -> bool:
    if not start_iso and not end_iso:
        return True
    if not value_iso:
        return False
    if start_iso and value_iso < start_iso:
        return False
    if end_iso and value_iso > end_iso:
        return False
    return True


def _filter_cat_ticket_rows(
    ticket_rows: list[dict],
    report_periods: list[str] | None,
    formed_start: str | None,
    formed_end: str | None,
    end_start: str | None,
    end_end: str | None,
) -> list[dict]:
    periods = {str(v).strip() for v in (report_periods or []) if str(v).strip()}
    out: list[dict] = []
    for r in ticket_rows:
        if periods and str(r.get("report_period", "")).strip() not in periods:
            continue
        if not _date_in_range(str(r.get("formed_date", "")), formed_start, formed_end):
            continue
        if not _date_in_range(str(r.get("end_date", "")), end_start, end_end):
            continue
        out.append(r)
    return out


def _cat_detail_rows(
    ticket_rows: list[dict],
    axis: str,
    unit: str,
    include_notref: bool,
    active_cell: dict | None,
    cat_table_data: list[dict] | None,
) -> tuple[str, list[dict]]:
    if not active_cell or not cat_table_data:
        return "Нажмите на числовую ячейку в «Своде по категориям».", []
    row_idx = active_cell.get("row")
    col_id = active_cell.get("column_id")
    if row_idx is None or col_id is None or row_idx >= len(cat_table_data):
        return "Нажмите на числовую ячейку в «Своде по категориям».", []

    selected_row = cat_table_data[row_idx] or {}
    selected_cat = str(selected_row.get("cat", "")).strip()
    selected_unit = str(selected_row.get("unit", "")).strip()
    rows = list(ticket_rows)
    if not include_notref:
        rows = [r for r in rows if not _is_notref_category(str(r.get("cat", "")).strip())]

    is_total_row = selected_cat.startswith("ИТОГО")
    if not is_total_row:
        if axis == "ds2":
            rows = [r for r in rows if selected_cat in [str(x).strip() for x in (r.get("ds2_categories") or [])]]
        else:
            rows = [r for r in rows if str(r.get("cat", "")).strip() == selected_cat]
            if unit == "yes":
                rows = [r for r in rows if str(r.get("unit", "")).strip() == selected_unit]

    if col_id in {"n_ok", "sum_ok", "n_ok_filtered", "sum_ok_filtered"}:
        rows = [r for r in rows if bool(r.get("svc_ok"))]
    elif col_id in {"n_bad", "sum_bad"}:
        rows = [r for r in rows if not bool(r.get("svc_ok"))]
    elif col_id in {"cat", "unit"}:
        return "Для детализации выбирайте числовые колонки.", []

    out = []
    for r in rows:
        out.append(
            {
                "tal": r.get("tal", ""),
                "status": r.get("status", ""),
                "report_period": r.get("report_period", ""),
                "formed_date_raw": r.get("formed_date_raw", ""),
                "end_date_raw": r.get("end_date_raw", ""),
                "cat": r.get("cat", ""),
                "unit": r.get("unit", ""),
                "ticket_sum": round(float(r.get("ticket_sum", 0.0) or 0.0), 2),
                "svc_ok": "Да" if bool(r.get("svc_ok")) else "Нет",
                "ds2_categories_line": "; ".join(r.get("ds2_categories") or []),
            }
        )
    out.sort(key=lambda x: (str(x.get("tal", "")), str(x.get("status", ""))))

    col_title = str(col_id)
    scope = "ИТОГО (все категории)" if is_total_row else f"Категория: {selected_cat}"
    if not is_total_row and axis != "ds2" and unit == "yes":
        scope += f"; Подразделение: {selected_unit}"
    title = f"{scope}; колонка: {col_title}; записей: {len(out)}"
    return title, out


def _is_notref_category(cat: str) -> bool:
    c = str(cat or "").strip().lower()
    return "нет в справочнике" in c


def _append_total_row(data: list[dict], cols: list[dict], *, by_unit: bool) -> list[dict]:
    if not data:
        return data
    numeric_ids = [str(c.get("id")) for c in cols if c.get("type") == "numeric"]
    total_row = {"cat": "ИТОГО (все категории)"}
    if by_unit:
        total_row["unit"] = "-"
    for cid in numeric_ids:
        s = 0.0
        for r in data:
            try:
                s += float(r.get(cid, 0.0) or 0.0)
            except (TypeError, ValueError):
                continue
        total_row[cid] = int(s) if float(s).is_integer() else round(s, 2)
    return [*data, total_row]


def _cat_table_from_ticket_rows(
    ticket_rows: list[dict],
    axis: str,
    unit: str,
    statuses: set[str] | None = None,
    include_notref: bool = True,
) -> tuple[list[dict], list[dict]]:
    rows = ticket_rows
    if statuses:
        rows = [r for r in rows if str(r.get("status", "")).strip() in statuses]
    if not include_notref:
        if axis == "ds2":
            rows = [
                r
                for r in rows
                if not any(_is_notref_category(str(x).strip()) for x in (r.get("ds2_categories") or []))
            ]
        else:
            rows = [r for r in rows if not _is_notref_category(str(r.get("cat", "")).strip())]

    if axis == "ds2":
        agg: dict[str, int] = {}
        for row in rows:
            for cat in row.get("ds2_categories") or []:
                key = str(cat).strip() or "(пусто)"
                agg[key] = int(agg.get(key, 0)) + 1
        data = [{"cat": k, "n": n} for k, n in agg.items()]
        data.sort(key=lambda x: (-x["n"], x["cat"]))
        return data, COLS_CAT_DS2

    by_unit_enabled = unit == "yes"
    agg_ds1: dict = {}
    for row in rows:
        key = (row.get("cat"), row.get("unit")) if by_unit_enabled else row.get("cat")
        if key not in agg_ds1:
            agg_ds1[key] = {"n": 0, "sum": 0.0, "n_ok": 0, "sum_ok": 0.0}
        ticket_sum = float(row.get("ticket_sum", 0.0) or 0.0)
        agg_ds1[key]["n"] += 1
        agg_ds1[key]["sum"] += ticket_sum
        if row.get("svc_ok"):
            agg_ds1[key]["n_ok"] += 1
            agg_ds1[key]["sum_ok"] += ticket_sum

    data = []
    for key, a in agg_ds1.items():
        n = int(a["n"])
        n_ok = int(a["n_ok"])
        s = round(float(a["sum"]), 2)
        s_ok = round(float(a["sum_ok"]), 2)
        row = {
            "cat": key[0] if by_unit_enabled else key,
            "n": n,
            "sum": s,
            "n_ok": n_ok,
            "sum_ok": s_ok,
            "n_bad": n - n_ok,
            "sum_bad": round(s - s_ok, 2),
        }
        if by_unit_enabled:
            row["unit"] = key[1]
        data.append(row)

    if by_unit_enabled:
        data.sort(key=lambda x: (-x["n"], str(x["cat"]), str(x["unit"])))
        return data, COLS_CAT_DS1_UNIT
    data.sort(key=lambda x: (-x["n"], str(x["cat"])))
    return data, COLS_CAT_DS1


def _price_matrix_from_ticket_rows(
    ticket_rows: list[dict],
    axis: str,
    metric: str,
) -> tuple[list[dict], list[dict], str]:
    statuses = sorted(
        {str(r.get("status", "")).strip() for r in ticket_rows if str(r.get("status", "")).strip()}
    )
    if not statuses:
        return [], [{"name": "Категория", "id": "cat"}], "Нет данных по статусам."

    agg: dict[str, dict[str, float]] = {}

    for row in ticket_rows:
        status = str(row.get("status", "")).strip()
        if not status:
            continue
        if axis == "ds2":
            cats = [str(v).strip() for v in (row.get("ds2_categories") or []) if str(v).strip()]
            if not cats:
                continue
        else:
            cats = [str(row.get("cat", "")).strip() or "(пусто)"]

        for cat in cats:
            if cat not in agg:
                agg[cat] = {st: 0.0 for st in statuses}
            if metric == "sum":
                agg[cat][status] += float(row.get("ticket_sum", 0.0) or 0.0)
            else:
                agg[cat][status] += 1.0

    if not agg:
        return [], [{"name": "Категория", "id": "cat"}], "Нет данных для выбранного режима."

    data = []
    for cat, by_st in agg.items():
        out = {"cat": cat}
        total = 0.0
        for st in statuses:
            v = float(by_st.get(st, 0.0))
            out[st] = round(v, 2) if metric == "sum" else int(v)
            total += v
        out["total"] = round(total, 2) if metric == "sum" else int(total)
        data.append(out)
    data.sort(key=lambda x: (-float(x.get("total", 0.0) or 0.0), str(x.get("cat", ""))))

    cols = [{"name": "Категория", "id": "cat"}]
    cols.extend({"name": f"Статус {st}", "id": st, "type": "numeric"} for st in statuses)
    cols.append({"name": "Итого", "id": "total", "type": "numeric"})

    if axis == "ds2":
        note = "DS2: талон может попасть в несколько категорий (по сопутствующим кодам)."
    else:
        note = "DS1: каждый талон учитывается в одной основной категории."
    return data, cols, note


def _price_bucket_labels() -> list[str]:
    return [f"{i}-{i + 400}" for i in range(0, 6000, 400)] + ["6000+"]


def _price_bucket_label(value: float) -> str:
    v = float(value or 0.0)
    if v >= 6000.0:
        return "6000+"
    low = int(v // 400) * 400
    high = low + 400
    return f"{low}-{high}"


def _price_bucket_matrix_from_ticket_rows(
    ticket_rows: list[dict],
    axis: str,
    metric: str,
) -> tuple[list[dict], list[dict], str]:
    buckets = _price_bucket_labels()
    agg: dict[str, dict[str, float]] = {}
    total_by_bucket = {b: 0.0 for b in buckets}

    for row in ticket_rows:
        ticket_sum = float(row.get("ticket_sum", 0.0) or 0.0)
        bucket = _price_bucket_label(ticket_sum)
        if axis == "ds2":
            cats = [str(v).strip() for v in (row.get("ds2_categories") or []) if str(v).strip()]
            if not cats:
                continue
        else:
            cats = [str(row.get("cat", "")).strip() or "(пусто)"]

        for cat in cats:
            if cat not in agg:
                agg[cat] = {b: 0.0 for b in buckets}
            add = ticket_sum if metric == "sum" else 1.0
            agg[cat][bucket] += add
            total_by_bucket[bucket] += add

    if not agg:
        cols = [{"name": "Группа", "id": "cat"}]
        cols.extend({"name": b, "id": b, "type": "numeric"} for b in buckets)
        cols.append({"name": "Итого", "id": "total", "type": "numeric"})
        return [], cols, "Нет данных для выбранного режима."

    data = []
    for cat, by_bucket in agg.items():
        out = {"cat": cat}
        total = 0.0
        for b in buckets:
            v = float(by_bucket.get(b, 0.0))
            out[b] = round(v, 2) if metric == "sum" else int(v)
            total += v
        out["total"] = round(total, 2) if metric == "sum" else int(total)
        data.append(out)
    data.sort(key=lambda x: (-float(x.get("total", 0.0) or 0.0), str(x.get("cat", ""))))

    row_total = {"cat": "Все группы"}
    total_all = 0.0
    for b in buckets:
        v = float(total_by_bucket.get(b, 0.0))
        row_total[b] = round(v, 2) if metric == "sum" else int(v)
        total_all += v
    row_total["total"] = round(total_all, 2) if metric == "sum" else int(total_all)
    data.append(row_total)

    cols = [{"name": "Группа", "id": "cat"}]
    cols.extend({"name": b, "id": b, "type": "numeric"} for b in buckets)
    cols.append({"name": "Итого", "id": "total", "type": "numeric"})

    note = (
        "Режим диапазонов: 0-400, 400-800, ... , 5600-6000, 6000+."
        " Строка «Все группы» показывает общий итог."
    )
    return data, cols, note


def _matrix_heatmap_styles(data: list[dict], cols: list[dict]) -> list[dict]:
    value_cols = [c.get("id") for c in cols if c.get("id") not in {"cat", "total"}]
    value_cols = [c for c in value_cols if c]
    styles: list[dict] = []
    for row_idx, row in enumerate(data):
        values: list[float] = []
        for cid in value_cols:
            try:
                values.append(float(row.get(cid, 0.0) or 0.0))
            except (TypeError, ValueError):
                values.append(0.0)
        row_max = max(values) if values else 0.0
        if row_max <= 0:
            continue
        for cid, val in zip(value_cols, values):
            ratio = max(0.0, min(1.0, val / row_max))
            alpha = 0.12 + 0.68 * ratio
            styles.append(
                {
                    "if": {"row_index": row_idx, "column_id": cid},
                    "backgroundColor": f"rgba(13, 110, 253, {alpha:.3f})",
                    "color": "#111",
                    "fontWeight": "600" if ratio >= 0.98 else "500",
                }
            )
    return styles


_SERVICE_CODE_IN_TEXT_RE = re.compile(r"\b([AB]\d{2}\.\d{2,3}\.\d{3}(?:\.\d{3})?)\b", re.IGNORECASE)


def _expected_services_from_suggestion(s: str, begin_date: str, end_date: str) -> list[dict]:
    codes: list[str] = []
    seen: set[str] = set()
    for m in _SERVICE_CODE_IN_TEXT_RE.finditer(str(s or "")):
        c = m.group(1).upper()
        if c not in seen:
            seen.add(c)
            codes.append(c)
    out = []
    for c in codes:
        out.append(
            {
                "code": c,
                "begin_date": begin_date,
                "end_date": end_date,
                "qty": 1,
            }
        )
    return out


def _errors_visibility(flt: str):
    show_svc = flt in ("all", "svc")
    show_dx = flt in ("all", "dx")
    return (
        {} if show_svc else {"display": "none"},
        {} if show_dx else {"display": "none"},
    )


def _match_sum(value: float, op: str, threshold: float) -> bool:
    if op == "lt":
        return value < threshold
    if op == "eq":
        return value == threshold
    return value > threshold


def _block_params_normalized(params: dict | None) -> dict:
    p = params or {}
    statuses = [str(v).strip() for v in (p.get("statuses") or []) if str(v).strip()]
    only_errors = bool(p.get("only_errors", True))
    sum_enabled = bool(p.get("sum_enabled", False))
    op = str(p.get("sum_op") or "gt").strip()
    if op not in {"gt", "lt", "eq"}:
        op = "gt"
    threshold = None
    try:
        threshold = float(p.get("sum_value"))
    except (TypeError, ValueError):
        threshold = None
    logic = str(p.get("logic") or "and").strip().lower()
    if logic not in {"and", "or"}:
        logic = "and"
    return {
        "statuses": statuses,
        "only_errors": only_errors,
        "sum_enabled": sum_enabled,
        "sum_op": op,
        "sum_threshold": threshold,
        "logic": logic,
    }


def _filter_block_rows(rows: list[dict], params: dict) -> list[dict]:
    p = _block_params_normalized(params)
    data = list(rows)

    if p["statuses"]:
        st = set(p["statuses"])
        data = [r for r in data if str(r.get("status", "")).strip() in st]

    conds = []
    if p["only_errors"]:
        conds.append(lambda r: str(r.get("error", "")) == "Да")
    if p["sum_enabled"] and p["sum_threshold"] is not None:
        op = p["sum_op"]
        thr = float(p["sum_threshold"])
        conds.append(lambda r, _op=op, _thr=thr: _match_sum(float(r.get("sum", 0.0) or 0.0), _op, _thr))

    if not conds:
        return data
    if p["logic"] == "or" and len(conds) > 1:
        return [r for r in data if any(c(r) for c in conds)]
    return [r for r in data if all(c(r) for c in conds)]


@app.callback(
    Output(f"{PREFIX}-block-statuses", "options"),
    Input(f"{PREFIX}-report-store", "data"),
)
def update_block_status_options(store):
    rows = (store or {}).get("block_tickets") or []
    values = sorted({str(r.get("status", "")).strip() for r in rows if str(r.get("status", "")).strip()})
    return [{"label": v, "value": v} for v in values]


@app.callback(
    Output(f"{PREFIX}-block-sum-controls", "style"),
    Input(f"{PREFIX}-block-sum-enabled", "value"),
)
def toggle_block_sum_controls(sum_enabled):
    return {} if bool(sum_enabled) else {"display": "none"}


@app.callback(
    Output(f"{PREFIX}-block-applied", "data"),
    Input(f"{PREFIX}-block-apply", "n_clicks"),
    State(f"{PREFIX}-block-statuses", "value"),
    State(f"{PREFIX}-block-only-errors", "value"),
    State(f"{PREFIX}-block-sum-enabled", "value"),
    State(f"{PREFIX}-block-sum-op", "value"),
    State(f"{PREFIX}-block-sum-value", "value"),
    State(f"{PREFIX}-block-logic", "value"),
    prevent_initial_call=True,
)
def apply_block_filters(n_clicks, statuses, only_errors, sum_enabled, sum_op, sum_value, logic):
    _ = n_clicks
    return {
        "statuses": statuses or [],
        "only_errors": "yes" in (only_errors or []),
        "sum_enabled": bool(sum_enabled),
        "sum_op": sum_op or "gt",
        "sum_value": sum_value,
        "logic": logic or "and",
    }


@app.callback(
    Output(f"{PREFIX}-tbl-block", "data"),
    Output(f"{PREFIX}-tbl-block", "columns"),
    Output(f"{PREFIX}-block-summary", "children"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-block-applied", "data"),
)
def update_block_table(store, applied):
    rows = (store or {}).get("block_tickets") or []
    total = len(rows)
    params = applied or {"statuses": [], "only_errors": True, "sum_enabled": False, "sum_op": "gt", "sum_value": None, "logic": "and"}
    data = _filter_block_rows(rows, params)
    p = _block_params_normalized(params)
    logic_label = "ИЛИ" if p["logic"] == "or" else "И"
    summary = f"Отобрано талонов: {len(data)} из {total}. Логика ошибок/стоимости: {logic_label}."
    return data, COLS_BLOCK, summary


@app.callback(
    Output(f"{PREFIX}-cat-sum-applied", "data"),
    Input(f"{PREFIX}-cat-sum-apply", "n_clicks"),
    State(f"{PREFIX}-cat-sum-op", "value"),
    State(f"{PREFIX}-cat-sum-value", "value"),
    prevent_initial_call=True,
)
def apply_cat_sum_filter(n_clicks, op, value):
    _ = n_clicks
    return {
        "op": op or "gt",
        "value": value,
    }


@app.callback(
    Output(f"{PREFIX}-cat-statuses", "options"),
    Input(f"{PREFIX}-report-store", "data"),
)
def update_cat_status_options(store):
    rows = _ticket_rows_with_dates(_cat_ticket_rows_for_filter(store))
    values = sorted({str(r.get("status", "")).strip() for r in rows if str(r.get("status", "")).strip()})
    return [{"label": v, "value": v} for v in values]


@app.callback(
    Output(f"{PREFIX}-cat-report-periods", "options"),
    Input(f"{PREFIX}-report-store", "data"),
)
def update_cat_period_options(store):
    rows = _ticket_rows_with_dates(_cat_ticket_rows_for_filter(store))
    values = sorted({str(r.get("report_period", "")).strip() for r in rows if str(r.get("report_period", "")).strip()})
    return [{"label": v, "value": v} for v in values]


@app.callback(
    Output(f"{PREFIX}-tbl-cat", "data"),
    Output(f"{PREFIX}-tbl-cat", "columns"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-cat-report-periods", "value"),
    Input(f"{PREFIX}-cat-formed-range", "start_date"),
    Input(f"{PREFIX}-cat-formed-range", "end_date"),
    Input(f"{PREFIX}-cat-end-range", "start_date"),
    Input(f"{PREFIX}-cat-end-range", "end_date"),
    Input(f"{PREFIX}-cat-statuses", "value"),
    Input(f"{PREFIX}-cat-include-notref", "value"),
    Input(f"{PREFIX}-cat-axis", "value"),
    Input(f"{PREFIX}-cat-unit", "value"),
    Input(f"{PREFIX}-cat-sum-enabled", "value"),
    Input(f"{PREFIX}-cat-sum-applied", "data"),
)
def update_cat_table(
    store,
    periods_value,
    formed_start,
    formed_end,
    end_start,
    end_end,
    statuses_value,
    include_notref,
    axis,
    unit,
    sum_enabled,
    cat_sum_applied,
):
    axis = axis or "ds1"
    unit = unit or "no"
    ticket_rows = _ticket_rows_with_dates(_cat_ticket_rows_for_filter(store))
    ticket_rows = _filter_cat_ticket_rows(
        ticket_rows,
        periods_value,
        formed_start,
        formed_end,
        end_start,
        end_end,
    )
    statuses = _normalize_statuses(statuses_value)
    include_notref = bool(include_notref)
    data, cols = _cat_table_from_ticket_rows(
        ticket_rows,
        axis,
        unit,
        statuses,
        include_notref=include_notref,
    )
    if bool(sum_enabled) and axis == "ds1":
        op, threshold = _cat_sum_filter_from_applied(cat_sum_applied)
        data, cols = _append_cat_filtered_columns(
            data,
            cols,
            ticket_rows,
            statuses,
            op,
            threshold,
            by_unit=(unit == "yes"),
        )
    data = _append_total_row(data, cols, by_unit=(unit == "yes" and axis != "ds2"))
    return data, cols


@app.callback(
    Output(f"{PREFIX}-cat-details-title", "children"),
    Output(f"{PREFIX}-tbl-cat-details", "data"),
    Output(f"{PREFIX}-tbl-cat-details", "columns"),
    Input(f"{PREFIX}-tbl-cat", "active_cell"),
    State(f"{PREFIX}-tbl-cat", "data"),
    State(f"{PREFIX}-report-store", "data"),
    State(f"{PREFIX}-cat-report-periods", "value"),
    State(f"{PREFIX}-cat-formed-range", "start_date"),
    State(f"{PREFIX}-cat-formed-range", "end_date"),
    State(f"{PREFIX}-cat-end-range", "start_date"),
    State(f"{PREFIX}-cat-end-range", "end_date"),
    State(f"{PREFIX}-cat-statuses", "value"),
    State(f"{PREFIX}-cat-include-notref", "value"),
    State(f"{PREFIX}-cat-axis", "value"),
    State(f"{PREFIX}-cat-unit", "value"),
)
def update_cat_details_table(
    active_cell,
    cat_table_data,
    store,
    periods_value,
    formed_start,
    formed_end,
    end_start,
    end_end,
    statuses_value,
    include_notref,
    axis,
    unit,
):
    axis = axis or "ds1"
    unit = unit or "no"
    ticket_rows = _ticket_rows_with_dates(_cat_ticket_rows_for_filter(store))
    ticket_rows = _filter_cat_ticket_rows(
        ticket_rows,
        periods_value,
        formed_start,
        formed_end,
        end_start,
        end_end,
    )
    statuses = _normalize_statuses(statuses_value)
    if statuses:
        ticket_rows = [r for r in ticket_rows if str(r.get("status", "")).strip() in statuses]

    title, data = _cat_detail_rows(
        ticket_rows,
        axis,
        unit,
        bool(include_notref),
        active_cell,
        cat_table_data,
    )
    return title, data, COLS_CAT_DETAILS


@app.callback(
    Output(f"{PREFIX}-pm-statuses", "options"),
    Input(f"{PREFIX}-report-store", "data"),
)
def update_price_matrix_status_options(store):
    rows = _cat_ticket_rows_for_filter(store)
    values = sorted({str(r.get("status", "")).strip() for r in rows if str(r.get("status", "")).strip()})
    return [{"label": v, "value": v} for v in values]


@app.callback(
    Output(f"{PREFIX}-tbl-price-matrix", "data"),
    Output(f"{PREFIX}-tbl-price-matrix", "columns"),
    Output(f"{PREFIX}-tbl-price-matrix", "style_data_conditional"),
    Output(f"{PREFIX}-pm-note", "children"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-pm-statuses", "value"),
    Input(f"{PREFIX}-pm-mode", "value"),
    Input(f"{PREFIX}-pm-axis", "value"),
    Input(f"{PREFIX}-pm-metric", "value"),
)
def update_price_matrix_table(store, statuses_value, mode, axis, metric):
    rows = _cat_ticket_rows_for_filter(store)
    statuses = _normalize_statuses(statuses_value)
    if statuses:
        rows = [r for r in rows if str(r.get("status", "")).strip() in statuses]
    mode = mode or "status"
    axis = axis or "ds1"
    metric = metric or "count"
    if mode == "price":
        data, cols, note = _price_bucket_matrix_from_ticket_rows(rows, axis, metric)
    else:
        data, cols, note = _price_matrix_from_ticket_rows(rows, axis, metric)
    styles = _matrix_heatmap_styles(data, cols)
    return data, cols, styles, note


@app.callback(
    Output(f"{PREFIX}-cat-sum-controls", "style"),
    Input(f"{PREFIX}-cat-sum-enabled", "value"),
)
def toggle_cat_sum_controls(sum_enabled):
    return {} if bool(sum_enabled) else {"display": "none"}


@app.callback(
    Output(f"{PREFIX}-tbl-errors-svc", "data"),
    Output(f"{PREFIX}-tbl-errors-svc", "columns"),
    Output(f"{PREFIX}-tbl-errors-dx", "data"),
    Output(f"{PREFIX}-tbl-errors-dx", "columns"),
    Output(f"{PREFIX}-errors-svc-wrap", "style"),
    Output(f"{PREFIX}-errors-dx-wrap", "style"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-errors-filter", "value"),
)
def update_errors_tables(store, flt):
    flt = flt or "all"
    st_svc, st_dx = _errors_visibility(flt)
    if not store:
        return [], COLS_SVC_TICKET, [], COLS_DX_MISMATCH, st_svc, st_dx
    return (
        store.get("svc_ticket") or [],
        COLS_SVC_TICKET,
        store.get("dx_mismatch") or [],
        COLS_DX_MISMATCH,
        st_svc,
        st_dx,
    )


@app.callback(
    Output(f"{PREFIX}-bot-enqueue-msg", "children"),
    Input(f"{PREFIX}-bot-enqueue", "n_clicks"),
    State(f"{PREFIX}-report-store", "data"),
    prevent_initial_call=True,
)
def enqueue_bot_tasks(n_clicks, store):
    _ = n_clicks
    if not store:
        return "Нет данных отчёта. Сначала загрузите и обработайте CSV."

    svc_rows = store.get("svc_ticket") or []
    if not svc_rows:
        return "Нет ошибок по услугам — задачи не сформированы."

    rows_by_tal = {str(r.get("tal")): r for r in (store.get("cat_ticket_rows") or [])}

    tasks: list[bot_db.TaskPayload] = []
    for r in svc_rows:
        tal = str(r.get("tal") or "").strip()
        if not tal:
            continue

        cat_row = rows_by_tal.get(tal) or {}
        end_iso = _date_to_iso(cat_row.get("end_date_raw", ""))
        formed_iso = _date_to_iso(cat_row.get("formed_date_raw", ""))
        d = _iso_today_fallback(end_iso, formed_iso)

        expected = _expected_services_from_suggestion(r.get("svc_dx", ""), d, d)
        if not expected:
            continue

        payload = bot_db.TaskPayload(
            talon_id=tal,
            expected_services=[bot_db.ExpectedService(**x) for x in expected],
            mode="add_update",
            context={"source": "analysis_errors_svc", "status": str(r.get("status") or "")},
        )
        tasks.append(payload)

    if not tasks:
        return "Не получилось извлечь «ожидаемые услуги» из колонки «Услуги по диагнозам»."

    bot_db.init_db()
    ids = bot_db.enqueue_tasks(tasks)
    return f"Задачи добавлены в очередь: {len(ids)}."


@app.callback(
    Output(f"{PREFIX}-tbl-bot-tasks", "data"),
    Output(f"{PREFIX}-tbl-bot-tasks", "columns"),
    Output(f"{PREFIX}-bot-last-updated", "children"),
    Output(f"{PREFIX}-bot-poll", "disabled"),
    Output(f"{PREFIX}-bot-queue-stats", "children"),
    Input(f"{PREFIX}-bot-poll", "n_intervals"),
    Input(f"{PREFIX}-bot-refresh", "n_clicks"),
    Input(f"{PREFIX}-bot-autorefresh", "value"),
)
def update_bot_tasks_table(_n, _refresh, autoval):
    bot_db.init_db()
    rows = bot_db.list_tasks(limit=200)
    stats = bot_db.queue_stats()
    data = []
    for t in rows:
        art = t.get("artifact_dir") or ""
        st = t.get("status", "")
        data.append(
            {
                "id": t.get("id"),
                "talon_id": t.get("talon_id", ""),
                "status": st,
                "status_ru": _bot_status_ru(st),
                "attempt": t.get("attempt", 0),
                "created": _ts_to_dt_str(t.get("created_at")),
                "locked": _ts_to_dt_str(t.get("locked_at")),
                "worker": t.get("locked_by", ""),
                "error": (t.get("last_error") or "")[:200],
                "artifacts": f"[open]({('file:///' + art.replace('\\\\','/'))})" if art else "",
            }
        )

    cols = [
        {"name": "id", "id": "id"},
        {"name": "attempt", "id": "attempt"},
        {"name": "created", "id": "created"},
        {"name": "locked", "id": "locked"},
        {"name": "talon", "id": "talon_id"},
        {"name": "status", "id": "status"},
        {"name": "статус (рус)", "id": "status_ru"},
        {"name": "worker", "id": "worker"},
        {"name": "error", "id": "error"},
        {"name": "artifacts", "id": "artifacts", "presentation": "markdown"},
    ]
    disabled = "on" not in (autoval or [])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # render stats
    bs = stats.get("by_status") or {}
    pw = stats.get("per_worker") or []
    totals_line = (
        f"Очередь: queued={bs.get('queued',0)} · running={bs.get('running',0)} · "
        f"succeeded={bs.get('succeeded',0)} · failed={bs.get('failed',0)} · cancelled={bs.get('cancelled',0)}"
    )
    worker_lines = []
    for r in pw:
        avg = r.get("avg_sec")
        avg_s = f"{avg/60:.1f} мин" if isinstance(avg, (int, float)) else "—"
        worker_lines.append(
            f"{r.get('worker')}: ok={r.get('succeeded',0)} err={r.get('failed',0)} "
            f"run={r.get('running',0)} avg={avg_s}"
        )
    stats_text = totals_line + ("\n" + "\n".join(worker_lines) if worker_lines else "")
    return data, cols, f"Последнее обновление: {ts}", disabled, html.Pre(stats_text, className="mb-0")


@app.callback(
    Output(f"{PREFIX}-bot-worker-cmd", "children"),
    Output(f"{PREFIX}-bot-worker-cmds", "value"),
    Input(f"{PREFIX}-bot-worker-headful", "value"),
    Input(f"{PREFIX}-bot-worker-slowmo", "value"),
    Input(f"{PREFIX}-bot-worker-n", "value"),
    Input(f"{PREFIX}-bot-worker-one-headful", "value"),
)
def bot_worker_cmd(headful_val, slowmo, n_workers, one_headful_val):
    headful = "on" in (headful_val or [])
    try:
        slow = int(slowmo or 0)
    except (TypeError, ValueError):
        slow = 0
    db_path = str(bot_db.get_db_path())
    try:
        n = int(n_workers or 1)
    except (TypeError, ValueError):
        n = 1
    n = max(1, min(20, n))
    one_headful = "on" in (one_headful_val or [])
    parts = []
    parts.append(f"$env:DASH_DN_BOT_TASKS_SQLITE='{db_path}';")
    if headful:
        parts.append("$env:CLAIM_BOT_HEADLESS='false';")
        parts.append(f"$env:CLAIM_BOT_SLOWMO_MS='{max(0, slow)}';")
    else:
        parts.append("$env:CLAIM_BOT_HEADLESS='true';")
    parts.append("$env:CLAIM_BOT_BROWSER='chromium';")
    parts.append("py -3 -c \"from apps.dash_dn.claim_bot.worker import run_forever; run_forever()\"")
    single_cmd = " ".join(parts)

    lines: list[str] = []
    for i in range(1, n + 1):
        wid = f"worker-{i}"
        head = False
        if one_headful:
            head = i == 1
        else:
            head = headful
        l: list[str] = [f"# {wid}", f"$env:DASH_DN_BOT_TASKS_SQLITE='{db_path}';"]
        if head:
            l += ["$env:CLAIM_BOT_HEADLESS='false';", f"$env:CLAIM_BOT_SLOWMO_MS='{max(0, slow)}';"]
        else:
            l += ["$env:CLAIM_BOT_HEADLESS='true';"]
        l += [
            "$env:CLAIM_BOT_BROWSER='chromium';",
            f"$env:CLAIM_BOT_WORKER_ID='{wid}';",
            'py -3 -c "from apps.dash_dn.claim_bot.worker import run_forever; run_forever()"',
        ]
        lines.append(" ".join(l))
        lines.append("")
    multi_cmds = "\n".join(lines).strip()
    return single_cmd, multi_cmds


@app.callback(
    Output(f"{PREFIX}-bot-queue-msg", "children"),
    Input(f"{PREFIX}-bot-cancel-queued", "n_clicks"),
    Input(f"{PREFIX}-bot-requeue-running", "n_clicks"),
    Input(f"{PREFIX}-bot-purge-all", "n_clicks"),
)
def bot_queue_controls(n_cancel, n_requeue, n_purge):
    if not n_cancel and not n_requeue and not n_purge:
        raise PreventUpdate
    triggered = (callback_context.triggered[0]["prop_id"] if callback_context.triggered else "")
    if triggered.endswith("bot-cancel-queued.n_clicks"):
        n = bot_db.cancel_queued()
        return f"Отменено queued задач: {n}. (Воркер их не возьмёт.)"
    if triggered.endswith("bot-requeue-running.n_clicks"):
        n = bot_db.requeue_stuck_running(older_than_seconds=300)
        return f"Сброшено зависших running задач обратно в queued: {n}."
    if triggered.endswith("bot-purge-all.n_clicks"):
        n = bot_db.purge_tasks()
        return f"Удалено задач из очереди: {n}."
    raise PreventUpdate


def _split_prefixes(s: str) -> set[str]:
    out = set()
    for part in str(s or "").replace(";", ",").split(","):
        p = part.strip().upper()
        if p:
            out.add(p)
    return out


_DOCTOR_ID_RE = re.compile(r"\b(\d{5,})\b")


def _extract_doctor_id(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    m = _DOCTOR_ID_RE.search(s)
    return m.group(1) if m else ""


@app.callback(
    Output(f"{PREFIX}-bot-cand-status", "options"),
    Output(f"{PREFIX}-bot-cand-doctor", "options"),
    Output(f"{PREFIX}-bot-cand-unit", "options"),
    Output(f"{PREFIX}-bot-cand-specialty-id", "options"),
    Output(f"{PREFIX}-bot-bulk-specialty-id", "options"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-work-catalog", "value"),
)
def update_bot_candidate_options(store, work_catalog):
    if not store:
        return [], [], [], [], []
    wc = str(work_catalog or default_active_catalog()).strip() or default_active_catalog()
    rows = store.get("svc_ticket") or []
    statuses = sorted({str(r.get("status") or "").strip() for r in rows if str(r.get("status") or "").strip()})
    doctors = sorted({str(r.get("doctor") or "").strip() for r in rows if str(r.get("doctor") or "").strip()})
    units = sorted({str(r.get("unit") or "").strip() for r in rows if str(r.get("unit") or "").strip()})
    return (
        [{"label": s, "value": s} for s in statuses],
        [{"label": d, "value": d} for d in doctors],
        [{"label": u, "value": u} for u in units],
        _specialty_options(wc),
        _specialty_options(wc),
    )


def _status_bucket(status_raw: str) -> str:
    s = str(status_raw or "").strip()
    if s in {"1", "2"}:
        return "new"
    if s == "3":
        return "paid"
    if s == "4":
        return "cap"
    if s in {"5", "7", "12", "18"}:
        return "refused"
    if s in {"6", "8", "19"}:
        return "fix_pending"
    if s in {"0", "13", "17"}:
        return "cancelled"
    return "other"


def _load_price_map_for_period(period_id: int | None = None) -> dict[str, float]:
    """base_code -> price for selected price period.

    Каталог цен: user (если есть записи), иначе «после 01.04», иначе «до 01.04».
    """
    import sqlite3

    ma = matrix_catalog_after()
    mb = matrix_catalog_before()

    def _has_cat_prices(con, cat: str) -> bool:
        return (
            con.execute(
                "SELECT 1 FROM dn_service_price WHERE catalog=? LIMIT 1", (cat,)
            ).fetchone()
            is not None
        )

    p = get_db_path()
    con = sqlite3.connect(str(p))
    con.row_factory = sqlite3.Row
    has_user = (
        con.execute("SELECT 1 FROM dn_service_price WHERE catalog='user' LIMIT 1").fetchone()
        is not None
    )
    if has_user:
        price_catalog = "user"
    elif _has_cat_prices(con, ma):
        price_catalog = ma
    elif _has_cat_prices(con, mb):
        price_catalog = mb
    else:
        price_catalog = ma
    service_catalog = price_catalog
    if period_id is None:
        # pick latest active period that actually has prices (for chosen catalog)
        row = con.execute(
            """
            SELECT pp.id
            FROM dn_service_price_period pp
            WHERE pp.is_active=1
              AND EXISTS (
                SELECT 1 FROM dn_service_price sp
                 WHERE sp.period_id = pp.id AND sp.catalog = ?
              )
            ORDER BY pp.date_start DESC, pp.id DESC
            LIMIT 1
            """,
            (price_catalog,),
        ).fetchone()
        period_id = int(row["id"]) if row else None
    if period_id is None:
        return {}
    rows = con.execute(
        """
        SELECT UPPER(TRIM(s.code)) AS code, sp.price AS price
        FROM dn_service_price sp
        JOIN dn_service s ON s.id = sp.service_id
        WHERE sp.period_id = ?
          AND s.catalog=?
          AND sp.catalog=?
        """,
        (int(period_id), service_catalog, price_catalog),
    ).fetchall()
    out: dict[str, float] = {}
    for r in rows:
        code = str(r["code"] or "").strip().upper()
        if not code:
            continue
        m = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", code)
        base = m.group(1) if m else code
        try:
            out[base] = float(r["price"] or 0.0)
        except Exception:
            out[base] = 0.0
    return out


@app.callback(
    Output(f"{PREFIX}-loss-unit", "options"),
    Output(f"{PREFIX}-loss-status", "options"),
    Input(f"{PREFIX}-report-store", "data"),
)
def loss_unit_options(store):
    if not store:
        return [], []
    rows = store.get("tickets_all") or []
    units = sorted(
        {
            str(r.get("подразделение") or r.get("unit") or "").strip()
            for r in rows
            if str(r.get("подразделение") or r.get("unit") or "").strip()
        }
    )
    statuses = sorted(
        {
            str(r.get("статус") or r.get("status") or "").strip()
            for r in rows
            if str(r.get("статус") or r.get("status") or "").strip()
        }
    )
    return [{"label": u, "value": u} for u in units], [{"label": s, "value": s} for s in statuses]


@app.callback(
    Output(f"{PREFIX}-loss-msg", "children"),
    Output(f"{PREFIX}-tbl-loss-sum", "data"),
    Output(f"{PREFIX}-tbl-loss-sum", "columns"),
    Output(f"{PREFIX}-tbl-loss-details", "data"),
    Output(f"{PREFIX}-tbl-loss-details", "columns"),
    Output(f"{PREFIX}-loss-store", "data"),
    Input(f"{PREFIX}-loss-run", "n_clicks"),
    State(f"{PREFIX}-report-store", "data"),
    State(f"{PREFIX}-loss-status", "value"),
    State(f"{PREFIX}-loss-unit", "value"),
    State(f"{PREFIX}-loss-by-unit", "value"),
    State(f"{PREFIX}-loss-show-status", "value"),
    State(f"{PREFIX}-work-catalog", "value"),
    prevent_initial_call=True,
)
def run_loss(_n, store, statuses, units, by_unit_val, show_status_val, work_catalog):
    if not store:
        return (
            dbc.Alert("Сначала загрузите и обработайте detail_services/journal.", color="warning", className="py-2 mb-0"),
            [],
            [],
            [],
            [],
            None,
        )
    # Use ALL tickets (not only service mismatches)
    rows = store.get("tickets_all") or []
    cat_rows = {str(r.get("tal") or ""): r for r in (store.get("cat_ticket_rows") or [])}
    units_set = {str(u).strip() for u in (units or []) if str(u).strip()}
    statuses_set = {str(s).strip() for s in (statuses or []) if str(s).strip()}
    by_unit = "on" in (by_unit_val or [])
    show_status = "on" in (show_status_val or [])

    wc = str(work_catalog or default_active_catalog()).strip() or default_active_catalog()
    price_map = _load_price_map_for_period()

    # Preload required services from DN by (ds1_code, specialty_id) for all tickets.
    diag_codes: set[str] = set()
    spec_ids: set[int] = set()
    for r in rows:
        ds1 = str(r.get("ds1_code") or "").strip().upper()
        sid = r.get("specialty_id", None)
        try:
            sid_i = int(sid) if sid not in (None, "", "-") else None
        except Exception:
            sid_i = None
        if ds1:
            diag_codes.add(ds1)
        if sid_i and sid_i > 0:
            spec_ids.add(int(sid_i))
    req_map: dict[tuple[str, int], list[tuple[str, str]]] = {}
    if diag_codes and spec_ids:
        req_map = load_required_services_for_icd_codes_by_specialty(diag_codes, spec_ids, catalog=wc) or {}

    out = []
    for r in rows:
        tal = str(r.get("талон") or r.get("tal") or "").strip()
        st = str(r.get("статус") or r.get("status") or "").strip()
        if statuses_set and st not in statuses_set:
            continue
        unit = str(r.get("подразделение") or r.get("unit") or "").strip()
        if units_set and unit not in units_set:
            continue
        sid_raw = r.get("specialty_id", None)
        try:
            sid_i = int(sid_raw) if sid_raw not in (None, "", "-") else None
        except Exception:
            sid_i = None
        ds1 = str(r.get("ds1_code") or "").strip().upper()

        # expected services from DN catalog (ds1_code + specialty_id)
        exp_bases: list[str] = []
        if ds1 and sid_i and sid_i > 0:
            items = req_map.get((ds1, int(sid_i))) or []
            seen = set()
            for sc, _nm in items or []:
                m = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", str(sc or "").upper())
                base = m.group(1) if m else str(sc or "").upper()
                if base and base not in seen:
                    seen.add(base)
                    exp_bases.append(base)
        exp_sum = round(sum(price_map.get(x, 0.0) for x in exp_bases), 2)
        # fact sum from per_ticket
        fact_sum = float(r.get("сумма_талона") or r.get("sum") or 0.0)
        delta = round(fact_sum - exp_sum, 2)
        missed = round(max(0.0, exp_sum - fact_sum), 2)
        grp = (cat_rows.get(tal) or {}).get("cat", "") or str(r.get("ds1_category") or "")

        # service correctness: strict need subset of have (by base codes)
        have_line = str(r.get("услуги") or "")
        have = [m.group(1).upper() for m in _SERVICE_CODE_IN_TEXT_RE.finditer(have_line)]
        have_b = set()
        for c in have:
            mm = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", c)
            have_b.add(mm.group(1) if mm else c)
        need_b = set(exp_bases)
        is_ok = (not need_b) or (need_b.issubset(have_b))

        out.append(
            {
                "tal": tal,
                "status": st,
                "unit": unit,
                "diag_group": grp,
                "specialty_id": sid_i,
                "diag": str(r.get("диагноз") or r.get("diag") or ""),
                "expected_services": "; ".join(exp_bases),
                "expected_sum": exp_sum,
                "fact_sum": round(fact_sum, 2),
                "delta_sum": delta,
                "missed_sum": missed,
                "svc_ok": "Да" if is_ok else "Нет",
            }
        )

    # summary by diag_group (+ unit optional) and status (optional) + ok/bad splits
    agg: dict[tuple[str, str, str], dict[str, float]] = {}
    for x in out:
        g = str(x.get("diag_group") or "")
        u = str(x.get("unit") or "") if by_unit else ""
        st = str(x.get("status") or "") if show_status else ""
        k = (g, u, st)
        a = agg.setdefault(
            k,
            {
                "n": 0.0,
                "expected": 0.0,
                "fact": 0.0,
                "delta": 0.0,
                "missed": 0.0,
                "n_ok": 0.0,
                "exp_ok": 0.0,
                "fact_ok": 0.0,
                "delta_ok": 0.0,
                "miss_ok": 0.0,
                "n_bad": 0.0,
                "exp_bad": 0.0,
                "fact_bad": 0.0,
                "delta_bad": 0.0,
                "miss_bad": 0.0,
            },
        )
        a["n"] += 1.0
        a["expected"] += float(x.get("expected_sum") or 0.0)
        a["fact"] += float(x.get("fact_sum") or 0.0)
        a["delta"] += float(x.get("delta_sum") or 0.0)
        a["missed"] += float(x.get("missed_sum") or 0.0)
        if str(x.get("svc_ok")) == "Да":
            a["n_ok"] += 1.0
            a["exp_ok"] += float(x.get("expected_sum") or 0.0)
            a["fact_ok"] += float(x.get("fact_sum") or 0.0)
            a["delta_ok"] += float(x.get("delta_sum") or 0.0)
            a["miss_ok"] += float(x.get("missed_sum") or 0.0)
        else:
            a["n_bad"] += 1.0
            a["exp_bad"] += float(x.get("expected_sum") or 0.0)
            a["fact_bad"] += float(x.get("fact_sum") or 0.0)
            a["delta_bad"] += float(x.get("delta_sum") or 0.0)
            a["miss_bad"] += float(x.get("missed_sum") or 0.0)
    sum_rows = [
        {
            "diag_group": k[0],
            "unit": k[1] if by_unit else "",
            "status": k[2],
            "n": int(v["n"]),
            "expected_sum": round(v["expected"], 2),
            "fact_sum": round(v["fact"], 2),
            "delta_sum": round(v["delta"], 2),
            "missed_sum": round(v["missed"], 2),
            "n_ok": int(v["n_ok"]),
            "expected_ok": round(v["exp_ok"], 2),
            "fact_ok": round(v["fact_ok"], 2),
            "delta_ok": round(v["delta_ok"], 2),
            "missed_ok": round(v["miss_ok"], 2),
            "n_bad": int(v["n_bad"]),
            "expected_bad": round(v["exp_bad"], 2),
            "fact_bad": round(v["fact_bad"], 2),
            "delta_bad": round(v["delta_bad"], 2),
            "missed_bad": round(v["miss_bad"], 2),
        }
        for k, v in sorted(agg.items(), key=lambda kv: (-kv[1]["missed"], kv[0][0], kv[0][1], kv[0][2]))
    ]
    # totals row
    total_n = sum(r["n"] for r in sum_rows)
    total_expected = round(sum(r["expected_sum"] for r in sum_rows), 2)
    total_fact = round(sum(r["fact_sum"] for r in sum_rows), 2)
    total_delta = round(sum(r.get("delta_sum", 0.0) for r in sum_rows), 2)
    total_missed = round(sum(r["missed_sum"] for r in sum_rows), 2)
    total_n_ok = sum(r.get("n_ok", 0) for r in sum_rows)
    total_expected_ok = round(sum(r.get("expected_ok", 0.0) for r in sum_rows), 2)
    total_fact_ok = round(sum(r.get("fact_ok", 0.0) for r in sum_rows), 2)
    total_delta_ok = round(sum(r.get("delta_ok", 0.0) for r in sum_rows), 2)
    total_missed_ok = round(sum(r.get("missed_ok", 0.0) for r in sum_rows), 2)
    total_n_bad = sum(r.get("n_bad", 0) for r in sum_rows)
    total_expected_bad = round(sum(r.get("expected_bad", 0.0) for r in sum_rows), 2)
    total_fact_bad = round(sum(r.get("fact_bad", 0.0) for r in sum_rows), 2)
    total_delta_bad = round(sum(r.get("delta_bad", 0.0) for r in sum_rows), 2)
    total_missed_bad = round(sum(r.get("missed_bad", 0.0) for r in sum_rows), 2)
    sum_rows.insert(
        0,
        {
            "diag_group": "ИТОГО",
            "unit": "",
            "status": "",
            "n": total_n,
            "expected_sum": total_expected,
            "fact_sum": total_fact,
            "delta_sum": total_delta,
            "missed_sum": total_missed,
            "n_ok": int(total_n_ok),
            "expected_ok": total_expected_ok,
            "fact_ok": total_fact_ok,
            "delta_ok": total_delta_ok,
            "missed_ok": total_missed_ok,
            "n_bad": int(total_n_bad),
            "expected_bad": total_expected_bad,
            "fact_bad": total_fact_bad,
            "delta_bad": total_delta_bad,
            "missed_bad": total_missed_bad,
        },
    )
    sum_cols = [
        {"name": "Группа диагноза", "id": "diag_group"},
        {"name": "Подразделение", "id": "unit"},
        {"name": "Статус", "id": "status"} if show_status else {"name": "Статус", "id": "status", "hideable": True},
        {"name": "Талонов", "id": "n", "type": "numeric", "format": {"specifier": ",d"}},
        {"name": "Ожидаемая сумма", "id": "expected_sum", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Факт", "id": "fact_sum", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Разница (Факт−Ожид)", "id": "delta_sum", "type": "numeric", "format": {"specifier": "+,.2f"}},
        {"name": "Упущено", "id": "missed_sum", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "OK талонов", "id": "n_ok", "type": "numeric", "format": {"specifier": ",d"}},
        {"name": "OK ожидаемо", "id": "expected_ok", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "OK факт", "id": "fact_ok", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "OK разница", "id": "delta_ok", "type": "numeric", "format": {"specifier": "+,.2f"}},
        {"name": "OK упущено", "id": "missed_ok", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Ошибка талонов", "id": "n_bad", "type": "numeric", "format": {"specifier": ",d"}},
        {"name": "Ошибка ожидаемо", "id": "expected_bad", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Ошибка факт", "id": "fact_bad", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Ошибка разница", "id": "delta_bad", "type": "numeric", "format": {"specifier": "+,.2f"}},
        {"name": "Ошибка упущено", "id": "missed_bad", "type": "numeric", "format": {"specifier": ",.2f"}},
    ]
    # details table: same out
    det_cols = [
        {"name": "Талон", "id": "tal"},
        {"name": "Статус", "id": "status"},
        {"name": "Подразделение", "id": "unit"},
        {"name": "Группа диагноза", "id": "diag_group"},
        {"name": "specialty_id", "id": "specialty_id"},
        {"name": "Диагноз", "id": "diag"},
        {"name": "Ожидаемые услуги", "id": "expected_services"},
        {"name": "Ожидаемая сумма", "id": "expected_sum", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Факт (сумма талона)", "id": "fact_sum", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Разница (Факт−Ожид)", "id": "delta_sum", "type": "numeric", "format": {"specifier": "+,.2f"}},
        {"name": "Упущено", "id": "missed_sum", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Услуги OK", "id": "svc_ok"},
    ]
    msg = dbc.Alert(f"Готово. Талонов: {len(out)}.", color="success", className="py-2 mb-0")
    return msg, sum_rows, sum_cols, out, det_cols, {"rows": out, "summary": sum_rows, "by_unit": by_unit}


@app.callback(
    Output(f"{PREFIX}-loss-download", "data"),
    Input(f"{PREFIX}-loss-download-btn", "n_clicks"),
    State(f"{PREFIX}-loss-store", "data"),
    prevent_initial_call=True,
)
def download_loss(_n, store):
    if not store or not store.get("rows"):
        raise PreventUpdate
    rows = store["rows"]
    header = list(rows[0].keys())

    def _writer(bytes_io):
        import io as _io

        buf = _io.TextIOWrapper(bytes_io, encoding="utf-8-sig", newline="")
        w = csv.DictWriter(buf, fieldnames=header, delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
        buf.flush()

    return dcc.send_bytes(_writer, "loss_report.csv")


@app.callback(
    Output(f"{PREFIX}-bot-candidates", "data"),
    Output(f"{PREFIX}-bot-candidates", "columns"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-bot-doctor-overrides", "data"),
    Input(f"{PREFIX}-bot-specialty-overrides", "data"),
    Input(f"{PREFIX}-bot-cand-status", "value"),
    Input(f"{PREFIX}-bot-cand-doctor", "value"),
    Input(f"{PREFIX}-bot-cand-unit", "value"),
    Input(f"{PREFIX}-bot-cand-specialty-id", "value"),
    Input(f"{PREFIX}-bot-cand-diag-include", "value"),
    Input(f"{PREFIX}-bot-cand-diag-exclude", "value"),
    Input(f"{PREFIX}-bot-cand-only-allowed-status", "value"),
    Input(f"{PREFIX}-bot-cand-hide-in-queue", "value"),
    Input(f"{PREFIX}-bot-cand-end-date", "start_date"),
    Input(f"{PREFIX}-bot-cand-end-date", "end_date"),
    Input(f"{PREFIX}-work-catalog", "value"),
)
def update_bot_candidates_table(
    store,
    overrides,
    spec_overrides,
    statuses,
    doctors,
    units,
    specialty_ids,
    diag_inc,
    diag_exc,
    only_allowed,
    hide_in_queue,
    end_start,
    end_end,
    work_catalog,
):
    if not store:
        return [], []
    wc = str(work_catalog or default_active_catalog()).strip() or default_active_catalog()
    rows = store.get("svc_ticket") or []
    statuses = set(statuses or [])
    doctors = set(doctors or [])
    units = set(units or [])
    specialty_ids = {int(x) for x in (specialty_ids or []) if str(x).strip()}
    inc = _split_prefixes(diag_inc)
    exc = _split_prefixes(diag_exc)
    allowed = {"1", "6", "8", "19"}
    only_allowed = "on" in (only_allowed or [])
    overrides = overrides or {}
    spec_overrides = spec_overrides or {}
    hide_in_queue = "on" in (hide_in_queue or [])

    # Join treatment end date from category details.
    end_by_tal = {
        str(x.get("tal") or "").strip(): str(x.get("end_date_raw") or "").strip()
        for x in (store.get("cat_ticket_rows") or [])
        if str(x.get("tal") or "").strip()
    }
    end_start_iso = str(end_start or "").strip()
    end_end_iso = str(end_end or "").strip()

    def _diag_code(x: str) -> str:
        m = re.search(r"\b([A-Z]\d{2}(?:\.\d+)?)\b", str(x or "").upper())
        return m.group(1) if m else ""

    # Batch recompute svc_dx for overridden pairs (diag_code, specialty_id)
    diag_codes: set[str] = set()
    spec_ids: set[int] = set()
    for r in rows:
        tal0 = str(r.get("tal") or "").strip()
        diag0 = _diag_code(str(r.get("diag") or ""))
        sid0 = spec_overrides.get(tal0, r.get("specialty_id", None))
        try:
            sid0i = int(sid0) if sid0 not in (None, "", "-") else None
        except Exception:
            sid0i = None
        if diag0 and sid0i:
            diag_codes.add(diag0)
            spec_ids.add(sid0i)

    svc_map: dict[tuple[str, int], str] = {}
    if diag_codes and spec_ids:
        req = load_required_services_for_icd_codes_by_specialty(diag_codes, spec_ids, catalog=wc)
        for (dcode, sid), items in (req or {}).items():
            codes = []
            seen = set()
            for sc, _nm in items or []:
                m = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", str(sc or "").upper())
                base = m.group(1) if m else str(sc or "").upper()
                if base and base not in seen:
                    seen.add(base)
                    codes.append(base)
            svc_map[(str(dcode).upper(), int(sid))] = (
                f"Основной ({str(dcode).upper()}): " + "; ".join(codes)
                if codes
                else f"Основной ({str(dcode).upper()}): нет обязательных услуг в справочнике"
            )

    # Precompute talons already queued/running if requested.
    in_queue: set[str] = set()
    if hide_in_queue:
        in_queue = bot_db.active_talons(statuses=("queued", "running"))

    out = []
    for r in rows:
        tal = str(r.get("tal") or "").strip()
        if hide_in_queue and tal and tal in in_queue:
            continue
        st = str(r.get("status") or "").strip()
        if only_allowed and st not in allowed:
            continue
        if statuses and st not in statuses:
            continue
        doc = str(r.get("doctor") or "").strip()
        if doctors and doc not in doctors:
            continue
        unit = str(r.get("unit") or "").strip()
        if units and unit not in units:
            continue
        # specialty filter (effective specialty_id after overrides)
        sid_eff = spec_overrides.get(tal, r.get("specialty_id", None))
        try:
            sid_eff_i = int(sid_eff) if sid_eff not in (None, "", "-") else None
        except Exception:
            sid_eff_i = None
        if specialty_ids and (sid_eff_i is None or sid_eff_i not in specialty_ids):
            continue
        diag = str(r.get("diag") or "").strip()
        diag_code = diag.split()[0].strip().upper() if diag else ""
        if inc and (not diag_code or diag_code[0] not in inc):
            continue
        if exc and diag_code and diag_code[0] in exc:
            continue

        # treatment end date filter
        end_raw = end_by_tal.get(tal, "")
        end_iso = _date_to_iso(end_raw) if end_raw else ""
        if end_start_iso and end_iso and end_iso < end_start_iso:
            continue
        if end_end_iso and end_iso and end_iso > end_end_iso:
            continue

        sid = sid_eff_i if sid_eff_i is not None else spec_overrides.get(tal, r.get("specialty_id", None))
        try:
            sid_i = int(sid) if sid not in (None, "", "-") else None
        except Exception:
            sid_i = None
        diag_code = _diag_code(diag)
        svc_dx = str(r.get("svc_dx") or "")
        if diag_code and sid_i:
            svc_dx = svc_map.get((diag_code, sid_i), svc_dx)

        out.append(
            {
                "tal": str(r.get("tal") or "").strip(),
                "status": st,
                "doctor": doc,
                "doctor_id": str(
                    overrides.get(str(r.get("tal") or "").strip(), "")
                    or _extract_doctor_id(doc)
                    or ""
                ),
                "unit": unit,
                "specialty": str(r.get("specialty") or ""),
                "position": str(r.get("position") or ""),
                "specialty_id": sid_i if sid_i is not None else r.get("specialty_id", None),
                "end_date_raw": end_raw,
                "diag": diag,
                "svc_dx": svc_dx,
                "reasons": str(r.get("reasons") or ""),
            }
        )

    cols = [
        {"name": "Талон", "id": "tal"},
        {"name": "Статус", "id": "status"},
        {"name": "Врач", "id": "doctor"},
        {"name": "doctor_id", "id": "doctor_id", "editable": True},
        {"name": "Подразделение", "id": "unit"},
        {"name": "Специальность", "id": "specialty"},
        {"name": "Должность", "id": "position"},
        {"name": "specialty_id", "id": "specialty_id"},
        {"name": "Окончание лечения", "id": "end_date_raw"},
        {"name": "Диагноз", "id": "diag"},
        {"name": "Ожидаемые услуги (svc_dx)", "id": "svc_dx"},
        {"name": "Причины", "id": "reasons"},
    ]
    return out, cols


@app.callback(
    Output(f"{PREFIX}-bot-doctor-overrides", "data"),
    Input(f"{PREFIX}-bot-candidates", "data_timestamp"),
    State(f"{PREFIX}-bot-candidates", "data"),
    State(f"{PREFIX}-bot-doctor-overrides", "data"),
)
def cache_doctor_overrides(_ts, data, prev):
    prev = prev or {}
    if not data:
        return prev
    out = dict(prev)
    for r in data:
        tal = str(r.get("tal") or "").strip()
        if not tal:
            continue
        did = str(r.get("doctor_id") or "").strip()
        if did:
            out[tal] = did
        elif tal in out:
            # если пользователь очистил поле — убираем override
            out.pop(tal, None)
    return out


@app.callback(
    Output(f"{PREFIX}-bot-doctor-overrides", "data", allow_duplicate=True),
    Output(f"{PREFIX}-bot-specialty-overrides", "data", allow_duplicate=True),
    Input(f"{PREFIX}-bot-bulk-apply-selected", "n_clicks"),
    Input(f"{PREFIX}-bot-bulk-apply-firstn", "n_clicks"),
    Input(f"{PREFIX}-bot-bulk-reset-selected", "n_clicks"),
    State(f"{PREFIX}-bot-bulk-doctor-id", "value"),
    State(f"{PREFIX}-bot-bulk-specialty-id", "value"),
    State(f"{PREFIX}-bot-bulk-n", "value"),
    State(f"{PREFIX}-bot-candidates", "selected_rows"),
    State(f"{PREFIX}-bot-candidates", "derived_virtual_data"),
    State(f"{PREFIX}-bot-doctor-overrides", "data"),
    State(f"{PREFIX}-bot-specialty-overrides", "data"),
    prevent_initial_call=True,
)
def bulk_apply_doctor_specialty(
    _n_sel,
    _n_first,
    _n_reset,
    doctor_id,
    specialty_id,
    n_first,
    selected_rows,
    virt_data,
    doc_prev,
    spec_prev,
):
    triggered = (callback_context.triggered[0]["prop_id"] if callback_context.triggered else "")
    if not triggered:
        return no_update, no_update
    doc_prev = doc_prev or {}
    spec_prev = spec_prev or {}
    doc_out = dict(doc_prev)
    spec_out = dict(spec_prev)

    def _talons(indices: list[int]) -> list[str]:
        if not virt_data:
            return []
        out_t: list[str] = []
        for i in indices:
            try:
                row = virt_data[int(i)]
            except Exception:
                continue
            tal = str((row or {}).get("tal") or "").strip()
            if tal:
                out_t.append(tal)
        return out_t

    if triggered.endswith("bot-bulk-reset-selected.n_clicks"):
        for tal in _talons(selected_rows or []):
            doc_out.pop(tal, None)
            spec_out.pop(tal, None)
        return doc_out, spec_out

    did = str(doctor_id or "").strip()
    try:
        sid_i = int(specialty_id) if specialty_id not in (None, "", "-") else None
    except Exception:
        sid_i = None

    if triggered.endswith("bot-bulk-apply-firstn.n_clicks"):
        try:
            n = int(n_first or 0)
        except Exception:
            n = 0
        n = max(1, min(5000, n))
        idxs = list(range(min(n, len(virt_data or []))))
        talons = _talons(idxs)
    else:
        talons = _talons(selected_rows or [])

    for tal in talons:
        if did:
            doc_out[tal] = did
        if sid_i is not None:
            spec_out[tal] = sid_i
    return doc_out, spec_out


@app.callback(
    Output(f"{PREFIX}-bot-candidates", "selected_rows"),
    Input(f"{PREFIX}-bot-cand-select-all", "n_clicks"),
    Input(f"{PREFIX}-bot-cand-select-all-filtered", "n_clicks"),
    Input(f"{PREFIX}-bot-cand-clear", "n_clicks"),
    State(f"{PREFIX}-bot-candidates", "derived_viewport_indices"),
    State(f"{PREFIX}-bot-candidates", "derived_virtual_indices"),
    State(f"{PREFIX}-bot-candidates", "selected_rows"),
    prevent_initial_call=True,
)
def bot_select_all_candidates(n_all, n_all_filtered, n_clear, viewport_idxs, virtual_idxs, selected):
    _ = (n_all, n_all_filtered, n_clear)
    triggered = (callback_context.triggered[0]["prop_id"] if callback_context.triggered else "")
    if triggered.endswith("bot-cand-clear.n_clicks"):
        return []
    if triggered.endswith("bot-cand-select-all.n_clicks"):
        # Select all rows currently visible in the viewport (current page after sort/filter).
        if viewport_idxs is None:
            return selected or []
        return list(viewport_idxs)
    if triggered.endswith("bot-cand-select-all-filtered.n_clicks"):
        # Select all rows across all pages after applying current sort/filter.
        if virtual_idxs is None:
            return selected or []
        return list(virtual_idxs)
    raise PreventUpdate


@app.callback(
    Output(f"{PREFIX}-bot-enqueue-selected-msg", "children"),
    Input(f"{PREFIX}-bot-enqueue-selected", "n_clicks"),
    State(f"{PREFIX}-bot-candidates", "selected_rows"),
    State(f"{PREFIX}-bot-candidates", "data"),
    State(f"{PREFIX}-report-store", "data"),
    State(f"{PREFIX}-bot-mode", "value"),
    State(f"{PREFIX}-bot-doctor-id", "value"),
    prevent_initial_call=True,
)
def enqueue_selected_bot_tasks(n_clicks, selected_rows, cand_data, store, mode, doctor_id):
    _ = n_clicks
    if not store:
        return "Нет данных отчёта. Сначала загрузите и обработайте CSV."
    if not cand_data:
        return "Список кандидатов пуст — измените фильтры."
    sel = selected_rows or []
    if not sel:
        return "Не выбраны талоны (кликните галочки слева в таблице)."

    rows_by_tal = {str(r.get("tal")): r for r in (store.get("cat_ticket_rows") or [])}
    tasks: list[bot_db.TaskPayload] = []
    default_doctor_id = str(doctor_id or "").strip()
    selected_talons: list[str] = []
    for idx in sel:
        if idx < 0 or idx >= len(cand_data):
            continue
        r = cand_data[idx]
        tal = str(r.get("tal") or "").strip()
        if not tal:
            continue
        selected_talons.append(tal)
        cat_row = rows_by_tal.get(tal) or {}
        end_iso = _date_to_iso(cat_row.get("end_date_raw", ""))
        formed_iso = _date_to_iso(cat_row.get("formed_date_raw", ""))
        d = _iso_today_fallback(end_iso, formed_iso)
        expected = _expected_services_from_suggestion(r.get("svc_dx", ""), d, d)
        if not expected:
            continue

        row_doctor_id = str(r.get("doctor_id") or "").strip()
        use_doctor_id = row_doctor_id or default_doctor_id
        payload = bot_db.TaskPayload(
            talon_id=tal,
            expected_services=[bot_db.ExpectedService(**x) for x in expected],
            mode=(mode or "sync"),
            context={
                "source": "analysis_candidates",
                "doctor_id": use_doctor_id,
            },
        )
        tasks.append(payload)

    if not tasks:
        return "Не получилось сформировать ожидаемые услуги из выбранных строк."
    # Skip talons that are already in queue (queued/running)
    already = bot_db.talons_in_queue(selected_talons, statuses=("queued", "running"))
    if already:
        tasks = [t for t in tasks if str(t.talon_id) not in already]
    bot_db.init_db()
    if not tasks:
        return f"Все выбранные талоны уже в очереди (queued/running): {len(already)}."
    ids = bot_db.enqueue_tasks(tasks)
    skipped = len(already)
    return f"Задачи добавлены в очередь: {len(ids)}. Пропущено уже в очереди: {skipped}."


app.clientside_callback(
    """
    function(n_clicks, active_tab, sel_one, data_one, sel_multi, data_multi, sel_block, data_block, err_flt, sel_esvc, data_esvc, sel_edx, data_edx, base) {
        if (!n_clicks) {
            return '';
        }
        if (!base || String(base).length < 10) {
            return '';
        }
        var sel = null;
        var data = null;
        if (active_tab === 'a-one') { sel = sel_one; data = data_one; }
        else if (active_tab === 'a-multi') { sel = sel_multi; data = data_multi; }
        else if (active_tab === 'a-block') { sel = sel_block; data = data_block; }
        else if (active_tab === 'a-errors') {
            var f = err_flt || 'all';
            if (f === 'svc') {
                sel = sel_esvc; data = data_esvc;
            } else if (f === 'dx') {
                sel = sel_edx; data = data_edx;
            } else {
                if (sel_esvc && sel_esvc.length && data_esvc && data_esvc.length) {
                    sel = sel_esvc; data = data_esvc;
                } else if (sel_edx && sel_edx.length && data_edx && data_edx.length) {
                    sel = sel_edx; data = data_edx;
                }
            }
            if (!sel || !sel.length) {
                return '';
            }
        } else { return ''; }
        if (!sel || !sel.length || !data || !data.length) {
            return '';
        }
        var row = data[sel[0]];
        if (!row || row.tal === undefined || row.tal === null) {
            return '';
        }
        var tal = String(row.tal).trim();
        if (!tal) {
            return '';
        }
        var u = String(base).trim();
        if (!u.endsWith('/')) { u += '/'; }
        var url = u + encodeURIComponent(tal);
        window.open(url, '_blank', 'noopener,noreferrer');
        return '';
    }
    """,
    Output(f"{PREFIX}-dummy-clientside", "children"),
    Input(f"{PREFIX}-btn-open-claim", "n_clicks"),
    State(f"{PREFIX}-inner-tabs", "active_tab"),
    State(f"{PREFIX}-tbl-one", "selected_rows"),
    State(f"{PREFIX}-tbl-one", "data"),
    State(f"{PREFIX}-tbl-multi", "selected_rows"),
    State(f"{PREFIX}-tbl-multi", "data"),
    State(f"{PREFIX}-tbl-block", "selected_rows"),
    State(f"{PREFIX}-tbl-block", "data"),
    State(f"{PREFIX}-errors-filter", "value"),
    State(f"{PREFIX}-tbl-errors-svc", "selected_rows"),
    State(f"{PREFIX}-tbl-errors-svc", "data"),
    State(f"{PREFIX}-tbl-errors-dx", "selected_rows"),
    State(f"{PREFIX}-tbl-errors-dx", "data"),
    State(f"{PREFIX}-claim-base-url", "data"),
    prevent_initial_call=True,
)
