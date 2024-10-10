# отчет по диспансеризации
def sql_query_dispensary():
    return """
    SELECT
        coalesce(department, 'Итого')              as Корпус,
        sum(case when goal = 'ДВ4' then 1 else 0 end) as ДВ4,
        sum(case when goal = 'ДВ2' then 1 else 0 end) as ДВ2,
        sum(case when goal = 'ОПВ' then 1 else 0 end) as ОПВ,
        sum(case when goal = 'УД1' then 1 else 0 end) as УД1,
        sum(case when goal = 'УД2' then 1 else 0 end) as УД2
    from data_loader_omsdata
    where to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') 
    and to_date(:end_date, 'DD-MM-YYYY')
      AND department NOT LIKE '%ДП%'
      and department NOT LIKE '%ЖК%'
    group by rollup (department)
"""


def sql_query_do_korpus_dd(sql_cond):
    return f"""
        select COALESCE(department, 'Итого') AS department,
        count(*) as "Всего",
        sum(case when status = '3' then 1 else 0 end)  as Оплачено,
        sum(case when status = '2' or status = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when status = '5' or status = '7' or status = '12' then 1 else 0 end)  as "Отказано",
        sum(case when status = '0' or status = '13' or status = '17' then 1 else 0 end)  as "Отменен",
        sum(case when status = '1' then 1 else 0 end)  as "1",
        sum(case when status = '2' then 1 else 0 end)  as "2",
        sum(case when status = '3' then 1 else 0 end)  as "3",
        sum(case when status = '5' then 1 else 0 end)  as "5",
        sum(case when status = '6' then 1 else 0 end)  as "6",
        sum(case when status = '7' then 1 else 0 end)  as "7",
        sum(case when status = '8' then 1 else 0 end)  as "8",
        sum(case when status = '12' then 1 else 0 end) as "12",
        sum(case when status = '13' then 1 else 0 end) as "13",
        sum(case when status = '17' then 1 else 0 end) as "17",
        sum(case when status = '0' then 1 else 0 end)  as "0"
from data_loader_omsdata
where goal = :text_1
    and tariff != '0'
and department not like '%ДП%'
AND report_period IN ({sql_cond})
GROUP BY ROLLUP(department)
    """


sql_query_adults_age_dispensary = """
WITH data AS (SELECT 2024 - CAST(substring(birth_date FROM LENGTH(birth_date) - 3) AS integer)                        as Возраст,
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN gender = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN department = 'ГП №3' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                     SUM(CASE WHEN department = 'ГП №3' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                     SUM(CASE WHEN department = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                     SUM(CASE WHEN department = 'ГП №11' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                     SUM(CASE WHEN department = 'ГП №11' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                     SUM(CASE WHEN department = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                     SUM(CASE WHEN department = 'ОАПП №1' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                     SUM(CASE WHEN department = 'ОАПП №1' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                     SUM(CASE WHEN department = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                     SUM(CASE WHEN department = 'ОАПП №2' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                     SUM(CASE WHEN department = 'ОАПП №2' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                     SUM(CASE WHEN department = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
              FROM data_loader_omsdata
              WHERE goal IN ('ДВ4', 'ОПВ')
                and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                AND status IN :status_list
              GROUP BY Возраст)
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
        "Всего",
        "М",
        "Ж",
        "М ГП3",
        "Ж ГП3",
        "ГП3",
        "М ГП11",
        "Ж ГП11",
        "ГП11",
        "М ОАПП1",
        "Ж ОАПП1",
        "ОАПП1",
        "М ОАПП2",
        "Ж ОАПП2",
        "ОАПП2"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
        SUM("М ГП3"),  
        SUM("М ГП3"),  
        SUM("ГП3"),
        SUM("М ГП11"),
        SUM("Ж ГП11"),
        SUM("ГП11"),
        SUM("М ОАПП1"),
        SUM("Ж ОАПП1"),
        SUM("ОАПП1"),
        SUM("М ОАПП2"),
        SUM("Ж ОАПП2"),
        SUM("ОАПП2")
      FROM data) d
"""

sql_query_adults_age_dispensary_dv4 = """
WITH data AS (SELECT 2024 - CAST(substring(birth_date FROM LENGTH(birth_date) - 3) AS integer)                        as Возраст,
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN gender = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN department = 'ГП №3' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                     SUM(CASE WHEN department = 'ГП №3' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                     SUM(CASE WHEN department = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                     SUM(CASE WHEN department = 'ГП №11' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                     SUM(CASE WHEN department = 'ГП №11' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                     SUM(CASE WHEN department = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                     SUM(CASE WHEN department = 'ОАПП №1' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                     SUM(CASE WHEN department = 'ОАПП №1' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                     SUM(CASE WHEN department = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                     SUM(CASE WHEN department = 'ОАПП №2' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                     SUM(CASE WHEN department = 'ОАПП №2' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                     SUM(CASE WHEN department = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
              FROM data_loader_omsdata
              WHERE goal IN ('ДВ4')
                and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                AND status IN :status_list
              GROUP BY Возраст)
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
        "Всего",
        "М",
        "Ж",
        "М ГП3",
        "Ж ГП3",
        "ГП3",
        "М ГП11",
        "Ж ГП11",
        "ГП11",
        "М ОАПП1",
        "Ж ОАПП1",
        "ОАПП1",
        "М ОАПП2",
        "Ж ОАПП2",
        "ОАПП2"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
        SUM("М ГП3"),  
        SUM("М ГП3"),  
        SUM("ГП3"),
        SUM("М ГП11"),
        SUM("Ж ГП11"),
        SUM("ГП11"),
        SUM("М ОАПП1"),
        SUM("Ж ОАПП1"),
        SUM("ОАПП1"),
        SUM("М ОАПП2"),
        SUM("Ж ОАПП2"),
        SUM("ОАПП2")
      FROM data) d
"""


def sql_query_adults_age_dispensary():
    return f"""
            WITH data AS (SELECT 2024 - CAST(substring(birth_date FROM LENGTH(birth_date) - 3) AS integer)                        as Возраст,
                                 COUNT(*)                                                                   AS "Всего",
                                 SUM(CASE WHEN gender = 'М' THEN 1 ELSE 0 END) AS "М",
                                 SUM(CASE WHEN gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                                 SUM(CASE WHEN department = 'ГП №3' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                                 SUM(CASE WHEN department = 'ГП №3' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                                 SUM(CASE WHEN department = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                                 SUM(CASE WHEN department = 'ГП №11' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                                 SUM(CASE WHEN department = 'ГП №11' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                                 SUM(CASE WHEN department = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                                 SUM(CASE WHEN department = 'ОАПП №1' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                                 SUM(CASE WHEN department = 'ОАПП №1' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                                 SUM(CASE WHEN department = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                                 SUM(CASE WHEN department = 'ОАПП №2' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                                 SUM(CASE WHEN department = 'ОАПП №2' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                                 SUM(CASE WHEN department = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
                          FROM data_loader_omsdata
                          WHERE goal IN ('ОПВ', 'ДВ4')
                            and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                            AND status IN :status_list
                          GROUP BY Возраст)
            SELECT CASE
                       WHEN Возраст IS NULL THEN 'Итого'
                       ELSE Возраст::text
                       END AS Возраст,
                    "Всего",
                    "М",
                    "Ж",
                    "М ГП3",
                    "Ж ГП3",
                    "ГП3",
                    "М ГП11",
                    "Ж ГП11",
                    "ГП11",
                    "М ОАПП1",
                    "Ж ОАПП1",
                    "ОАПП1",
                    "М ОАПП2",
                    "Ж ОАПП2",
                    "ОАПП2"
            FROM data
            UNION ALL
            select *
            from (SELECT 'Итого' as Возраст,
                         SUM("Всего"),
                         SUM("М"),
                         SUM("Ж"),
                    SUM("М ГП3"),  
                    SUM("М ГП3"),  
                    SUM("ГП3"),
                    SUM("М ГП11"),
                    SUM("Ж ГП11"),
                    SUM("ГП11"),
                    SUM("М ОАПП1"),
                    SUM("Ж ОАПП1"),
                    SUM("ОАПП1"),
                    SUM("М ОАПП2"),
                    SUM("Ж ОАПП2"),
                    SUM("ОАПП2")
                  FROM data) d
            """


def query_age_dispensary(sql_cond):
    return f"""
    WITH data AS (SELECT 2024 - CAST(substring(birth_date FROM LENGTH(birth_date) - 3) AS integer) as "Возраст",
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN gender = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN department = 'ГП №3' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                     SUM(CASE WHEN department = 'ГП №3' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                     SUM(CASE WHEN department = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                     SUM(CASE WHEN department = 'ГП №11' and gender = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                     SUM(CASE WHEN department = 'ГП №11' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                     SUM(CASE WHEN department = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                     SUM(CASE WHEN department = 'ОАПП №1' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                     SUM(CASE WHEN department = 'ОАПП №1' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                     SUM(CASE WHEN department = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                     SUM(CASE WHEN department = 'ОАПП №2' and gender = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                     SUM(CASE WHEN department = 'ОАПП №2' and gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                     SUM(CASE WHEN department = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
              FROM data_loader_omsdata
              WHERE goal = :cel
                and report_period IN ({sql_cond})
                AND status IN :status_list
                AND tariff != '0'
                and smo_code like '360%'
                AND sanctions != '-'
              GROUP BY "Возраст")
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
        "Всего",
        "М",
        "Ж",
        "М ГП3",
        "Ж ГП3",
        "ГП3",
        "М ГП11",
        "Ж ГП11",
        "ГП11",
        "М ОАПП1",
        "Ж ОАПП1",
        "ОАПП1",
        "М ОАПП2",
        "Ж ОАПП2",
        "ОАПП2"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
        SUM("М ГП3"),  
        SUM("М ГП3"),  
        SUM("ГП3"),
        SUM("М ГП11"),
        SUM("Ж ГП11"),
        SUM("ГП11"),
        SUM("М ОАПП1"),
        SUM("Ж ОАПП1"),
        SUM("ОАПП1"),
        SUM("М ОАПП2"),
        SUM("Ж ОАПП2"),
        SUM("ОАПП2")
      FROM data) d
"""


def query_dv4_price(sql_cond=None):
    return f"""
select department,
       count(*) as "Всего",
       sum(case when CAST(amount AS numeric(15, 2)) < 2000 then 1 else 0 end) as "<2000",
       sum(case when CAST(amount AS numeric(15, 2)) >= 2000 and CAST(amount AS numeric(15, 2)) < 3000 then 1 else 0 end) as "2000-3000",
       sum(case when CAST(amount AS numeric(15, 2)) >= 3000 and CAST(amount AS numeric(15, 2)) < 4000 then 1 else 0 end) as "3000-4000",
       sum(case when CAST(amount AS numeric(15, 2)) >= 4000 and CAST(amount AS numeric(15, 2)) < 5000 then 1 else 0 end) as "4000-5000",
       sum(case when CAST(amount AS numeric(15, 2)) >= 5000  then 1 else 0 end) as ">5000"
from data_loader_omsdata
              WHERE 
              goal = :cel 
              and tariff != '0'
                and smo_code like '360%'
                AND sanctions != '-'
                and report_period IN ({sql_cond})
                AND status IN :status_list
    group by ROLLUP (department)
"""
