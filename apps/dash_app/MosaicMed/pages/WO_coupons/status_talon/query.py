sql_query_status = """ select COALESCE("Цель", 'Итого') AS "Цель",
        count(*) as "Всего",
        sum(case when "Статус" = '3' then 1 else 0 end)  as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
        sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end)  as "Отменен",
        sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
        sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
        sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
        sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
        sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
        sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
        sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12",
        sum(case when "Статус" = '13' then 1 else 0 end) as "13",
        sum(case when "Статус" = '17' then 1 else 0 end) as "17",
        sum(case when "Статус" = '0' then 1 else 0 end)  as "0"
from oms.oms_data
where "Тариф" != '0' 
    and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY ROLLUP("Цель")
"""

sql_query_status_spec = """ select COALESCE("Цель", 'Итого') AS "Цель",
        count(*) as "Всего",
        sum(case when "Статус" = '3' then 1 else 0 end)  as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
        sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end)  as "Отменен",
        sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
        sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
        sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
        sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
        sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
        sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
        sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12",
        sum(case when "Статус" = '13' then 1 else 0 end) as "13",
        sum(case when "Статус" = '17' then 1 else 0 end) as "17",
        sum(case when "Статус" = '0' then 1 else 0 end)  as "0"
from oms.oms_data
where "Тариф" != '0' 
    and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
    and "Врач (Профиль МП)" like :value_spec
GROUP BY ROLLUP("Цель")
"""

sql_query_status_korpus = f"""
select COALESCE("Подразделение", 'Итого') AS "Корпус",
        count(*) as "Всего",
        sum(case when "Статус" = '3' then 1 else 0 end)  as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
        sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end)  as "Отменен",
        sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
        sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
        sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
        sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
        sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
        sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
        sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12",
        sum(case when "Статус" = '13' then 1 else 0 end) as "13",
        sum(case when "Статус" = '17' then 1 else 0 end) as "17",
        sum(case when "Статус" = '0' then 1 else 0 end)  as "0"
from oms.oms_data
where "Тариф" != '0'
    and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
    and "Цель" = :cel
GROUP BY ROLLUP("Корпус")
"""

sql_query_status_spec_korp = """ select COALESCE("Цель", 'Итого') AS "Цель",
        count(*) as "Всего",
        sum(case when "Статус" = '3' then 1 else 0 end)  as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
        sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end)  as "Отменен",
        sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
        sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
        sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
        sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
        sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
        sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
        sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12",
        sum(case when "Статус" = '13' then 1 else 0 end) as "13",
        sum(case when "Статус" = '17' then 1 else 0 end) as "17",
        sum(case when "Статус" = '0' then 1 else 0 end)  as "0"
from oms.oms_data
where "Тариф" != '0' 
    and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
    and "Врач (Профиль МП)" like :value_spec and "Подразделение" = :korp
GROUP BY ROLLUP("Цель")
"""

sql_query_status_korpus_date_fin = """
select COALESCE("Окончание лечения", 'Итого') AS "Окончание лечения",
       count(*) as "Всего",
        sum(case when "Подразделение" = 'ГП №3' then 1 else 0 end)  as "ГП3",
        sum(case when "Подразделение" = 'ГП №11' then 1 else 0 end)  as "ГП11",
        sum(case when "Подразделение" = 'ОАПП №1' then 1 else 0 end)  as "ОАПП1",
        sum(case when "Подразделение" = 'ОАПП №2' then 1 else 0 end)  as "ОАПП2",
        sum(case when "Подразделение" = 'ДП №1' then 1 else 0 end)  as "ДП1",
        sum(case when "Подразделение" = 'ДП №8' then 1 else 0 end)  as "ДП8",
        sum(case when "Подразделение" = 'ДП №8 К7' then 1 else 0 end)  as "ДП8 К7",
        sum(case when "Подразделение" = 'ДП №8 ЦОЗ' then 1 else 0 end)  as "ДП8 ЦОЗ"


from oms.oms_data
where "Тариф" != '0'
    and to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY ROLLUP("Окончание лечения")
order by to_date("Окончание лечения", 'DD-MM-YYYY') DESC
"""


sql_query_cel_dia = """
select COALESCE("Подразделение", 'Итого')                                              AS "Корпус",
       count(*)                                                                        as "Всего",
        sum(case when "Статус" = '3' then 1 else 0 end)  as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
        sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end)  as "Отменен",
        sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
        sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
        sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
        sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
        sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
        sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
        sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12",
        sum(case when "Статус" = '13' then 1 else 0 end) as "13",
        sum(case when "Статус" = '17' then 1 else 0 end) as "17",
        sum(case when "Статус" = '0' then 1 else 0 end)  as "0"
from oms.oms_data
where "Тариф" != '0'
  and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
  and "Цель" like any (:cel)
  and "Диагноз основной (DS1)" like any (:dia)
GROUP BY ROLLUP ("Корпус")
"""


sql_query_patient_dia = """
WITH RankedData AS (
    SELECT
        "ЕНП",
        "Пациент",
        "Дата рождения",
        "Пол",
        "Цель",
        SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) AS "DS1",
        SUBSTRING("Сопутствующий диагноз (DS2)", 1, POSITION(' ' IN "Сопутствующий диагноз (DS2)") - 1) AS "DS2",
        ROW_NUMBER() OVER (PARTITION BY "ЕНП" ORDER BY "ЕНП") AS RowNum
    FROM oms.oms_data
),
FirstData AS (
    SELECT DISTINCT ON ("ЕНП")
        "ЕНП",
        "Пациент",
        "Дата рождения",
        "Пол"
    FROM RankedData
    WHERE RowNum = 1
),
UniqueDiagnoses AS (
    SELECT
        "ЕНП",
        unnest(array["DS1", "DS2"]) AS "Diagnosis"
    FROM RankedData
    WHERE "DS1" IS NOT NULL OR "DS2" IS NOT NULL
),
SortedDiagnoses AS (
    SELECT
        "ЕНП",
        array_agg(DISTINCT "Diagnosis" ORDER BY "Diagnosis") AS "SortedDiagnosisArray"
    FROM UniqueDiagnoses
    GROUP BY "ЕНП"
),
UniqueGoals AS (
    SELECT
        "ЕНП",
        "Цель"
    FROM RankedData
    WHERE "Цель" IS NOT NULL
),
SortedGoals AS (
    SELECT
        "ЕНП",
        array_agg(DISTINCT "Цель" ORDER BY "Цель") AS "SortedGoalArray"
    FROM UniqueGoals
    GROUP BY "ЕНП"
)
SELECT
    f."ЕНП",
    f."Пациент",
    f."Дата рождения",
    f."Пол",
    array_to_string(d."SortedDiagnosisArray", ', ') AS "Диагнозы",
    array_to_string(g."SortedGoalArray", ', ') AS "Цели"
FROM FirstData f
LEFT JOIN SortedDiagnoses d ON f."ЕНП" = d."ЕНП"
LEFT JOIN SortedGoals g ON f."ЕНП" = g."ЕНП"
order by "Пациент"
"""