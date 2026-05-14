"""
Вкладка «ИСЗЛ» — загрузка CSV из внешней системы и расчет потребности в услугах ДН.
"""
from __future__ import annotations

import base64
import csv
import io
import re
from collections import defaultdict
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, dash_table
from dash.exceptions import PreventUpdate
from sqlalchemy import bindparam, text

from apps.dash_dn.app import dash_dn_app as app
from apps.dash_dn.catalog_periods import default_active_catalog
from apps.dash_dn.sqlite_catalog.db import get_engine

PREFIX = "dash-dn-iszl"

ICD10_CODE_RE = re.compile(r"\b([A-Z]\d{2}(?:\.\d+)?)\b", re.IGNORECASE)
SERVICE_CODE_RE = re.compile(r"^([AB]\d{2}\.\d{2,3}\.\d{3})(?:\.\d{3})*$", re.IGNORECASE)


def _table(table_id: str, page_size: int = 20):
    return dash_table.DataTable(
        id=table_id,
        columns=[],
        data=[],
        page_size=page_size,
        page_action="native",
        filter_action="native",
        sort_action="native",
        export_format="xlsx",
        export_headers="display",
        style_table={
            "overflowX": "auto",
            "maxHeight": "450px",
            "border": "1px solid #dee2e6",
            "borderRadius": "0.375rem",
        },
        style_cell={
            "fontSize": "0.85rem",
            "padding": "6px 8px",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#f1f5f9"},
    )


def layout_body():
    return html.Div(
        [
            html.P(
                "Загрузите CSV из ИСЗЛ (формат Report - *.csv). "
                "Расчет: для каждого пациента берутся все диагнозы, затем подбираются услуги "
                "из справочника ДН. Если одна и та же услуга встречается по нескольким диагнозам "
                "одного пациента, она учитывается один раз.",
                className="text-muted small",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Upload(
                            id=f"{PREFIX}-upload",
                            children=html.Div(
                                [
                                    html.I(className="bi bi-cloud-upload me-2"),
                                    "Перетащите CSV сюда или нажмите для выбора файла",
                                ],
                                className="small",
                            ),
                            className="border rounded-3 p-4 text-center bg-white",
                            style={"cursor": "pointer"},
                            multiple=False,
                        ),
                        md=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Год плана (PlanYear)", className="small fw-semibold"),
                            dbc.Input(
                                id=f"{PREFIX}-year",
                                type="number",
                                min=2010,
                                max=2100,
                                step=1,
                                value=datetime.now().year,
                                size="sm",
                            ),
                            dbc.Checklist(
                                id=f"{PREFIX}-only-active",
                                options=[
                                    {
                                        "label": " Только состоящие на учете (DateEnd пустой)",
                                        "value": "only_active",
                                    }
                                ],
                                value=["only_active"],
                                className="small mt-2",
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="g-3 mb-3",
            ),
            html.Div(id=f"{PREFIX}-msg", className="mb-2"),
            html.Div(id=f"{PREFIX}-summary", className="mb-3"),
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="Перечень услуг",
                        tab_id="iszl-services",
                        children=html.Div(_table(f"{PREFIX}-tbl-services"), className="pt-3"),
                    ),
                    dbc.Tab(
                        label="Свод по диагнозам",
                        tab_id="iszl-diagnoses",
                        children=html.Div(_table(f"{PREFIX}-tbl-diagnoses"), className="pt-3"),
                    ),
                ]
            ),
        ]
    )


def _decode_csv_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1251", "windows-1251", "latin1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Не удалось декодировать файл (utf-8/cp1251/windows-1251/latin1).")


def _read_iszl_csv(raw: bytes) -> list[dict[str, str]]:
    text = _decode_csv_bytes(raw)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not reader.fieldnames:
        raise ValueError("Пустой CSV или не найден заголовок.")
    rows = [dict(r) for r in reader]
    if not rows:
        raise ValueError("В CSV нет строк данных.")
    return rows


def _norm_text(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\u00a0", " ").strip()


def _norm_enp(value) -> str:
    return _norm_text(value).replace("`", "")


def _is_empty_date_end(value) -> bool:
    v = _norm_text(value).lower()
    return v in {"", "-", "—", "none", "nan", "null"}


def _extract_icd_codes(value: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in ICD10_CODE_RE.finditer(_norm_text(value).upper()):
        code = m.group(1).upper()
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def _service_code_base(code: str) -> str:
    c = _norm_text(code).upper()
    if not c:
        return ""
    m = SERVICE_CODE_RE.match(c)
    if m:
        return m.group(1).upper()
    return c


def _load_services_for_icd_codes(
    icd_codes: set[str] | list[str],
    catalog: str | None = None,
) -> dict[str, list[tuple[str, str, int]]]:
    """
    Код МКБ -> список (код услуги, название, is_required).
    Возвращаем и обязательные, и необязательные услуги.
    """
    from apps.dash_dn.catalog_periods import default_active_catalog

    catalog = (catalog or default_active_catalog()).strip() or default_active_catalog()
    codes = sorted({str(c).upper().strip() for c in icd_codes if str(c).strip()})
    out: dict[str, list[tuple[str, str, int]]] = {c: [] for c in codes}
    if not codes:
        return out

    q = text(
        """
        SELECT DISTINCT
            UPPER(TRIM(d.code)) AS dcode,
            srv.code AS scode,
            srv.name AS sname,
            sr.is_required AS is_required
        FROM dn_diagnosis d
        JOIN dn_diagnosis_group_membership gm
          ON gm.diagnosis_id = d.id AND gm.catalog = :cat AND gm.is_active = 1
        JOIN dn_service_requirement sr
          ON sr.group_id = gm.group_id AND sr.catalog = :cat
        JOIN dn_service srv
          ON srv.id = sr.service_id AND srv.catalog = :cat AND srv.is_active = 1
        WHERE d.catalog = :cat AND d.is_active = 1
          AND UPPER(TRIM(d.code)) IN :codes
        ORDER BY dcode, scode
        """
    ).bindparams(bindparam("codes", expanding=True))

    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(q, {"cat": catalog, "codes": codes}).fetchall()

    seen: dict[str, set[tuple[str, int]]] = defaultdict(set)
    for dcode, scode, sname, is_required in rows:
        if not dcode or not scode:
            continue
        key = str(dcode).upper()
        req = 1 if int(is_required or 0) == 1 else 0
        uniq = (str(scode), req)
        if uniq in seen[key]:
            continue
        seen[key].add(uniq)
        out.setdefault(key, []).append((str(scode), str(sname or ""), req))
    return out


def _build_iszl_report(
    rows: list[dict[str, str]],
    target_year: int,
    only_active: bool,
    *,
    catalog: str | None = None,
) -> dict:
    from apps.dash_dn.catalog_periods import default_active_catalog

    catalog = (catalog or default_active_catalog()).strip() or default_active_catalog()
    required_columns = {"ENP", "DS"}
    missing = [c for c in required_columns if c not in rows[0]]
    if missing:
        raise KeyError(f"В CSV нет обязательных колонок: {', '.join(missing)}.")

    has_year = "PlanYear" in rows[0]
    has_date_end = "DateEnd" in rows[0]

    filtered_rows: list[dict[str, str]] = []
    skipped_not_year = 0
    skipped_inactive = 0
    skipped_no_enp = 0
    skipped_no_ds = 0

    for row in rows:
        enp = _norm_enp(row.get("ENP"))
        if not enp:
            skipped_no_enp += 1
            continue

        ds = _norm_text(row.get("DS"))
        if not ds:
            skipped_no_ds += 1
            continue

        if has_year:
            raw_year = _norm_text(row.get("PlanYear"))
            try:
                year = int(float(raw_year))
            except ValueError:
                skipped_not_year += 1
                continue
            if year != target_year:
                skipped_not_year += 1
                continue

        if only_active and has_date_end and not _is_empty_date_end(row.get("DateEnd")):
            skipped_inactive += 1
            continue

        filtered_rows.append(row)

    if not filtered_rows:
        raise ValueError("После фильтрации не осталось строк для анализа.")

    patient_to_diag_codes: dict[str, set[str]] = defaultdict(set)
    for row in filtered_rows:
        enp = _norm_enp(row.get("ENP"))
        codes = _extract_icd_codes(row.get("DS"))
        if not codes:
            continue
        for code in codes:
            patient_to_diag_codes[enp].add(code)

    if not patient_to_diag_codes:
        raise ValueError("В отфильтрованных строках не удалось извлечь коды МКБ из колонки DS.")

    all_diag_codes = sorted({c for codes in patient_to_diag_codes.values() for c in codes})
    all_diag_for_lookup = sorted({*all_diag_codes, *[c.split(".")[0] for c in all_diag_codes]})
    services_by_diag_lookup = _load_services_for_icd_codes(all_diag_for_lookup, catalog=catalog)

    patient_to_service_bases: dict[str, set[str]] = defaultdict(set)
    service_meta: dict[str, tuple[str, str]] = {}
    service_required_state: dict[str, set[int]] = defaultdict(set)

    for enp, diag_codes in patient_to_diag_codes.items():
        for diag in sorted(diag_codes):
            direct_services = services_by_diag_lookup.get(diag, [])
            fallback_services = services_by_diag_lookup.get(diag.split(".")[0], [])
            chosen = direct_services or fallback_services

            service_bases_for_diag: set[str] = set()
            for svc_code, svc_name, svc_required in chosen:
                base = _service_code_base(svc_code)
                if not base:
                    continue
                service_bases_for_diag.add(base)
                patient_to_service_bases[enp].add(base)
                if base not in service_meta:
                    service_meta[base] = (str(svc_code), str(svc_name or ""))
                service_required_state[base].add(1 if int(svc_required or 0) == 1 else 0)

    by_diag: dict[str, dict] = defaultdict(lambda: {"patients_set": set(), "services_set": set()})
    for enp, diag_codes in patient_to_diag_codes.items():
        for diag in diag_codes:
            by_diag[diag]["patients_set"].add(enp)
            direct_services = services_by_diag_lookup.get(diag, [])
            fallback_services = services_by_diag_lookup.get(diag.split(".")[0], [])
            chosen = direct_services or fallback_services
            for svc_code, _svc_name, _svc_required in chosen:
                base = _service_code_base(svc_code)
                if base:
                    by_diag[diag]["services_set"].add(base)

    diagnosis_table = []
    for diag, agg in by_diag.items():
        diagnosis_table.append(
            {
                "diag": diag,
                "patients": len(agg["patients_set"]),
                "svc_count": len(agg["services_set"]),
                "services": "; ".join(sorted(agg["services_set"])),
            }
        )
    diagnosis_table.sort(key=lambda x: (-x["patients"], x["diag"]))

    service_to_patients: dict[str, set[str]] = defaultdict(set)
    for enp, svc_set in patient_to_service_bases.items():
        for svc in svc_set:
            service_to_patients[svc].add(enp)

    services_table = []
    for base, patients in service_to_patients.items():
        src_code, src_name = service_meta.get(base, (base, ""))
        req_vals = service_required_state.get(base, set())
        if 1 in req_vals and 0 in req_vals:
            req_label = "Обязательная и необязательная"
        elif 1 in req_vals:
            req_label = "Обязательная"
        else:
            req_label = "Необязательная"
        services_table.append(
            {
                "svc_code": base,
                "svc_source_code": src_code,
                "svc_name": src_name,
                "svc_type": req_label,
                "patients": len(patients),
            }
        )
    services_table.sort(key=lambda x: (-x["patients"], x["svc_code"]))

    total_with_any_service = sum(1 for _enp, svc in patient_to_service_bases.items() if svc)
    total_patients = len(patient_to_diag_codes)
    uncovered_patients = total_patients - total_with_any_service

    return {
        "total_rows": len(rows),
        "rows_after_filter": len(filtered_rows),
        "unique_patients": total_patients,
        "patients_with_services": total_with_any_service,
        "patients_without_services": uncovered_patients,
        "unique_diagnoses": len(all_diag_codes),
        "unique_services": len(service_to_patients),
        "skipped_not_year": skipped_not_year,
        "skipped_inactive": skipped_inactive,
        "skipped_no_enp": skipped_no_enp,
        "skipped_no_ds": skipped_no_ds,
        "services_table": services_table,
        "diagnosis_table": diagnosis_table,
    }


COLS_SERVICES = [
    {"name": "Код услуги (база)", "id": "svc_code"},
    {"name": "Код из справочника", "id": "svc_source_code"},
    {"name": "Наименование услуги", "id": "svc_name"},
    {"name": "Тип услуги", "id": "svc_type"},
    {"name": "Пациентов", "id": "patients", "type": "numeric"},
]

COLS_DIAG = [
    {"name": "Диагноз (МКБ)", "id": "diag"},
    {"name": "Пациентов", "id": "patients", "type": "numeric"},
    {"name": "Услуг по диагнозу", "id": "svc_count", "type": "numeric"},
    {"name": "Коды услуг", "id": "services"},
]


@app.callback(
    Output(f"{PREFIX}-msg", "children"),
    Output(f"{PREFIX}-summary", "children"),
    Output(f"{PREFIX}-tbl-services", "data"),
    Output(f"{PREFIX}-tbl-services", "columns"),
    Output(f"{PREFIX}-tbl-diagnoses", "data"),
    Output(f"{PREFIX}-tbl-diagnoses", "columns"),
    Input(f"{PREFIX}-upload", "contents"),
    State(f"{PREFIX}-upload", "filename"),
    State(f"{PREFIX}-year", "value"),
    State(f"{PREFIX}-only-active", "value"),
    State("dash-dn-active-catalog", "data"),
    prevent_initial_call=True,
)
def run_iszl_analysis(contents, filename, year_value, only_active_flags, active_catalog):
    if not contents:
        raise PreventUpdate
    try:
        _meta, content_string = contents.split(",", 1)
        raw = base64.b64decode(content_string)
    except Exception:
        return (
            dbc.Alert("Не удалось прочитать загруженный файл.", color="danger", className="py-2 mb-0"),
            None,
            [],
            COLS_SERVICES,
            [],
            COLS_DIAG,
        )

    if not raw:
        raise PreventUpdate

    try:
        year = int(year_value) if year_value is not None else datetime.now().year
    except (TypeError, ValueError):
        year = datetime.now().year

    only_active = "only_active" in (only_active_flags or [])

    cat = str(active_catalog or default_active_catalog()).strip() or default_active_catalog()

    try:
        rows = _read_iszl_csv(raw)
        report = _build_iszl_report(rows, year, only_active, catalog=cat)
    except Exception as e:
        return (
            dbc.Alert(f"Ошибка анализа: {e}", color="danger", className="py-2 mb-0"),
            None,
            [],
            COLS_SERVICES,
            [],
            COLS_DIAG,
        )

    msg = dbc.Alert(
        f"Обработан файл: {filename or 'файл'}. "
        f"Строк в файле: {report['total_rows']}, после фильтров: {report['rows_after_filter']}. "
        f"Пациентов: {report['unique_patients']}, услуг в итоге: {report['unique_services']}. "
        f"Каталог справочника: {cat}.",
        color="success",
        className="py-2 mb-0",
    )

    summary = dbc.Row(
        [
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Пациентов", className="text-muted small"), html.H4(str(report["unique_patients"]), className="mb-0")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Пациентов с услугами", className="text-muted small"), html.H4(str(report["patients_with_services"]), className="mb-0")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Без услуг по справочнику", className="text-muted small"), html.H4(str(report["patients_without_services"]), className="mb-0")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Уникальных диагнозов", className="text-muted small"), html.H4(str(report["unique_diagnoses"]), className="mb-0")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Уникальных услуг", className="text-muted small"), html.H4(str(report["unique_services"]), className="mb-0")])), md=2),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div("Отфильтровано строк", className="text-muted small"),
                            html.H4(
                                str(
                                    report["skipped_not_year"]
                                    + report["skipped_inactive"]
                                    + report["skipped_no_enp"]
                                    + report["skipped_no_ds"]
                                ),
                                className="mb-0",
                            ),
                        ]
                    )
                ),
                md=2,
            ),
        ],
        className="g-2",
    )

    return (
        msg,
        summary,
        report["services_table"],
        COLS_SERVICES,
        report["diagnosis_table"],
        COLS_DIAG,
    )
