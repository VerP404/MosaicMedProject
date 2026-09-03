# -*- coding: utf-8 -*-
"""Разбор талонов цели 307, периодичность и план ИСЗЛ."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Iterable

import pandas as pd

from apps.health_schools.services.catalog import active_catalog
from apps.health_schools.services.matching import (
    SchoolSpec,
    age_years,
    match_schools,
    primary_school,
)

VALID_307_STATUSES = {"1", "2", "3", "4", "6", "8", "19"}


def _parse_date(value: object) -> date | None:
    if value is None or value == "" or value == "-":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def _norm_enp(value: object) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _status_ok(status: object) -> bool:
    return str(status or "").strip() in VALID_307_STATUSES


def fetch_oms_307(year: int, *, lookback_years: int = 10) -> pd.DataFrame:
    from sqlalchemy import text

    from apps.analytical_app.query_executor import engine

    y = int(year)
    sql = text(
        """
        SELECT
            talon,
            enp,
            patient,
            birth_date,
            treatment_start,
            treatment_end,
            main_diagnosis_code,
            additional_diagnosis_codes,
            status,
            building,
            doctor,
            specialty,
            mo_visits,
            report_year
        FROM load_data_oms_data
        WHERE goal = '307'
          AND report_year BETWEEN :y_from AND :y
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"y": y, "y_from": y - int(lookback_years)})
    return df


def fetch_iszl_plan(year: int) -> pd.DataFrame:
    from sqlalchemy import text

    from apps.analytical_app.query_executor import engine

    y = int(year)
    sql = text(
        """
        SELECT
            regexp_replace(COALESCE(p.enp, ''), '\\D', '', 'g') AS enp,
            p.fio,
            p.dr,
            l.ds_code,
            l.plan_month,
            l.status,
            p.lpuuch
        FROM dn_app_dnline l
        JOIN dn_app_person p ON p.id = l.person_id
        WHERE l.plan_year = :y
          AND l.is_current = TRUE
          AND COALESCE(l.ds_code, '') <> ''
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"y": y})


def _spec_payload(spec: SchoolSpec | None) -> dict[str, Any]:
    if spec is None:
        return {
            "школа": "",
            "код_услуги": "",
            "явки": "",
            "тариф": "",
            "период_лет": "",
            "№_школы": "",
        }
    return {
        "школа": spec.name,
        "код_услуги": spec.service_code,
        "явки": spec.visits,
        "тариф": spec.tariff,
        "период_лет": spec.period_years,
        "№_школы": spec.number,
    }


def classify_talons(
    oms: pd.DataFrame,
    catalog: Iterable[SchoolSpec],
    year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    catalog_list = list(catalog)
    y = int(year)
    rows = []
    history: dict[tuple[str, int], list[dict]] = defaultdict(list)

    records = oms.fillna("").to_dict("records") if not oms.empty else []
    prepared = []
    for rec in records:
        enp = _norm_enp(rec.get("enp"))
        start = _parse_date(rec.get("treatment_start"))
        end = _parse_date(rec.get("treatment_end")) or start
        birth = _parse_date(rec.get("birth_date"))
        age = age_years(birth, start or date(y, 7, 1))
        main = str(rec.get("main_diagnosis_code") or "")
        extra = str(rec.get("additional_diagnosis_codes") or "")
        primary, hits = primary_school(main, [extra], catalog_list, age=age)
        item = {
            "raw": rec,
            "enp": enp,
            "start": start,
            "end": end,
            "age": age,
            "primary": primary,
            "hits": hits,
            "status_ok": _status_ok(rec.get("status")),
            "in_year": str(rec.get("report_year") or "") == str(y) or (start and start.year == y),
        }
        prepared.append(item)
        if item["status_ok"] and item["end"]:
            for spec in hits:
                history[(enp, spec.number)].append({"end": item["end"], "talon": rec.get("talon")})

    for key in history:
        history[key].sort(key=lambda x: x["end"])

    for item in prepared:
        if not item["in_year"]:
            continue
        rec = item["raw"]
        primary: SchoolSpec | None = item["primary"]
        payload = _spec_payload(primary)
        prev = None
        period_ok = ""
        last_date = ""
        years_ago = ""
        if primary and item["enp"] and item["start"]:
            past = [
                h
                for h in history.get((item["enp"], primary.number), [])
                if h["end"] < item["start"] and str(h["talon"]) != str(rec.get("talon"))
            ]
            if past:
                prev = past[-1]
                last_date = prev["end"].isoformat()
                delta = (item["start"] - prev["end"]).days / 365.25
                years_ago = round(delta, 2)
                period_ok = "да" if delta >= primary.period_years else "нет"
            else:
                period_ok = "первый курс"
        rows.append(
            {
                "Талон": rec.get("talon"),
                "ЕНП": item["enp"],
                "Пациент": rec.get("patient"),
                "Дата рождения": rec.get("birth_date"),
                "Возраст": item["age"] if item["age"] is not None else "",
                "Начало": rec.get("treatment_start"),
                "Окончание": rec.get("treatment_end"),
                "Статус": rec.get("status"),
                "Корпус": rec.get("building"),
                "Врач": rec.get("doctor"),
                "DS1": rec.get("main_diagnosis_code"),
                "DS2": rec.get("additional_diagnosis_codes"),
                **payload,
                "все_школы": "; ".join(h.name for h in item["hits"]),
                "периодичность_ок": period_ok,
                "предыдущий_курс": last_date,
                "лет_с_прошлого": years_ago,
            }
        )
    talons = pd.DataFrame(rows)
    too_soon = talons[talons["периодичность_ок"] == "нет"].copy() if not talons.empty else talons
    return talons, too_soon


def _iszl_schools(iszl: pd.DataFrame, catalog: list[SchoolSpec]) -> pd.DataFrame:
    rows = []
    if iszl is None or iszl.empty:
        return pd.DataFrame(rows)
    for rec in iszl.fillna("").to_dict("records"):
        enp = _norm_enp(rec.get("enp"))
        ds = str(rec.get("ds_code") or "")
        hits = match_schools([ds], catalog)
        if not hits:
            continue
        for spec in hits:
            rows.append(
                {
                    "ЕНП": enp,
                    "ФИО": rec.get("fio"),
                    "Дата рождения": rec.get("dr"),
                    "МКБ_ИСЗЛ": ds,
                    "месяц_плана": rec.get("plan_month"),
                    "статус_ИСЗЛ": rec.get("status"),
                    "участок": rec.get("lpuuch"),
                    **_spec_payload(spec),
                }
            )
    return pd.DataFrame(rows)


def annotate_iszl(talons: pd.DataFrame, iszl_schools: pd.DataFrame) -> pd.DataFrame:
    if talons.empty:
        return talons
    planned: dict[tuple[str, str], set[str]] = defaultdict(set)
    if iszl_schools is not None and not iszl_schools.empty:
        for rec in iszl_schools.to_dict("records"):
            planned[(str(rec.get("ЕНП") or ""), str(rec.get("школа") or ""))].add(str(rec.get("МКБ_ИСЗЛ") or ""))
    out = talons.copy()
    flags = []
    mkbs = []
    for rec in out.to_dict("records"):
        key = (str(rec.get("ЕНП") or ""), str(rec.get("школа") or ""))
        found = planned.get(key, set())
        flags.append("да" if found else "нет")
        mkbs.append(", ".join(sorted(x for x in found if x)))
    out["в_плане_ИСЗЛ"] = flags
    out["МКБ_в_плане"] = mkbs
    return out


def due_list(
    iszl_schools: pd.DataFrame,
    oms: pd.DataFrame,
    catalog: list[SchoolSpec],
    *,
    as_of: date,
) -> pd.DataFrame:
    """Пациенты с планом ИСЗЛ на школу и без курса 307 в пределах периодичности."""
    last_end: dict[tuple[str, int], date] = {}
    if oms is not None and not oms.empty:
        catalog_list = catalog
        for rec in oms.fillna("").to_dict("records"):
            if not _status_ok(rec.get("status")):
                continue
            enp = _norm_enp(rec.get("enp"))
            end = _parse_date(rec.get("treatment_end")) or _parse_date(rec.get("treatment_start"))
            if not enp or not end:
                continue
            birth = _parse_date(rec.get("birth_date"))
            age = age_years(birth, end)
            _, hits = primary_school(
                str(rec.get("main_diagnosis_code") or ""),
                [str(rec.get("additional_diagnosis_codes") or "")],
                catalog_list,
                age=age,
            )
            for spec in hits:
                key = (enp, spec.number)
                prev = last_end.get(key)
                if prev is None or end > prev:
                    last_end[key] = end

    if iszl_schools is None or iszl_schools.empty:
        return pd.DataFrame()

    rows = []
    seen = set()
    for rec in iszl_schools.to_dict("records"):
        enp = str(rec.get("ЕНП") or "")
        number = rec.get("№_школы")
        key = (enp, number)
        if key in seen:
            continue
        seen.add(key)
        try:
            period = int(rec.get("период_лет") or 3)
            num = int(number)
        except (TypeError, ValueError):
            continue
        last = last_end.get((enp, num))
        cutoff = as_of - timedelta(days=int(period * 365.25))
        if last and last > cutoff:
            continue
        rows.append(
            {
                "ЕНП": enp,
                "ФИО": rec.get("ФИО"),
                "Дата рождения": rec.get("Дата рождения"),
                "школа": rec.get("школа"),
                "№_школы": num,
                "код_услуги": rec.get("код_услуги"),
                "явки": rec.get("явки"),
                "период_лет": period,
                "МКБ_в_плане": rec.get("МКБ_ИСЗЛ"),
                "последний_307": last.isoformat() if last else "",
                "участок": rec.get("участок"),
            }
        )
    return pd.DataFrame(rows)


def summarize(talons: pd.DataFrame) -> pd.DataFrame:
    if talons is None or talons.empty:
        return pd.DataFrame()
    g = (
        talons.groupby(["школа", "код_услуги", "явки"], dropna=False)
        .agg(
            талонов=("Талон", "count"),
            в_плане=("в_плане_ИСЗЛ", lambda s: int((s == "да").sum()) if "в_плане_ИСЗЛ" in talons.columns else 0),
            рано=("периодичность_ок", lambda s: int((s == "нет").sum())),
        )
        .reset_index()
        .sort_values("талонов", ascending=False)
    )
    return g


def run_analysis(year: int, *, catalog: list[SchoolSpec] | None = None, as_of: date | None = None) -> dict[str, Any]:
    catalog_list = catalog if catalog is not None else active_catalog()
    lookback = max((s.period_years for s in catalog_list), default=3) + 1
    oms = fetch_oms_307(year, lookback_years=lookback)
    iszl = fetch_iszl_plan(year)
    talons, too_soon = classify_talons(oms, catalog_list, year)
    iszl_schools = _iszl_schools(iszl, catalog_list)
    talons = annotate_iszl(talons, iszl_schools)
    if not too_soon.empty and "в_плане_ИСЗЛ" in talons.columns:
        too_soon = talons[talons["периодичность_ок"] == "нет"].copy()
    due = due_list(iszl_schools, oms, catalog_list, as_of=as_of or date(int(year), 12, 31))
    catalog_df = pd.DataFrame(
        [
            {
                "№": s.number,
                "школа": s.name,
                "группа": s.group_name,
                "МКБ": s.mkb_rule,
                "явки": s.visits,
                "код_услуги": s.service_code,
                "период_лет": s.period_years,
                "критерий": s.criterion,
            }
            for s in catalog_list
        ]
    )
    no_school = talons[talons["школа"] == ""].copy() if not talons.empty else talons
    return {
        "year": year,
        "catalog": catalog_df,
        "summary": summarize(talons),
        "talons": talons,
        "too_soon": too_soon,
        "no_school": no_school,
        "iszl_schools": iszl_schools,
        "due": due,
        "counts": {
            "talons": 0 if talons is None or talons.empty else len(talons),
            "too_soon": 0 if too_soon is None or too_soon.empty else len(too_soon),
            "iszl": 0 if iszl_schools is None or iszl_schools.empty else int(iszl_schools[["ЕНП", "школа"]].drop_duplicates().shape[0]),
            "due": 0 if due is None or due.empty else len(due),
            "no_school": 0 if no_school is None or no_school.empty else len(no_school),
            "catalog": len(catalog_list),
        },
    }
