sql_query_sharapova = """
with sharapova as (select CASE
           WHEN GROUPING("Подразделение") = 1 THEN 'Итого'
           ELSE "Подразделение"
           END                                                                                       AS "Подразделение",
       sum(case when "Диагноз основной (DS1)" like 'I%' then 1 else 0 end)                             as "БСК",
       sum(case when "Диагноз основной (DS1)" like any (array ['I%', 'C%', 'J44%']) then 0 else 1 end) as "Другая",
       sum(case when "Диагноз основной (DS1)" like 'C%' then 1 else 0 end)                             as "Онко",
       sum(case when "Диагноз основной (DS1)" like 'J44%' then 1 else 0 end)                           as "Хобл",
       sum(case when "Диагноз основной (DS1)" like any (array ['E10%', 'E11%']) then 1 else 0 end)     as "СД",
       count(*) AS "Итого",
       CASE WHEN GROUPING("Подразделение") = 1 THEN 1 ELSE 0 END                                       AS is_total
from oms.oms_data
where "Цель" = '3'
  AND "Подразделение" NOT LIKE '%ДП%'
 and to_date(oms.oms_data."Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
group by
    rollup ("Подразделение")
order by is_total, "Подразделение")

select "Подразделение", "БСК", "Другая", "Онко", "Хобл", "СД", "Итого"
from sharapova
"""