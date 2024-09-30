# Список талонов по БСК для блокировки по причине "Проведено ДН по БСК более 1 раза в году"
sql_query_list_patients = """
select "К-во ЕНП" as "К-во талонов",
       "Талон",
       "Статус",
       "Цель",
       "Пациент",
       "ЕНП",
       "Врач",
       "Подразделение",
        SUBSTRING("Диагноз основной (DS1)", 1,
           POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
        "Первоначальная дата ввода" as "Дата ввода"
from (
SELECT COUNT("Полис") OVER (PARTITION BY "Полис") AS "К-во ЕНП",
       *
    FROM oms.oms_data
    WHERE "Цель" = '3'
    and "Диагноз основной (DS1)" like 'I%'
    and "Статус" in ('1', '2', '3', '6', '8')) as oms
where "К-во ЕНП" > 1
and "Статус" in ('1', '6', '8')
and "Диагноз основной (DS1)" like 'I%'
"""


sql_query_list_patients_svod = """
with dat as (select "К-во ЕНП" as "К-во талонов",
       "Талон",
       "Статус",
       "Цель",
       "Пациент",
       "ЕНП",
       "Врач",
       "Подразделение",
        SUBSTRING("Диагноз основной (DS1)", 1,
           POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
        "Первоначальная дата ввода" as "Дата ввода"
from (
SELECT COUNT("Полис") OVER (PARTITION BY "Полис") AS "К-во ЕНП",
       *
    FROM oms.oms_data
    WHERE "Цель" = '3'
    and "Диагноз основной (DS1)" like 'I%'
    and "Статус" in ('1', '2', '3', '6', '8')) as oms
where "К-во ЕНП" > 1
and "Статус" in ('1', '6', '8')
and "Диагноз основной (DS1)" like 'I%')

select "Дата ввода",
       sum(case when "Подразделение" = 'ГП №11' then 1 else 0 end ) as "ГП11",
       sum(case when "Подразделение" = 'ГП №3' then 1 else 0 end ) as "ГП3",
       sum(case when "Подразделение" = 'ОАПП №1' then 1 else 0 end ) as "ОАПП1",
       sum(case when "Подразделение" = 'ОАПП №2' then 1 else 0 end ) as "ОАПП2",
       count(*) as "Всего"
from dat
group by "Дата ввода"
order by "Дата ввода"
"""



