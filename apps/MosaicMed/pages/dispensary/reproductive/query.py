sqlquery_people_reproductive = """
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
                      left join info.area_data on people_data."LPUUCH" = info.area_data."Участок"),

     nas_gr as (select *,
                       case
                           when "Возраст" >= 18 and "Возраст" <= 29 then '18-29'
                           when "Возраст" >= 30 and "Возраст" <= 49 then '30-49'
                           else '-'
                           end as "Группа"
                from nas),

     iszl_nas as (select "Корпус",
                         "LPUUCH",
                         count(*)                                                            as "Всего",
                         sum(case when пол = 'ж' then 1 else 0 end)                          as "ж",
                         sum(case when пол = 'м' then 1 else 0 end)                          as "м",
                         sum(case when "Группа" = '18-29' then 1 else 0 end)                 as "18-29",
                         sum(case when (пол = 'ж' and "Группа" = '18-29') then 1 else 0 end) as "18-29 ж",
                         sum(case when (пол = 'м' and "Группа" = '18-29') then 1 else 0 end) as "18-29 м",
                         sum(case when "Группа" = '30-49' then 1 else 0 end)                 as "30-49",
                         sum(case when (пол = 'ж' and "Группа" = '30-49') then 1 else 0 end) as "30-49 ж",
                         sum(case when (пол = 'м' and "Группа" = '30-49') then 1 else 0 end) as "30-49 м"

                  from nas_gr
                  where "Группа" in ('18-29', '30-49')
                  group by "Корпус", "LPUUCH")

select iszl_nas."LPUUCH",
       iszl_nas."Всего",
       iszl_nas."ж",
       iszl_nas."м",
       iszl_nas."18-29",
       iszl_nas."18-29 ж",
       iszl_nas."18-29 м",
       iszl_nas."30-49",
       iszl_nas."30-49 ж",
       iszl_nas."30-49 м"
from iszl_nas
where "Корпус" = :korp
union all
select 'Итого',
       count(*)                                                            as "Всего",
       sum(case when пол = 'ж' then 1 else 0 end)                          as "ж",
       sum(case when пол = 'м' then 1 else 0 end)                          as "м",
       sum(case when "Группа" = '18-29' then 1 else 0 end)                 as "18-29",
       sum(case when (пол = 'ж' and "Группа" = '18-29') then 1 else 0 end) as "18-29 ж",
       sum(case when (пол = 'м' and "Группа" = '18-29') then 1 else 0 end) as "18-29 м",
       sum(case when "Группа" = '30-49' then 1 else 0 end)                 as "30-49",
       sum(case when (пол = 'ж' and "Группа" = '30-49') then 1 else 0 end) as "30-49 ж",
       sum(case when (пол = 'м' and "Группа" = '30-49') then 1 else 0 end) as "30-49 м"
from nas_gr
where "Корпус" = :korp and "Группа" in ('18-29', '30-49')
order by "LPUUCH"
"""

def sqlquery_people_reproductive_all():
    return f"""
    WITH nas AS (
        SELECT 
            iszl.people_data."FIO",
            iszl.people_data."DR",
            iszl.people_data."ENP",
            iszl.people_data."LPUUCH",
            info.area_data."Корпус",
            info.area_data."Врач",
            EXTRACT(YEAR FROM CURRENT_DATE) - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
            CASE
                WHEN "FIO" LIKE ANY (ARRAY['%%НА', '%%на', '%%ЫЗЫ', '%%ызы', '%%а', '%%я', '%%А', '%%Я', '%%а ', '%%я ', '%%А ', '%%Я '])
                    THEN 'ж'
                WHEN "FIO" LIKE ANY (ARRAY['%%ИЧ', '%%ич', '%%ГЛЫ', '%%глы'])
                    THEN 'м'
                ELSE 'м'
            END AS "пол"
        FROM iszl.people_data
        LEFT JOIN info.area_data ON iszl.people_data."LPUUCH" = info.area_data."Участок"
    ),
    nas_gr AS (
        SELECT *,
            CASE
                WHEN "Возраст" >= 18 AND "Возраст" <= 29 THEN '18-29'
                WHEN "Возраст" >= 30 AND "Возраст" <= 49 THEN '30-49'
                ELSE '-'
            END AS "Группа"
        FROM nas
    ),
    iszl_nas AS (
        SELECT "Корпус",
            COUNT(*) AS "Всего",
            SUM(CASE WHEN пол = 'ж' THEN 1 ELSE 0 END) AS "ж",
            SUM(CASE WHEN пол = 'м' THEN 1 ELSE 0 END) AS "м",
            SUM(CASE WHEN "Группа" = '18-29' THEN 1 ELSE 0 END) AS "18-29",
            SUM(CASE WHEN (пол = 'ж' AND "Группа" = '18-29') THEN 1 ELSE 0 END) AS "18-29 ж",
            SUM(CASE WHEN (пол = 'м' AND "Группа" = '18-29') THEN 1 ELSE 0 END) AS "18-29 м",
            SUM(CASE WHEN "Группа" = '30-49' THEN 1 ELSE 0 END) AS "30-49",
            SUM(CASE WHEN (пол = 'ж' AND "Группа" = '30-49') THEN 1 ELSE 0 END) AS "30-49 ж",
            SUM(CASE WHEN (пол = 'м' AND "Группа" = '30-49') THEN 1 ELSE 0 END) AS "30-49 м"
        FROM nas_gr
        WHERE "Группа" IN ('18-29', '30-49')
        GROUP BY "Корпус"
    )
    SELECT 
        iszl_nas."Корпус",
        iszl_nas."Всего",
        iszl_nas."ж",
        iszl_nas."м",
        iszl_nas."18-29",
        iszl_nas."18-29 ж",
        iszl_nas."18-29 м",
        iszl_nas."30-49",
        iszl_nas."30-49 ж",
        iszl_nas."30-49 м"
    FROM iszl_nas
    UNION ALL
    SELECT 
        'Итого',
        COUNT(*) AS "Всего",
        SUM(CASE WHEN пол = 'ж' THEN 1 ELSE 0 END) AS "ж",
        SUM(CASE WHEN пол = 'м' THEN 1 ELSE 0 END) AS "м",
        SUM(CASE WHEN "Группа" = '18-29' THEN 1 ELSE 0 END) AS "18-29",
        SUM(CASE WHEN (пол = 'ж' AND "Группа" = '18-29') THEN 1 ELSE 0 END) AS "18-29 ж",
        SUM(CASE WHEN (пол = 'м' AND "Группа" = '18-29') THEN 1 ELSE 0 END) AS "18-29 м",
        SUM(CASE WHEN "Группа" = '30-49' THEN 1 ELSE 0 END) AS "30-49",
        SUM(CASE WHEN (пол = 'ж' AND "Группа" = '30-49') THEN 1 ELSE 0 END) AS "30-49 ж",
        SUM(CASE WHEN (пол = 'м' AND "Группа" = '30-49') THEN 1 ELSE 0 END) AS "30-49 м"
    FROM nas_gr
    WHERE "Группа" IN ('18-29', '30-49')
    """



def sqlquery_people_reproductive_tab2(sql_cond):
    return f"""
        select
               COALESCE("Подразделение", 'Итого') AS "Подразделение",
               sum(case when "Статус" in ('1', '2', '3', '4', '5', '6', '7', '8', '12') then 1 else 0 end)         as "Всего",
               sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end)                   as "В работе",
               sum(case when "Статус" = '3' then 1 else 0 end)                                  as Оплачено,
               sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)                  as "В ТФОМС",
               sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end) as "Отказано",
               sum(case when "Статус" = '6' or "Статус" = '8' then 1 else 0 end)                  as "Исправлен",
               sum(case when "Статус" = '1' then 1 else 0 end)                                  as "1",
               sum(case when "Статус" = '2' then 1 else 0 end)                                  as "2",
               sum(case when "Статус" = '3' then 1 else 0 end)                                  as "3",
               sum(case when "Статус" = '4' then 1 else 0 end)                                  as "4",
               sum(case when "Статус" = '5' then 1 else 0 end)                                  as "5",
               sum(case when "Статус" = '6' then 1 else 0 end)                                  as "6",
               sum(case when "Статус" = '7' then 1 else 0 end)                                  as "7",
               sum(case when "Статус" = '8' then 1 else 0 end)                                  as "8",
               sum(case when "Статус" = '12' then 1 else 0 end)                                 as "12"
        from oms.oms_data
        where "Цель" = :cel
            and "Тариф" != '0'
            and "Пол" = :text_1
        AND "Отчетный период выгрузки" IN ({sql_cond})
        GROUP BY ROLLUP("Подразделение")
        """


sqlquery_people_reproductive_tab3 = """
with DR as ( select EXTRACT(YEAR FROM CURRENT_DATE) -
                    CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer) as "Возраст",
    "Талон",
    "Статус",
    "Пациент",
    "Дата рождения",
    "Пол",
    "Цель",
    "ЕНП",
    "Начало лечения",
    "Окончание лечения",
    "Врач",
    "Подразделение",
        SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) AS "DS1",
        SUBSTRING("Сопутствующий диагноз (DS2)", 1, POSITION(' ' IN "Сопутствующий диагноз (DS2)") - 1) AS "DS2"
from oms.oms_data
where "Цель" = 'ДР1'),
    DV_OPV as (
        select EXTRACT(YEAR FROM CURRENT_DATE) -
                    CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer) as "Возраст",
    "Талон",
    "Статус",
    "Пациент",
    "Дата рождения",
    "Пол",
    "Цель",
    "ЕНП",
    "Начало лечения",
    "Окончание лечения",
    "Врач",
    "Подразделение",
        SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) AS "DS1",
        SUBSTRING("Сопутствующий диагноз (DS2)", 1, POSITION(' ' IN "Сопутствующий диагноз (DS2)") - 1) AS "DS2"
from oms.oms_data
where "Цель" in ('ДВ4', 'ОПВ') and "Статус" = '3'
    ),
    itog as (
        select DV_OPV."Пациент",
               DV_OPV."Дата рождения",
               DV_OPV."Возраст",
               DV_OPV."ЕНП",
               DV_OPV."Пол",
               DV_OPV."Цель",
               DV_OPV."Окончание лечения",
               DV_OPV."Врач",
               DV_OPV."Подразделение",
               case when DR."Цель" = 'ДР1' then 'да' else 'нет' end as "Статус ДР",
               DR."DS1"
        from DV_OPV left join DR on DV_OPV."ЕНП" = DR."ЕНП"
    )

select *
from itog
where "Возраст" > 17 and "Возраст" < 50
order by "Пациент"
"""
