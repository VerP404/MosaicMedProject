from __future__ import annotations

from collections import defaultdict
from typing import Any

from apps.analytical_app.components.filters import status_groups


MONTH_MAP = {
    1: "янв", 2: "февр", 3: "мар", 4: "апр",
    5: "май", 6: "июн", 7: "июл", 8: "авг",
    9: "сент", 10: "окт", 11: "ноя", 12: "дек",
}

REPORT_COL_MAP = {
    "enp": "ЕНП", "patient": "Пациент", "birth_date": "ДР",
    "talon": "ОМС: Талон", "report_period": "ОМС: Период",
    "place_service": "ОМС: Место", "status": "ОМС: Статус",
    "treatment_end": "ОМС: Дата", "doctor": "ОМС: Врач",
    "doctor_profile": "ОМС: Профиль", "ds1": "ОМС: ds1",
    "ds2": "ОМС: ds2", "external_id": "ИСЗЛ: Номер",
    "mo_prikreplenia": "ИСЗЛ: Прикрепление",
    "org_prof_m": "ИСЗЛ: Организация", "ds_norm": "ИСЗЛ: Диагноз",
    "disp_date": "ИСЗЛ: Дата", "month_d": "ИСЗЛ: Месяц",
    "year_d": "ИСЗЛ: Год", "duplicate": "Проверка дубликата",
}


def normalize_ds2(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v]
    text = str(value).strip()
    if not text or text == "-":
        return []
    if ", " in text:
        return [part.strip() for part in text.split(", ") if part.strip()]
    return [text]


def ds2_display(ds2_list: list[str]) -> str:
    return ", ".join(ds2_list)


def diagnoses_match(ds_norm: str | None, ds1: str | None, ds2_list: list[str]) -> bool:
    if not ds_norm:
        return False
    if ds1 and ds_norm == ds1:
        return True
    return ds_norm in ds2_list


def period_match(tal: dict, disp: dict) -> bool:
    return (
        tal.get("month_end") == disp.get("month_d")
        and tal.get("year_end") == disp.get("year_d")
    )


def _serialize_record(record: dict) -> dict:
    out = dict(record)
    if "ds2" in out:
        out["ds2"] = normalize_ds2(out["ds2"])
    return out


def _format_patient_name(name: str | None) -> str | None:
    if not name:
        return name
    return name.strip().title()


def _decorate_flags(disp: list[dict], tal: list[dict]) -> tuple[list[dict], list[dict]]:
    disp_out = [dict(d, has_tal=False, _match_place_service=None) for d in disp]
    tal_out = [dict(t, has_disp=False) for t in tal]

    for t in tal_out:
        ds2_list = normalize_ds2(t.get("ds2"))
        for d in disp_out:
            if d.get("duplicate"):
                continue
            if period_match(t, d) and diagnoses_match(d.get("ds_norm"), t.get("ds1"), ds2_list):
                t["has_disp"] = True
                break

    for d in disp_out:
        if d.get("duplicate"):
            continue
        for t in tal_out:
            ds2_list = normalize_ds2(t.get("ds2"))
            if period_match(t, d) and diagnoses_match(d.get("ds_norm"), t.get("ds1"), ds2_list):
                d["has_tal"] = True
                d["_match_place_service"] = t.get("place_service")
                break

    for d in disp_out:
        place = d.get("_match_place_service")
        if place == "-":
            d["has_tal"] = "🔵"
        else:
            d["has_tal"] = "🟢" if d.get("has_tal") else "🔴"
        d["duplicate"] = "🔴" if d.get("duplicate") else "🟢"
        d.pop("_match_place_service", None)

    for t in tal_out:
        t["ds2"] = ds2_display(normalize_ds2(t.get("ds2")))
        if t.get("place_service") == "-":
            t["has_disp"] = "🔵"
        else:
            t["has_disp"] = "🟢" if t.get("has_disp") else "🔴"

    return disp_out, tal_out


def build_store_payload(disp_rows: list[dict], tal_rows: list[dict]) -> dict:
    disp_by_enp: dict[str, list[dict]] = defaultdict(list)
    tal_by_enp: dict[str, list[dict]] = defaultdict(list)

    for row in disp_rows:
        disp_by_enp[row["enp"]].append(_serialize_record(row))

    seen_talons: dict[str, set[str]] = defaultdict(set)
    for row in tal_rows:
        enp = row["enp"]
        talon = row.get("talon")
        if talon and talon in seen_talons[enp]:
            continue
        if talon:
            seen_talons[enp].add(talon)
        tal_by_enp[enp].append(_serialize_record(row))

    patients: dict[str, dict] = {}
    flat_rows: list[dict] = []
    all_enps = set(disp_by_enp) | set(tal_by_enp)

    for enp in all_enps:
        disp_list = disp_by_enp.get(enp, [])
        tal_list = tal_by_enp.get(enp, [])
        disp_ui, tal_ui = _decorate_flags(disp_list, tal_list)

        patient_name = None
        birth_date = None
        for t in tal_list:
            if t.get("patient"):
                patient_name = _format_patient_name(t["patient"])
                birth_date = t.get("birth_date")
                break
        if not patient_name and disp_list:
            patient_name = _format_patient_name(disp_list[0].get("fio_norm"))
            birth_date = disp_list[0].get("dr_norm")

        patients[enp] = {
            "enp": enp,
            "patient": patient_name,
            "birth_date": birth_date,
            "disp": disp_ui,
            "tal": tal_ui,
            "org_prof_m": [d.get("org_prof_m") for d in disp_list if d.get("org_prof_m")],
            "statuses": [t.get("status") for t in tal_list if t.get("status")],
        }

        matched_disp_ids: set[str] = set()
        matched_talons: set[str] = set()

        for t in tal_list:
            ds2_list = normalize_ds2(t.get("ds2"))
            row_matched = False
            for d in disp_list:
                if period_match(t, d) and diagnoses_match(d.get("ds_norm"), t.get("ds1"), ds2_list):
                    flat_rows.append(_flat_join_row(enp, patient_name, birth_date, d, t))
                    matched_disp_ids.add(d.get("external_id"))
                    matched_talons.add(t.get("talon"))
                    row_matched = True
            if not row_matched:
                flat_rows.append(_flat_join_row(enp, patient_name, birth_date, None, t))
                matched_talons.add(t.get("talon"))

        for d in disp_list:
            if d.get("external_id") not in matched_disp_ids:
                flat_rows.append(_flat_join_row(enp, patient_name, birth_date, d, None))

    return {"patients": patients, "flat": flat_rows}


def _flat_join_row(enp, patient, birth_date, disp: dict | None, tal: dict | None) -> dict:
    row = {
        "enp": enp,
        "patient": patient,
        "birth_date": birth_date,
        "talon": None,
        "report_period": None,
        "place_service": None,
        "status": None,
        "treatment_end": None,
        "month_end": None,
        "year_end": None,
        "doctor": None,
        "doctor_profile": None,
        "ds1": None,
        "ds2": [],
        "external_id": None,
        "mo_prikreplenia": None,
        "org_prof_m": None,
        "ds_norm": None,
        "disp_date": None,
        "month_d": None,
        "year_d": None,
        "duplicate": None,
    }
    if disp:
        row.update({
            "external_id": disp.get("external_id"),
            "mo_prikreplenia": disp.get("mo_prikreplenia"),
            "org_prof_m": disp.get("org_prof_m"),
            "ds_norm": disp.get("ds_norm"),
            "disp_date": disp.get("disp_date"),
            "month_d": disp.get("month_d"),
            "year_d": disp.get("year_d"),
            "duplicate": disp.get("duplicate"),
        })
        if not row["patient"]:
            row["patient"] = disp.get("fio_norm")
        if not row["birth_date"]:
            row["birth_date"] = disp.get("dr_norm")
    if tal:
        row.update({
            "talon": tal.get("talon"),
            "report_period": tal.get("report_period"),
            "place_service": tal.get("place_service"),
            "status": tal.get("status"),
            "treatment_end": tal.get("treatment_end"),
            "month_end": tal.get("month_end"),
            "year_end": tal.get("year_end"),
            "doctor": tal.get("doctor"),
            "doctor_profile": tal.get("doctor_profile"),
            "ds1": tal.get("ds1"),
            "ds2": normalize_ds2(tal.get("ds2")),
        })
        if not row["patient"]:
            row["patient"] = tal.get("patient")
        if not row["birth_date"]:
            row["birth_date"] = tal.get("birth_date")
    return row


def get_status_list(status_filter_mode, status_mode, sel_group, sel_ind) -> list[str]:
    if status_filter_mode != "by_status" or status_mode not in ("group", "individual"):
        return []
    if status_mode == "group":
        return list(status_groups.get(sel_group, []))
    return list(sel_ind or [])


def patient_passes_filters(
    patient: dict,
    *,
    selected_orgs,
    status_list: list[str],
    dup_filter: str,
    has_tal_filter: str,
    has_disp_filter: str,
) -> bool:
    if selected_orgs:
        orgs = set(patient.get("org_prof_m") or [])
        if not orgs.intersection(selected_orgs):
            return False

    if status_list:
        statuses = set(patient.get("statuses") or [])
        if not statuses.intersection(status_list):
            return False

    disp = patient.get("disp") or []
    tal = patient.get("tal") or []

    has_dup = any(d.get("duplicate") == "🔴" for d in disp)
    if dup_filter == "dup_only" and not has_dup:
        return False
    if dup_filter == "no_dup" and has_dup:
        return False

    if has_tal_filter == "has" and not any(d.get("has_tal") == "🟢" for d in disp):
        return False
    if has_tal_filter == "no" and not any(d.get("has_tal") == "🔴" for d in disp):
        return False

    if has_disp_filter == "has" and not any(t.get("has_disp") == "🟢" for t in tal):
        return False
    if has_disp_filter == "no" and not any(t.get("has_disp") == "🔴" for t in tal):
        return False

    return True


def filter_flat_rows(
    flat_rows: list[dict],
    *,
    year,
    orgs,
    status_list: list[str],
    place_service: str = "all",
    dup_report: str = "all",
) -> list[dict]:
    rows = flat_rows
    if year:
        rows = [r for r in rows if r.get("year_d") == year or r.get("year_end") == year]
    if orgs:
        org_set = set(orgs)
        rows = [r for r in rows if r.get("org_prof_m") in org_set]
    if status_list:
        rows = [r for r in rows if r.get("status") in status_list]
    if place_service != "all":
        rows = [r for r in rows if r.get("place_service") == place_service]
    if dup_report == "yes":
        rows = [r for r in rows if r.get("duplicate") is True]
    elif dup_report == "no":
        rows = [r for r in rows if r.get("duplicate") is False]
    return rows


def build_report_table(flat_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    import pandas as pd

    if not flat_rows:
        return [], []

    df = pd.DataFrame(flat_rows)
    if df.empty or "org_prof_m" not in df.columns:
        return [], []

    df = df[df["org_prof_m"].notna() & df["month_d"].notna()]

    grp = (
        df.groupby(["org_prof_m", "month_d"])["enp"]
        .nunique()
        .reset_index(name="count")
    )
    if grp.empty:
        return [], []

    pivot = grp.pivot(index="org_prof_m", columns="month_d", values="count").fillna(0).astype(int)
    pivot = pivot.rename(columns=MONTH_MAP)
    for label in MONTH_MAP.values():
        if label not in pivot.columns:
            pivot[label] = 0

    df_out = pivot.reset_index().rename(columns={"org_prof_m": "Организация"})
    months = [MONTH_MAP[i] for i in range(1, 13)]
    df_out["Всего"] = df_out[months].sum(axis=1)
    cols = ["Организация", "Всего"] + months
    df_out = df_out[cols]

    totals = df_out[months + ["Всего"]].sum()
    total_row = {"Организация": "Итого", **totals.to_dict()}
    df_out = pd.concat([df_out, pd.DataFrame([total_row])], ignore_index=True)

    columns = [{"name": c, "id": c} for c in df_out.columns]
    return columns, df_out.to_dict("records")


def build_report_detail(
    flat_rows: list[dict],
    active_cell: dict,
) -> tuple[list[dict], list[dict]]:
    import pandas as pd

    if not flat_rows or not active_cell:
        return [], []

    df = pd.DataFrame(flat_rows)
    if df.empty:
        return [], []

    grp = (
        df.groupby(["org_prof_m", "month_d"])["enp"]
        .nunique()
        .reset_index(name="count")
    )
    pivot = grp.pivot(index="org_prof_m", columns="month_d", values="count").fillna(0).astype(int)
    pivot = pivot.rename(columns=MONTH_MAP)
    org_list = list(pivot.index)
    total_idx = len(org_list)

    row_i = active_cell["row"]
    col_id = active_cell["column_id"]

    if row_i == total_idx:
        detail = df.copy()
    else:
        org = org_list[row_i]
        detail = df[df["org_prof_m"] == org]

    if col_id not in ("Организация", "Всего"):
        inv = {v: k for k, v in MONTH_MAP.items()}
        month_num = inv.get(col_id)
        if month_num:
            detail = detail[detail["month_d"] == month_num]

    if detail.empty:
        return [], []

    detail = detail.drop(columns=["month_end", "year_end"], errors="ignore")
    detail["ds2"] = detail["ds2"].apply(
        lambda v: ds2_display(normalize_ds2(v)) if v is not None else ""
    )

    cols_final = [c for c in detail.columns if c in REPORT_COL_MAP]
    columns = [{"name": REPORT_COL_MAP[c], "id": c} for c in cols_final]
    return columns, detail[cols_final].to_dict("records")
