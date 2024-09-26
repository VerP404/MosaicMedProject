sql_query_people_iszl = """
with nas as (select iszl.people_data."FIO",
                    iszl.people_data."DR",
                    iszl.people_data."ENP",
                    iszl.people_data."LPUUCH",
                    info.area_data."Корпус",
                    info.area_data."Врач",
                    2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
                    case
                        when "FIO" like any
                             (array ['%НА','%на', '%ЫЗЫ', '%ызы', '%а', '%я', '%А', '%Я', '%а ', '%я ', '%А ', '%Я '])
                            then 'ж'
                        when "FIO" like any (array ['%ИЧ','%ич', '%ГЛЫ', '%глы']) then 'м'
                        else 'м' end                         as "пол"

             from iszl.people_data
                      left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"),

     nas_gr as (select *,
                       case
                           when "Возраст" < 18 then '0-17'
                           when "Возраст" >= 18 and "Возраст" <= 55 and пол = 'ж' then '18-55'
                           when "Возраст" >= 18 and "Возраст" <= 60 and пол = 'м' then '18-60'
                           when "Возраст" > 55 and пол = 'ж' then '56+'
                           when "Возраст" > 60 and пол = 'м' then '61+'
                           end as "Группа"
                from nas),

     iszl_nas as (select "Корпус",
                         "LPUUCH",
                         count(*)                                                          as "Всего",
                         sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
                         sum(case when (пол = 'ж' and "Группа" = '18-55') or 
                         (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
                         sum(case when (пол = 'ж' and "Группа" = '56+') or 
                         (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
                         sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
                         sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
                         sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
                         sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
                         sum(case when пол = 'м' then 1 end)                               as "М",
                         sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
                         sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
                         sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
                  from nas_gr
                  group by "Корпус", "LPUUCH")

select iszl_nas."LPUUCH",
       iszl_nas."Всего",
       iszl_nas."0-17",
       iszl_nas."18-55 и 18-60",
       iszl_nas."56+ и 61+",
       iszl_nas."Ж",
       iszl_nas."0-17 ж",
       iszl_nas."18-55 ж",
       iszl_nas."56+ ж",
       iszl_nas."М",
       iszl_nas."0-17 м",
       iszl_nas."18-60 м",
       iszl_nas."61+ м"
from iszl_nas
where "Корпус" = :korp
union all
select 'Итого',
       count(*)                                                          as "Всего",
       sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
       sum(case when (пол = 'ж' and "Группа" = '18-55') or 
       (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
       sum(case when (пол = 'ж' and "Группа" = '56+') or 
       (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
       sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
       sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
       sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
       sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
       sum(case when пол = 'м' then 1 end)                               as "М",
       sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
       sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
       sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
from nas_gr
where "Корпус" = :korp
order by "LPUUCH"
"""

sql_query_people_iszl_all = """
with nas as (select iszl.people_data."FIO",
                    iszl.people_data."DR",
                    iszl.people_data."ENP",
                    iszl.people_data."LPUUCH",
                    info.area_data."Корпус",
                    info.area_data."Врач",
                    EXTRACT(YEAR FROM CURRENT_DATE) - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
                    case
                        when "FIO" like any
                             (array ['%НА','%на', '%ЫЗЫ', '%ызы', '%а', '%я', '%А', '%Я', '%а ', '%я ', '%А ', '%Я '])
                            then 'ж'
                        when "FIO" like any (array ['%ИЧ','%ич', '%ГЛЫ', '%глы']) then 'м'
                        else 'м' end                         as "пол"

             from iszl.people_data
                      left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"),
     nas_gr as (select *,
                       case
                           when "Возраст" < 18 then '0-17'
                           when "Возраст" >= 18 and "Возраст" <= 55 and пол = 'ж' then '18-55'
                           when "Возраст" >= 18 and "Возраст" <= 60 and пол = 'м' then '18-60'
                           when "Возраст" > 55 and пол = 'ж' then '56+'
                           when "Возраст" > 60 and пол = 'м' then '61+'
                           end as "Группа"
                from nas),

     iszl_nas as (select "Корпус",
                         sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
                           sum(case when (пол = 'ж' and "Группа" = '18-55') or 
                           (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
                           sum(case when (пол = 'ж' and "Группа" = '56+') or 
                           (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
                         sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
                         sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
                         sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
                         sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
                         sum(case when пол = 'м' then 1 end)                               as "М",
                         sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
                         sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
                         sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м",
                         count(*)                                                          as "Всего"
                  from nas_gr
                  group by "Корпус")

select iszl_nas."Корпус",
       iszl_nas."Всего",
              iszl_nas."0-17",
       iszl_nas."18-55 и 18-60",
       iszl_nas."56+ и 61+",
       iszl_nas."Ж",
       iszl_nas."0-17 ж",
       iszl_nas."18-55 ж",
       iszl_nas."56+ ж",
       iszl_nas."М",
       iszl_nas."0-17 м",
       iszl_nas."18-60 м",
       iszl_nas."61+ м"
from iszl_nas
union all
select ' Итого',
       count(*)                                                          as "Всего",
       sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
       sum(case when (пол = 'ж' and "Группа" = '18-55') or 
       (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
       sum(case when (пол = 'ж' and "Группа" = '56+') or 
       (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
       sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
       sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
       sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
       sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
       sum(case when пол = 'м' then 1 end)                               as "М",
       sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
       sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
       sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
from nas_gr
order by "Корпус"
"""

sql_query_people_iszl_168n = """
with nas as (select iszl.people_data."FIO",
                    iszl.people_data."DR",
                    iszl.people_data."ENP",
                    iszl.people_data."LPUUCH",
                    info.area_data."Корпус",
                    info.area_data."Врач",
                    2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
                    case
                        when "FIO" like any
                             (array ['%НА','%на', '%ЫЗЫ', '%ызы', '%а', '%я', '%А', '%Я', '%а ', '%я ', '%А ', '%Я '])
                            then 'ж'
                        when "FIO" like any (array ['%ИЧ','%ич', '%ГЛЫ', '%глы']) then 'м'
                        else 'м' end                         as "пол"

             from iszl.people_data
                      left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"),

     nas_gr as (select *,
                       case
                           when "Возраст" < 18 then '0-17'
                           when "Возраст" >= 18 and "Возраст" <= 55 and пол = 'ж' then '18-55'
                           when "Возраст" >= 18 and "Возраст" <= 60 and пол = 'м' then '18-60'
                           when "Возраст" > 55 and пол = 'ж' then '56+'
                           when "Возраст" > 60 and пол = 'м' then '61+'
                           end as "Группа"
                from nas),

     iszl_nas as (select "Корпус",
                         "LPUUCH",
                         count(*)                                                          as "Всего",
                         sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
                         sum(case when (пол = 'ж' and "Группа" = '18-55') or 
                         (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
                         sum(case when (пол = 'ж' and "Группа" = '56+') or 
                         (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
                         sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
                         sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
                         sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
                         sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
                         sum(case when пол = 'м' then 1 end)                               as "М",
                         sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
                         sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
                         sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
                  from nas_gr
                  where nas_gr."ENP" in (select distinct "ENP"
                     from iszl.iszl_data
                              left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                                        on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
                     where "Код МКБ" is not null)
                  group by "Корпус", "LPUUCH")

select iszl_nas."LPUUCH",
       iszl_nas."Всего",
       iszl_nas."0-17",
       iszl_nas."18-55 и 18-60",
       iszl_nas."56+ и 61+",
       iszl_nas."Ж",
       iszl_nas."0-17 ж",
       iszl_nas."18-55 ж",
       iszl_nas."56+ ж",
       iszl_nas."М",
       iszl_nas."0-17 м",
       iszl_nas."18-60 м",
       iszl_nas."61+ м"
from iszl_nas
where "Корпус" = :korp
union all
select 'Итого',
       count(*)                                                          as "Всего",
       sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
       sum(case when (пол = 'ж' and "Группа" = '18-55') or 
       (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
       sum(case when (пол = 'ж' and "Группа" = '56+') or 
       (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
       sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
       sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
       sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
       sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
       sum(case when пол = 'м' then 1 end)                               as "М",
       sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
       sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
       sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
from nas_gr

where "Корпус" = :korp
and nas_gr."ENP" in (select distinct "ENP"
     from iszl.iszl_data
              left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                        on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
     where "Код МКБ" is not null)
order by "LPUUCH"
"""

sql_query_people_iszl_all_168n = """
with nas as (select iszl.people_data."FIO",
                    iszl.people_data."DR",
                    iszl.people_data."ENP",
                    iszl.people_data."LPUUCH",
                    info.area_data."Корпус",
                    info.area_data."Врач",
                    EXTRACT(YEAR FROM CURRENT_DATE) - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
                    case
                        when "FIO" like any
                             (array ['%НА','%на', '%ЫЗЫ', '%ызы', '%а', '%я', '%А', '%Я', '%а ', '%я ', '%А ', '%Я '])
                            then 'ж'
                        when "FIO" like any (array ['%ИЧ','%ич', '%ГЛЫ', '%глы']) then 'м'
                        else 'м' end                         as "пол"

             from iszl.people_data
                      left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"),
     nas_gr as (select *,
                       case
                           when "Возраст" < 18 then '0-17'
                           when "Возраст" >= 18 and "Возраст" <= 55 and пол = 'ж' then '18-55'
                           when "Возраст" >= 18 and "Возраст" <= 60 and пол = 'м' then '18-60'
                           when "Возраст" > 55 and пол = 'ж' then '56+'
                           when "Возраст" > 60 and пол = 'м' then '61+'
                           end as "Группа"
                from nas),

     iszl_nas as (select "Корпус",
                         sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
                           sum(case when (пол = 'ж' and "Группа" = '18-55') or 
                           (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
                           sum(case when (пол = 'ж' and "Группа" = '56+') or 
                           (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
                         sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
                         sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
                         sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
                         sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
                         sum(case when пол = 'м' then 1 end)                               as "М",
                         sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
                         sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
                         sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м",
                         count(*)                                                          as "Всего"
                  from nas_gr
                  where nas_gr."ENP" in (select distinct "ENP"
                     from iszl.iszl_data
                              left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                                        on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
                     where "Код МКБ" is not null)
                  group by "Корпус")

select iszl_nas."Корпус",
       iszl_nas."Всего",
              iszl_nas."0-17",
       iszl_nas."18-55 и 18-60",
       iszl_nas."56+ и 61+",
       iszl_nas."Ж",
       iszl_nas."0-17 ж",
       iszl_nas."18-55 ж",
       iszl_nas."56+ ж",
       iszl_nas."М",
       iszl_nas."0-17 м",
       iszl_nas."18-60 м",
       iszl_nas."61+ м"
from iszl_nas
union all
select ' Итого',
       count(*)                                                          as "Всего",
       sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
       sum(case when (пол = 'ж' and "Группа" = '18-55') or 
       (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
       sum(case when (пол = 'ж' and "Группа" = '56+') or 
       (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
       sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
       sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
       sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
       sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
       sum(case when пол = 'м' then 1 end)                               as "М",
       sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
       sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
       sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
from nas_gr
where nas_gr."ENP" in (select distinct "ENP"
     from iszl.iszl_data
              left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                        on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
     where "Код МКБ" is not null)
order by "Корпус"
"""

sql_query_people_iszl_168n_oms = """
with nas as (select iszl.people_data."FIO",
                    iszl.people_data."DR",
                    iszl.people_data."ENP",
                    iszl.people_data."LPUUCH",
                    info.area_data."Корпус",
                    info.area_data."Врач",
                    2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
                    case
                        when "FIO" like any
                             (array ['%НА','%на', '%ЫЗЫ', '%ызы', '%а', '%я', '%А', '%Я', '%а ', '%я ', '%А ', '%Я '])
                            then 'ж'
                        when "FIO" like any (array ['%ИЧ','%ич', '%ГЛЫ', '%глы']) then 'м'
                        else 'м' end                         as "пол"

             from iszl.people_data
                      left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"),

     nas_gr as (select *,
                       case
                           when "Возраст" < 18 then '0-17'
                           when "Возраст" >= 18 and "Возраст" <= 55 and пол = 'ж' then '18-55'
                           when "Возраст" >= 18 and "Возраст" <= 60 and пол = 'м' then '18-60'
                           when "Возраст" > 55 and пол = 'ж' then '56+'
                           when "Возраст" > 60 and пол = 'м' then '61+'
                           end as "Группа"
                from nas),

     iszl_nas as (select "Корпус",
                         "LPUUCH",
                         count(*)                                                          as "Всего",
                         sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
                         sum(case when (пол = 'ж' and "Группа" = '18-55') or 
                         (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
                         sum(case when (пол = 'ж' and "Группа" = '56+') or 
                         (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
                         sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
                         sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
                         sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
                         sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
                         sum(case when пол = 'м' then 1 end)                               as "М",
                         sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
                         sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
                         sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
                  from nas_gr
                  where nas_gr."ENP" in (select distinct "ENP"
                     from iszl.iszl_data
                              left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                                        on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
                     where "Код МКБ" is not null)
                     and nas_gr."ENP" in (select distinct "ЕНП"
                       from oms.oms_data
                       where "Цель" = '3'
                         and "Статус" in ('1', '2', '3', '6', '8'))
                  group by "Корпус", "LPUUCH")

select iszl_nas."LPUUCH",
       iszl_nas."Всего",
       iszl_nas."0-17",
       iszl_nas."18-55 и 18-60",
       iszl_nas."56+ и 61+",
       iszl_nas."Ж",
       iszl_nas."0-17 ж",
       iszl_nas."18-55 ж",
       iszl_nas."56+ ж",
       iszl_nas."М",
       iszl_nas."0-17 м",
       iszl_nas."18-60 м",
       iszl_nas."61+ м"
from iszl_nas
where "Корпус" = :korp
union all
select 'Итого',
       count(*)                                                          as "Всего",
       sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
       sum(case when (пол = 'ж' and "Группа" = '18-55') or 
       (пол = 'м' and "Группа" = '18-60') then 1 else 0 end)             as "18-55 и 18-60",
       sum(case when (пол = 'ж' and "Группа" = '56+') or 
       (пол = 'м' and "Группа" = '61+') then 1 else 0 end)               as "56+ и 61+",
       sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
       sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
       sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
       sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
       sum(case when пол = 'м' then 1 end)                               as "М",
       sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
       sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
       sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
from nas_gr

where "Корпус" = :korp
and nas_gr."ENP" in (select distinct "ENP"
     from iszl.iszl_data
              left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                        on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
     where "Код МКБ" is not null)
     and nas_gr."ENP" in (select distinct "ЕНП"
                       from oms.oms_data
                       where "Цель" = '3'
                         and "Статус" in ('1', '2', '3', '6', '8'))
order by "LPUUCH"
"""

sql_query_people_iszl_all_168n_oms = """
with nas as (select iszl.people_data."FIO",
                    iszl.people_data."DR",
                    iszl.people_data."ENP",
                    iszl.people_data."LPUUCH",
                    info.area_data."Корпус",
                    info.area_data."Врач",
                    EXTRACT(YEAR FROM CURRENT_DATE) -
                    CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
                    case
                        when "FIO" like any
                             (array ['%НА','%на', '%ЫЗЫ', '%ызы', '%а', '%я', '%А', '%Я', '%а ', '%я ', '%А ', '%Я '])
                            then 'ж'
                        when "FIO" like any (array ['%ИЧ','%ич', '%ГЛЫ', '%глы']) then 'м'
                        else 'м' end                                       as "пол"

             from iszl.people_data
                      left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"),
     nas_gr as (select *,
                       case
                           when "Возраст" < 18 then '0-17'
                           when "Возраст" >= 18 and "Возраст" <= 55 and пол = 'ж' then '18-55'
                           when "Возраст" >= 18 and "Возраст" <= 60 and пол = 'м' then '18-60'
                           when "Возраст" > 55 and пол = 'ж' then '56+'
                           when "Возраст" > 60 and пол = 'м' then '61+'
                           end as "Группа"
                from nas),
     iszl_nas as (select "Корпус",
                         sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
                         sum(case
                                 when (пол = 'ж' and "Группа" = '18-55') or
                                      (пол = 'м' and "Группа" = '18-60') then 1
                                 else 0 end)                                               as "18-55 и 18-60",
                         sum(case
                                 when (пол = 'ж' and "Группа" = '56+') or
                                      (пол = 'м' and "Группа" = '61+') then 1
                                 else 0 end)                                               as "56+ и 61+",
                         sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
                         sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
                         sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
                         sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
                         sum(case when пол = 'м' then 1 end)                               as "М",
                         sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
                         sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
                         sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м",
                         count(*)                                                          as "Всего"
                  from nas_gr
                  where nas_gr."ENP" in (select distinct "ENP"
                                         from iszl.iszl_data
                                                  left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                                                            on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
                                         where "Код МКБ" is not null)
                    and nas_gr."ENP" in (select distinct "ЕНП"
                                         from oms.oms_data
                                         where "Цель" = '3'
                                           and "Статус" in ('1', '2', '3', '6', '8'))
                  group by "Корпус")

select iszl_nas."Корпус",
       iszl_nas."Всего",
       iszl_nas."0-17",
       iszl_nas."18-55 и 18-60",
       iszl_nas."56+ и 61+",
       iszl_nas."Ж",
       iszl_nas."0-17 ж",
       iszl_nas."18-55 ж",
       iszl_nas."56+ ж",
       iszl_nas."М",
       iszl_nas."0-17 м",
       iszl_nas."18-60 м",
       iszl_nas."61+ м"
from iszl_nas
union all
select ' Итого',
       count(*)                                                          as "Всего",
       sum(case when "Группа" = '0-17' then 1 else 0 end)                as "0-17",
       sum(case
               when (пол = 'ж' and "Группа" = '18-55') or
                    (пол = 'м' and "Группа" = '18-60') then 1
               else 0 end)                                               as "18-55 и 18-60",
       sum(case
               when (пол = 'ж' and "Группа" = '56+') or
                    (пол = 'м' and "Группа" = '61+') then 1
               else 0 end)                                               as "56+ и 61+",
       sum(case when пол = 'ж' then 1 else 0 end)                        as "Ж",
       sum(case when пол = 'ж' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 ж",
       sum(case when пол = 'ж' and "Группа" = '18-55' then 1 else 0 end) as "18-55 ж",
       sum(case when пол = 'ж' and "Группа" = '56+' then 1 else 0 end)   as "56+ ж",
       sum(case when пол = 'м' then 1 end)                               as "М",
       sum(case when пол = 'м' and "Группа" = '0-17' then 1 else 0 end)  as "0-17 м",
       sum(case when пол = 'м' and "Группа" = '18-60' then 1 else 0 end) as "18-60 м",
       sum(case when пол = 'м' and "Группа" = '61+' then 1 else 0 end)   as "61+ м"
from nas_gr
where nas_gr."ENP" in (select distinct "ENP"
                       from iszl.iszl_data
                                left join (select distinct "Код МКБ" from info.dn168n_data) as dia_pr168
                                          on iszl.iszl_data."DS" = dia_pr168."Код МКБ"
                       where "Код МКБ" is not null)
  and nas_gr."ENP" in (select distinct "ЕНП"
                       from oms.oms_data
                       where "Цель" = '3'
                         and "Статус" in ('1', '2', '3', '6', '8'))
order by "Корпус"
"""
