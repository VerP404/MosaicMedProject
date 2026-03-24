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
                "Загрузите CSV выгрузки услуг (разделитель «;», как в Квазар). "
                "Сверка кодов услуг — по справочнику в локальной SQLite (таблица dn_service, каталог global), "
                "той же базе, что использует вкладка «Подбор услуг ДН». "
                "Колонка «Услуги» строится из поля «Код услуги» построчно: если в файле стоит «-», "
                "в отчёте будет «без кода в выгрузке» — так бывает у части строк одного талона в выгрузке Квазар.",
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


def _summary_cards(report: dict, ref_line: str) -> html.Div:
    return html.Div(
        [
            html.P(ref_line, className="small text-muted mb-2"),
            dbc.Row(
                [
                    _card("Уникальных талонов", str(report["unique_tickets"])),
                    _card("Строк в выгрузке", str(report["total_rows"])),
                    _card("Талонов с 1 услугой", str(len(report["single_service"]))),
                    _card(
                        "Строк с проблемным кодом / без кода",
                        f"{len(report['invalid_lines'])} / {len(report['no_code_lines'])}",
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
            "status": t.get("статус", ""),
            "diag": t["диагноз"],
            "services": t.get("услуги", ""),
            "sum": round(float(t["сумма_талона"]), 2),
        }
        for t in sorted(report["single_service"], key=lambda x: x["талон"])
    ]


def _rows_multi(report: dict) -> list[dict]:
    return [
        {
            "tal": t["талон"],
            "status": t.get("статус", ""),
            "diag": t["диагноз"],
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
            "status": x.get("статус", ""),
            "diag": x["диагноз"],
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
            "status": x.get("статус", ""),
            "diag": x["диагноз"],
            "code": x["код_услуги"],
            "sum": round(float(x["сумма_услуги"]), 2),
        }
        for x in report["no_code_lines"]
    ]


COLS_DIAG = [
    {"name": "Диагноз основной (DS1)", "id": "diagnosis"},
    {"name": "Талонов", "id": "tickets", "type": "numeric"},
    {"name": "Сумма талонов", "id": "sum", "type": "numeric"},
]
COLS_ONE = [
    {"name": "Талон", "id": "tal"},
    {"name": "Статус", "id": "status"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "Услуги (код — сумма)", "id": "services"},
    {"name": "Сумма талона", "id": "sum", "type": "numeric"},
]
COLS_MULTI = [
    {"name": "Талон", "id": "tal"},
    {"name": "Статус", "id": "status"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "Услуги (код — сумма)", "id": "services"},
    {"name": "Сумма талона", "id": "sum", "type": "numeric"},
    {"name": "Число строк услуг", "id": "n", "type": "numeric"},
]
COLS_INV = [
    {"name": "Талон", "id": "tal"},
    {"name": "Статус", "id": "status"},
    {"name": "Диагноз (DS1)", "id": "diag"},
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
    {"name": "Статус", "id": "status"},
    {"name": "Диагноз (DS1)", "id": "diag"},
    {"name": "Поле «Код услуги»", "id": "code"},
    {"name": "Сумма услуги", "id": "sum", "type": "numeric"},
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
        _fn, rows = read_detail_csv_from_bytes(raw)
        report = build_report(rows, allowed)
    except Exception as e:
        return (
            dbc.Alert(f"Ошибка разбора: {e}", color="danger", className="py-2 mb-0"),
            None,
            *_empty_tables(),
        )

    db_path = get_db_path()
    ref_line = (
        f"Справочник: SQLite · dn_service (catalog=global) · {db_path} — {len(allowed)} кодов"
    )
    summary = _summary_cards(report, ref_line)
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
    )


app.clientside_callback(
    """
    function(n_clicks, active_tab, sel_one, data_one, sel_multi, data_multi, sel_inv, data_inv, sel_nocode, data_nocode, base) {
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
    State(f"{PREFIX}-claim-base-url", "data"),
    prevent_initial_call=True,
)
