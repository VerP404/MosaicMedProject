def sql_query_route_children_old(sql_cond):
    return f"""
WITH RankedData AS (SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY "Номер талона" ORDER BY (SELECT NULL)) AS RowNum
                    FROM (
                            SELECT oms.detaildd_data."Тип талона" as "Цель в талоне",
                                   oms.detaildd_data."Статус" as "Статус талона",
                                   *
                            FROM
                            oms.detaildd_data left join oms.oms_data on oms.detaildd_data."Номер талона" = oms.oms_data."Талон") as svod)
SELECT "Маршрут",
       count(*) as "К-во",
       SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "ДП1",
       
       round(sum(CAST("Сумма" AS numeric(15, 2))):: numeric, 2) as "Сумма",
            SUM(CASE WHEN "Подразделение" = 'ДП №1' THEN 1 ELSE 0 END) AS "ДП1",
     round(SUM(CASE WHEN "Подразделение" = 'ДП №1' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric, 2) AS "ДП1 сумма",
     SUM(CASE WHEN "Подразделение" = 'ДП №8' THEN 1 ELSE 0 END) AS "ДП8",
     round(SUM(CASE WHEN "Подразделение" = 'ДП №8' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric, 2) AS "ДП8 сумма",
     SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' THEN 1 ELSE 0 END) AS "ДП8 К7",
     round(SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric, 2) AS "ДП8 К7 сумма"

FROM RankedData
WHERE RowNum = 1
and "Отчетный период выгрузки" IN ({sql_cond})
  and "Цель в талоне" = 'ПН1'
  AND "Тариф" != '0'
    and "Код СМО" like '360%'
  AND "Санкции" is null
    AND "Статус талона" IN :status_list
group by "Маршрут"
order by case
             when "Маршрут" = '0 месяцев' then 1
             when "Маршрут" = '1 месяц' then 2
             when "Маршрут" = '2 месяца' then 3
             when "Маршрут" = '3 месяца' then 4
             when "Маршрут" = '4 месяца' then 5
             when "Маршрут" = '5 месяцев' then 6
             when "Маршрут" = '6 месяцев' then 7
             when "Маршрут" = '7 месяцев' then 8
             when "Маршрут" = '8 месяцев' then 9
             when "Маршрут" = '9 месяцев' then 10
             when "Маршрут" = '10 месяцев' then 11
             when "Маршрут" = '11 месяцев' then 12
             when "Маршрут" = '1 год 0 месяцев' then 13
             when "Маршрут" = '1 год 3 месяца' then 14
             when "Маршрут" = '1 год 6 месяцев' then 15
             when "Маршрут" = '2 года' then 16
             when "Маршрут" = '3 года' then 17
             when "Маршрут" = '4 года' then 18
             when "Маршрут" = '5 лет' then 19
             when "Маршрут" = '6 лет' then 20
             when "Маршрут" = '7 лет' then 21
             when "Маршрут" = '8 лет' then 22
             when "Маршрут" = '9 лет' then 23
             when "Маршрут" = '10 лет' then 24
             when "Маршрут" = '11 лет' then 25
             when "Маршрут" = '12 лет' then 26
             when "Маршрут" = '13 лет' then 27
             when "Маршрут" = '14 лет' then 28
             when "Маршрут" = '15 лет' then 29
             when "Маршрут" = '16 лет' then 30
             when "Маршрут" = '17 лет' then 31
             ELSE 32
             end
"""


def sql_query_route_children(sql_cond):
    return f"""
    WITH osm as (select "Талон",
                    "Статус",
                    "Пол",
                    "Сумма",
                    "Код СМО",
                    "Подразделение",
                    "Цель"
             from oms.oms_data
             where "Отчетный период выгрузки" IN ({sql_cond})
                  and "Цель" = 'ПН1'
                  AND "Тариф" != '0'
                    and "Код СМО" like '360%'
                  AND "Санкции" is null
                    AND "Статус" IN :status_list
               ),
     detailed as (select ROW_NUMBER() OVER (PARTITION BY "Номер талона" ORDER BY (SELECT NULL)) AS RowNum,
                       "Номер талона",
                       "Маршрут"
                from oms.detaildd_data
                where "Тип талона" = 'ПН1' 
                ),
     detail_uniq as (select "Номер талона",
                            "Маршрут"
                     from detailed
                     where RowNum = 1),

     svod AS (SELECT *
              FROM detail_uniq
                       left join osm on detail_uniq."Номер талона" = osm."Талон")

SELECT "Маршрут",
       count(*)                                                                      as "К-во",
       round(sum(CAST("Сумма" AS numeric(15, 2))):: numeric, 2)                      as "Сумма",

       SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END)                                  AS "Ж",
       round(SUM(CASE WHEN "Пол" = 'Ж' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric,
             2)                                                                      AS "Ж сумма",
       SUM(CASE WHEN "Пол" = 'М' THEN 1 ELSE 0 END)                                  AS "М",
       round(SUM(CASE WHEN "Пол" = 'М' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric,
             2)                                                                      AS "М сумма",

       SUM(CASE WHEN "Подразделение" = 'ДП №1' THEN 1 ELSE 0 END)                    AS "ДП1",
       round(SUM(CASE WHEN "Подразделение" = 'ДП №1' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric,
             2)                                                                      AS "ДП1 сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №1' and "Пол" = 'Ж' THEN 1 ELSE 0 END)    AS "ДП1 Ж",
       round(SUM(CASE
                     WHEN "Подразделение" = 'ДП №1' and "Пол" = 'Ж' THEN CAST("Сумма" AS numeric(10, 2))
                     ELSE 0 END):: numeric,
             2)                                                                      AS "ДП1 Ж сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №1' and "Пол" = 'М' THEN 1 ELSE 0 END)    AS "ДП1 М",
       round(SUM(CASE
                     WHEN "Подразделение" = 'ДП №1' and "Пол" = 'М' THEN CAST("Сумма" AS numeric(10, 2))
                     ELSE 0 END):: numeric,
             2)                                                                      AS "ДП1 М сумма",

       SUM(CASE WHEN "Подразделение" = 'ДП №8' THEN 1 ELSE 0 END)                    AS "ДП8",
       round(SUM(CASE WHEN "Подразделение" = 'ДП №8' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric,
             2)                                                                      AS "ДП8 сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №8' and "Пол" = 'Ж' THEN 1 ELSE 0 END)    AS "ДП8 Ж",
       round(SUM(CASE
                     WHEN "Подразделение" = 'ДП №8' and "Пол" = 'Ж' THEN CAST("Сумма" AS numeric(10, 2))
                     ELSE 0 END):: numeric,
             2)                                                                      AS "ДП8 Ж сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №8' and "Пол" = 'М' THEN 1 ELSE 0 END)    AS "ДП8 М",
       round(SUM(CASE
                     WHEN "Подразделение" = 'ДП №8' and "Пол" = 'М' THEN CAST("Сумма" AS numeric(10, 2))
                     ELSE 0 END):: numeric,
             2)                                                                      AS "ДП8 М сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' THEN 1 ELSE 0 END)                 AS "ДП8 К7",
       round(SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END):: numeric,
             2)                                                                      AS "ДП8 К7 сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "ДП8 К7 Ж",
       round(SUM(CASE
                     WHEN "Подразделение" = 'ДП №8 К7' and "Пол" = 'Ж' THEN CAST("Сумма" AS numeric(10, 2))
                     ELSE 0 END):: numeric,
             2)                                                                      AS "ДП8 К7 Ж сумма",
       SUM(CASE WHEN "Подразделение" = 'ДП №8 К7' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "ДП8 К7 М",
       round(SUM(CASE
                     WHEN "Подразделение" = 'ДП №8 К7' and "Пол" = 'М' THEN CAST("Сумма" AS numeric(10, 2))
                     ELSE 0 END):: numeric,
             2)                                                                      AS "ДП8 К7 М сумма"

FROM svod
WHERE "Номер талона" is not null
  and "Талон" is not null
group by "Маршрут"
order by case
             when "Маршрут" = '0 месяцев' then 1
             when "Маршрут" = '1 месяц' then 2
             when "Маршрут" = '2 месяца' then 3
             when "Маршрут" = '3 месяца' then 4
             when "Маршрут" = '4 месяца' then 5
             when "Маршрут" = '5 месяцев' then 6
             when "Маршрут" = '6 месяцев' then 7
             when "Маршрут" = '7 месяцев' then 8
             when "Маршрут" = '8 месяцев' then 9
             when "Маршрут" = '9 месяцев' then 10
             when "Маршрут" = '10 месяцев' then 11
             when "Маршрут" = '11 месяцев' then 12
             when "Маршрут" = '1 год 0 месяцев' then 13
             when "Маршрут" = '1 год 3 месяца' then 14
             when "Маршрут" = '1 год 6 месяцев' then 15
             when "Маршрут" = '2 года' then 16
             when "Маршрут" = '3 года' then 17
             when "Маршрут" = '4 года' then 18
             when "Маршрут" = '5 лет' then 19
             when "Маршрут" = '6 лет' then 20
             when "Маршрут" = '7 лет' then 21
             when "Маршрут" = '8 лет' then 22
             when "Маршрут" = '9 лет' then 23
             when "Маршрут" = '10 лет' then 24
             when "Маршрут" = '11 лет' then 25
             when "Маршрут" = '12 лет' then 26
             when "Маршрут" = '13 лет' then 27
             when "Маршрут" = '14 лет' then 28
             when "Маршрут" = '15 лет' then 29
             when "Маршрут" = '16 лет' then 30
             when "Маршрут" = '17 лет' then 31
             ELSE 32
             end
    """
