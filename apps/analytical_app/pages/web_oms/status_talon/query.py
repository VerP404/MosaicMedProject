sql_query_status = """ select COALESCE(goal, 'Итого') AS "Цель",
        count(*) as "Всего",
        sum(case when status = '3' then 1 else 0 end)  as Оплачено,
        sum(case when status = '2' or status = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when status = '5' or status = '7' or status = '12' then 1 else 0 end)  as "Отказано",
        sum(case when status = '0' or status = '13' or status = '17' then 1 else 0 end)  as "Отменен",
        sum(case when status = '1' then 1 else 0 end)  as "1",
        sum(case when status = '2' then 1 else 0 end)  as "2",
        sum(case when status = '3' then 1 else 0 end)  as "3",
        sum(case when status = '4' then 1 else 0 end)  as "4",
        sum(case when status = '5' then 1 else 0 end)  as "5",
        sum(case when status = '6' then 1 else 0 end)  as "6",
        sum(case when status = '7' then 1 else 0 end)  as "7",
        sum(case when status = '8' then 1 else 0 end)  as "8",
        sum(case when status = '12' then 1 else 0 end) as "12",
        sum(case when status = '13' then 1 else 0 end) as "13",
        sum(case when status = '17' then 1 else 0 end) as "17",
        sum(case when status = '0' then 1 else 0 end)  as "0"
from data_loader_omsdata
where tariff != '0' 
    and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY ROLLUP("Цель")
"""

sql_query_status_spec = """ select COALESCE(goal, 'Итого') AS "Цель",
        count(*) as "Всего",
        sum(case when status = '3' then 1 else 0 end)  as Оплачено,
        sum(case when status = '2' or status = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when status = '5' or status = '7' or status = '12' then 1 else 0 end)  as "Отказано",
        sum(case when status = '0' or status = '13' or status = '17' then 1 else 0 end)  as "Отменен",
        sum(case when status = '1' then 1 else 0 end)  as "1",
        sum(case when status = '2' then 1 else 0 end)  as "2",
        sum(case when status = '3' then 1 else 0 end)  as "3",
        sum(case when status = '4' then 1 else 0 end)  as "4",
        sum(case when status = '5' then 1 else 0 end)  as "5",
        sum(case when status = '6' then 1 else 0 end)  as "6",
        sum(case when status = '7' then 1 else 0 end)  as "7",
        sum(case when status = '8' then 1 else 0 end)  as "8",
        sum(case when status = '12' then 1 else 0 end) as "12",
        sum(case when status = '13' then 1 else 0 end) as "13",
        sum(case when status = '17' then 1 else 0 end) as "17",
        sum(case when status = '0' then 1 else 0 end)  as "0"
from data_loader_omsdata
where tariff != '0' 
    and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
    and doctor_profile like :value_spec
GROUP BY ROLLUP("Цель")
"""

sql_query_status_korpus = f"""
select COALESCE(department, 'Итого') AS "Корпус",
        count(*) as "Всего",
        sum(case when status = '3' then 1 else 0 end)  as Оплачено,
        sum(case when status = '2' or status = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when status = '5' or status = '7' or status = '12' then 1 else 0 end)  as "Отказано",
        sum(case when status = '0' or status = '13' or status = '17' then 1 else 0 end)  as "Отменен",
        sum(case when status = '1' then 1 else 0 end)  as "1",
        sum(case when status = '2' then 1 else 0 end)  as "2",
        sum(case when status = '3' then 1 else 0 end)  as "3",
        sum(case when status = '4' then 1 else 0 end)  as "4",
        sum(case when status = '5' then 1 else 0 end)  as "5",
        sum(case when status = '6' then 1 else 0 end)  as "6",
        sum(case when status = '7' then 1 else 0 end)  as "7",
        sum(case when status = '8' then 1 else 0 end)  as "8",
        sum(case when status = '12' then 1 else 0 end) as "12",
        sum(case when status = '13' then 1 else 0 end) as "13",
        sum(case when status = '17' then 1 else 0 end) as "17",
        sum(case when status = '0' then 1 else 0 end)  as "0"
from data_loader_omsdata
where tariff != '0'
    and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
    and goal = :cel
GROUP BY ROLLUP("Корпус")
"""

sql_query_status_spec_korp = """ select COALESCE(goal, 'Итого') AS "Цель",
        count(*) as "Всего",
        sum(case when status = '3' then 1 else 0 end)  as Оплачено,
        sum(case when status = '2' or status = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when status = '5' or status = '7' or status = '12' then 1 else 0 end)  as "Отказано",
        sum(case when status = '0' or status = '13' or status = '17' then 1 else 0 end)  as "Отменен",
        sum(case when status = '1' then 1 else 0 end)  as "1",
        sum(case when status = '2' then 1 else 0 end)  as "2",
        sum(case when status = '3' then 1 else 0 end)  as "3",
        sum(case when status = '4' then 1 else 0 end)  as "4",
        sum(case when status = '5' then 1 else 0 end)  as "5",
        sum(case when status = '6' then 1 else 0 end)  as "6",
        sum(case when status = '7' then 1 else 0 end)  as "7",
        sum(case when status = '8' then 1 else 0 end)  as "8",
        sum(case when status = '12' then 1 else 0 end) as "12",
        sum(case when status = '13' then 1 else 0 end) as "13",
        sum(case when status = '17' then 1 else 0 end) as "17",
        sum(case when status = '0' then 1 else 0 end)  as "0"
from data_loader_omsdata
where tariff != '0' 
    and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
    and doctor_profile like :value_spec and department = :korp
GROUP BY ROLLUP("Цель")
"""




sql_query_cel_dia = """
select COALESCE(department, 'Итого')                                              AS "Корпус",
       count(*)                                                                        as "Всего",
        sum(case when status = '3' then 1 else 0 end)  as Оплачено,
        sum(case when status = '2' or status = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when status = '5' or status = '7' or status = '12' then 1 else 0 end)  as "Отказано",
        sum(case when status = '0' or status = '13' or status = '17' then 1 else 0 end)  as "Отменен",
        sum(case when status = '1' then 1 else 0 end)  as "1",
        sum(case when status = '2' then 1 else 0 end)  as "2",
        sum(case when status = '3' then 1 else 0 end)  as "3",
        sum(case when status = '4' then 1 else 0 end)  as "4",
        sum(case when status = '5' then 1 else 0 end)  as "5",
        sum(case when status = '6' then 1 else 0 end)  as "6",
        sum(case when status = '7' then 1 else 0 end)  as "7",
        sum(case when status = '8' then 1 else 0 end)  as "8",
        sum(case when status = '12' then 1 else 0 end) as "12",
        sum(case when status = '13' then 1 else 0 end) as "13",
        sum(case when status = '17' then 1 else 0 end) as "17",
        sum(case when status = '0' then 1 else 0 end)  as "0"
from data_loader_omsdata
where tariff != '0'
  and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
  and goal like any (:cel)
  and main_diagnosis like any (:dia)
GROUP BY ROLLUP ("Корпус")
"""


# --- Конструктор отчётов (новая модель: строки / показатели / фильтры) ---

_DIAGNOSIS_EXPR = """CASE
          WHEN POSITION(' ' IN COALESCE(main_diagnosis, '') ) > 0
          THEN SUBSTRING(main_diagnosis, 1, POSITION(' ' IN main_diagnosis) - 1)
          ELSE COALESCE(main_diagnosis, '')
        END"""

_AMOUNT_EXPR = """NULLIF(
          REPLACE(REPLACE(REPLACE(COALESCE(amount, '0'), ' ', ''), ',', '.'), '-', '0'),
          ''
        )::numeric"""

CONSTRUCTOR_ROW_DIMS = {
    "goal": {"expr": "goal", "alias": "Цель", "label": "Цель"},
    "department": {
        "expr": "department",
        "alias": "Подразделение",
        "label": "Подразделение (корпус)",
    },
    "specialty": {"expr": "specialty", "alias": "Специальность", "label": "Специальность"},
    "doctor": {"expr": "doctor", "alias": "Врач", "label": "Врач"},
    "doctor_profile": {
        "expr": "doctor_profile",
        "alias": "Профиль МП",
        "label": "Профиль МП",
    },
    "diagnosis": {"expr": _DIAGNOSIS_EXPR, "alias": "Диагноз", "label": "Диагноз (код)"},
    "month": {
        "expr": None,  # подставляется по выбранному полю даты
        "alias": "Месяц",
        "label": "Месяц",
    },
    "status": {"expr": "status", "alias": "Статус", "label": "Статус"},
    "gender": {"expr": "gender", "alias": "Пол", "label": "Пол"},
    "care_conditions": {
        "expr": "care_conditions",
        "alias": "Условия",
        "label": "Условия оказания",
    },
}

# Пакеты показателей (колонки таблицы). Пользователь выбирает что показать.
CONSTRUCTOR_MEASURE_PACKS = {
    "total": {
        "label": "Всего",
        "count_sql": 'count(*) as "Всего"',
        "sum_sql": f'COALESCE(SUM({_AMOUNT_EXPR}), 0) as "Всего"',
        "unique_sql": 'count(DISTINCT NULLIF(enp, \'-\')) as "Всего"',
    },
    "paid": {
        "label": "Оплачено (3)",
        "count_sql": "sum(case when status = '3' then 1 else 0 end) as \"Оплачено\"",
        "sum_sql": f"COALESCE(SUM(CASE WHEN status = '3' THEN {_AMOUNT_EXPR} END), 0) as \"Оплачено\"",
        "unique_sql": "count(DISTINCT CASE WHEN status = '3' THEN NULLIF(enp, '-') END) as \"Оплачено\"",
    },
    "tfoms": {
        "label": "В ТФОМС (1+2)",
        "count_sql": "sum(case when status in ('1','2') then 1 else 0 end) as \"В ТФОМС\"",
        "sum_sql": f"COALESCE(SUM(CASE WHEN status in ('1','2') THEN {_AMOUNT_EXPR} END), 0) as \"В ТФОМС\"",
        "unique_sql": "count(DISTINCT CASE WHEN status in ('1','2') THEN NULLIF(enp, '-') END) as \"В ТФОМС\"",
    },
    "in_work": {
        "label": "В работе (1,2,3,4,6,8,19)",
        "count_sql": "sum(case when status in ('1','2','3','4','6','8','19') then 1 else 0 end) as \"В работе\"",
        "sum_sql": (
            f"COALESCE(SUM(CASE WHEN status in ('1','2','3','4','6','8','19') "
            f"THEN {_AMOUNT_EXPR} END), 0) as \"В работе\""
        ),
        "unique_sql": (
            "count(DISTINCT CASE WHEN status in ('1','2','3','4','6','8','19') "
            "THEN NULLIF(enp, '-') END) as \"В работе\""
        ),
    },
    "rejected": {
        "label": "Отказано (5,7,12)",
        "count_sql": "sum(case when status in ('5','7','12') then 1 else 0 end) as \"Отказано\"",
        "sum_sql": f"COALESCE(SUM(CASE WHEN status in ('5','7','12') THEN {_AMOUNT_EXPR} END), 0) as \"Отказано\"",
        "unique_sql": "count(DISTINCT CASE WHEN status in ('5','7','12') THEN NULLIF(enp, '-') END) as \"Отказано\"",
    },
    "cancelled": {
        "label": "Отменён (0,13,17)",
        "count_sql": "sum(case when status in ('0','13','17') then 1 else 0 end) as \"Отменен\"",
        "sum_sql": f"COALESCE(SUM(CASE WHEN status in ('0','13','17') THEN {_AMOUNT_EXPR} END), 0) as \"Отменен\"",
        "unique_sql": "count(DISTINCT CASE WHEN status in ('0','13','17') THEN NULLIF(enp, '-') END) as \"Отменен\"",
    },
}

for _st in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "12", "13", "17", "18", "19"):
    CONSTRUCTOR_MEASURE_PACKS[f"st_{_st}"] = {
        "label": f"Статус {_st}",
        "count_sql": f"sum(case when status = '{_st}' then 1 else 0 end) as \"{_st}\"",
        "sum_sql": f"COALESCE(SUM(CASE WHEN status = '{_st}' THEN {_AMOUNT_EXPR} END), 0) as \"{_st}\"",
        "unique_sql": f"count(DISTINCT CASE WHEN status = '{_st}' THEN NULLIF(enp, '-') END) as \"{_st}\"",
    }

DEFAULT_MEASURE_PACKS = ["total", "paid", "tfoms", "rejected", "cancelled"]

DATE_FIELD_MAP = {
    "initial_input": "initial_input_date",
    "treatment": "treatment_end",
}


def _bind_in(where, bind_params, column, values, prefix):
    values = [v for v in (values or []) if v not in (None, "")]
    if not values:
        return
    placeholders = ", ".join(f":{prefix}_{i}" for i in range(len(values)))
    where.append(f"{column} IN ({placeholders})")
    for i, v in enumerate(values):
        bind_params[f"{prefix}_{i}"] = v


def _bind_like_or(where, bind_params, column, values, prefix, pattern="{v}%"):
    values = [v for v in (values or []) if v not in (None, "")]
    if not values:
        return
    parts = []
    for i, v in enumerate(values):
        key = f"{prefix}_{i}"
        parts.append(f"{column} LIKE :{key}")
        bind_params[key] = pattern.format(v=v)
    where.append("(" + " OR ".join(parts) + ")")


def build_constructor_sql(
    *,
    rows,
    measures,
    value_mode="count",
    date_field="initial_input",
    start_date,
    end_date,
    goals=None,
    departments=None,
    specialties=None,
    diagnoses=None,
    statuses=None,
    doctors=None,
    include_rollup=True,
    exclude_zero_tariff=True,
):
    """
    Новый конструктор: произвольные строки + выбранные показатели + независимые фильтры.

    value_mode: count | sum | unique
    date_field: initial_input | treatment
    """
    if isinstance(rows, str):
        rows = [rows]
    rows = [r for r in (rows or []) if r in CONSTRUCTOR_ROW_DIMS]
    if not rows:
        rows = ["goal"]

    if isinstance(measures, str):
        measures = [measures]
    measures = [m for m in (measures or []) if m in CONSTRUCTOR_MEASURE_PACKS]
    if not measures:
        measures = list(DEFAULT_MEASURE_PACKS)

    date_col = DATE_FIELD_MAP.get(date_field or "initial_input", "initial_input_date")
    month_expr = f"SUBSTRING({date_col} FROM 4 FOR 2)"

    dims = []
    for key in rows:
        meta = dict(CONSTRUCTOR_ROW_DIMS[key])
        if key == "month":
            meta["expr"] = month_expr
        dims.append(meta)

    select_dims = ",\n        ".join(f'{d["expr"]} AS "{d["alias"]}"' for d in dims)
    group_exprs = ", ".join(d["expr"] for d in dims)
    group_clause = (
        f"GROUP BY ROLLUP ({group_exprs})" if include_rollup else f"GROUP BY {group_exprs}"
    )

    metric_key = {
        "count": "count_sql",
        "sum": "sum_sql",
        "unique": "unique_sql",
    }.get(value_mode or "count", "count_sql")
    measure_sql = ",\n        ".join(
        CONSTRUCTOR_MEASURE_PACKS[m][metric_key] for m in measures
    )

    where = [
        f"to_date({date_col}, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') "
        f"AND to_date(:end_date, 'DD-MM-YYYY')",
    ]
    bind_params = {"start_date": start_date, "end_date": end_date}

    if exclude_zero_tariff:
        where.append("(tariff IS NULL OR tariff NOT IN ('0', '-', ''))")

    _bind_in(where, bind_params, "goal", goals, "goal")
    _bind_in(where, bind_params, "department", departments, "dep")
    _bind_in(where, bind_params, "specialty", specialties, "spec")
    _bind_like_or(where, bind_params, "main_diagnosis", diagnoses, "dia", "{v}%")
    _bind_in(where, bind_params, "status", statuses, "st")
    _bind_like_or(where, bind_params, "doctor", doctors, "doc", "%{v}%")

    sql = f"""
select {select_dims},
        {measure_sql}
from data_loader_omsdata
where {' AND '.join(where)}
{group_clause}
"""
    return sql, bind_params, [d["alias"] for d in dims]


# Совместимость со старым именем
STATUS_CONSTRUCTOR_DIMENSIONS = CONSTRUCTOR_ROW_DIMS


def sql_query_status_constructor(group_by, **kwargs):
    """Обёртка: старый API → новый builder."""
    return build_constructor_sql(
        rows=group_by,
        measures=kwargs.get("measures") or DEFAULT_MEASURE_PACKS,
        value_mode=kwargs.get("value_mode", "count"),
        date_field=kwargs.get("date_field", "initial_input"),
        start_date=kwargs["start_date"],
        end_date=kwargs["end_date"],
        goals=kwargs.get("goals"),
        departments=kwargs.get("departments"),
        specialties=kwargs.get("specialties"),
        diagnoses=kwargs.get("diagnoses"),
        statuses=kwargs.get("statuses"),
        doctors=kwargs.get("doctors"),
        include_rollup=kwargs.get("include_rollup", True),
        exclude_zero_tariff=kwargs.get("exclude_zero_tariff", True),
    )


sql_query_patient_dia = """
WITH RankedData AS (
    SELECT
        enp,
        patient,
        birth_date,
        gender,
        goal,
        CASE
            WHEN POSITION(' ' IN main_diagnosis) > 0
            THEN SUBSTRING(main_diagnosis, 1, POSITION(' ' IN main_diagnosis) - 1)
            ELSE main_diagnosis
        END AS "DS1",
        CASE
            WHEN POSITION(' ' IN additional_diagnosis) > 0
            THEN SUBSTRING(additional_diagnosis, 1, POSITION(' ' IN additional_diagnosis) - 1)
            ELSE additional_diagnosis
        END AS "DS2",
        ROW_NUMBER() OVER (PARTITION BY enp ORDER BY enp) AS RowNum
    FROM data_loader_omsdata
),
FirstData AS (
    SELECT DISTINCT ON (enp)
        enp,
        patient,
        birth_date,
        gender
    FROM RankedData
    WHERE RowNum = 1
),
UniqueDiagnoses AS (
    SELECT
        enp,
        unnest(array["DS1", "DS2"]) AS "Diagnosis"
    FROM RankedData
    WHERE "DS1" IS NOT NULL OR "DS2" IS NOT NULL
),
SortedDiagnoses AS (
    SELECT
        enp,
        array_agg(DISTINCT "Diagnosis" ORDER BY "Diagnosis") AS "SortedDiagnosisArray"
    FROM UniqueDiagnoses
    GROUP BY enp
),
UniqueGoals AS (
    SELECT
        enp,
        goal
    FROM RankedData
    WHERE goal IS NOT NULL
),
SortedGoals AS (
    SELECT
        enp,
        array_agg(DISTINCT goal ORDER BY goal) AS "SortedGoalArray"
    FROM UniqueGoals
    GROUP BY enp
)
SELECT
    f.enp,
    f.patient,
    f.birth_date,
    f.gender,
    array_to_string(d."SortedDiagnosisArray", ', ') AS "Диагнозы",
    array_to_string(g."SortedGoalArray", ', ') AS "Цели"
FROM FirstData f
LEFT JOIN SortedDiagnoses d ON f.enp = d.enp
LEFT JOIN SortedGoals g ON f.enp = g.enp
order by patient
"""


GROUP_COL_NAMES = ("Дата", "Врач", "Специальность", "Корпус", "Отделение")

_GROUP_DIMS = {
    "date": [],
    "doctors": [
        ("COALESCE(doctor, '-')", "Врач", "doctor"),
        ("COALESCE(specialty, '-')", "Специальность", "specialty"),
        ("COALESCE(building, '-')", "Корпус", "building"),
        ("COALESCE(department, '-')", "Отделение", "department"),
    ],
    "buildings": [
        ("COALESCE(building, '-')", "Корпус", "building"),
    ],
    "departments": [
        ("COALESCE(department, '-')", "Отделение", "department"),
        ("COALESCE(building, '-')", "Корпус", "building"),
    ],
    "specialty": [
        ("COALESCE(specialty, '-')", "Специальность", "specialty"),
    ],
}


def _talons_group_fields(group_mode, date_char, date_expr, split_by_date):
    """Поля группировки: (select_expr, alias, group_expr)."""
    fields = list(_GROUP_DIMS.get(group_mode) or _GROUP_DIMS["date"])
    include_date = group_mode == "date" or bool(split_by_date)
    if include_date:
        fields.append((date_char, "Дата", date_expr))
    if not fields:
        fields.append((date_char, "Дата", date_expr))
    return fields


def sql_query_talons_by_dates(
    selected_year,
    months_placeholder,
    inogorod,
    sanction,
    amount_null,
    report_type,
    goals,
    input_start=None,
    input_end=None,
    treatment_start=None,
    treatment_end=None,
    status_list=None,
    specific_dates=None,
    hide_zero_rows=True,
    group_mode="date",
    split_by_date=False,
):
    """
    Талоны: фильтр по периоду или конкретным датам, группировка как у экономистов
    (даты / врачи / корпуса / отделения / специальности), опционально с разбивкой по дням.
    Столбцы группировки, затем Итого и выбранные цели.
    """
    from datetime import date, datetime

    from apps.analytical_app.pages.SQL_query.query import base_query

    if not months_placeholder or months_placeholder.strip() == "":
        months_placeholder = ", ".join(map(str, range(1, 13)))

    group_mode = group_mode or "date"

    dates_list = []
    for item in specific_dates or []:
        if isinstance(item, datetime):
            dates_list.append(item.date())
        elif isinstance(item, date):
            dates_list.append(item)
        elif isinstance(item, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
                try:
                    dates_list.append(datetime.strptime(item, fmt).date())
                    break
                except ValueError:
                    continue
    dates_list = sorted(set(dates_list))
    use_specific = bool(dates_list)

    input_start = input_start if report_type == "initial_input" and not use_specific else None
    input_end = input_end if report_type == "initial_input" and not use_specific else None
    treatment_start = treatment_start if report_type == "treatment" and not use_specific else None
    treatment_end = treatment_end if report_type == "treatment" and not use_specific else None

    base = base_query(
        selected_year,
        months_placeholder,
        inogorod,
        sanction,
        amount_null,
        building_ids=None,
        department_ids=None,
        profile_ids=None,
        doctor_ids=None,
        initial_input_date_start=input_start,
        initial_input_date_end=input_end,
        treatment_start=treatment_start,
        treatment_end=treatment_end,
        status_list=status_list,
    )

    if report_type == "treatment":
        date_expr = "TO_DATE(treatment_end, 'DD-MM-YYYY')"
        date_char = "TO_CHAR(TO_DATE(treatment_end, 'DD-MM-YYYY'), 'DD-MM-YYYY')"
    else:
        date_expr = "TO_DATE(initial_input_date, 'DD-MM-YYYY')"
        date_char = "TO_CHAR(TO_DATE(initial_input_date, 'DD-MM-YYYY'), 'DD-MM-YYYY')"

    fields = _talons_group_fields(group_mode, date_char, date_expr, split_by_date)
    group_select = ",\n       ".join(f'{expr} AS "{alias}"' for expr, alias, _ in fields)
    group_by = ", ".join(gexpr for _, _, gexpr in fields)
    order_by = ", ".join(
        f"{gexpr} DESC" if alias == "Дата" else gexpr
        for _, alias, gexpr in fields
    )
    date_only = group_mode == "date"

    if not goals:
        return f"""
        {base}
        SELECT {group_select}, 0 AS "Итого"
        FROM oms
        WHERE 1=0
        GROUP BY {group_by}
        """

    quoted_goals = ", ".join(f"'{g.replace(chr(39), chr(39) + chr(39))}'" for g in goals)
    goal_filter = f"AND goal IN ({quoted_goals})"

    goal_exprs = []
    goal_aliases = []
    for g in goals:
        safe_g = g.replace('"', '""')
        esc = g.replace("'", "''")
        goal_aliases.append(safe_g)
        goal_exprs.append(f"COUNT(*) FILTER (WHERE goal = '{esc}') AS \"{safe_g}\"")

    sum_parts = [expr[: expr.rfind(" AS ")] for expr in goal_exprs]
    total_expr = "(" + " + ".join(sum_parts) + ") AS \"Итого\""
    pivot_cols = total_expr + ",\n       " + ",\n       ".join(goal_exprs)
    having_expr = " + ".join(sum_parts) + " > 0"

    date_filter = ""
    if use_specific:
        in_list = ", ".join(f"DATE '{d.isoformat()}'" for d in dates_list)
        date_filter = f"AND {date_expr} IN ({in_list})"

    having_sql = f"HAVING ({having_expr})" if hide_zero_rows else ""

    use_spine = (not hide_zero_rows) and date_only
    if not use_spine:
        return f"""
    {base}
SELECT {group_select},
       {pivot_cols}
FROM oms
WHERE 1=1
  {goal_filter}
  {date_filter}
GROUP BY {group_by}
{having_sql}
ORDER BY {order_by}
"""

    if use_specific:
        values_sql = ", ".join(f"(DATE '{d.isoformat()}')" for d in dates_list)
        spine_cte = f"""
date_spine AS (
    SELECT dt::date AS dt
    FROM (VALUES {values_sql}) AS t(dt)
)"""
    else:
        range_start = input_start or treatment_start
        range_end = input_end or treatment_end
        spine_cte = f"""
date_spine AS (
    SELECT d::date AS dt
    FROM generate_series(
        to_date('{range_start}', 'DD-MM-YYYY'),
        to_date('{range_end}', 'DD-MM-YYYY'),
        interval '1 day'
    ) AS d
)"""

    coalesce_select = 'COALESCE(a."Итого", 0) AS "Итого"'
    for alias in goal_aliases:
        coalesce_select += f',\n       COALESCE(a."{alias}", 0) AS "{alias}"'

    base_sql = base.rstrip().rstrip(";")
    return f"""
    {base_sql},
{spine_cte},
agg AS (
    SELECT {date_expr} AS dt,
           {pivot_cols}
    FROM oms
    WHERE 1=1
      {goal_filter}
      {date_filter}
    GROUP BY {date_expr}
)
SELECT TO_CHAR(s.dt, 'DD-MM-YYYY') AS "Дата",
       {coalesce_select}
FROM date_spine s
LEFT JOIN agg a ON a.dt = s.dt
ORDER BY s.dt DESC
"""
