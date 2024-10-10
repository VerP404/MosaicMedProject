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
        SELECT SUM(CASE WHEN department NOT LIKE '%ДП%' THEN 1 ELSE 0 END) as все_талоны,
               SUM(CASE WHEN goal IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',
                 '307', '64', '640', '32') THEN CAST(visits AS numeric(8)) ELSE 0 END) as pos,
               SUM(CASE WHEN goal IN ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2') THEN 1 ELSE 0 END) as dd,
               SUM(CASE WHEN goal = 'В дневном стационаре' THEN CAST(visits AS numeric(8)) ELSE 0 END) as stac,
               COUNT(DISTINCT policy) as Уникальные
        FROM data_loader_omsdata
        WHERE to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          AND department NOT LIKE '%ДП%'
    ) as tab1

    UNION ALL

    SELECT 'Дети' as Тип,
           все_талоны,
           pn + pos - stac as "Количество посещений",
           Уникальные_дети as "Уникальные пациенты"
    FROM (
        SELECT SUM(CASE WHEN department LIKE '%ДП%' THEN 1 ELSE 0 END) as все_талоны,
               SUM(CASE WHEN goal IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',
                 '307', '64', '640', '32') THEN CAST(visits AS numeric(8)) ELSE 0 END) as pos,
               SUM(CASE WHEN goal IN ('ПН1', 'ДС2') THEN 1 ELSE 0 END) as pn,
               SUM(CASE WHEN goal = 'В дневном стационаре' THEN CAST(visits AS numeric(8)) ELSE 0 END) as stac,
               COUNT(DISTINCT policy) as Уникальные_дети
        FROM data_loader_omsdata
        WHERE to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          AND department LIKE '%ДП%'
    ) as tab2
) as result
GROUP BY rollup(Тип)
"""
sql_query_visits_korpus = """
select department as Тип,
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    from (select department,
                    count(*)                    as все_талоны,
                 sum(case when goal in ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',  
                 '307', '64', '640', '32') then CAST(visits AS numeric(8)) else 0 end) as pos,
                 sum(case when goal = 'ДВ4' or goal = 'ДВ2' or goal = 'ОПВ' or goal = 'УД1' or goal = 'УД2' or goal = 'ПН1' or goal = 'ДС2' then 1 else 0 end) as dd,
                 sum(case when goal = 'В дневном стационаре' then CAST(visits AS numeric(8)) else 0 end)          as stac,
                 COUNT(DISTINCT policy)                                                             as Уникальные
          from data_loader_omsdata
          where
            to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          GROUP BY ROLLUP(department)) as tab
"""

sql_query_visits_korpus_spec = r"""
select department,
            case 
            WHEN doctor_profile ~ '\(.*\)' THEN
                substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
            ELSE
                doctor_profile
            END                                                                        AS "Профиль",
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    from (select department,
                doctor_profile,
                    count(*)                    as все_талоны,
                 sum(case when goal in ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '301', '305',  
                 '307', '64', '640', '32') then CAST(visits AS numeric(8)) else 0 end) as pos,                                                                  
                 sum(case when goal = 'ДВ4' or goal = 'ДВ2' or goal = 'ОПВ' or goal = 'УД1' or goal = 'УД2' or goal = 'ПН1' or goal = 'ДС2' then 1 else 0 end) as dd,
                 sum(case when goal = 'В дневном стационаре' then CAST(visits AS numeric(8)) else 0 end)          as stac,
                 COUNT(DISTINCT policy)                                                             as Уникальные
          from data_loader_omsdata
          where
            to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          GROUP BY ROLLUP(department, doctor_profile)) as tab
"""

sql_query_visits_pos_home = f"""
select department,
                     SUM(CASE
             WHEN home_visits ~ '^-?[0-9]+$'
             THEN CAST(home_visits AS numeric(8))
             ELSE 0
           END) AS "Количество"
from data_loader_omsdata
where to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY ROLLUP(department)
"""