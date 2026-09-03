"""Посетившие поликлинику (журнал обращений) → строки простановки ДН."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

from apps.dn_matrix.services.batch_pick import parse_mkb_list
from apps.dn_matrix.services.matrix import normalize_mkb
from apps.dn_matrix.services.talon_bundle import TalonBundleItem, extract_doctor_id, norm_enp

JOURNAL_VISIT_OFFSET_WORKDAYS = 5


def _as_date(val: object) -> date | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    text = str(val)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _goal3_covers_group(
    existing: list[dict[str, str]],
    *,
    category: str,
    ds1: str,
) -> bool:
    """Пропуск, если по этой группе 168н уже есть цель 3. Сопутствующие МКБ не считаем группой."""
    cat = (category or "").strip().casefold()
    ds1_n = normalize_mkb(ds1)
    for row in existing:
        row_cat = (row.get("category_168n") or "").strip().casefold()
        if cat and row_cat and row_cat == cat:
            return True
        mkb = normalize_mkb(row.get("mkb") or "")
        if not cat and mkb and mkb == ds1_n:
            return True
    return False


def _resolve_doctor(
    last_name: str,
    first_name: str,
    codes: dict[tuple[str, str], str],
    default_doctor: str,
) -> str:
    last = (last_name or "").strip().lower()
    first = (first_name or "").strip().lower()
    if last and first and (last, first) in codes:
        return codes[(last, first)]
    if last and first:
        for (ln, fn), code in codes.items():
            if ln == last and fn.startswith(first[:1]) and first[:1]:
                return code
    return extract_doctor_id(default_doctor) or (default_doctor or "").strip()


def items_from_clinic_visitors(
    visits: list[dict[str, Any]],
    not_passed_rows: list[dict[str, Any]],
    *,
    blocked_by_enp: dict[str, set[date]],
    existing_goal3: dict[str, list[dict[str, str]]],
    doctor_codes: dict[tuple[str, str], str],
    default_doctor: str = "",
    default_corpus: str = "",
) -> tuple[list[TalonBundleItem], list[dict[str, Any]], list[str]]:
    """
    Один талон на пациента+профиль ДН.
    Якорь — первая дата приёма в журнале за выбранный период.
    Пропуск, если по группе 168н уже есть талон цели 3 в рабочих статусах.
    """
    warnings: list[str] = []
    preview: list[dict[str, Any]] = []
    items: list[TalonBundleItem] = []

    by_enp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in visits or []:
        enp = norm_enp(raw.get("enp_norm") or raw.get("enp"))
        visit_date = _as_date(raw.get("visit_date"))
        if not enp or not visit_date:
            continue
        by_enp[enp].append(raw)

    np_by_enp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in not_passed_rows or []:
        enp = norm_enp(row.get("ЕНП") or row.get("enp"))
        if enp:
            np_by_enp[enp].append(row)

    for enp, rows in by_enp.items():
        rows_sorted = sorted(rows, key=lambda r: _as_date(r.get("visit_date")) or date.max)
        first = rows_sorted[0]
        visit_date = _as_date(first.get("visit_date"))
        if not visit_date:
            continue
        doctor_id = _resolve_doctor(
            str(first.get("employee_last_name") or ""),
            str(first.get("employee_first_name") or ""),
            doctor_codes,
            default_doctor,
        )
        journal_number = str(first.get("journal_number") or "").strip()
        fio = str(first.get("fio") or "").strip()
        department = str(first.get("department") or "").strip()
        np_rows = np_by_enp.get(enp) or []
        if not np_rows:
            preview.append(
                {
                    "Дата приёма": visit_date.isoformat(),
                    "ЕНП": enp,
                    "ФИО": fio,
                    "Подразделение": department,
                    "Номер": journal_number,
                    "Группа 168н": "",
                    "Основной МКБ": "",
                    "Профиль": "",
                    "Статус": "нет непройденного ДН",
                }
            )
            continue

        blocked = set(blocked_by_enp.get(enp) or ())
        blocked.add(visit_date)
        existing = existing_goal3.get(enp) or []

        for np_row in np_rows:
            ds1 = normalize_mkb(np_row.get("Основной МКБ") or np_row.get("main_mkb") or "")
            ds2 = parse_mkb_list(np_row.get("Сопутствующие МКБ") or np_row.get("accompanying") or "")
            category = str(np_row.get("Группа основного") or np_row.get("main_category") or "").strip()
            profile = str(np_row.get("Профиль") or np_row.get("main_profile") or "").strip()
            if not ds1:
                continue
            if _goal3_covers_group(existing, category=category, ds1=ds1):
                preview.append(
                    {
                        "Дата приёма": visit_date.isoformat(),
                        "ЕНП": enp,
                        "ФИО": fio,
                        "Подразделение": department,
                        "Номер": journal_number,
                        "Группа 168н": category,
                        "Основной МКБ": ds1,
                        "Профиль": profile,
                        "Статус": "уже есть цель 3 по группе",
                    }
                )
                continue
            birth_raw = np_row.get("Дата рождения") or np_row.get("dr") or first.get("birth_date")
            birth = _as_date(birth_raw)
            items.append(
                TalonBundleItem(
                    enp=enp,
                    ds1=ds1,
                    ds2_list=ds2,
                    specialty=profile,
                    doctor_id=doctor_id,
                    corpus=default_corpus,
                    category_168n=category,
                    birth_date=birth,
                    journal_visit_date=visit_date,
                    blocked_dates=tuple(sorted(blocked)),
                )
            )
            preview.append(
                {
                    "Дата приёма": visit_date.isoformat(),
                    "ЕНП": enp,
                    "ФИО": fio,
                    "Подразделение": department,
                    "Номер": journal_number,
                    "Группа 168н": category,
                    "Основной МКБ": ds1,
                    "Профиль": profile,
                    "Статус": "в пакет",
                }
            )

    if not by_enp:
        warnings.append("В журнале обращений нет явок за выбранные даты и подразделения.")
    elif not items:
        warnings.append("Нет строк для пакета: все посетившие уже с целью 3 или без непройденного ДН.")
    return items, preview, warnings


def fetch_clinic_visitors(
    engine,
    *,
    year: int,
    date_from: date,
    date_to: date,
    departments: list[str] | None,
    default_doctor: str = "",
    default_corpus: str = "",
    category: str = "",
    profile: str = "",
) -> tuple[list[TalonBundleItem], list[dict[str, Any]], list[str]]:
    import pandas as pd

    from apps.analytical_app.pages.head.dn.query import (
        sql_doctor_codes_by_name,
        sql_goal3_active_by_group,
        sql_journal_blocked_dates,
        sql_journal_visits_in_period,
        sql_not_passed_grouped,
    )
    from apps.analytical_app.pages.head.dn.services import localize_df

    visits_df = pd.read_sql(sql_journal_visits_in_period(date_from, date_to, departments), con=engine)
    visits = visits_df.to_dict("records") if visits_df is not None and not visits_df.empty else []
    if not visits:
        return [], [], ["В журнале обращений нет явок за выбранные даты и подразделения."]
    enps = [norm_enp(r.get("enp_norm") or r.get("enp")) for r in visits]
    enps = [e for e in enps if e]
    if not enps:
        return [], [], ["В журнале обращений нет ЕНП у посетивших."]

    np_df = localize_df(pd.read_sql(sql_not_passed_grouped(year, category or "", profile or "", enps or None), con=engine))
    if np_df is not None and not np_df.empty and "Ошибка" in np_df.columns:
        return [], [], [str(np_df.iloc[0].get("Ошибка") or "ошибка непрошедших")]
    not_passed = np_df.to_dict("records") if np_df is not None and not np_df.empty else []

    blocked_by_enp: dict[str, set[date]] = defaultdict(set)
    if enps:
        blocked_df = pd.read_sql(sql_journal_blocked_dates(enps, date_from, date_to), con=engine)
        for row in blocked_df.to_dict("records") if blocked_df is not None and not blocked_df.empty else []:
            enp = norm_enp(row.get("enp_norm"))
            d = _as_date(row.get("visit_date"))
            if enp and d:
                blocked_by_enp[enp].add(d)

    existing_goal3: dict[str, list[dict[str, str]]] = defaultdict(list)
    if enps:
        g3 = pd.read_sql(sql_goal3_active_by_group(year, enps), con=engine)
        for row in g3.to_dict("records") if g3 is not None and not g3.empty else []:
            enp = norm_enp(row.get("enp_norm"))
            if not enp:
                continue
            existing_goal3[enp].append(
                {
                    "mkb": str(row.get("mkb") or ""),
                    "category_168n": str(row.get("category_168n") or ""),
                }
            )

    codes: dict[tuple[str, str], str] = {}
    try:
        doc_df = pd.read_sql(sql_doctor_codes_by_name(), con=engine)
        for row in doc_df.to_dict("records") if doc_df is not None and not doc_df.empty else []:
            last = str(row.get("last_name") or "").strip().lower()
            first = str(row.get("first_name") or "").strip().lower()
            code = str(row.get("doctor_code") or "").strip()
            if last and code:
                codes[(last, first)] = code
    except Exception:
        codes = {}

    return items_from_clinic_visitors(
        visits,
        not_passed,
        blocked_by_enp=blocked_by_enp,
        existing_goal3=existing_goal3,
        doctor_codes=codes,
        default_doctor=default_doctor,
        default_corpus=default_corpus,
    )
