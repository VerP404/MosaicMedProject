"""
Вкладка «Анализ» — загрузка detail_services CSV и те же отчёты, что в report_detail_services.py.
"""
from __future__ import annotations

import base64
import os

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, dash_table
from dash.exceptions import PreventUpdate

from apps.dash_dn.app import dash_dn_app as app
from apps.dash_dn.detail_services_report import (
    build_report,
    load_allowed_service_codes_from_db,
    load_diagnosis_lookup_from_db,
    read_detail_csv_from_bytes,
)
from apps.dash_dn.sqlite_catalog.paths import get_db_path

PREFIX = "dash-dn-analysis"


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
    return html.Div(
        [
            html.P(
                "Загрузите Детализацию талонов по услугам из web.ОМС (csv-файл). "
                "Сначала исключаются строки, где в «Код услуги» прочерк «-» или пусто (как в Квазар для части строк). "
                "Далее своды по оставшимся строкам; замечания — на вкладке «Ошибки».",
                className="text-muted small",
            ),
            dcc.Upload(
                id=f"{PREFIX}-upload",
                children=html.Div(
                    [
                        html.I(className="bi bi-cloud-upload me-2"),
                        "Перетащите CSV сюда или нажмите для выбора файла",
                    ],
                    className="small",
                ),
                className="border rounded-3 p-4 text-center bg-white mb-3",
                style={"cursor": "pointer"},
                multiple=False,
            ),
            html.Div(id=f"{PREFIX}-msg", className="mb-2"),
            dcc.Store(id=f"{PREFIX}-report-store", data=None),
            dcc.Store(id=f"{PREFIX}-cat-sum-applied", data=None),
            dcc.Store(id=f"{PREFIX}-claim-base-url", data=_default_claim_ambulatory_base()),
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
                                                    lg=5,
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
                                                    lg=7,
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
                                                            dbc.Label(
                                                                "Режим",
                                                                className="small fw-semibold mb-1",
                                                            ),
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
                                                                className="mb-2",
                                                            ),
                                                            dbc.Label(
                                                                "Сумма",
                                                                className="small fw-semibold mb-1",
                                                            ),
                                                            dbc.Input(
                                                                id=f"{PREFIX}-cat-sum-value",
                                                                type="number",
                                                                min=0,
                                                                step="0.01",
                                                                placeholder="Введите сумму талона",
                                                                size="sm",
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
        "dx_mismatch": _rows_dx_mismatch(report),
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
    {"name": "Талонов", "id": "n", "type": "numeric"},
    {"name": "Сумма талонов", "id": "sum", "type": "numeric"},
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
]
COLS_CAT_DS1_UNIT = [
    {"name": "Категория (DS1)", "id": "cat"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Талонов", "id": "n", "type": "numeric"},
    {"name": "Сумма талонов", "id": "sum", "type": "numeric"},
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
    Input(f"{PREFIX}-upload", "contents"),
    State(f"{PREFIX}-upload", "filename"),
    prevent_initial_call=True,
)
def run_analysis(contents, upload_filename):
    if not contents:
        raise PreventUpdate

    try:
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

    try:
        allowed = load_allowed_service_codes_from_db("global")
        dx_lookup = load_diagnosis_lookup_from_db("global")
        _fn, rows = read_detail_csv_from_bytes(raw)
        report = build_report(rows, allowed, dx_lookup)
    except Exception as e:
        return (
            dbc.Alert(f"Ошибка разбора: {e}", color="danger", className="py-2 mb-0"),
            None,
            *_empty_tables(),
        )

    db_path = get_db_path()
    ref_line = (
        f"Справочник услуг: SQLite · dn_service (catalog=global) · {db_path} — {len(allowed)} кодов"
    )
    dx_line = (
        f"Справочник диагнозов: dn_diagnosis + dn_diagnosis_category (catalog=global) · "
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


def _cat_table_from_store(store: dict | None, axis: str, unit: str):
    if not store:
        return [], COLS_CAT_DS1
    if axis == "ds2":
        return store.get("cat_ds2") or [], COLS_CAT_DS2
    if unit == "yes":
        return store.get("cat_ds1_unit") or [], COLS_CAT_DS1_UNIT
    return store.get("cat_ds1") or [], COLS_CAT_DS1


def _cat_ticket_rows_for_filter(store: dict | None) -> list[dict]:
    if not store:
        return []
    return store.get("cat_ticket_rows") or []


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
    by_unit: bool,
) -> dict:
    out: dict = {}
    for row in ticket_rows:
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

    metrics = _filtered_ok_metrics(ticket_rows, op, threshold, by_unit=by_unit)
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
    Output(f"{PREFIX}-tbl-cat", "data"),
    Output(f"{PREFIX}-tbl-cat", "columns"),
    Input(f"{PREFIX}-report-store", "data"),
    Input(f"{PREFIX}-cat-axis", "value"),
    Input(f"{PREFIX}-cat-unit", "value"),
    Input(f"{PREFIX}-cat-sum-enabled", "value"),
    Input(f"{PREFIX}-cat-sum-applied", "data"),
)
def update_cat_table(store, axis, unit, sum_enabled, cat_sum_applied):
    axis = axis or "ds1"
    unit = unit or "no"
    data, cols = _cat_table_from_store(store, axis, unit)
    if bool(sum_enabled) and axis == "ds1":
        op, threshold = _cat_sum_filter_from_applied(cat_sum_applied)
        data, cols = _append_cat_filtered_columns(
            data,
            cols,
            _cat_ticket_rows_for_filter(store),
            op,
            threshold,
            by_unit=(unit == "yes"),
        )
    return data, cols


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


app.clientside_callback(
    """
    function(n_clicks, active_tab, sel_one, data_one, sel_multi, data_multi, err_flt, sel_esvc, data_esvc, sel_edx, data_edx, base) {
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
    State(f"{PREFIX}-errors-filter", "value"),
    State(f"{PREFIX}-tbl-errors-svc", "selected_rows"),
    State(f"{PREFIX}-tbl-errors-svc", "data"),
    State(f"{PREFIX}-tbl-errors-dx", "selected_rows"),
    State(f"{PREFIX}-tbl-errors-dx", "data"),
    State(f"{PREFIX}-claim-base-url", "data"),
    prevent_initial_call=True,
)
