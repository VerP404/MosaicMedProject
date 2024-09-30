sql_query_for_smo = """
SELECT
    '01' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2))ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Января%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '02' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Февраля%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '03' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Марта%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '04' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Апреля%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '05' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Мая%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '06' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Июня%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '07' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Июля%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '08' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Августа%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '09' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Сентября%'
    AND "Статус" IN ('2', '3')
GROUP BY "Месяц"
UNION ALL
SELECT
    '10' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Октября%'
    AND "Статус" IN ('2', '3')
    and "Санкции" is null
GROUP BY "Месяц"
UNION ALL
SELECT
    '11' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Ноября%'
    AND "Статус" IN ('2', '3')
    and "Санкции" is null
GROUP BY "Месяц"
UNION ALL
SELECT
    '12' as "Месяц",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36065' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Инко-Мед",
    TO_CHAR(sum(CASE WHEN "Код СМО" = '36071' THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "СОГАЗ",
    TO_CHAR(sum(CASE WHEN "Код СМО" in ('36071','36065') THEN CAST("Сумма" AS numeric(10, 2)) ELSE 0 END)::numeric, 'FM999999990.00') as "Итого"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" LIKE '%Декабря%'
    AND "Статус" IN ('2', '3')
    and "Санкции" is null
GROUP BY "Месяц"
order by "Месяц"
"""