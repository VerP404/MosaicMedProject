"""
Сверка плана ИСЗЛ с журналом талонов и detail_services (логика как во вкладке «Анализ»).
"""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from typing import Any

from apps.dash_dn.detail_services_report import (
    _match_specialty_id,
    load_diagnosis_lookup_from_db,
    load_required_services_for_icd_codes_by_specialty,
    load_specialties_from_db,
    read_detail_csv_from_bytes,
)

ICD10_CODE_RE = re.compile(r"\b([A-Z]\d{2}(?:\.\d+)?)\b", re.IGNORECASE)
SVC_CODE_RE = re.compile(r"\b([AB]\d{2}\.\d{2,3}\.\d{3}(?:\.\d{3})?)\b", re.IGNORECASE)

_EQUIV_GROUPS: list[set[str]] = [
    {"B04.047.001", "B04.047.003"},
]
_EQUIV_MAP: dict[str, str] = {}
for _g in _EQUIV_GROUPS:
    _canon = sorted(_g)[0]
    for _x in _g:
        _EQUIV_MAP[_x] = _canon


def _norm_text(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\u00a0", " ").strip()


def norm_enp_digits(value) -> str:
    return re.sub(r"\D", "", _norm_text(value).replace("`", ""))


def normalize_diagnosis(value) -> str:
    s = _norm_text(value).upper()
    if not s or s == "-":
        return ""
    return s


def get_primary_code(diagnosis: str) -> str:
    if not diagnosis:
        return ""
    return diagnosis.split(".")[0].split()[0]


def extract_icd_code(value: str) -> str:
    m = ICD10_CODE_RE.search(_norm_text(value).upper())
    return m.group(1).upper() if m else ""


def is_diagnosis_closed(iszl_diag: str, oms_diagnoses: set[str]) -> bool:
    """Закрыт ли диагноз плана: точное совпадение или по основному коду (как analyze_iszl.py)."""
    iszl_norm = normalize_diagnosis(iszl_diag)
    if not iszl_norm:
        return False
    if iszl_norm in oms_diagnoses:
        return True
    iszl_primary = get_primary_code(iszl_norm)
    if not iszl_primary:
        return False
    for oms_diag in oms_diagnoses:
        if not oms_diag:
            continue
        oms_primary = get_primary_code(oms_diag)
        if oms_primary == iszl_primary:
            return True
        if oms_diag.startswith(iszl_primary):
            return True
    return False


def category_label(code: str, dx_lookup: dict[str, str | None]) -> str:
    if not code:
        return ""
    u = code.upper()
    if u not in dx_lookup:
        return "нет в справочнике (dn_diagnosis)"
    cat = dx_lookup.get(u)
    return cat if cat else "(без категории в справочнике)"


def _svc_base(code: str) -> str:
    m = re.match(r"^([AB]\d{2}\.\d{2,3}\.\d{3})", str(code or "").upper())
    return m.group(1) if m else str(code or "").upper()


def _canon_svc(code_base: str) -> str:
    b = _svc_base(code_base)
    return _EQUIV_MAP.get(b, b)


def _find_column(headers: list[str], *needles: str) -> str | None:
    hl = {h: str(h).lower() for h in headers}
    for h in headers:
        s = hl.get(h, "")
        if all(n in s for n in needles):
            return h
    return None


def read_semicolon_csv(raw: bytes) -> list[dict[str, str]]:
    for enc in ("utf-8-sig", "cp1251", "windows-1251", "latin1"):
        try:
            text = raw.decode(enc)
            if enc == "utf-8-sig" and "\ufffd" in text:
                continue
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin1", errors="replace")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    return [dict(r) for r in reader]


def filter_iszl_rows(
    rows: list[dict[str, str]],
    target_year: int,
    only_active: bool,
) -> list[dict[str, str]]:
    if not rows:
        return []
    has_year = "PlanYear" in rows[0]
    has_date_end = "DateEnd" in rows[0]
    out: list[dict[str, str]] = []
    for row in rows:
        enp = norm_enp_digits(row.get("ENP"))
        if not enp:
            continue
        ds = _norm_text(row.get("DS"))
        if not ds:
            continue
        if has_year:
            try:
                year = int(float(_norm_text(row.get("PlanYear"))))
            except ValueError:
                continue
            if year != target_year:
                continue
        if only_active and has_date_end:
            v = _norm_text(row.get("DateEnd")).lower()
            if v and v not in {"-", "—", "none", "nan", "null"}:
                continue
        out.append(row)
    return out


def aggregate_iszl_patients(filtered_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    """ENP (digits) -> метаданные пациента и список диагнозов из плана."""
    patients: dict[str, dict[str, Any]] = {}
    for row in filtered_rows:
        enp = norm_enp_digits(row.get("ENP"))
        if not enp:
            continue
        if enp not in patients:
            patients[enp] = {
                "enp": enp,
                "fio": _norm_text(row.get("FIO")),
                "dr": _norm_text(row.get("DR")),
                "lpuuch": _norm_text(row.get("LPUUCH")),
                "adr": _norm_text(row.get("ADR")),
                "fio_doctor": _norm_text(row.get("FIO_DOCTOR")),
                "ss_doctor": _norm_text(row.get("SS_DOCTOR")).lstrip("`"),
                "diagnoses": [],
                "diagnosis_codes": set(),
            }
        p = patients[enp]
        if not p["fio"]:
            p["fio"] = _norm_text(row.get("FIO"))
        if not p["dr"]:
            p["dr"] = _norm_text(row.get("DR"))
        if not p["lpuuch"]:
            p["lpuuch"] = _norm_text(row.get("LPUUCH"))
        if not p["adr"]:
            p["adr"] = _norm_text(row.get("ADR"))
        if not p["fio_doctor"]:
            p["fio_doctor"] = _norm_text(row.get("FIO_DOCTOR"))
        if not p["ss_doctor"]:
            p["ss_doctor"] = _norm_text(row.get("SS_DOCTOR")).lstrip("`")
        ds = _norm_text(row.get("DS"))
        if ds and ds not in p["diagnoses"]:
            p["diagnoses"].append(ds)
            for code in ICD10_CODE_RE.findall(ds.upper()):
                p["diagnosis_codes"].add(code.upper())
    return patients


def _services_by_talon_from_detail(detail_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    svc_by_tal: dict[str, list[str]] = defaultdict(list)
    for dr in detail_rows:
        tal = _norm_text(dr.get("Талон"))
        code = _norm_text(dr.get("Код услуги"))
        if not tal:
            continue
        m = SVC_CODE_RE.search(code)
        if not m:
            continue
        c = m.group(1).upper()
        if c not in svc_by_tal[tal]:
            svc_by_tal[tal].append(c)
    return dict(svc_by_tal)


def _enp_to_talons(detail_rows: list[dict[str, str]], journal_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    """ЕНП (digits) -> список номеров талонов."""
    enp_talons: dict[str, set[str]] = defaultdict(set)

    if detail_rows:
        col_enp = _find_column(list(detail_rows[0].keys()), "енп") or "ЕНП"
        col_tal = "Талон" if "Талон" in detail_rows[0] else _find_column(list(detail_rows[0].keys()), "талон")
        for dr in detail_rows:
            enp = norm_enp_digits(dr.get(col_enp or "ЕНП"))
            tal = _norm_text(dr.get(col_tal or "Талон"))
            if enp and tal:
                enp_talons[enp].add(tal)

    if journal_rows:
        headers = list(journal_rows[0].keys())
        col_tal = _find_column(headers, "талон") or _find_column(headers, "talon") or headers[0]
        col_enp = _find_column(headers, "енп") or _find_column(headers, "enp")
        for jr in journal_rows:
            tal = _norm_text(jr.get(col_tal or ""))
            if not tal:
                continue
            if col_enp:
                enp = norm_enp_digits(jr.get(col_enp))
                if enp:
                    enp_talons[enp].add(tal)
    return {k: sorted(v) for k, v in enp_talons.items()}


def reconcile_journal_rows(
    journal_rows: list[dict[str, str]],
    detail_rows: list[dict[str, str]] | None,
    *,
    catalog: str,
) -> dict[str, dict[str, Any]]:
    """
    Номер талона -> результат сверки (статус ok/error/n/a, группа, услуги и т.д.).
    Логика совпадает с run_journal_analyze во вкладке «Анализ».
    """
    if not journal_rows:
        return {}

    headers = list(journal_rows[0].keys())
    col_tal = _find_column(headers, "талон") or _find_column(headers, "talon") or headers[0]
    col_diag = _find_column(headers, "диагноз") or _find_column(headers, "ds1")
    col_spec = _find_column(headers, "спец") or _find_column(headers, "special")
    col_pos = _find_column(headers, "долж") or _find_column(headers, "post") or _find_column(headers, "position")

    svc_by_tal = _services_by_talon_from_detail(detail_rows or [])
    has_detail = bool(detail_rows)
    dx_lookup = load_diagnosis_lookup_from_db(catalog)
    spec_items = load_specialties_from_db(catalog=catalog)

    def _norm_spec_text(s: str) -> str:
        t = str(s or "").strip().lower().replace("ё", "е")
        t = re.sub(r"[^0-9a-zа-я]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t.replace("врач ", "").replace("врач", "").strip()

    def _match_sid(spec_text: str, pos_text: str) -> int | None:
        src = " ".join([_norm_spec_text(spec_text), _norm_spec_text(pos_text)]).strip()
        if not src:
            return None
        src_tokens = set(src.split())
        best: tuple[float, int] | None = None
        for sid, name in spec_items:
            n = _norm_spec_text(name)
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

    pairs: set[tuple[str, int]] = set()
    for r in journal_rows:
        d = extract_icd_code(r.get(col_diag, "") if col_diag else "")
        sid = _match_sid(
            r.get(col_spec, "") if col_spec else "",
            r.get(col_pos, "") if col_pos else "",
        )
        if d and sid:
            pairs.add((d, sid))

    exp_map: dict[tuple[str, int], list[str]] = {}
    if pairs:
        diag_codes = {d for d, _ in pairs}
        spec_ids = {sid for _, sid in pairs}
        req = load_required_services_for_icd_codes_by_specialty(diag_codes, spec_ids, catalog=catalog)
        for (dcode, sid), items in (req or {}).items():
            codes: list[str] = []
            seen: set[str] = set()
            for sc, _nm in items or []:
                base = _svc_base(sc)
                if base and base not in seen:
                    seen.add(base)
                    codes.append(base)
            exp_map[(str(dcode).upper(), int(sid))] = codes

    out: dict[str, dict[str, Any]] = {}
    for r in journal_rows:
        tal = _norm_text(r.get(col_tal))
        if not tal:
            continue
        diag_raw = _norm_text(r.get(col_diag, "") if col_diag else "")
        dcode = extract_icd_code(diag_raw)
        grp = category_label(dcode, dx_lookup) if dcode else ""
        have = svc_by_tal.get(tal, [])
        sid = _match_sid(
            r.get(col_spec, "") if col_spec else "",
            r.get(col_pos, "") if col_pos else "",
        )
        need = exp_map.get((dcode, int(sid))) if (dcode and sid) else []

        if not has_detail:
            status = "n/a"
            missing: list[str] = []
            need_str = ""
        elif need:
            have_b = {_canon_svc(x) for x in have if x}
            need_b = {_canon_svc(x) for x in need if x}
            missing = sorted(x for x in need_b if x not in have_b)
            status = "ok" if not missing else "error"
            need_str = "; ".join(sorted(need_b)) if missing else ""
        else:
            missing = []
            status = "n/a"
            need_str = ""

        out[tal] = {
            "talon": tal,
            "diagnosis_raw": diag_raw,
            "diagnosis_code": dcode,
            "group": grp,
            "status": status,
            "services_in_card": "; ".join(have),
            "required_services": need_str,
            "missing": "; ".join(missing) if missing else "",
            "specialty_id": sid,
        }
    return out


def _pick_primary_diagnosis(
    patient: dict[str, Any],
    talon_results: list[dict[str, Any]],
    oms_diagnoses: set[str],
    dx_lookup: dict[str, str | None],
) -> tuple[str, str, str]:
    """
    (основной диагноз текст, код МКБ, группа).
    Приоритет: DS1 из успешного талона, иначе первый талон, иначе первый незакрытый из ИСЗЛ.
    """
    ok_talons = [t for t in talon_results if t.get("status") == "ok"]
    for bucket in (ok_talons, talon_results):
        for t in bucket:
            if t.get("diagnosis_code"):
                code = str(t["diagnosis_code"])
                return t.get("diagnosis_raw") or code, code, t.get("group") or category_label(code, dx_lookup)
        for t in bucket:
            if t.get("diagnosis_raw"):
                code = extract_icd_code(t["diagnosis_raw"])
                return t["diagnosis_raw"], code, t.get("group") or category_label(code, dx_lookup)

    for ds in patient.get("diagnoses") or []:
        if not is_diagnosis_closed(ds, oms_diagnoses):
            code = extract_icd_code(ds) or get_primary_code(normalize_diagnosis(ds))
            return ds, code, category_label(code, dx_lookup) if code else ""
    if patient.get("diagnoses"):
        ds = patient["diagnoses"][0]
        code = extract_icd_code(ds) or get_primary_code(normalize_diagnosis(ds))
        return ds, code, category_label(code, dx_lookup) if code else ""
    return "", "", ""


def build_not_passed_report(
    iszl_rows: list[dict[str, str]],
    journal_rows: list[dict[str, str]] | None,
    detail_rows: list[dict[str, str]] | None,
    target_year: int,
    only_active: bool,
    *,
    catalog: str,
) -> dict[str, Any]:
    filtered = filter_iszl_rows(iszl_rows, target_year, only_active)
    if not filtered:
        raise ValueError("После фильтрации ИСЗЛ не осталось строк для сверки.")

    patients = aggregate_iszl_patients(filtered)
    journal_rows = journal_rows or []
    detail_rows = detail_rows or []

    talon_recon = reconcile_journal_rows(journal_rows, detail_rows, catalog=catalog)
    enp_talons = _enp_to_talons(detail_rows, journal_rows)
    dx_lookup = load_diagnosis_lookup_from_db(catalog)

    not_passed: list[dict[str, Any]] = []
    passed_count = 0

    for enp, patient in sorted(patients.items(), key=lambda x: (x[1].get("lpuuch") or "", x[1].get("fio") or "")):
        talons = enp_talons.get(enp, [])
        talon_results = [talon_recon[t] for t in talons if t in talon_recon]

        oms_diagnoses: set[str] = set()
        for t in talon_results:
            if t.get("diagnosis_code"):
                oms_diagnoses.add(str(t["diagnosis_code"]).upper())
            raw = t.get("diagnosis_raw") or ""
            if raw:
                oms_diagnoses.add(normalize_diagnosis(raw))

        unclosed = [d for d in patient["diagnoses"] if not is_diagnosis_closed(d, oms_diagnoses)]
        has_ok_talon = any(t.get("status") == "ok" for t in talon_results)
        has_error_only = bool(talons and talon_results and not has_ok_talon and any(
            t.get("status") == "error" for t in talon_results
        ))
        has_detail = bool(detail_rows)
        diagnosis_closed = (
            len(unclosed) < len(patient["diagnoses"]) if patient["diagnoses"] else False
        )

        if not talons:
            passed = False
            reason = "Нет талона"
        elif has_detail:
            if not has_ok_talon:
                passed = False
                reason = (
                    "Талон(ы) не прошли сверку услуг"
                    if has_error_only
                    else "Нет талона с успешной сверкой услуг"
                )
            elif not diagnosis_closed:
                passed = False
                reason = "Сверка услуг OK, но диагноз плана не закрыт"
            else:
                passed = True
                reason = ""
        elif not diagnosis_closed:
            passed = False
            reason = "Талон есть, диагноз плана не закрыт"
        else:
            passed = True
            reason = ""

        if passed:
            passed_count += 1
            continue

        primary_text, primary_code, primary_group = _pick_primary_diagnosis(
            patient, talon_results, oms_diagnoses, dx_lookup
        )

        talon_lines = []
        for t in talon_results:
            talon_lines.append(
                f"{t.get('talon')}: {t.get('status')} "
                f"({t.get('diagnosis_code') or '—'}; missing: {t.get('missing') or '—'})"
            )

        not_passed.append(
            {
                "enp": enp,
                "fio": patient.get("fio") or "",
                "dr": patient.get("dr") or "",
                "lpuuch": patient.get("lpuuch") or "",
                "adr": patient.get("adr") or "",
                "fio_doctor": patient.get("fio_doctor") or "",
                "ss_doctor": patient.get("ss_doctor") or "",
                "iszl_diagnoses": "; ".join(patient.get("diagnoses") or []),
                "unclosed_diagnoses": "; ".join(unclosed),
                "primary_diagnosis": primary_text,
                "primary_code": primary_code,
                "diagnosis_group": primary_group,
                "talons": ", ".join(talons),
                "talon_details": " | ".join(talon_lines),
                "reason": reason,
                "status": "Не прошёл",
            }
        )

    return {
        "total_patients": len(patients),
        "passed_count": passed_count,
        "not_passed_count": len(not_passed),
        "not_passed_rows": not_passed,
        "has_journal": bool(journal_rows),
        "has_detail": bool(detail_rows),
    }
