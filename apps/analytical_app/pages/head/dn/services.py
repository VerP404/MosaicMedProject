"""Сервисы отчётов head/dn на SQL (silver)."""
from __future__ import annotations

import io
from typing import Any

import pandas as pd

from apps.analytical_app.pages.head.dn.query import (
    STATUS_RU,
    sql_by_category,
    sql_dropped_diagnoses,
    sql_etl_status,
    sql_iszl_not_in_kvazar,
    sql_kvazar_not_in_iszl,
    sql_kvazar_stats,
    sql_line_summary,
    sql_missing_prior,
    sql_not_passed,
    sql_not_passed_grouped,
    sql_out_of_168n,
    sql_patient_card,
    sql_patient_meta,
    sql_patient_search,
)

# id колонки → русское имя для таблиц (если SQL ещё отдал eng-id)
COL_RU = {
    "enp": "ЕНП",
    "fio": "ФИО",
    "dr": "Дата рождения",
    "lpuuch": "Участок",
    "is_detached": "Откреплён",
    "ldwid": "ldwID (диагноз)",
    "pdwid": "pdwID (план)",
    "ds_code": "МКБ",
    "ds": "Диагноз",
    "ds_raw": "Диагноз (сырой)",
    "plan_month": "Месяц плана",
    "plan_year": "Год плана",
    "prior_year": "Год (предыдущий)",
    "doctor": "Врач",
    "category_168n": "Группа 168н",
    "profile_cluster": "Профиль",
    "out_of_168n": "Вне 168н",
    "status": "Статус",
    "suggested_goal": "Рекоменд. цель",
    "action": "Действие",
    "issue": "Расхождение",
    "iszl_diag_rows": "Диагнозов в ИСЗЛ",
    "completed": "С талоном (выполнено)",
    "not_passed": "Не прошедшие",
    "table_name": "Таблица",
    "start_time": "Начало",
    "end_time": "Окончание",
    "count_before": "Было строк",
    "count_after": "Стало строк",
    "duration": "Длительность, с",
    "error_occurred": "Ошибка",
    "main_category": "Группа основного",
    "main_profile": "Профиль",
    "main_mkb": "Основной МКБ",
    "main_plan_month": "Месяц плана",
    "main_doctor": "Врач",
    "main_ldwid": "ldwID основного",
    "accompanying": "Сопутствующие МКБ",
    "diag_count": "Всего диагнозов",
}

def _read(engine, sql: str) -> pd.DataFrame:
    try:
        return pd.read_sql(sql, con=engine)
    except Exception as e:
        return pd.DataFrame([{"Ошибка": str(e)}])


def localize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    out = df.copy()
    if "status" in out.columns:
        out["status"] = out["status"].map(lambda x: STATUS_RU.get(str(x), x))
    if "is_detached" in out.columns:
        out["is_detached"] = out["is_detached"].map(
            lambda x: "да" if x in (True, "True", "true", "t", 1, "1") else "нет"
        )
    if "out_of_168n" in out.columns:
        out["out_of_168n"] = out["out_of_168n"].map(
            lambda x: "да" if x in (True, "True", "true", "t", 1, "1") else "нет"
        )
    rename = {c: COL_RU[c] for c in out.columns if c in COL_RU}
    return out.rename(columns=rename)


def build_summary(engine, year: int) -> dict[str, Any]:
    s = _read(engine, sql_line_summary(year))
    row = s.iloc[0].to_dict() if not s.empty and "Ошибка" not in s.columns else {}
    by_cat = localize_df(_read(engine, sql_by_category(year)))
    plan = int(row.get("iszl_diag_rows") or 0)
    done = int(row.get("completed") or 0)
    return {
        "iszl_diag_rows": plan,
        "iszl_enp": int(row.get("iszl_enp") or 0),
        "completed_rows": done,
        "not_passed_rows": int(row.get("not_passed") or 0),
        "out_of_168n": int(row.get("out_of_168n") or 0),
        "pct_completed": round(100.0 * done / plan, 1) if plan else 0.0,
        "by_category": by_cat.to_dict("records") if not by_cat.empty else [],
    }


def build_not_passed(engine, year: int, category: str = "", profile: str = "") -> pd.DataFrame:
    return localize_df(_read(engine, sql_not_passed(year, category, profile, limit=5000)))


def build_not_passed_grouped(engine, year: int, category: str = "", profile: str = "") -> pd.DataFrame:
    return localize_df(_read(engine, sql_not_passed_grouped(year, category, profile)))


def build_out_of_168n(engine, year: int) -> pd.DataFrame:
    return localize_df(_read(engine, sql_out_of_168n(year)))


def build_missing_prior(engine, year: int) -> pd.DataFrame:
    return localize_df(_read(engine, sql_missing_prior(year)))


def build_dropped_diagnoses(engine, year: int) -> pd.DataFrame:
    return localize_df(_read(engine, sql_dropped_diagnoses(year)))


def build_etl_status(engine) -> pd.DataFrame:
    return localize_df(_read(engine, sql_etl_status()))


def search_patients(engine, q: str) -> pd.DataFrame:
    if not q or len(q.strip()) < 3:
        return pd.DataFrame()
    return localize_df(_read(engine, sql_patient_search(q)))


def patient_meta(engine, enp: str, year: int) -> dict[str, Any]:
    df = _read(engine, sql_patient_meta(enp, year))
    if df.empty or "Ошибка" in df.columns:
        return {}
    return df.iloc[0].to_dict()


def patient_card(engine, enp: str, year: int) -> pd.DataFrame:
    if not enp:
        return pd.DataFrame()
    return _read(engine, sql_patient_card(enp, year))


def build_kvazar_stats(engine, year: int) -> dict[str, Any]:
    df = _read(engine, sql_kvazar_stats(year))
    if df.empty or "Ошибка" in df.columns:
        return {}
    r = df.iloc[0].to_dict()
    iszl_p = int(r.get("iszl_pairs") or 0)
    kv_p = int(r.get("kvazar_pairs") or 0)
    both_p = int(r.get("both_pairs") or 0)
    iszl_e = int(r.get("iszl_enp") or 0)
    kv_e = int(r.get("kvazar_enp") or 0)
    both_e = int(r.get("both_enp") or 0)
    return {
        "iszl_pairs": iszl_p,
        "kvazar_pairs": kv_p,
        "both_pairs": both_p,
        "iszl_enp": iszl_e,
        "kvazar_enp": kv_e,
        "both_enp": both_e,
        "pct_iszl_in_kvazar": round(100.0 * both_p / iszl_p, 1) if iszl_p else 0.0,
        "pct_kvazar_in_iszl": round(100.0 * both_p / kv_p, 1) if kv_p else 0.0,
        "pct_enp_overlap_iszl": round(100.0 * both_e / iszl_e, 1) if iszl_e else 0.0,
        "pct_enp_overlap_kvazar": round(100.0 * both_e / kv_e, 1) if kv_e else 0.0,
    }


def build_kvazar_not_in_iszl(engine, year: int) -> pd.DataFrame:
    return localize_df(_read(engine, sql_kvazar_not_in_iszl(year)))


def build_iszl_not_in_kvazar(engine, year: int) -> pd.DataFrame:
    return localize_df(_read(engine, sql_iszl_not_in_kvazar(year)))


def dataframe_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            sheet = (name or "data")[:31]
            if df is None or df.empty:
                pd.DataFrame({"info": ["нет данных"]}).to_excel(writer, sheet_name=sheet, index=False)
            else:
                df.to_excel(writer, sheet_name=sheet, index=False)
    return buf.getvalue()
