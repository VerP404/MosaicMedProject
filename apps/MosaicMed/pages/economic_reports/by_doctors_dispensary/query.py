def sql_query_by_doctor_dispensary_adult_f1(sql_cond):
    return f"""
with oms as (select "Врач",
                    "Врач (Профиль МП)",
                    "Цель",
                    "Пол",
                    "Сумма",
                    "Подразделение",
                    split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
                    '.' || left(split_part("Врач", ' ', 4), 1) || '.' || ' / ' || "Врач (Профиль МП)" as "ВР/проф_омс"
             from oms.oms_data
             where "Отчетный период выгрузки" IN ({sql_cond})
               AND "Статус" IN :status_list
               and "Тип талона" like '%Диспа%'
               and "Подразделение" not like '%ДП%'),
     all_combinations as (SELECT "Подразделение",
                                 "ВР/проф_омс",
                                 unnest(array ['ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2']) as "Цель"
                          FROM oms
                          GROUP BY "Подразделение", "ВР/проф_омс")


SELECT all_combinations."Подразделение",
       all_combinations."ВР/проф_омс" as "Врач / профиль",
       all_combinations."Цель",
       sum(case when "Пол" = 'М' then 1 else 0 end)                                     as "К-во М",
       sum(case when "Пол" = 'Ж' then 1 else 0 end)                                     as "К-во Ж",
       sum(case when "Пол" = 'М' then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма М",
       sum(case when "Пол" = 'Ж' then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма Ж",
       sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end)                             as "К-во",
       sum(case when "Пол" in ('М', 'Ж') then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма"
FROM all_combinations
         LEFT JOIN
     oms
     ON
                 all_combinations."Подразделение" = oms."Подразделение"
             AND all_combinations."ВР/проф_омс" = oms."ВР/проф_омс"
             AND all_combinations."Цель" = oms."Цель"
GROUP BY all_combinations."Подразделение", "Врач / профиль", all_combinations."Цель"
ORDER BY all_combinations."Подразделение", "Врач / профиль"
"""


def sql_query_by_doctor_dispensary_adult_f2(sql_cond):
    return f"""
with detail as (select oms.detail_dd_data."Пол",
                       "Номер талона",
                       "Тип талона",
                       "Доктор (Код)",
                       "Доктор (ФИО)",
                       "Название услуги",
                       "Статус-Услуги",
                       "Доктор-Услуги (Код)",
                       "Доктор-Услуги (ФИО)",
                       oms.doctors_oms_data."Структурное подразделение:" as "Корпус",
                       oms.doctors_oms_data."Код профиля медпомощи:" as "Профиль"
                from oms.detail_dd_data
                         left join oms.doctors_oms_data on oms.detail_dd_data."Доктор (Код)" = oms.doctors_oms_data."Код врача:"
                where  "Статус-Услуги" = 'Да'
                and "Статус" IN :status_list
                and "Тип талона" in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2')),
    oms as (
        select "Талон",
               "Отчетный период выгрузки"
        from oms.oms_data
        where "Цель" in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2')
        and "Статус" IN :status_list
    ),
    detail_oms as (
        select *
        from detail left join oms on "Номер талона" =oms."Талон"
    )

    select "Корпус",
           "Тип талона" as "Цель",
           "Название услуги" as "Услуга",
           sum(case when "Пол" = 'М' then 1 else 0 end)         as "К-во М",
           sum(case when "Пол" = 'Ж' then 1 else 0 end)         as "К-во Ж",
           sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end) as "К-во"
    from detail_oms
    where "Отчетный период выгрузки" IN ({sql_cond})
    group by "Корпус", "Тип талона", "Услуга"
    order by "Корпус",     CASE "Тип талона"
        WHEN 'ДВ4' THEN 1
        WHEN 'ДВ2' THEN 2
        WHEN 'ОПВ' THEN 3
        WHEN 'УД1' THEN 4
        WHEN 'УД2' THEN 5
        ELSE 6
        END, "Услуга"
"""


def sql_query_by_doctor_dispensary_adult_f3(sql_cond):
    return f"""
with detail as (select oms.detail_dd_data."Пол",
                       "Номер талона",
                       "Тип талона",
                       "Доктор (Код)",
                       "Доктор (ФИО)",
                       "Название услуги",
                       "Статус-Услуги",
                       "Доктор-Услуги (Код)",
                       "Доктор-Услуги (ФИО)",
                       oms.doctors_oms_data."Структурное подразделение:" as "Корпус",
                                              CASE
                        WHEN oms.doctors_oms_data."Код профиля медпомощи:" LIKE '%136 акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)%'
                        THEN 'акушерство и гинекология'
                        ELSE oms.doctors_oms_data."Код профиля медпомощи:" END as "Профиль"
                from oms.detail_dd_data
                         left join oms.doctors_oms_data on oms.detail_dd_data."Доктор-Услуги (Код)" = oms.doctors_oms_data."Код врача:"
                where  "Статус-Услуги" = 'Да'
                AND "Статус" IN :status_list
                and "Тип талона" in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2')),
    oms as (
        select "Талон",
               "Отчетный период выгрузки"
        from oms.oms_data
        where "Цель" in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2')
        AND "Статус" IN :status_list
    ),
    detail_oms as (
        select *
        from detail left join oms on "Номер талона" =oms."Талон"
    )

select "Корпус",
       "Тип талона" as "Цель",
       "Доктор-Услуги (ФИО)" || ' / ' || "Профиль" as "Врач/профиль",
       sum(case when "Пол" = 'М' then 1 else 0 end)         as "К-во М",
       sum(case when "Пол" = 'Ж' then 1 else 0 end)         as "К-во Ж",
       sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end) as "К-во"
from detail_oms
where "Отчетный период выгрузки" IN ({sql_cond})
group by "Корпус", "Тип талона", "Врач/профиль"
order by "Корпус", CASE "Тип талона"
        WHEN 'ДВ4' THEN 1
        WHEN 'ДВ2' THEN 2
        WHEN 'ОПВ' THEN 3
        WHEN 'УД1' THEN 4
        WHEN 'УД2' THEN 5
        ELSE 6
    END, "Врач/профиль"
"""



def sql_query_by_doctor_dispensary_children_f1(sql_cond):
    return f"""
with oms as (select "Врач",
                    "Врач (Профиль МП)",
                    "Цель",
                    "Пол",
                    "Сумма",
                    "Подразделение",
                    split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
                    '.' || left(split_part("Врач", ' ', 4), 1) || '.' || ' / ' || "Врач (Профиль МП)" as "ВР/проф_омс"
             from oms.oms_data
             where "Отчетный период выгрузки" IN ({sql_cond})
               AND "Статус" IN :status_list
               and "Цель" in ('ПН1', 'ДС2')
               and "Подразделение" like '%ДП%'),
     all_combinations as (SELECT "Подразделение",
                                 "ВР/проф_омс",
                                 unnest(array ['ПН1', 'ДС2']) as "Цель"
                          FROM oms
                          GROUP BY "Подразделение", "ВР/проф_омс")


SELECT all_combinations."Подразделение",
       all_combinations."ВР/проф_омс" as "Врач / профиль",
       all_combinations."Цель",
       sum(case when "Пол" = 'М' then 1 else 0 end)                                     as "К-во М",
       sum(case when "Пол" = 'Ж' then 1 else 0 end)                                     as "К-во Ж",
       sum(case when "Пол" = 'М' then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма М",
       sum(case when "Пол" = 'Ж' then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма Ж",
       sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end)                             as "К-во",
       sum(case when "Пол" in ('М', 'Ж') then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма"
FROM all_combinations
         LEFT JOIN
     oms
     ON
                 all_combinations."Подразделение" = oms."Подразделение"
             AND all_combinations."ВР/проф_омс" = oms."ВР/проф_омс"
             AND all_combinations."Цель" = oms."Цель"
GROUP BY all_combinations."Подразделение", "Врач / профиль", all_combinations."Цель"
ORDER BY all_combinations."Подразделение", "Врач / профиль"
"""


def sql_query_by_doctor_dispensary_children_f2(sql_cond):
    return f"""
with detail as (select oms.detail_dd_data."Пол",
                       "Номер талона",
                       "Тип талона",
                       "Доктор (Код)",
                       "Доктор (ФИО)",
                       "Название услуги",
                       "Статус-Услуги",
                       "Доктор-Услуги (Код)",
                       "Доктор-Услуги (ФИО)",
                       oms.doctors_oms_data."Структурное подразделение:" as "Корпус",
                       oms.doctors_oms_data."Код профиля медпомощи:" as "Профиль"
                from oms.detail_dd_data
                         left join oms.doctors_oms_data on oms.detail_dd_data."Доктор (Код)" = oms.doctors_oms_data."Код врача:"
                where  "Статус-Услуги" = 'Да'
                and "Статус" IN :status_list
                and "Тип талона" in ('ПН1', 'ДС2')),
    oms as (
        select "Талон",
               "Отчетный период выгрузки"
        from oms.oms_data
        where "Цель" in ('ПН1', 'ДС2')
        and "Статус" IN :status_list
    ),
    detail_oms as (
        select *
        from detail left join oms on "Номер талона" =oms."Талон"
    )

    select "Корпус",
           "Тип талона" as "Цель",
           "Название услуги" as "Услуга",
           sum(case when "Пол" = 'М' then 1 else 0 end)         as "К-во М",
           sum(case when "Пол" = 'Ж' then 1 else 0 end)         as "К-во Ж",
           sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end) as "К-во"
    from detail_oms
    where "Отчетный период выгрузки" IN ({sql_cond})
    group by "Корпус", "Тип талона", "Услуга"
    order by "Корпус",     CASE "Тип талона"
            WHEN 'ПН1' THEN 1
            WHEN 'ДС2' THEN 2
            ELSE 3
        END, "Услуга"
"""


def sql_query_by_doctor_dispensary_children_f3(sql_cond):
    return f"""
with detail as (select oms.detail_dd_data."Пол",
                       "Номер талона",
                       "Тип талона",
                       "Доктор (Код)",
                       "Доктор (ФИО)",
                       "Название услуги",
                       "Статус-Услуги",
                       "Доктор-Услуги (Код)",
                       "Доктор-Услуги (ФИО)",
                       oms.doctors_oms_data."Структурное подразделение:" as "Корпус",
                                              CASE
                        WHEN oms.doctors_oms_data."Код профиля медпомощи:" LIKE '%136 акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)%'
                        THEN 'акушерство и гинекология'
                        ELSE oms.doctors_oms_data."Код профиля медпомощи:" END as "Профиль"
                from oms.detail_dd_data
                         left join oms.doctors_oms_data on oms.detail_dd_data."Доктор-Услуги (Код)" = oms.doctors_oms_data."Код врача:"
                where  "Статус-Услуги" = 'Да'
                AND "Статус" IN :status_list
                and "Тип талона" in ('ПН1', 'ДС2')),
    oms as (
        select "Талон",
               "Отчетный период выгрузки"
        from oms.oms_data
        where "Цель" in ('ПН1', 'ДС2')
        AND "Статус" IN :status_list
    ),
    detail_oms as (
        select *
        from detail left join oms on "Номер талона" =oms."Талон"
    )

select "Корпус",
       "Тип талона" as "Цель",
       "Доктор-Услуги (ФИО)" || ' / ' || "Профиль" as "Врач/профиль",
       sum(case when "Пол" = 'М' then 1 else 0 end)         as "К-во М",
       sum(case when "Пол" = 'Ж' then 1 else 0 end)         as "К-во Ж",
       sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end) as "К-во"
from detail_oms
where "Отчетный период выгрузки" IN ({sql_cond})
group by "Корпус", "Тип талона", "Врач/профиль"
order by "Корпус", CASE "Тип талона"
            WHEN 'ПН1' THEN 1
            WHEN 'ДС2' THEN 2
            ELSE 3
    END, "Врач/профиль"
"""


def sql_query_by_doctor_dispensary_reproductive_f1(sql_cond):
    return f"""
with oms as (select "Врач",
                    "Врач (Профиль МП)",
                    "Цель",
                    "Пол",
                    "Сумма",
                    "Подразделение",
                    split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
                    '.' || left(split_part("Врач", ' ', 4), 1) || '.' || ' / ' || "Врач (Профиль МП)" as "ВР/проф_омс"
             from oms.oms_data
             where "Отчетный период выгрузки" IN ({sql_cond})
               AND "Статус" IN :status_list
               and "Тип талона" like '%Диспа%'
               and "Подразделение" not like '%ДП%'),
     all_combinations as (SELECT "Подразделение",
                                 "ВР/проф_омс",
                                 unnest(array ['ДР1', 'ДР2']) as "Цель"
                          FROM oms
                          GROUP BY "Подразделение", "ВР/проф_омс")


SELECT all_combinations."Подразделение",
       all_combinations."ВР/проф_омс" as "Врач / профиль",
       all_combinations."Цель",
       sum(case when "Пол" = 'М' then 1 else 0 end)                                     as "К-во М",
       sum(case when "Пол" = 'Ж' then 1 else 0 end)                                     as "К-во Ж",
       sum(case when "Пол" = 'М' then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма М",
       sum(case when "Пол" = 'Ж' then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма Ж",
       sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end)                             as "К-во",
       sum(case when "Пол" in ('М', 'Ж') then CAST("Сумма" AS numeric(15, 2)) else 0 end) as "Сумма"
FROM all_combinations
         LEFT JOIN
     oms
     ON
                 all_combinations."Подразделение" = oms."Подразделение"
             AND all_combinations."ВР/проф_омс" = oms."ВР/проф_омс"
             AND all_combinations."Цель" = oms."Цель"
GROUP BY all_combinations."Подразделение", "Врач / профиль", all_combinations."Цель"
ORDER BY all_combinations."Подразделение", "Врач / профиль"
"""


def sql_query_by_doctor_dispensary_reproductive_f2(sql_cond):
    return f"""
with detail as (select oms.detail_dd_data."Пол",
                       "Номер талона",
                       "Тип талона",
                       "Доктор (Код)",
                       "Доктор (ФИО)",
                       "Название услуги",
                       "Статус-Услуги",
                       "Доктор-Услуги (Код)",
                       "Доктор-Услуги (ФИО)",
                       oms.doctors_oms_data."Структурное подразделение:" as "Корпус",
                       oms.doctors_oms_data."Код профиля медпомощи:" as "Профиль"
                from oms.detail_dd_data
                         left join oms.doctors_oms_data on oms.detail_dd_data."Доктор (Код)" = oms.doctors_oms_data."Код врача:"
                where  "Статус-Услуги" = 'Да'
                and "Статус" IN :status_list
                and "Тип талона" in ('ДР1', 'ДР2')),
    oms as (
        select "Талон",
               "Отчетный период выгрузки"
        from oms.oms_data
        where "Цель" in ('ДР1', 'ДР2')
        and "Статус" IN :status_list
    ),
    detail_oms as (
        select *
        from detail left join oms on "Номер талона" =oms."Талон"
    )

    select "Корпус",
           "Тип талона" as "Цель",
           "Название услуги" as "Услуга",
           sum(case when "Пол" = 'М' then 1 else 0 end)         as "К-во М",
           sum(case when "Пол" = 'Ж' then 1 else 0 end)         as "К-во Ж",
           sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end) as "К-во"
    from detail_oms
    where "Отчетный период выгрузки" IN ({sql_cond})
    group by "Корпус", "Тип талона", "Услуга"
    order by "Корпус",     CASE "Тип талона"
        WHEN 'ДР1' THEN 1
        WHEN 'ДЗ2' THEN 2
        ELSE 3
        END, "Услуга"
"""


def sql_query_by_doctor_dispensary_reproductive_f3(sql_cond):
    return f"""
with detail as (select oms.detail_dd_data."Пол",
                       "Номер талона",
                       "Тип талона",
                       "Доктор (Код)",
                       "Доктор (ФИО)",
                       "Название услуги",
                       "Статус-Услуги",
                       "Доктор-Услуги (Код)",
                       "Доктор-Услуги (ФИО)",
                       oms.doctors_oms_data."Структурное подразделение:" as "Корпус",
                                              CASE
                        WHEN oms.doctors_oms_data."Код профиля медпомощи:" LIKE '%136 акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)%'
                        THEN 'акушерство и гинекология'
                        ELSE oms.doctors_oms_data."Код профиля медпомощи:" END as "Профиль"
                from oms.detail_dd_data
                         left join oms.doctors_oms_data on oms.detail_dd_data."Доктор-Услуги (Код)" = oms.doctors_oms_data."Код врача:"
                where  "Статус-Услуги" = 'Да'
                AND "Статус" IN :status_list
                and "Тип талона" in ('ДР1', 'ДР2')),
    oms as (
        select "Талон",
               "Отчетный период выгрузки"
        from oms.oms_data
        where "Цель" in ('ДР1', 'ДР2')
        AND "Статус" IN :status_list
    ),
    detail_oms as (
        select *
        from detail left join oms on "Номер талона" =oms."Талон"
    )

select "Корпус",
       "Тип талона" as "Цель",
       "Доктор-Услуги (ФИО)" || ' / ' || "Профиль" as "Врач/профиль",
       sum(case when "Пол" = 'М' then 1 else 0 end)         as "К-во М",
       sum(case when "Пол" = 'Ж' then 1 else 0 end)         as "К-во Ж",
       sum(case when "Пол" in ('М', 'Ж') then 1 else 0 end) as "К-во"
from detail_oms
where "Отчетный период выгрузки" IN ({sql_cond})
group by "Корпус", "Тип талона", "Врач/профиль"
order by "Корпус", CASE "Тип талона"
        WHEN 'ДР1' THEN 1
        WHEN 'ДР2' THEN 2
        ELSE 3
    END, "Врач/профиль"
"""
