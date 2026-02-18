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
):
    """
    Талоны по датам: группировка по дате формирования или дате окончания лечения.
    Столбцы: Дата, Итого, затем все доступные цели (динамически, как в economist/doctors).
    """
    from apps.analytical_app.pages.SQL_query.query import base_query

    if not months_placeholder or months_placeholder.strip() == "":
        months_placeholder = ", ".join(map(str, range(1, 13)))

    input_start = input_start if report_type == "initial_input" else None
    input_end = input_end if report_type == "initial_input" else None
    treatment_start = treatment_start if report_type == "treatment" else None
    treatment_end = treatment_end if report_type == "treatment" else None

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

    if not goals:
        return f"""
        {base}
        SELECT {date_char} AS "Дата", 0 AS "Итого"
        FROM oms
        WHERE 1=0
        GROUP BY {date_expr}
        """

    quoted_goals = ", ".join(f"'{g.replace(chr(39), chr(39) + chr(39))}'" for g in goals)
    goal_filter = f"AND goal IN ({quoted_goals})"

    goal_exprs = []
    for g in goals:
        safe_g = g.replace('"', '""')
        esc = g.replace("'", "''")
        goal_exprs.append(f"COUNT(*) FILTER (WHERE goal = '{esc}') AS \"{safe_g}\"")

    sum_parts = [expr.split(" AS ")[0] for expr in goal_exprs]
    total_expr = "(" + " + ".join(sum_parts) + ") AS \"Итого\""
    # Порядок: Дата, Итого, затем все цели
    pivot_cols = total_expr + ",\n       " + ",\n       ".join(goal_exprs)
    having_expr = " + ".join(sum_parts) + " > 0"

    return f"""
    {base}
SELECT {date_char} AS "Дата",
       {pivot_cols}
FROM oms
WHERE 1=1
  {goal_filter}
GROUP BY {date_expr}
HAVING ({having_expr})
ORDER BY {date_expr} DESC
"""