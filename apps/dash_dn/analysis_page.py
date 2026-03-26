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
                ,
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
                                label="Коды вне справочника / формат",
                                tab_id="a-inv",
                                children=html.Div(_table("tbl-inv", selectable_ticket=True), className="pt-3"),
                            ),
                            dbc.Tab(
                                label="Свод по «левым» кодам",
                                tab_id="a-codes",
                                children=html.Div(_table("tbl-codes", page_size=50), className="pt-3"),
                            ),
                            dbc.Tab(
                                label="Строки без кода услуги",
                                tab_id="a-nocode",
                                children=html.Div(_table("tbl-nocode", selectable_ticket=True), className="pt-3"),
                            ),
                            dbc.Tab(
                                label="Талоны — проблемы по услугам",
                                tab_id="a-svc-ticket",
                                children=html.Div(
                                    _table(
                                        "tbl-svc-ticket",
                                        page_size=25,
                                        wrap_long_text=True,
                                        selectable_ticket=True,
                                    ),
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Свод по категориям (DS1)",
                                tab_id="a-cat-ds1",
                                children=html.Div(_table("tbl-cat-ds1", page_size=40), className="pt-3"),
                            ),
                            dbc.Tab(
                                label="Категории (DS1) по подразделениям",
                                tab_id="a-cat-ds1-unit",
                                children=html.Div(
                                    _table("tbl-cat-ds1-unit", page_size=40),
                                    className="pt-3",
                                ),
                            ),
                            dbc.Tab(
                                label="Сопутствующие по категориям",
                                tab_id="a-cat-ds2",
                                children=html.Div(_table("tbl-cat-ds2", page_size=40), className="pt-3"),
                            ),
                            dbc.Tab(
                                label="Диагнозы — несоответствия",
                                tab_id="a-dx-mismatch",
                                children=html.Div(
                                    _table("tbl-dx-mismatch", selectable_ticket=True),
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
    return html.Div(
        [
            html.P(ref_line, className="small text-muted mb-2"),
            html.P(dx_line, className="small text-muted mb-2"),
            dbc.Row(
                [
                    _card("Уникальных талонов", str(report["unique_tickets"])),
                    _card("Строк в выгрузке", str(report["total_rows"])),
                    _card("Талонов с 1 услугой", str(len(report["single_service"]))),
                    _card(
                        "Строк с проблемным кодом / без кода",
                        f"{len(report['invalid_lines'])} / {len(report['no_code_lines'])}",
                    ),
                    _card(
                        "Замечаний по диагнозам (справочник)",
                        str(len(report.get("diagnosis_mismatches") or [])),
                    ),
                    _card(
                        "Талонов с проблемами по услугам",
                        str(len(report.get("tickets_service_mismatch") or [])),
                    ),
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


def _rows_invalid(report: dict) -> list[dict]:
    return [
        {
            "tal": x["талон"],
            "enp": x.get("енп", ""),
            "status": x.get("статус", ""),
            "unit": x.get("подразделение", ""),
            "doctor": x.get("врач", ""),
            "diag": x["диагноз"],
            "ds2": x.get("диагноз_ds2", ""),
            "code": x["код_услуги"],
            "reason": x["причина"],
            "sum": round(float(x["сумма_услуги"]), 2),
        }
        for x in report["invalid_lines"]
    ]


def _rows_invalid_codes(report: dict) -> list[dict]:
    return [{"code": c, "n": n} for c, n in report["invalid_by_code"].items()]


def _rows_no_code(report: dict) -> list[dict]:
    return [
        {
            "tal": x["талон"],
            "enp": x.get("енп", ""),
            "status": x.get("статус", ""),
            "unit": x.get("подразделение", ""),
            "doctor": x.get("врач", ""),
            "diag": x["диагноз"],
            "ds2": x.get("диагноз_ds2", ""),
            "code": x["код_услуги"],
            "sum": round(float(x["сумма_услуги"]), 2),
        }
        for x in report["no_code_lines"]
    ]


def _rows_cat_ds1(report: dict) -> list[dict]:
    bc = report.get("by_category_ds1") or {}
    out = []
    for cat, agg in sorted(
        bc.items(),
        key=lambda x: (-x[1]["талонов"], x[0]),
    ):
        out.append(
            {
                "cat": cat,
                "n": agg["талонов"],
                "sum": round(float(agg["сумма_талонов"]), 2),
                "n_ok": int(agg.get("талонов_услуги_ок", 0)),
                "sum_ok": round(float(agg.get("сумма_услуги_ок", 0.0)), 2),
            }
        )
    return out


def _rows_cat_ds1_unit(report: dict) -> list[dict]:
    rows = report.get("by_category_ds1_by_unit") or []
    out = []
    for r in rows:
        out.append(
            {
                "cat": r["категория"],
                "unit": r["подразделение"],
                "n": r["талонов"],
                "sum": r["сумма_талонов"],
                "n_ok": r["талонов_услуги_ок"],
                "sum_ok": r["сумма_услуги_ок"],
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
            "diag": t["диагноз"],
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
COLS_INV = [
    {"name": "Талон", "id": "tal"},
    {"name": "ЕНП", "id": "enp"},
    {"name": "Статус", "id": "status"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "Сопутствующий (DS2)", "id": "ds2"},
    {"name": "Код услуги", "id": "code"},
    {"name": "Причина", "id": "reason"},
    {"name": "Сумма услуги", "id": "sum", "type": "numeric"},
]
COLS_CODES = [
    {"name": "Код услуги", "id": "code"},
    {"name": "Строк в выгрузке", "id": "n", "type": "numeric"},
]
COLS_NOCODE = [
    {"name": "Талон", "id": "tal"},
    {"name": "ЕНП", "id": "enp"},
    {"name": "Статус", "id": "status"},
    {"name": "Подразделение", "id": "unit"},
    {"name": "Врач", "id": "doctor"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "Сопутствующий (DS2)", "id": "ds2"},
    {"name": "Поле «Код услуги»", "id": "code"},
    {"name": "Сумма услуги", "id": "sum", "type": "numeric"},
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
    {"name": "Диагноз (DS1)", "id": "diag"},
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
    Output(f"{PREFIX}-tbl-inv", "data"),
    Output(f"{PREFIX}-tbl-inv", "columns"),
    Output(f"{PREFIX}-tbl-codes", "data"),
    Output(f"{PREFIX}-tbl-codes", "columns"),
    Output(f"{PREFIX}-tbl-nocode", "data"),
    Output(f"{PREFIX}-tbl-nocode", "columns"),
    Output(f"{PREFIX}-tbl-svc-ticket", "data"),
    Output(f"{PREFIX}-tbl-svc-ticket", "columns"),
    Output(f"{PREFIX}-tbl-cat-ds1", "data"),
    Output(f"{PREFIX}-tbl-cat-ds1", "columns"),
    Output(f"{PREFIX}-tbl-cat-ds1-unit", "data"),
    Output(f"{PREFIX}-tbl-cat-ds1-unit", "columns"),
    Output(f"{PREFIX}-tbl-cat-ds2", "data"),
    Output(f"{PREFIX}-tbl-cat-ds2", "columns"),
    Output(f"{PREFIX}-tbl-dx-mismatch", "data"),
    Output(f"{PREFIX}-tbl-dx-mismatch", "columns"),
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
    msg = dbc.Alert(
        f"Обработан файл: {shown_name}. "
        f"Уникальных талонов: {report['unique_tickets']}; строк: {report['total_rows']}.",
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
        _rows_invalid(report),
        COLS_INV,
        _rows_invalid_codes(report),
        COLS_CODES,
        _rows_no_code(report),
        COLS_NOCODE,
        _rows_svc_ticket(report),
        COLS_SVC_TICKET,
        _rows_cat_ds1(report),
        COLS_CAT_DS1,
        _rows_cat_ds1_unit(report),
        COLS_CAT_DS1_UNIT,
        _rows_cat_ds2(report),
        COLS_CAT_DS2,
        _rows_dx_mismatch(report),
        COLS_DX_MISMATCH,
    )


def _empty_tables():
    return (
        [],
        COLS_DIAG,
        [],
        COLS_ONE,
        [],
        COLS_MULTI,
        [],
        COLS_INV,
        [],
        COLS_CODES,
        [],
        COLS_NOCODE,
        [],
        COLS_SVC_TICKET,
        [],
        COLS_CAT_DS1,
        [],
        COLS_CAT_DS1_UNIT,
        [],
        COLS_CAT_DS2,
        [],
        COLS_DX_MISMATCH,
    )


app.clientside_callback(
    """
    function(n_clicks, active_tab, sel_one, data_one, sel_multi, data_multi, sel_inv, data_inv, sel_nocode, data_nocode, sel_svc, data_svc, sel_dx, data_dx, base) {
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
        else if (active_tab === 'a-inv') { sel = sel_inv; data = data_inv; }
        else if (active_tab === 'a-nocode') { sel = sel_nocode; data = data_nocode; }
        else if (active_tab === 'a-svc-ticket') { sel = sel_svc; data = data_svc; }
        else if (active_tab === 'a-dx-mismatch') { sel = sel_dx; data = data_dx; }
        else { return ''; }
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
    State(f"{PREFIX}-tbl-inv", "selected_rows"),
    State(f"{PREFIX}-tbl-inv", "data"),
    State(f"{PREFIX}-tbl-nocode", "selected_rows"),
    State(f"{PREFIX}-tbl-nocode", "data"),
    State(f"{PREFIX}-tbl-svc-ticket", "selected_rows"),
    State(f"{PREFIX}-tbl-svc-ticket", "data"),
    State(f"{PREFIX}-tbl-dx-mismatch", "selected_rows"),
    State(f"{PREFIX}-tbl-dx-mismatch", "data"),
    State(f"{PREFIX}-claim-base-url", "data"),
    prevent_initial_call=True,
)
