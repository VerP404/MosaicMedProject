"""Сверка талонов цели 3 с матрицей и выгрузка для BrowserAuto/исправление_услуг."""

from __future__ import annotations

import csv
import io
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from apps.dn_matrix.models import DnSpecialty, MatrixEdition
from apps.dn_matrix.services.batch_pick import resolve_specialty_id
from apps.dn_matrix.services.matrix import (
    MatrixPickCache,
    build_matrix_pick_cache,
    cap_doctor_visits,
    category_for_mkb_in_cache,
    normalize_mkb,
    normalize_patient_sex,
    resolve_edition_for_date,
    select_services_from_cache,
)
from apps.dn_matrix.services.pick_pricing import is_per_visit_service
from apps.dn_matrix.services.service_codes import (
    ServiceCodeEquivalence,
    compare_expected_actual_services,
    normalize_dn_service_code,
    service_codes_compatible,
)
from apps.dn_matrix.services.talon_bundle import (
    DEFAULT_HEADER_DEFAULTS,
    extract_doctor_id,
    norm_enp,
    render_talon_bundle_zip,
    _is_oncology_row,
    codes_from_birth_year,
)

EDITABLE_STATUSES = frozenset({"1", "5", "6", "7", "8", "18", "19"})
# Без \\b после кода: иначе I11.9ГИПЕРТЕНЗИЯ (пробел съел normalize) даёт ложный I11.
ICD10_CODE_RE = re.compile(r"(?<![A-ZА-Я0-9])([A-ZА-Я]\d{2}(?:\.\d{1,4})?)", re.IGNORECASE)


def norm_status(raw: object) -> str:
    text = str(raw or "").strip()
    if not text or text in {"-", "nan", "None"}:
        return ""
    try:
        return str(int(float(text.replace(",", "."))))
    except ValueError:
        return text


def is_ticket_fixable(
    status: str,
    *,
    mismatch: bool,
    expected: list[dict[str, Any]],
    enp: str,
    ds1: str,
    allowed_statuses: set[str] | frozenset[str] | None = None,
) -> bool:
    allowed = {norm_status(s) for s in (allowed_statuses or EDITABLE_STATUSES)}
    return bool(mismatch and expected and norm_status(status) in allowed and enp and ds1)


@dataclass
class DetailLine:
    code: str
    qty: int
    start: str
    end: str
    doctor: str


@dataclass
class FixTicket:
    ticket: str
    status: str
    enp: str
    fio: str
    ds1: str
    ds2: list[str]
    ds2_full: list[str]
    specialty: str
    doctor: str
    department: str
    start_ui: str
    end_ui: str
    actual: dict[str, int]
    expected: list[dict[str, Any]]
    missing: list[dict[str, Any]]
    extra: list[dict[str, Any]]
    fixable: bool
    detail_lines: list[DetailLine] = field(default_factory=list)
    gender: str = ""
    messages: list[str] = field(default_factory=list)
    header_extra: dict[str, str] = field(default_factory=dict)
    birth_ui: str = ""


def extract_icd_list(raw: str) -> list[str]:
    """Все коды МКБ из строки журнала, без усечения I11.9 → I11."""
    text = str(raw or "").strip().upper().replace("А", "A").replace("В", "B")
    if not text or text in {"-", "—", "НЕТ"}:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for match in ICD10_CODE_RE.finditer(text):
        code = normalize_mkb(match.group(1))
        if not code or code in seen:
            continue
        seen.add(code)
        found.append(code)
    return drop_covered_mkb_prefixes(found)


def extract_icd(raw: str) -> str:
    codes = extract_icd_list(raw)
    return codes[0] if codes else ""


def drop_covered_mkb_prefixes(codes: list[str]) -> list[str]:
    """Если есть I11.9, не оставляем пустышку I11."""
    norms = [normalize_mkb(c) for c in codes if normalize_mkb(c)]
    specific = {c for c in norms if "." in c}
    out: list[str] = []
    for code in norms:
        if "." not in code and any(spec.startswith(code + ".") for spec in specific):
            continue
        if code not in out:
            out.append(code)
    return out


def parse_ui_date(raw: object) -> str:
    """dd-mm-yy для web.ОМС / BrowserAuto. Пусто, если разобрать нельзя."""
    if raw is None:
        return ""
    if isinstance(raw, datetime):
        return raw.date().strftime("%d-%m-%y")
    if isinstance(raw, date):
        return raw.strftime("%d-%m-%y")
    text = str(raw).strip()
    if not text or text in {"-", "nan", "None"}:
        return ""
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d-%m-%y", "%d.%m.%y"):
        try:
            return datetime.strptime(text[:10] if len(text) > 10 else text, fmt).date().strftime("%d-%m-%y")
        except ValueError:
            continue
    if len(text) >= 8 and text[2] in ".-" and text[5] in ".-":
        return text.replace(".", "-")[:8]
    return ""


def parse_as_date(raw: object) -> date | None:
    ui = parse_ui_date(raw)
    if not ui:
        return None
    try:
        return datetime.strptime(ui, "%d-%m-%y").date()
    except ValueError:
        return None


def _decode_csv(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8-sig")
        if "\ufffd" in text:
            raise UnicodeDecodeError("utf-8", raw, 0, 1, "replacement")
        return text
    except UnicodeDecodeError:
        return raw.decode("cp1251", errors="replace")


def _norm_header(name: object) -> str:
    return str(name or "").replace("\ufeff", "").strip().lower().replace("ё", "е")


def _parse_qty(raw: object) -> int:
    text = str(raw or "").strip().replace(",", ".")
    if not text:
        return 1
    try:
        return max(1, int(float(text)))
    except ValueError:
        return 1


def norm_ticket_id(raw: object) -> str:
    """Номер талона журнала и файла услуг к одному виду (без .0 из Excel)."""
    text = str(raw or "").replace("\ufeff", "").strip()
    if not text or text.lower() in {"-", "nan", "none"}:
        return ""
    compact = text.replace(" ", "")
    try:
        return str(int(float(compact.replace(",", "."))))
    except ValueError:
        return text


def parse_detail_services(raw: bytes, filename: str = "") -> dict[str, list[DetailLine]]:
    """Разбор detail_services CSV/Excel: факт услуг по номеру талона."""
    name = (filename or "").lower()
    rows: list[dict[str, Any]]
    if name.endswith((".xlsx", ".xls")):
        import pandas as pd

        df = pd.read_excel(io.BytesIO(raw), dtype=str)
        rows = df.fillna("").to_dict("records")
    else:
        content = _decode_csv(raw)
        sample = content[:4000]
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        rows = [dict(r) for r in reader] if reader.fieldnames else []

    if not rows:
        return {}
    headers = {_norm_header(k): k for k in rows[0].keys()}

    def col(*aliases: str) -> str | None:
        for alias in aliases:
            if alias in headers:
                return headers[alias]
        return None

    ticket_col = col("талон", "talon", "номер талона")
    code_col = col("код услуги", "услуга код", "код")
    qty_col = col("кол-во услуг", "количество услуг", "количество", "кол-во", "qty")
    amount_col = col("сумма услуги", "сумма")
    start_col = col("дата начала услуги", "дата начала")
    end_col = col("дата окончания услуги", "дата окончания")
    doctor_col = col("врач в услуге", "врач услуги", "врач")
    if not ticket_col or not code_col:
        raise ValueError("В файле услуг нужны колонки «Талон» и «Код услуги».")

    out: dict[str, list[DetailLine]] = defaultdict(list)
    for row in rows:
        ticket = norm_ticket_id(row.get(ticket_col))
        if not ticket or ticket in {"-", "nan"}:
            continue
        if amount_col:
            amt = str(row.get(amount_col) or "").strip().replace(",", ".")
            try:
                if amt and float(amt) == 0:
                    continue
            except ValueError:
                pass
        code = normalize_dn_service_code(str(row.get(code_col) or ""))
        if not code:
            continue
        start = parse_ui_date(row.get(start_col) if start_col else "")
        end = parse_ui_date(row.get(end_col) if end_col else "") or start
        doctor = str(row.get(doctor_col) or "").strip() if doctor_col else ""
        out[ticket].append(
            DetailLine(
                code=code,
                qty=_parse_qty(row.get(qty_col) if qty_col else 1),
                start=start,
                end=end,
                doctor=doctor,
            )
        )
    return dict(out)


def _billable_iszl(codes: set[str], specialty_id: int | None, cache: MatrixPickCache) -> set[str]:
    if specialty_id is None or not codes:
        return set()
    out: set[str] = set()
    for mkb in codes:
        did = cache.mkb_to_diagnosis_id.get(normalize_mkb(mkb))
        if did is None:
            continue
        if (did, specialty_id) in cache.diagnosis_specialty_billable:
            out.add(normalize_mkb(mkb))
    return out


def _merge_ds2(journal_ds2: list[str], extra: set[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in list(journal_ds2 or []) + sorted(extra):
        n = normalize_mkb(raw)
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return drop_covered_mkb_prefixes(out)


def _fmt_codes(items: list[dict[str, Any]]) -> str:
    ordered = sorted(
        items,
        key=lambda i: (str(i.get("code") or ""), int(i.get("qty") or 1)),
    )
    return ", ".join(
        f"{i['code']}×{i['qty']}" if int(i.get("qty") or 1) > 1 else str(i["code"]) for i in ordered
    )


def _pick_service_dates(
    *,
    code: str,
    title: str,
    detail_lines: list[DetailLine],
    ticket_start: str,
    ticket_end: str,
    code_equiv: ServiceCodeEquivalence,
) -> tuple[str, str, str]:
    """Даты не выдумываем: из детализации, иначе период талона (для новых строк Web.ОМС требует даты)."""
    matches = [ln for ln in detail_lines if service_codes_compatible(ln.code, code, code_equiv=code_equiv)]
    if is_per_visit_service(title):
        doctor = next((ln.doctor for ln in matches if ln.doctor), "")
        return ticket_start or ticket_end, ticket_end or ticket_start, doctor
    if matches:
        ln = matches[0]
        begin = ln.start or ticket_start
        end = ln.end or ln.start or ticket_start
        doctor = next((ln.doctor for ln in matches if ln.doctor), "")
        return begin, end, doctor
    first_existing = next((ln for ln in detail_lines if ln.start), None)
    if first_existing:
        return first_existing.start, first_existing.start, first_existing.doctor
    return ticket_start, ticket_start, ""


def _journal_visits(raw: object) -> int:
    text = str(raw or "").strip().replace(",", ".")
    try:
        return max(0, int(float(text)))
    except ValueError:
        return 0


def _ticket_to_preview(item: FixTicket) -> dict[str, Any]:
    in_file = bool(item.detail_lines or item.actual)
    if in_file:
        fact = _fmt_codes([{"code": c, "qty": q} for c, q in sorted(item.actual.items())])
        missing = _fmt_codes(item.missing)
    else:
        fact = "нет в файле"
        missing = "весь набор матрицы (талона нет в файле)"
    return {
        "Талон": item.ticket,
        "Статус": item.status,
        "ЕНП": item.enp,
        "ФИО": item.fio,
        "DS1": item.ds1,
        "DS2": ", ".join(item.ds2),
        "DS2 журнал+ИСЗЛ": ", ".join(item.ds2_full),
        "Специальность": item.specialty,
        "Факт": fact,
        "По матрице": _fmt_codes(item.expected),
        "Недостаёт": missing,
        "Лишнее": _fmt_codes(item.extra),
        "Исправить": "да" if item.fixable else "нет",
        "Комментарий": " ".join(item.messages),
    }


def _journal_header_extra(raw: dict[str, Any]) -> dict[str, str]:
    mapping = {
        "цель": raw.get("goal"),
        "случай": raw.get("case_code"),
        "посещений в МО": raw.get("mo_visits") or raw.get("visits"),
        "ДИСП. НАБЛ": raw.get("dispensary_monitoring"),
        "тип": raw.get("talon_type"),
        "результат": raw.get("result"),
        "исход": raw.get("outcome"),
        "характер": raw.get("main_disease_character"),
        "напр дано": raw.get("care_conditions"),
    }
    out: dict[str, str] = {}
    for key, val in mapping.items():
        text = str(val or "").strip()
        if text and text not in {"-", "nan", "None"}:
            out[key] = text
    return out


def reconcile_ticket_row(
    raw: dict[str, Any],
    *,
    detail_lines: list[DetailLine],
    iszl_mkbs: set[str],
    edition: MatrixEdition,
    cache: MatrixPickCache,
    specs: list[DnSpecialty],
    equiv: ServiceCodeEquivalence,
    price_on: date,
    allowed_statuses: set[str] | frozenset[str] | None = None,
) -> FixTicket:
    """Сверка одной строки журнала с матрицей (без SQL)."""
    oms = norm_ticket_id(raw.get("talon"))
    ds1 = extract_icd(str(raw.get("main_diagnosis") or ""))
    ds2 = [c for c in extract_icd_list(str(raw.get("additional_diagnosis") or "")) if c and c != ds1]
    profile = str(raw.get("specialty") or raw.get("doctor_profile") or "").strip()
    spec_id = resolve_specialty_id(cache, specs, profile=profile, mkb_code=ds1)
    spec_title = next((s.title for s in specs if s.id == spec_id), profile) if spec_id else profile
    sex = normalize_patient_sex(raw.get("gender"))
    actual: Counter[str] = Counter()
    for ln in detail_lines:
        actual[ln.code] += ln.qty
    enp = norm_enp(raw.get("enp"))
    iszl_billable = _billable_iszl(iszl_mkbs, spec_id, cache)
    ds1_n = normalize_mkb(ds1)
    ds2_full = _merge_ds2(ds2, {c for c in iszl_billable if c != ds1_n})
    header_extra = _journal_header_extra(raw)
    common = dict(
        ticket=oms,
        status=norm_status(raw.get("status")),
        enp=enp,
        fio=str(raw.get("patient") or "").strip(),
        ds1=ds1,
        ds2=ds2,
        ds2_full=ds2_full,
        specialty=spec_title,
        doctor=str(raw.get("doctor") or "").strip(),
        department=str(raw.get("department") or "").strip(),
        start_ui=parse_ui_date(raw.get("treatment_start")),
        end_ui=parse_ui_date(raw.get("treatment_end")),
        actual=dict(actual),
        detail_lines=detail_lines,
        gender=str(raw.get("gender") or ""),
        header_extra=header_extra,
        birth_ui=parse_ui_date(raw.get("birth_date")),
    )
    if spec_id is None:
        return FixTicket(
            **common,
            expected=[],
            missing=[],
            extra=[{"code": c, "qty": q} for c, q in sorted(actual.items())],
            fixable=False,
            messages=["специальность не сопоставлена с матрицей"]
            + (["талона нет в файле услуг"] if not detail_lines else []),
        )

    rows, _, _ = select_services_from_cache(
        cache,
        specialty_id=spec_id,
        mkb_code=ds1,
        price_on=price_on,
        secondary_mkb_list=ds2_full or None,
        patient_sex=sex,
    )
    per_visit_codes = {
        normalize_dn_service_code(str(r.get("code") or ""))
        for r in rows
        if is_per_visit_service(str(r.get("title") or ""))
    }
    detail_visits = 0
    for code, qty in actual.items():
        if any(service_codes_compatible(code, pv, code_equiv=equiv) for pv in per_visit_codes):
            detail_visits += int(qty)
    journal_visits = _journal_visits(raw.get("visits") or raw.get("mo_visits"))
    visit_cap = cap_doctor_visits(edition, detail_visits or journal_visits or 1)

    expected: list[dict[str, Any]] = []
    expected_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("unavailable"):
            continue
        code = normalize_dn_service_code(str(row.get("code") or ""))
        if not code:
            continue
        title = str(row.get("title") or "")
        qty = visit_cap if is_per_visit_service(title) else 1
        info = {"code": code, "title": title, "qty": qty}
        expected_map[code] = info
        expected.append(info)

    expected.sort(key=lambda i: str(i.get("code") or ""))
    missing, extra = compare_expected_actual_services(expected_map, actual, code_equiv=equiv)
    st = norm_status(raw.get("status"))
    mismatch = bool(missing or extra)
    messages: list[str] = []
    if missing:
        messages.append("недостаёт: " + _fmt_codes(missing))
    if extra:
        messages.append("лишнее: " + _fmt_codes(extra))
    if not ds1:
        messages.append("нет DS1")
    if not detail_lines:
        messages.append("талона нет в файле услуг — недостаёт весь набор матрицы")
    fixable = is_ticket_fixable(
        st,
        mismatch=mismatch,
        expected=expected,
        enp=enp,
        ds1=ds1,
        allowed_statuses=allowed_statuses,
    )
    return FixTicket(
        **common,
        expected=expected,
        missing=missing,
        extra=extra,
        fixable=fixable,
        messages=messages,
    )


def run_service_fix_report(
    engine,
    *,
    year: int,
    date_from: date,
    date_to: date,
    departments: list[str] | None,
    statuses: list[str] | None,
    detail_bytes: bytes,
    detail_filename: str = "",
    edition_id: int | None = None,
) -> tuple[list[FixTicket], list[dict[str, Any]], list[str]]:
    import pandas as pd

    from apps.analytical_app.pages.head.dn.query import sql_goal3_journal_talons, sql_iszl_mkb_by_enp
    from apps.dn_matrix.services.workspace import get_edition

    warnings: list[str] = []
    detail_by_ticket = parse_detail_services(detail_bytes, detail_filename)
    if not detail_by_ticket:
        return [], [], ["В файле услуг нет строк с талоном и кодом."]

    talons_df = pd.read_sql(
        sql_goal3_journal_talons(year, date_from, date_to, departments, statuses),
        con=engine,
    )
    wanted = {norm_status(s) for s in (statuses or []) if norm_status(s)}
    if wanted and talons_df is not None and not talons_df.empty and "status" in talons_df.columns:
        talons_df = talons_df[talons_df["status"].map(norm_status).isin(wanted)]
    if talons_df is None or talons_df.empty:
        return [], [], ["В журнале нет талонов цели 3 за выбранные даты и фильтры."]

    editions = list(MatrixEdition.objects.exclude(status=MatrixEdition.Status.ARCHIVED).order_by("-effective_from", "id"))
    forced = get_edition(edition_id) if edition_id else None
    cache_by_id: dict[int, tuple[MatrixEdition, MatrixPickCache, list[DnSpecialty], ServiceCodeEquivalence]] = {}

    def edition_pack(on: date) -> tuple[MatrixEdition, MatrixPickCache, list[DnSpecialty], ServiceCodeEquivalence] | None:
        ed = forced or resolve_edition_for_date(editions, on)
        if not ed:
            return None
        packed = cache_by_id.get(ed.id)
        if packed:
            return packed
        cache = build_matrix_pick_cache(ed)
        specs = list(ed.specialties.all().order_by("sort_order", "id"))
        equiv = ServiceCodeEquivalence([(s.id, s.code, s.title) for s in ed.services.all().only("id", "code", "title")])
        packed = (ed, cache, specs, equiv)
        cache_by_id[ed.id] = packed
        return packed

    enps = [norm_enp(r.get("enp")) for r in talons_df.to_dict("records")]
    enps = [e for e in enps if e]
    iszl_by_enp: dict[str, set[str]] = defaultdict(set)
    if enps:
        iszl_df = pd.read_sql(sql_iszl_mkb_by_enp(year, enps), con=engine)
        for row in iszl_df.to_dict("records") if iszl_df is not None and not iszl_df.empty else []:
            enp = norm_enp(row.get("enp_norm"))
            mkb = normalize_mkb(row.get("mkb") or "")
            if enp and mkb:
                iszl_by_enp[enp].add(mkb)

    tickets: list[FixTicket] = []
    for raw in talons_df.to_dict("records"):
        oms = norm_ticket_id(raw.get("talon"))
        if not oms:
            continue
        end_date = parse_as_date(raw.get("treatment_end")) or date_to
        pack = edition_pack(end_date)
        if not pack:
            warnings.append(f"Талон {oms}: нет редакции матрицы на {end_date.isoformat()}.")
            continue
        edition, cache, specs, equiv = pack
        enp = norm_enp(raw.get("enp"))
        tickets.append(
            reconcile_ticket_row(
                raw,
                detail_lines=detail_by_ticket.get(oms, []),
                iszl_mkbs=iszl_by_enp.get(enp) or set(),
                edition=edition,
                cache=cache,
                specs=specs,
                equiv=equiv,
                price_on=end_date,
                allowed_statuses=wanted or None,
            )
        )

    preview = [_ticket_to_preview(t) for t in tickets]
    mismatch_n = sum(1 for t in tickets if t.missing or t.extra)
    fix_n = sum(1 for t in tickets if t.fixable)
    if not tickets:
        warnings.append("Нет строк после сверки.")
    else:
        st_label = ",".join(sorted(wanted, key=lambda x: int(x) if x.isdigit() else 99)) if wanted else "—"
        warnings.insert(0, f"Талонов: {len(tickets)}, расхождений: {mismatch_n}, к исправлению (статусы {st_label}): {fix_n}.")
        not_in_file = sum(1 for t in tickets if not t.detail_lines)
        if not_in_file:
            warnings.append(
                f"У {not_in_file} талонов нет строк в файле услуг: колонка «Факт» = «нет в файле», "
                "«Недостаёт» = весь набор матрицы. Это не дубль колонок — в выгрузке Web.ОМС нет этого номера талона."
            )
    return tickets, preview, warnings


def build_fix_export_zip(tickets: list[FixTicket], *, only_fixable: bool = True) -> tuple[bytes, str]:
    rows = [t for t in tickets if (t.fixable if only_fixable else (t.missing or t.extra))]
    if not rows:
        raise ValueError("Нет талонов для выгрузки (нужны расхождения в выбранных статусах).")

    editions = list(MatrixEdition.objects.exclude(status=MatrixEdition.Status.ARCHIVED))
    cache_by_id: dict[int, tuple[MatrixPickCache, ServiceCodeEquivalence]] = {}

    def equiv_for(end_ui: str) -> ServiceCodeEquivalence:
        on = parse_as_date(end_ui) or date.today()
        ed = resolve_edition_for_date(editions, on)
        if not ed:
            return ServiceCodeEquivalence()
        packed = cache_by_id.get(ed.id)
        if packed:
            return packed[1]
        cache = build_matrix_pick_cache(ed)
        equiv = ServiceCodeEquivalence([(s.id, s.code, s.title) for s in ed.services.all().only("id", "code", "title")])
        cache_by_id[ed.id] = (cache, equiv)
        return equiv

    headers: list[dict[str, str]] = []
    services: list[dict[str, str]] = []
    for item in rows:
        oms = str(item.ticket or "").strip()
        if not oms:
            continue
        doctor_id = extract_doctor_id(item.doctor) or item.doctor
        start = item.start_ui
        end = item.end_ui or start
        cat_code = ""
        cat_title = ""
        on = parse_as_date(item.end_ui)
        ed = resolve_edition_for_date(editions, on or date.today()) if on else None
        if ed:
            packed = cache_by_id.get(ed.id)
            cache = packed[0] if packed else build_matrix_pick_cache(ed)
            if packed is None:
                cache_by_id[ed.id] = (
                    cache,
                    ServiceCodeEquivalence(
                        [(s.id, s.code, s.title) for s in ed.services.all().only("id", "code", "title")]
                    ),
                )
            found = category_for_mkb_in_cache(cache, item.ds1)
            cat_code = (found[0] if found else "") or ""
            cat_title = (found[1] if found else "") or ""
        visits = "1"
        for exp in item.expected:
            if is_per_visit_service(str(exp.get("title") or "")):
                visits = str(exp.get("qty") or 1)
                break
        else:
            if item.header_extra.get("посещений в МО"):
                visits = item.header_extra["посещений в МО"]
        social, employment = codes_from_birth_year(parse_as_date(item.birth_ui))
        row = {
            "Талон": oms,
            "талон_омс": oms,
            "начало": start,
            "окончание": end,
            "ЕНП": item.enp,
            "врач": doctor_id,
            "Корпус": item.department,
            "Диагноз": item.ds1,
            "Диагноз 2": ", ".join(item.ds2_full),
            "Категория": cat_title,
            "напр дата": start,
            "посещений в МО": visits,
            "Соцстатус": social,
            "Вид занятости": employment,
        }
        for key, default in DEFAULT_HEADER_DEFAULTS.items():
            row.setdefault(key, default)
        for key, val in (item.header_extra or {}).items():
            if key == "посещений в МО":
                continue
            if val:
                row[key] = val
        if _is_oncology_row(specialty=item.specialty, category_code=cat_code, category_title=cat_title):
            row["Цель консил"] = "0"
            row["Повод"] = "3"
            row["дополнительное направление организация"] = row.get("напр орган") or "360025"
            row["дополнительное направление дата"] = start
            row["дополнительное направление вид"] = "Направление к онкологу"
        headers.append(row)

        equiv = equiv_for(item.end_ui)
        for exp in sorted(item.expected, key=lambda x: str(x.get("code") or "")):
            begin, finish, svc_doctor = _pick_service_dates(
                code=str(exp.get("code") or ""),
                title=str(exp.get("title") or ""),
                detail_lines=item.detail_lines,
                ticket_start=start,
                ticket_end=end,
                code_equiv=equiv,
            )
            services.append(
                {
                    "Талон": oms,
                    "Код услуги": str(exp.get("code") or ""),
                    "Дата начала": begin,
                    "Дата окончания": finish,
                    "Кол-во": str(exp.get("qty") or 1),
                    "Врач": extract_doctor_id(svc_doctor) or doctor_id,
                }
            )

    zip_bytes, stamp = render_talon_bundle_zip(headers=headers, services=services)
    return zip_bytes, stamp


def tickets_to_store(tickets: list[FixTicket]) -> list[dict[str, Any]]:
    out = []
    for t in tickets:
        out.append(
            {
                "ticket": t.ticket,
                "status": t.status,
                "enp": t.enp,
                "fio": t.fio,
                "ds1": t.ds1,
                "ds2": t.ds2,
                "ds2_full": t.ds2_full,
                "specialty": t.specialty,
                "doctor": t.doctor,
                "department": t.department,
                "start_ui": t.start_ui,
                "end_ui": t.end_ui,
                "actual": t.actual,
                "expected": t.expected,
                "missing": t.missing,
                "extra": t.extra,
                "fixable": t.fixable,
                "gender": t.gender,
                "messages": t.messages,
                "header_extra": t.header_extra,
                "birth_ui": t.birth_ui,
                "detail_lines": [
                    {"code": ln.code, "qty": ln.qty, "start": ln.start, "end": ln.end, "doctor": ln.doctor}
                    for ln in t.detail_lines
                ],
            }
        )
    return out


def tickets_from_store(rows: list[dict[str, Any]]) -> list[FixTicket]:
    items: list[FixTicket] = []
    for row in rows or []:
        items.append(
            FixTicket(
                ticket=str(row.get("ticket") or ""),
                status=str(row.get("status") or ""),
                enp=str(row.get("enp") or ""),
                fio=str(row.get("fio") or ""),
                ds1=str(row.get("ds1") or ""),
                ds2=list(row.get("ds2") or []),
                ds2_full=list(row.get("ds2_full") or []),
                specialty=str(row.get("specialty") or ""),
                doctor=str(row.get("doctor") or ""),
                department=str(row.get("department") or ""),
                start_ui=str(row.get("start_ui") or ""),
                end_ui=str(row.get("end_ui") or ""),
                actual=dict(row.get("actual") or {}),
                expected=list(row.get("expected") or []),
                missing=list(row.get("missing") or []),
                extra=list(row.get("extra") or []),
                fixable=bool(row.get("fixable")),
                gender=str(row.get("gender") or ""),
                messages=list(row.get("messages") or []),
                header_extra=dict(row.get("header_extra") or {}),
                birth_ui=str(row.get("birth_ui") or ""),
                detail_lines=[
                    DetailLine(
                        code=str(ln.get("code") or ""),
                        qty=int(ln.get("qty") or 1),
                        start=str(ln.get("start") or ""),
                        end=str(ln.get("end") or ""),
                        doctor=str(ln.get("doctor") or ""),
                    )
                    for ln in (row.get("detail_lines") or [])
                ],
            )
        )
    return items
