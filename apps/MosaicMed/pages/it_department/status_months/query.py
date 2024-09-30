sql_query_stat_month = """
SELECT
    "Отчетный период выгрузки" AS "Значение",
    count(*) AS "Количество",
    sum(case when "Статус" = '3' then 1 else 0 end) as Оплачено,
    sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end) as "В ТФОМС",
    sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end) as "Отказано",
    sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end) as "Отменен",
    sum(case when "Статус" = '1' then 1 else 0 end) as "1",
    sum(case when "Статус" = '2' then 1 else 0 end) as "2",
    sum(case when "Статус" = '3' then 1 else 0 end) as "3",
    sum(case when "Статус" = '4' then 1 else 0 end) as "4",
    sum(case when "Статус" = '5' then 1 else 0 end) as "5",
    sum(case when "Статус" = '6' then 1 else 0 end) as "6",
    sum(case when "Статус" = '7' then 1 else 0 end) as "7",
    sum(case when "Статус" = '8' then 1 else 0 end) as "8",
    sum(case when "Статус" = '12' then 1 else 0 end) as "12",
    sum(case when "Статус" = '13' then 1 else 0 end) as "13",
    sum(case when "Статус" = '17' then 1 else 0 end) as "17",
    sum(case when "Статус" = '0' then 1 else 0 end) as "0"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" != '-' AND "Санкции" IS NULL
GROUP BY "Отчетный период выгрузки"
ORDER BY 
    CASE 
        WHEN "Отчетный период выгрузки" LIKE '%Января%' THEN 1
        WHEN "Отчетный период выгрузки" LIKE '%Февраля%' THEN 2
        WHEN "Отчетный период выгрузки" LIKE '%Марта%' THEN 3
        WHEN "Отчетный период выгрузки" LIKE '%Апреля%' THEN 4
        WHEN "Отчетный период выгрузки" LIKE '%Мая%' THEN 5
        WHEN "Отчетный период выгрузки" LIKE '%Июня%' THEN 6
        WHEN "Отчетный период выгрузки" LIKE '%Июля%' THEN 7
        WHEN "Отчетный период выгрузки" LIKE '%Августа%' THEN 8
        WHEN "Отчетный период выгрузки" LIKE '%Сентября%' THEN 9
        WHEN "Отчетный период выгрузки" LIKE '%Октября%' THEN 10
        WHEN "Отчетный период выгрузки" LIKE '%Ноября%' THEN 11
        WHEN "Отчетный период выгрузки" LIKE '%Декабря%' THEN 12
    END,
    "Отчетный период выгрузки";

"""
