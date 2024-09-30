# Отчет по профосмотрам детским
def sql_query_pn():
    return f"""
    select coalesce("Подразделение", 'Итого')               as Корпус,
           sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
           sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
           sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
           sum(case when "Статус" = '4' then 1 else 0 end)  as "4",
           sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
           sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
           sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
           sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
           sum(case when "Статус" = '12' then 1 else 0 end) as "12",
           sum(case when "Статус" = '13' then 1 else 0 end) as "13",
           sum(case when "Статус" = '17' then 1 else 0 end) as "17",
           sum(case when "Статус" = '0' then 1 else 0 end)  as "0",
           sum(case
                   when "Статус" = '0' or "Статус" = '1' or "Статус" = '2' or "Статус" = '3' or "Статус" = '5'
                       or "Статус" = '6' or "Статус" = '7' or "Статус" = '8' or "Статус" = '12' or "Статус" = '13' or
                        "Статус" = '17'
                       then 1
                   else 0 end)                              as Итого
    from oms.oms_data
    where to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY') 
    and ("Подразделение" like '%ДП%')
      and ("Цель" = 'ПН1')
    group by rollup ("Подразделение")
    order by Корпус DESC
"""


# Отчет по профосмотрам детским
def sql_query_ds2():
    return f"""
        select coalesce("Подразделение", 'Итого')               as Корпус,
           sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
           sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
           sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
           sum(case when "Статус" = '4' then 1 else 0 end)  as "4",
           sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
           sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
           sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
           sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
           sum(case when "Статус" = '12' then 1 else 0 end) as "12",
           sum(case when "Статус" = '13' then 1 else 0 end) as "13",
           sum(case when "Статус" = '17' then 1 else 0 end) as "17",
           sum(case when "Статус" = '0' then 1 else 0 end)  as "0",
               sum(case
                       when "Статус" = '0' or "Статус" = '1' or "Статус" = '2' or "Статус" = '3' or "Статус" = '5'
                           or "Статус" = '6' or "Статус" = '7' or "Статус" = '8' or "Статус" = '12' or "Статус" = '13' or
                            "Статус" = '17' then 1 else 0 end)                              as Итого
        from oms.oms_data
        where to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY') 
        and ("Подразделение" like '%ДП%')
          and ("Цель" = 'ДС2')
        group by rollup ("Подразделение")
        order by Корпус DESC
    """


# Отчет по уникальным детям в профосмотрах
def sql_query_pn_uniq_tal():
    return """
        with ss as (select
                        ROW_NUMBER() OVER (PARTITION BY "Полис" ORDER BY "Номер счёта") AS rnk,
                        case when "Подразделение" = 'ДП №8 К7' then 'ДП №8' else "Подразделение" end as Корпус ,
                        *
                    from oms.oms_data
                    where to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                      and "Цель" = 'ПН1'
                      and "Статус" = '3'),
            ff as (select *
                   from ss
                   where rnk = 1),
        
            un as (select coalesce(Корпус, 'Итого')                                as Корпус,
                   COUNT(DISTINCT "Полис")                                           as Уникальные_дети
            from ff
            group by rollup (Корпус)
            order by Корпус DESC),
        
            talon as (select coalesce(Корпус, 'Итого')                                as Корпус,
                      sum(case when "Цель" = 'ПН1' then 1 else 0 end) as Талоны
            from ss
            group by rollup (Корпус)
            order by Корпус DESC)
        
        select un.Корпус AS "Корпус",
               Талоны,
               Уникальные_дети
        from un left join talon on un.Корпус=talon.Корпус
        """


def sql_query_pn_talon(year_placeholder):
    return f"""
    WITH data_with_last_month AS (
        SELECT
            "Подразделение",
            "Отчетный период выгрузки",
            CASE
                WHEN "Отчетный период выгрузки" IS NULL THEN MAX("Отчетный период выгрузки") OVER ()
                ELSE "Отчетный период выгрузки"
            END AS "Actual Отчетный период выгрузки",
            "Статус"
        FROM oms.oms_data
        WHERE "Цель" = 'ПН1'
          AND "Санкции" IS NULL
          AND "Тариф" != '0'
          AND "Код СМО" LIKE '360%'
    )
    SELECT
        COALESCE("Подразделение", 'Итого талонов') AS "Подразделение",
        "Actual Отчетный период выгрузки" AS "Отчетный период выгрузки",
        sum(case when "Статус" in ('1', '2', '3', '4', '5', '6', '7', '8', '12') then 1 else 0 end) as "Всего",
        sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as "В работе",
        sum(case when "Статус" = '3' then 1 else 0 end) as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end) as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end) as "Отказано",
        sum(case when "Статус" = '6' or "Статус" = '8' then 1 else 0 end) as "Исправлен",
        sum(case when "Статус" = '1' then 1 else 0 end) as "1",
        sum(case when "Статус" = '2' then 1 else 0 end) as "2",
        sum(case when "Статус" = '3' then 1 else 0 end) as "3",
        sum(case when "Статус" = '4' then 1 else 0 end) as "4",
        sum(case when "Статус" = '5' then 1 else 0 end) as "5",
        sum(case when "Статус" = '6' then 1 else 0 end) as "6",
        sum(case when "Статус" = '7' then 1 else 0 end) as "7",
        sum(case when "Статус" = '8' then 1 else 0 end) as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12"
    FROM data_with_last_month
    WHERE "Actual Отчетный период выгрузки" LIKE '%{year_placeholder}%' OR "Actual Отчетный период выгрузки" LIKE '%-%'
    GROUP BY ROLLUP ("Actual Отчетный период выгрузки", "Подразделение")
    ORDER BY
        CASE
            WHEN "Actual Отчетный период выгрузки" LIKE '%Января%' THEN 1
            WHEN "Actual Отчетный период выгрузки" LIKE '%Февраля%' THEN 2
            WHEN "Actual Отчетный период выгрузки" LIKE '%Марта%' THEN 3
            WHEN "Actual Отчетный период выгрузки" LIKE '%Апреля%' THEN 4
            WHEN "Actual Отчетный период выгрузки" LIKE '%Мая%' THEN 5
            WHEN "Actual Отчетный период выгрузки" LIKE '%Июня%' THEN 6
            WHEN "Actual Отчетный период выгрузки" LIKE '%Июля%' THEN 7
            WHEN "Actual Отчетный период выгрузки" LIKE '%Августа%' THEN 8
            WHEN "Actual Отчетный период выгрузки" LIKE '%Сентября%' THEN 9
            WHEN "Actual Отчетный период выгрузки" LIKE '%Октября%' THEN 10
            WHEN "Actual Отчетный период выгрузки" LIKE '%Ноября%' THEN 11
            WHEN "Actual Отчетный период выгрузки" LIKE '%Декабря%' THEN 12
        END,
        "Подразделение";
    """


def sql_query_pn_uniq(year_placeholder):
    return f"""
    WITH data_with_last_month AS (
        SELECT
            "Подразделение",
            "Отчетный период выгрузки",
            "ЕНП",
            CASE
                WHEN "Отчетный период выгрузки" IS NULL THEN MAX("Отчетный период выгрузки") OVER ()
                ELSE "Отчетный период выгрузки"
            END AS "Actual Отчетный период выгрузки",
            "Статус"
        FROM oms.oms_data
        WHERE "Цель" = 'ПН1'
          AND "Санкции" IS NULL
          AND "Тариф" != '0'
          AND "Код СМО" LIKE '360%'
    ),
    first_occurrence AS (
        SELECT
            "Подразделение",
            "Actual Отчетный период выгрузки",
            "ЕНП",
            ROW_NUMBER() OVER (PARTITION BY "ЕНП" ORDER BY "Actual Отчетный период выгрузки") AS rn,
            "Статус"
        FROM data_with_last_month
    )
    SELECT
        COALESCE("Подразделение", 'Итого талонов') AS "Подразделение",
        "Actual Отчетный период выгрузки" AS "Отчетный период выгрузки",
        COUNT(DISTINCT CASE WHEN rn = 1 THEN "ЕНП" END) AS "Уникальные ЕНП",
        sum(case when "Статус" in ('1', '2', '3', '4', '5', '6', '7', '8', '12') then 1 else 0 end) as "Всего",
        sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as "В работе",
        sum(case when "Статус" = '3' then 1 else 0 end) as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end) as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end) as "Отказано",
        sum(case when "Статус" = '6' or "Статус" = '8' then 1 else 0 end) as "Исправлен",
        sum(case when "Статус" = '1' then 1 else 0 end) as "1",
        sum(case when "Статус" = '2' then 1 else 0 end) as "2",
        sum(case when "Статус" = '3' then 1 else 0 end) as "3",
        sum(case when "Статус" = '4' then 1 else 0 end) as "4",
        sum(case when "Статус" = '5' then 1 else 0 end) as "5",
        sum(case when "Статус" = '6' then 1 else 0 end) as "6",
        sum(case when "Статус" = '7' then 1 else 0 end) as "7",
        sum(case when "Статус" = '8' then 1 else 0 end) as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12"
    FROM first_occurrence
    WHERE rn = 1 AND ("Actual Отчетный период выгрузки" LIKE '%{year_placeholder}%' OR "Actual Отчетный период выгрузки" LIKE '%-%')
    GROUP BY ROLLUP ("Actual Отчетный период выгрузки", "Подразделение")
    ORDER BY
        CASE
            WHEN "Actual Отчетный период выгрузки" LIKE '%Января%' THEN 1
            WHEN "Actual Отчетный период выгрузки" LIKE '%Февраля%' THEN 2
            WHEN "Actual Отчетный период выгрузки" LIKE '%Марта%' THEN 3
            WHEN "Actual Отчетный период выгрузки" LIKE '%Апреля%' THEN 4
            WHEN "Actual Отчетный период выгрузки" LIKE '%Мая%' THEN 5
            WHEN "Actual Отчетный период выгрузки" LIKE '%Июня%' THEN 6
            WHEN "Actual Отчетный период выгрузки" LIKE '%Июля%' THEN 7
            WHEN "Actual Отчетный период выгрузки" LIKE '%Августа%' THEN 8
            WHEN "Actual Отчетный период выгрузки" LIKE '%Сентября%' THEN 9
            WHEN "Actual Отчетный период выгрузки" LIKE '%Октября%' THEN 10
            WHEN "Actual Отчетный период выгрузки" LIKE '%Ноября%' THEN 11
            WHEN "Actual Отчетный период выгрузки" LIKE '%Декабря%' THEN 12
        END,
        "Подразделение";
    """


def sql_query_children_age_dispensary():
    return  f"""
WITH data AS (SELECT 2024 - CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer)                        as Возраст,
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN "Пол" = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN "Подразделение" = 'ДП №1' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ДП №1",
                     SUM(CASE WHEN "Подразделение" = 'ДП №1' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ДП №1",
                     SUM(CASE WHEN "Подразделение" = 'ДП №1' THEN 1 ELSE 0 END)                 AS "ДП №1",
                     SUM(CASE WHEN "Подразделение" = 'ДП №8' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ДП №8",
                     SUM(CASE WHEN "Подразделение" = 'ДП №8' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ДП №8",
                     SUM(CASE WHEN "Подразделение" = 'ДП №8' THEN 1 ELSE 0 END)                 AS "ДП №8",
                     SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ДП №8 К7",
                     SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ДП №8 К7",                  
                     SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' THEN 1 ELSE 0 END)              AS "ДП №8 К7"
              FROM oms.oms_data
              WHERE "Цель" IN ('ПН1')
                and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
              GROUP BY Возраст)
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
       "Всего",
       "М",
       "Ж",
       "М ДП №1",
       "Ж ДП №1",
       "ДП №1",
       "М ДП №8",
       "Ж ДП №8",
       "ДП №8",
       "М ДП №8 К7",
       "Ж ДП №8 К7",
       "ДП №8 К7"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
             SUM("М ДП №1"),
             SUM("Ж ДП №1"),
             SUM("ДП №1"),
             SUM("М ДП №8"),
             SUM("Ж ДП №8"),
             SUM("ДП №8"),
             SUM("М ДП №8 К7"),
             SUM("Ж ДП №8 К7"),
             SUM("ДП №8 К7")
      FROM data) d
"""


query_download_children_list_not_pn1 = """
with
    sel_nas as (
        select iszl.people_data."FIO",
               iszl.people_data."DR",
               2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as  "Возраст",
               iszl.people_data."ENP",
               iszl.people_data."LPUUCH",
               info.area_data."Корпус"
        from iszl.people_data left join info.area_data on iszl.people_data."LPUUCH" = info.area_data."Участок"
        where 2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) < 18
),
    itog as     (
        select *,
               case when sel_nas."ENP" in (select "ЕНП" from oms.oms_data where "Цель" = 'ПН1') then 'да' else 'нет' end as "Есть ПН1"
        from sel_nas
    ),

    nas as (
        select itog.*,
               info.naselenie_data."Пол",
               info.naselenie_data."Телефон Квазар",
               info.naselenie_data."Телефон МИС КАУЗ",
               info.naselenie_data."Адрес Квазар",
               info.naselenie_data."Адрес ИСЗЛ",
               info.naselenie_data."Адрес МИС КАУЗ 1"

        from itog left join info.naselenie_data on itog."ENP" = info.naselenie_data."ЕНП"
    )
select *
from nas
where "Есть ПН1" = 'нет'
order by "FIO"
"""
