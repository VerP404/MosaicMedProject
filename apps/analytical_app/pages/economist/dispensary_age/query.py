# -*- coding: utf-8 -*-
"""
Запросы для анализа вторых этапов диспансеризации (ДВ4/ДВ2, ДР1/ДР2, УД1/УД2)
из load_data_detailed_medical_examination. Номенклатура B*.
"""
from typing import List, Optional, Tuple, Any
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.query_executor import engine

# Варианты целей с двумя этапами: (тип 1-го этапа, тип 2-го этапа)
GOAL_TYPE_PAIRS = {
    "ДВ4": ("ДВ4", "ДВ2"),
    "ДР1": ("ДР1", "ДР2"),
    "УД1": ("УД1", "УД2"),
}

# Колонка для фильтра по периоду в зависимости от типа отчёта
REPORT_TYPE_DATE_COLUMN = {
    "month": "start_date",           # по отчетному месяцу
    "initial_input": "upload_date",   # по дате формирования
    "treatment": "end_date",          # по дате окончания лечения
}


def _year_month_condition(date_col: str, year: int, months: Optional[List[int]]) -> str:
    """Формирует SQL-условие по году и месяцам для start_date (varchar).
    Поддерживает форматы YYYY-MM-DD и DD.MM.YYYY.
    """
    year_str = str(year)
    cond_year = (
        f"(SUBSTRING(TRIM({date_col}) FROM 1 FOR 4) = '{year_str}' "
        f"OR SUBSTRING(TRIM({date_col}) FROM 7 FOR 4) = '{year_str}')"
    )
    if not months:
        return cond_year
    month_strs = [f"{m:02d}" for m in months]
    month_list = ", ".join(f"'{s}'" for s in month_strs)
    cond_month = (
        f"(SUBSTRING(TRIM({date_col}) FROM 6 FOR 2) IN ({month_list}) "
        f"OR SUBSTRING(TRIM({date_col}) FROM 4 FOR 2) IN ({month_list}))"
    )
    return f"({cond_year} AND {cond_month})"


def _date_range_condition(date_col: str, start_date: str, end_date: str) -> str:
    """Условие по диапазону дат. start_date, end_date — строки YYYY-MM-DD."""
    return f"(TRIM({date_col})::date BETWEEN '{start_date}'::date AND '{end_date}'::date)"


def sql_query_dr_raw(
    selected_year: int,
    selected_months: Optional[List[int]],
    talon_types: Tuple[str, str],
    report_type: str = "month",
    status_list: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    SQL для выборки из load_data_detailed_medical_examination:
    номенклатура B*, talon_type IN (type1, type2).
    Период: при report_type=month — год+месяцы; при initial_input/treatment — start_date..end_date (YYYY-MM-DD).
    """
    date_col = REPORT_TYPE_DATE_COLUMN.get(report_type, "start_date")
    if report_type in ("initial_input", "treatment") and start_date and end_date:
        date_cond = _date_range_condition(date_col, start_date, end_date)
    else:
        date_cond = _year_month_condition(date_col, selected_year, selected_months)
    status_filter = ""
    if status_list:
        statuses = ", ".join(f"'{s}'" for s in status_list)
        status_filter = f" AND status IN ({statuses})"
    type1, type2 = talon_types
    types_sql = ", ".join(f"'{t}'" for t in (type1, type2))

    return f"""
    SELECT
        talon_number,
        talon_type,
        enp,
        policy_number,
        last_name,
        first_name,
        middle_name,
        gender,
        birth_date,
        health_group,
        cost,
        service_nomenclature,
        service_name,
        doctor_services_fio,
        service_department,
        status,
        route,
        start_date,
        end_date
    FROM load_data_detailed_medical_examination
    WHERE service_nomenclature LIKE 'B%'
      AND talon_type IN ({types_sql})
      AND {date_cond}
      {status_filter}
    ORDER BY talon_number, service_nomenclature
    """


def get_dr_raw_df(
    selected_year: int,
    selected_months: Optional[List[int]],
    talon_types: Tuple[str, str],
    report_type: str = "month",
    status_list: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Загружает сырые данные из БД в DataFrame."""
    q = sql_query_dr_raw(
        selected_year=selected_year,
        selected_months=selected_months,
        talon_types=talon_types,
        report_type=report_type,
        status_list=status_list,
        start_date=start_date,
        end_date=end_date,
    )
    with engine.connect() as conn:
        df = pd.read_sql(text(q), conn)
    return df


def _parse_cost(s: Any) -> float:
    """Приведение стоимости к float (в БД может быть varchar с запятой)."""
    if s is None or (isinstance(s, str) and not s.strip()):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(str(s).replace(",", ".").replace(" ", "").strip())
    except (ValueError, TypeError):
        return 0.0


def build_main_services_df(df: pd.DataFrame) -> pd.DataFrame:
    """По одной «главной» строке на талон (первая по талону из отфильтрованных B-кодов)."""
    if df is None or df.empty:
        return pd.DataFrame()
    main = []
    for talon_number in df["talon_number"].unique():
        block = df[df["talon_number"] == talon_number]
        main.append(block.iloc[0].to_dict())
    return pd.DataFrame(main)


def build_patient_costs_df(main_services_df: pd.DataFrame, type1: str, type2: str) -> List[dict]:
    """
    Агрегация по ЕНП: стоимость по этапам (type1, type2), группы здоровья и т.д.
    Ключи в выходных dict используют type1/type2 (напр. «Группа здоровья ДВ4», «Стоимость ДР1»).
    """
    if main_services_df is None or main_services_df.empty:
        return []

    patient_costs = []
    for enp in main_services_df["enp"].dropna().unique():
        enp_str = str(enp).strip()
        if not enp_str or enp_str in ("-", "nan"):
            continue
        patient_data = main_services_df[main_services_df["enp"] == enp]

        data1 = patient_data[patient_data["talon_type"] == type1]
        data2 = patient_data[patient_data["talon_type"] == type2]

        cost1 = sum(_parse_cost(c) for c in data1["cost"]) if len(data1) > 0 else 0.0
        cost2 = sum(_parse_cost(c) for c in data2["cost"]) if len(data2) > 0 else 0.0

        stage2_directed = any(
            "Направлен на II этап" in str(h) for h in patient_data["health_group"]
        )
        row0 = patient_data.iloc[0]

        def _str_val(x, default=""):
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return default
            s = str(x).strip()
            return s if s and s != "-" else default

        def _num_str(x):
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return ""
            try:
                return str(int(float(x)))
            except (ValueError, TypeError):
                return _str_val(x)

        patient_costs.append({
            "ЕНП": _num_str(enp),
            "Номер полиса": _num_str(row0.get("policy_number")),
            "Фамилия": _str_val(row0.get("last_name")),
            "Имя": _str_val(row0.get("first_name")),
            "Отчество": _str_val(row0.get("middle_name")),
            "Пол": _str_val(row0.get("gender")),
            "Дата рождения": _str_val(row0.get("birth_date")),
            f"Маршрут {type1}": _str_val(data1["route"].iloc[0]) if len(data1) > 0 else "",
            f"Группа здоровья {type1}": _str_val(data1["health_group"].iloc[0]) if len(data1) > 0 else "",
            f"Группа здоровья {type2}": _str_val(data2["health_group"].iloc[0]) if len(data2) > 0 else "",
            "Направлен на II этап": stage2_directed,
            f"Стоимость {type1}": round(cost1, 2),
            f"Стоимость {type2}": round(cost2, 2),
            "Общая стоимость": round(cost1 + cost2, 2),
            f"Количество талонов {type1}": len(data1),
            f"Статус {type1}": _str_val(data1["status"].iloc[0]) if len(data1) > 0 else "",
            f"Количество талонов {type2}": len(data2),
            f"Статус {type2}": _str_val(data2["status"].iloc[0]) if len(data2) > 0 else "",
            f"Номер талона {type1}": _str_val(data1["talon_number"].iloc[0]) if len(data1) > 0 else "",
            f"Номер талона {type2}": _str_val(data2["talon_number"].iloc[0]) if len(data2) > 0 else "",
            f"Доктор {type1}": _str_val(data1["doctor_services_fio"].iloc[0]) if len(data1) > 0 else "",
            f"Доктор {type2}": _str_val(data2["doctor_services_fio"].iloc[0]) if len(data2) > 0 else "",
            f"Подразделение {type1}": _str_val(data1["service_department"].iloc[0]) if len(data1) > 0 else "",
            f"Подразделение {type2}": _str_val(data2["service_department"].iloc[0]) if len(data2) > 0 else "",
        })

    return patient_costs


def build_summary_dr1_dr2_df(patient_costs: List[dict], type1: str, type2: str) -> List[dict]:
    """
    Сводная по полу и группам здоровья (type1, type2): количество, суммы.
    """
    if not patient_costs:
        return []

    k_grp1 = f"Группа здоровья {type1}"
    k_grp2 = f"Группа здоровья {type2}"
    k_cost1 = f"Стоимость {type1}"
    k_cost2 = f"Стоимость {type2}"

    df = pd.DataFrame(patient_costs)
    df["Пол"] = df["Пол"].fillna("").astype(str)
    df[k_grp1] = df[k_grp1].fillna("").astype(str)
    df[k_grp2] = df[k_grp2].fillna("").astype(str)

    agg = df.groupby(
        ["Пол", k_grp1, k_grp2],
        dropna=False,
    ).agg(
        Количество_пациентов=("ЕНП", "count"),
        Стоимость_1=(k_cost1, "sum"),
        Стоимость_2=(k_cost2, "sum"),
    ).reset_index()

    agg["Общая стоимость"] = (agg["Стоимость_1"] + agg["Стоимость_2"]).round(2)
    agg["Стоимость_1"] = agg["Стоимость_1"].round(2)
    agg["Стоимость_2"] = agg["Стоимость_2"].round(2)

    result = []
    for _, row in agg.iterrows():
        result.append({
            "Пол": row["Пол"] or "—",
            k_grp1: row[k_grp1] or "—",
            k_grp2: row[k_grp2] or "—",
            "Количество пациентов": int(row["Количество_пациентов"]),
            k_cost1: row["Стоимость_1"],
            k_cost2: row["Стоимость_2"],
            "Общая стоимость": row["Общая стоимость"],
        })
    return result


def _normalize_gender(пол: str) -> str:
    """Приводит пол к Ж или М для сводных."""
    if not пол or not str(пол).strip():
        return "М"  # по умолчанию
    s = str(пол).strip().upper()
    if s in ("Ж", "ЖЕН", "ЖЕНСКИЙ", "F", "FEMALE"):
        return "Ж"
    if s in ("М", "МУЖ", "МУЖСКОЙ", "M", "MALE"):
        return "М"
    return "Ж" if s.startswith("Ж") else "М"


def build_summary_dr_pivot(
    patient_costs: List[dict],
    health_group_key: str,
    cost_key: str,
) -> List[dict]:
    """
    Сводная в формате: иерархия по группе здоровья и стоимости,
    колонки Ж, М, Общий итог. Количество по полю Фамилия (уникальные пациенты).
    Возвращает строки с _row_type: 'detail' | 'subtotal' | 'grand_total' для стилей.
    """
    if not patient_costs:
        return []

    df = pd.DataFrame(patient_costs)
    df["_пол_норм"] = df["Пол"].map(_normalize_gender)
    df["_группа"] = df[health_group_key].fillna("").astype(str).str.strip().replace("", "—")
    df["_стоимость"] = df[cost_key]
    # Один пациент может быть только один раз в группе с одной стоимостью
    agg = df.groupby(["_группа", "_стоимость", "_пол_норм"], dropna=False).size().reset_index(name="count")

    # Свод по (группа, стоимость) -> Ж, М
    pivot = agg.pivot_table(
        index=["_группа", "_стоимость"],
        columns="_пол_норм",
        values="count",
        aggfunc="sum",
        fill_value=0,
    )
    for col in ["Ж", "М"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot.reindex(columns=["Ж", "М"], fill_value=0).reset_index()
    pivot["Общий итог"] = pivot["Ж"] + pivot["М"]

    # Сортируем: по группе, затем по стоимости
    pivot = pivot.sort_values(["_группа", "_стоимость"])

    rows = []
    total_ж, total_м, total_all = 0, 0, 0

    for group_name, grp in pivot.groupby("_группа", sort=False):
        sub_ж, sub_м = 0, 0
        for _, r in grp.iterrows():
            cost_val = r["_стоимость"]
            ж = int(r["Ж"])
            м = int(r["М"])
            итог = int(r["Общий итог"])
            cost_display = f"{cost_val:,.2f}".replace(",", " ").replace(".", ",") if isinstance(cost_val, (int, float)) else str(cost_val)
            rows.append({
                "Группа здоровья": group_name,
                "Стоимость": cost_display,
                "Ж": ж,
                "М": м,
                "Общий итог": итог,
                "_row_type": "detail",
            })
            sub_ж += ж
            sub_м += м
        rows.append({
            "Группа здоровья": group_name,
            "Стоимость": "Итого по группе",
            "Ж": sub_ж,
            "М": sub_м,
            "Общий итог": sub_ж + sub_м,
            "_row_type": "subtotal",
        })
        total_ж += sub_ж
        total_м += sub_м

    rows.append({
        "Группа здоровья": "Общий итог",
        "Стоимость": "",
        "Ж": total_ж,
        "М": total_м,
        "Общий итог": total_ж + total_м,
        "_row_type": "grand_total",
    })

    return rows


def build_summary_dr1_pivot(patient_costs: List[dict], type1: str) -> List[dict]:
    """Сводная по первому этапу (type1): группа здоровья, стоимость, Ж/М/Общий итог."""
    return build_summary_dr_pivot(
        patient_costs,
        health_group_key=f"Группа здоровья {type1}",
        cost_key=f"Стоимость {type1}",
    )


def build_summary_dr2_pivot(patient_costs: List[dict], type2: str) -> List[dict]:
    """Сводная по второму этапу (type2). Учитываются только пациенты с данными по type2."""
    cost_key = f"Стоимость {type2}"
    grp_key = f"Группа здоровья {type2}"
    stage2_only = [
        p for p in patient_costs
        if (p.get(cost_key) or 0) != 0 or (str(p.get(grp_key) or "").strip())
    ]
    return build_summary_dr_pivot(
        stage2_only,
        health_group_key=grp_key,
        cost_key=cost_key,
    )


def build_summary_combined_pivot(summary_list: List[dict], type1: str, type2: str) -> List[dict]:
    """
    Сводная по двум этапам: агрегат по (Группа type1, Группа type2), Ж/М, стоимости.
    Ключи в строках используют type1/type2 (напр. «Группа здоровья ДВ4», «Стоимость ДР2»).
    """
    if not summary_list:
        return []

    k_grp1 = f"Группа здоровья {type1}"
    k_grp2 = f"Группа здоровья {type2}"
    k_cost1 = f"Стоимость {type1}"
    k_cost2 = f"Стоимость {type2}"

    df = pd.DataFrame(summary_list)
    df["Пол"] = df["Пол"].fillna("").astype(str).str.strip().replace("", "—")
    df[k_grp1] = df[k_grp1].fillna("").astype(str).str.strip().replace("", "—")
    df[k_grp2] = df[k_grp2].fillna("").astype(str).str.strip().replace("", "—")
    df["_пол"] = df["Пол"].map(lambda x: "Ж" if str(x).upper().startswith("Ж") or x in ("женский", "Жен") else "М")

    agg = (
        df.groupby([k_grp1, k_grp2, "_пол"], dropna=False)
        .agg(
            Количество=("Количество пациентов", "sum"),
            Стоимость_1=(k_cost1, "sum"),
            Стоимость_2=(k_cost2, "sum"),
            Общая=("Общая стоимость", "sum"),
        )
        .reset_index()
    )
    pivot = agg.pivot_table(
        index=[k_grp1, k_grp2],
        columns="_пол",
        values="Количество",
        aggfunc="sum",
        fill_value=0,
    )
    for c in ["Ж", "М"]:
        if c not in pivot.columns:
            pivot[c] = 0
    pivot = pivot.reindex(columns=["Ж", "М"], fill_value=0).reset_index()
    costs = (
        df.groupby([k_grp1, k_grp2], dropna=False)
        .agg(Стоимость_1=(k_cost1, "sum"), Стоимость_2=(k_cost2, "sum"), Общая=("Общая стоимость", "sum"))
        .reset_index()
    )
    merge_df = pivot.merge(costs, on=[k_grp1, k_grp2], how="left")
    merge_df["Общий итог"] = merge_df["Ж"] + merge_df["М"]
    merge_df = merge_df.sort_values([k_grp1, k_grp2])

    rows = []
    for grp1, grp_block in merge_df.groupby(k_grp1, sort=False):
        sub_ж, sub_м, sub_s1, sub_s2, sub_all = 0, 0, 0.0, 0.0, 0.0
        for _, r in grp_block.iterrows():
            rows.append({
                k_grp1: grp1,
                k_grp2: r[k_grp2],
                "Ж": int(r["Ж"]),
                "М": int(r["М"]),
                "Общий итог": int(r["Общий итог"]),
                k_cost1: round(float(r["Стоимость_1"]), 2),
                k_cost2: round(float(r["Стоимость_2"]), 2),
                "Общая стоимость": round(float(r["Общая"]), 2),
                "_row_type": "detail",
            })
            sub_ж += int(r["Ж"])
            sub_м += int(r["М"])
            sub_s1 += float(r["Стоимость_1"])
            sub_s2 += float(r["Стоимость_2"])
            sub_all += float(r["Общая"])
        rows.append({
            k_grp1: grp1,
            k_grp2: "Итого по группе",
            "Ж": sub_ж,
            "М": sub_м,
            "Общий итог": sub_ж + sub_м,
            k_cost1: round(sub_s1, 2),
            k_cost2: round(sub_s2, 2),
            "Общая стоимость": round(sub_all, 2),
            "_row_type": "subtotal",
        })

    total_ж = sum(r["Ж"] for r in rows if r.get("_row_type") == "detail")
    total_м = sum(r["М"] for r in rows if r.get("_row_type") == "detail")
    total_s1 = sum(r[k_cost1] for r in rows if r.get("_row_type") == "detail")
    total_s2 = sum(r[k_cost2] for r in rows if r.get("_row_type") == "detail")
    total_all = sum(r["Общая стоимость"] for r in rows if r.get("_row_type") == "detail")
    rows.append({
        k_grp1: "Общий итог",
        k_grp2: "",
        "Ж": total_ж,
        "М": total_м,
        "Общий итог": total_ж + total_м,
        k_cost1: round(total_s1, 2),
        k_cost2: round(total_s2, 2),
        "Общая стоимость": round(total_all, 2),
        "_row_type": "grand_total",
    })
    return rows


def get_dr_analysis_data(
    selected_year: int,
    selected_months: Optional[List[int]],
    talon_types: Tuple[str, str],
    report_type: str = "month",
    status_list: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[List[dict], List[dict]]:
    """
    Основная точка входа: загрузка из БД, расчёт по пациентам и сводная.
    talon_types — пара (type1, type2). report_type — «month» | «initial_input» | «treatment».
    Для initial_input/treatment передайте start_date, end_date (YYYY-MM-DD).
    """
    raw = get_dr_raw_df(
        selected_year=selected_year,
        selected_months=selected_months,
        talon_types=talon_types,
        report_type=report_type,
        status_list=status_list,
        start_date=start_date,
        end_date=end_date,
    )
    if raw.empty:
        return [], []

    type1, type2 = talon_types
    main_df = build_main_services_df(raw)
    patient_costs = build_patient_costs_df(main_df, type1, type2)
    summary = build_summary_dr1_dr2_df(patient_costs, type1, type2)
    return patient_costs, summary
