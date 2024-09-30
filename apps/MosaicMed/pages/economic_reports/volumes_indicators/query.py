sql_query_pgg_amb = """
SELECT "Отчетный период выгрузки" AS "Месяц",
       SUM(CASE WHEN "Цель" in ('30', '301', '305') THEN 1 ELSE 0 END) AS "Обращения",
       SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)               AS "Неотложка",
       SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                AS "Д.наб",
       SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)               AS "Гериатрия",
       SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)               AS "307",
       SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)               AS "561",
       SUM(CASE WHEN "Цель" in ('541') and "Сумма" = '542.13' THEN 1 ELSE 0 END) AS "541 УЗИ",
       SUM(CASE WHEN "Цель" in ('541') and "Сумма" = '857.55' THEN 1 ELSE 0 END) AS "541 Эндоскопия",
       SUM(CASE WHEN "Цель" in ('541') and "Сумма" = '2004.27' THEN 1 ELSE 0 END) AS "541 Колоноскопия"
FROM oms.oms_data
WHERE "Статус" = '3'
  AND "Санкции" IS NULL
  AND "Код СМО" like '360%'
GROUP BY "Месяц"
UNION ALL
SELECT 'Итого',
       SUM(CASE WHEN "Цель" in ('30', '301', '305') THEN 1 ELSE 0 END) AS "Обращения",
       SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)               AS "Неотложка",
       SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                AS "Д.наб",
       SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)               AS "Гериатрия",
       SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)               AS "307",
       SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)               AS "561",
       SUM(CASE WHEN "Цель" in ('541') and "Сумма" = '542.13' THEN 1 ELSE 0 END) AS "541 УЗИ",
       SUM(CASE WHEN "Цель" in ('541') and "Сумма" = '857.55' THEN 1 ELSE 0 END) AS "541 Эндоскопия",
       SUM(CASE WHEN "Цель" in ('541') and "Сумма" = '2004.27' THEN 1 ELSE 0 END) AS "541 Колоноскопия"
FROM oms.oms_data
WHERE "Статус" = '3'
  AND "Санкции" IS NULL
  AND "Код СМО" like '360%'
ORDER BY "Месяц"
        """


sql_query_pgg_dd = """
SELECT "Отчетный период выгрузки" AS "Месяц",
       SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 else 0 END)              AS "ДВ4",
       ROUND(SUM(CASE WHEN "Цель" in ('ДВ4') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2) AS "ДВ4 сумма",
       SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 else 0 END)              AS "ДВ2",
       ROUND(SUM(CASE WHEN "Цель" in ('ДВ2') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "ДВ2 сумма",
       SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 else 0 END)              AS "ОПВ",
       ROUND(SUM(CASE WHEN "Цель" in ('ОПВ') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "ОПВ сумма",
       SUM(CASE WHEN "Цель" in ('УД1') THEN 1 else 0 END)              AS "УД1",
       ROUND(SUM(CASE WHEN "Цель" in ('УД1') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "УД1 сумма",
       SUM(CASE WHEN "Цель" in ('УД2') THEN 1 else 0 END)              AS "УД2",
       ROUND(SUM(CASE WHEN "Цель" in ('УД2') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "УД2 сумма",
       SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 else 0 END)              AS "ПН1",
       ROUND(SUM(CASE WHEN "Цель" in ('ПН1') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)             AS "ПН1 сумма",
       SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 else 0 END)              AS "ДС2",
       ROUND(SUM(CASE WHEN "Цель" in ('ДС2') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "ДС2 сумма"
FROM oms.oms_data
WHERE "Статус" = '3'
  AND "Санкции" IS NULL
  AND "Код СМО" like '360%'
GROUP BY "Месяц"
UNION ALL
SELECT 'Итого',
       SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 else 0 END)              AS "ДВ4",
       ROUND(SUM(CASE WHEN "Цель" in ('ДВ4') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2) AS "ДВ4 сумма",
       SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 else 0 END)              AS "ДВ2",
       ROUND(SUM(CASE WHEN "Цель" in ('ДВ2') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "ДВ2 сумма",
       SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 else 0 END)              AS "ОПВ",
       ROUND(SUM(CASE WHEN "Цель" in ('ОПВ') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "ОПВ сумма",
       SUM(CASE WHEN "Цель" in ('УД1') THEN 1 else 0 END)              AS "УД1",
       ROUND(SUM(CASE WHEN "Цель" in ('УД1') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "УД1 сумма",
       SUM(CASE WHEN "Цель" in ('УД2') THEN 1 else 0 END)              AS "УД2",
       ROUND(SUM(CASE WHEN "Цель" in ('УД2') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "УД2 сумма",
       SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 else 0 END)              AS "ПН1",
       ROUND(SUM(CASE WHEN "Цель" in ('ПН1') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)             AS "ПН1 сумма",
       SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 else 0 END)              AS "ДС2",
       ROUND(SUM(CASE WHEN "Цель" in ('ДС2') THEN CAST("Сумма" AS numeric(15, 2)) else 0 END), 2)              AS "ДС2 сумма"
FROM oms.oms_data
WHERE "Статус" = '3'
  AND "Санкции" IS NULL
  AND "Код СМО" like '360%'
ORDER BY "Месяц";

"""

sql_query_pgg_ds = """
SELECT "Отчетный период выгрузки" AS "Месяц",
        count(*) as "Всего",
        ROUND(SUM(CAST("Сумма" AS numeric(15, 2))) ::numeric, 2) AS "Всего сумма",
       SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN 1 ELSE 0 END) AS "В дневном стационаре",
       ROUND(SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN CAST("Сумма" AS numeric(15, 2)) ELSE 0 END) ::numeric, 2) AS "В дневном стационаре сумма",
       SUM(CASE WHEN "Цель" = 'На дому' THEN 1 ELSE 0 END) AS "На дому",
       ROUND(SUM(CASE WHEN "Цель" = 'На дому' THEN CAST("Сумма" AS numeric(15, 2)) ELSE 0 END) ::numeric, 2) AS "На дому сумма"
FROM oms.oms_data
WHERE "Статус" = '3'
  AND "Тип талона" = 'Стационар'
  AND "Санкции" IS NULL
  AND "Код СМО" like '360%'
GROUP BY "Месяц"
UNION ALL
SELECT 'Итого',
        count(*) as "Всего",
        ROUND(SUM(CAST("Сумма" AS numeric(15, 2))) ::numeric, 2) AS "Всего сумма",
       SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN 1 ELSE 0 END) AS "В дневном стационаре",
       ROUND(SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN CAST("Сумма" AS numeric(15, 2)) ELSE 0 END) ::numeric, 2) AS "В дневном стационаре сумма",
       SUM(CASE WHEN "Цель" = 'На дому' THEN 1 ELSE 0 END) AS "На дому",
       ROUND(SUM(CASE WHEN "Цель" = 'На дому' THEN CAST("Сумма" AS numeric(15, 2)) ELSE 0 END) ::numeric, 2) AS "На дому сумма"
FROM oms.oms_data
WHERE "Статус" = '3'
  AND "Тип талона" = 'Стационар'
  AND "Санкции" IS NULL
  AND "Код СМО" like '360%'
ORDER BY "Месяц";

"""