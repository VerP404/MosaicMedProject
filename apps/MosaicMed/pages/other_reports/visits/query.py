# Отчет по посещениям
sql_query_visits = """
SELECT Тип,
       SUM("Количество талонов") as "Общее количество талонов",
       SUM("Количество посещений") as "Общее количество посещений",
       SUM("Уникальные пациенты") as "Общее количество уникальных пациентов"
FROM (
    SELECT 'Взрослые' as Тип,
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    FROM (
        SELECT SUM(CASE WHEN "Подразделение" NOT LIKE '%ДП%' THEN 1 ELSE 0 END) as все_талоны,
               SUM(CASE WHEN "Цель" IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',
                 '307', '64', '640', '32') THEN CAST("Посещения" AS numeric(8)) ELSE 0 END) as pos,
               SUM(CASE WHEN "Цель" IN ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2') THEN 1 ELSE 0 END) as dd,
               SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN CAST("Посещения" AS numeric(8)) ELSE 0 END) as stac,
               COUNT(DISTINCT "Полис") as Уникальные
        FROM oms.oms_data
        WHERE to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          AND "Подразделение" NOT LIKE '%ДП%'
    ) as tab1

    UNION ALL

    SELECT 'Дети' as Тип,
           все_талоны,
           pn + pos - stac as "Количество посещений",
           Уникальные_дети as "Уникальные пациенты"
    FROM (
        SELECT SUM(CASE WHEN "Подразделение" LIKE '%ДП%' THEN 1 ELSE 0 END) as все_талоны,
               SUM(CASE WHEN "Цель" IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',
                 '307', '64', '640', '32') THEN CAST("Посещения" AS numeric(8)) ELSE 0 END) as pos,
               SUM(CASE WHEN "Цель" IN ('ПН1', 'ДС2') THEN 1 ELSE 0 END) as pn,
               SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN CAST("Посещения" AS numeric(8)) ELSE 0 END) as stac,
               COUNT(DISTINCT "Полис") as Уникальные_дети
        FROM oms.oms_data
        WHERE to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          AND "Подразделение" LIKE '%ДП%'
    ) as tab2
) as result
GROUP BY rollup(Тип)
"""
sql_query_visits_korpus = """
select "Подразделение" as Тип,
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    from (select "Подразделение",
                    count(*)                    as все_талоны,
                 sum(case when "Цель" in ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',  
                 '307', '64', '640', '32') then CAST("Посещения" AS numeric(8)) else 0 end) as pos,
                 sum(case when "Цель" = 'ДВ4' or "Цель" = 'ДВ2' or"Цель" = 'ОПВ' or "Цель" = 'УД1' or "Цель" = 'УД2' or "Цель" = 'ПН1' or "Цель" = 'ДС2' then 1 else 0 end) as dd,
                 sum(case when "Цель" = 'В дневном стационаре' then CAST("Посещения" AS numeric(8)) else 0 end)          as stac,
                 COUNT(DISTINCT "Полис")                                                             as Уникальные
          from oms.oms_data
          where
            to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          GROUP BY ROLLUP("Подразделение")) as tab
"""

sql_query_visits_korpus_spec = r"""
select "Подразделение",
            case 
            WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
            ELSE
                "Врач (Профиль МП)"
            END                                                                        AS "Профиль",
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    from (select "Подразделение",
                "Врач (Профиль МП)",
                    count(*)                    as все_талоны,
                 sum(case when "Цель" in ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',  
                 '307', '64', '640', '32') then CAST("Посещения" AS numeric(8)) else 0 end) as pos,                                                                  
                 sum(case when "Цель" = 'ДВ4' or "Цель" = 'ДВ2' or"Цель" = 'ОПВ' or "Цель" = 'УД1' or "Цель" = 'УД2' or "Цель" = 'ПН1' or "Цель" = 'ДС2' then 1 else 0 end) as dd,
                 sum(case when "Цель" = 'В дневном стационаре' then CAST("Посещения" AS numeric(8)) else 0 end)          as stac,
                 COUNT(DISTINCT "Полис")                                                             as Уникальные
          from oms.oms_data
          where
            to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          GROUP BY ROLLUP("Подразделение", "Врач (Профиль МП)")) as tab
"""

sql_query_visits_pos_home ="""
select "Подразделение",
       sum(CAST("Посещения на Дому" AS numeric(8))) as "Количество"
from oms.oms_data
where to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY ROLLUP("Подразделение")
"""