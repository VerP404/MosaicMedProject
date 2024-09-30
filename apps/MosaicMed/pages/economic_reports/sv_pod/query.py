def sql_qery_sv_pod(sql_cond):
    return f"""

    SELECT CASE
               WHEN "Цель" = '541' and "Сумма" in ('589.82', '1179.64', '1769.46', '2359.28') THEN '541 УЗИ' 
               WHEN "Цель" = '541' and "Сумма" = '895.02' THEN '541 Эндоскопия'
               WHEN "Цель" = '541' and "Сумма" = '2077.79' THEN '541 Колоноскопия'
               WHEN "Цель" = '541' and "Сумма" = '2972.81' THEN '541 гастроскопия и Колоноскопия'
               WHEN "Цель" = '541' and "Сумма" = '399.6' THEN '541 ошибка'
               END                                                 AS "Цель",
           COUNT(*)                                                AS "К-во",
           ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"
    FROM oms.oms_data
    WHERE "Отчетный период выгрузки" IN ({sql_cond})
      AND "Статус" IN :status_list
      AND "Тариф" != '0'
      and "Код СМО" like '360%'
      AND "Санкции" is null
      AND "Цель" = '541'
    group by "Цель", "Сумма"   
union all

SELECT "Цель",
       count(*)                        as "К-во",
       ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
  and "Код СМО" like '360%'
  AND "Санкции" is null
  AND "Цель" IN ('64', '13', '32', 'ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1', 'ДС2', '307', '561')
GROUP BY "Цель"
union all

SELECT      CASE
        WHEN "Цель" = 'ДР1' AND "Пол" = 'Ж' THEN 'ДР1 Ж'
        WHEN "Цель" = 'ДР1' AND "Пол" = 'М' THEN 'ДР1 М'        
        WHEN "Цель" = 'ДР2' AND "Пол" = 'Ж' THEN 'ДР2 Ж'
        WHEN "Цель" = 'ДР2' AND "Пол" = 'М' THEN 'ДР2 М'
        ELSE 'ДР'
    END as Цель_,
       count(*)                        as "К-во",
       ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
  and "Код СМО" like '360%'
  AND "Санкции" is null
  AND "Цель" in ('ДР1', 'ДР2')
GROUP BY Цель_

union all

SELECT concat("Цель", ' ', "Тариф") as Цель_,
       count(*)                        as "К-во",
       ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
  and "Код СМО" like '360%'
  AND "Санкции" is null
  AND "Цель" = '307'
GROUP BY Цель_

union all

SELECT      CASE
        WHEN "Цель" = '22' AND "Посещения на Дому" = '0' THEN '22 в МО'
        WHEN "Цель" = '22' AND "Посещения на Дому" = '1' THEN '22 на дому'
        ELSE "Цель" || ' ' || "Посещения на Дому"
    END as Цель_,
       count(*)                        as "К-во",
       ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
  and "Код СМО" like '360%'
  AND "Санкции" is null
  AND "Цель" = '22'
GROUP BY Цель_

union all

SELECT CASE
           WHEN "Цель" = '3' and "Профиль МП" = '136' THEN '3 акушерство и гинекология'
           WHEN "Цель" = '3' and "Профиль МП" = '28' THEN '3 инфекционные болезни'
           WHEN "Цель" = '3' and "Профиль МП" = '29' and "Диагноз основной (DS1)" not like 'I%' THEN '3 кардиологии другие'
           WHEN "Цель" = '3' and "Профиль МП" = '29' and "Диагноз основной (DS1)" like 'I%' THEN '3 кардиологии БСК'
           WHEN "Цель" = '3' and "Профиль МП" = '53' THEN '3 неврологии'
           WHEN "Цель" = '3' and ("Профиль МП" = '57' or "Профиль МП" = '97') and "Диагноз основной (DS1)" like 'E11%' THEN '3 Терапия сахарный диабет'
           WHEN "Цель" = '3' and ("Профиль МП" = '57' or "Профиль МП" = '97') and "Диагноз основной (DS1)" like 'I%' THEN '3 Терапия БСК'  
           WHEN "Цель" = '3' and ("Профиль МП" = '57' or "Профиль МП" = '97') and "Диагноз основной (DS1)" not like any(array['I%', 'E11%'])THEN '3 Терапия другие'                                                     
           WHEN "Цель" = '3' and "Профиль МП" = '60' and "Диагноз основной (DS1)" like 'C%' and "Диагноз основной (DS1)" not like 'C44%' THEN '3 онкологии C44'
           WHEN "Цель" = '3' and "Профиль МП" = '60' and "Диагноз основной (DS1)" like 'C44%' THEN '3 онкологии C01-C96'
           WHEN "Цель" = '3' and "Профиль МП" = '60' and "Диагноз основной (DS1)" not like 'C%' THEN '3 онкологии'
           WHEN "Цель" = '3' and "Профиль МП" = '162' THEN '3 оториноларингологии'
           WHEN "Цель" = '3' and "Профиль МП" = '65' THEN '3 офтальмологии'
           WHEN "Цель" = '3' and "Профиль МП" = '100' THEN '3 травматологии и ортопедии'
           WHEN "Цель" = '3' and "Профиль МП" = '108' THEN '3 урологии'
           WHEN "Цель" = '3' and "Профиль МП" = '112' THEN '3 хирургии'
           WHEN "Цель" = '3' and "Профиль МП" = '122' THEN '3 эндокринологии'
           ELSE "Цель" 
           END                         AS "Цель",
       COUNT(*)                        AS "К-во",
       ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND ("Санкции" is null or "Санкции" = '1288.7')
  AND "Цель" = '3'
  AND "Тариф" != '0'
  and "Код СМО" like '360%'
GROUP BY  CASE
           WHEN "Цель" = '3' and "Профиль МП" = '136' THEN '3 акушерство и гинекология'
           WHEN "Цель" = '3' and "Профиль МП" = '28' THEN '3 инфекционные болезни'
           WHEN "Цель" = '3' and "Профиль МП" = '29' and "Диагноз основной (DS1)" not like 'I%' THEN '3 кардиологии другие'
           WHEN "Цель" = '3' and "Профиль МП" = '29' and "Диагноз основной (DS1)" like 'I%' THEN '3 кардиологии БСК'
           WHEN "Цель" = '3' and "Профиль МП" = '53' THEN '3 неврологии'
           WHEN "Цель" = '3' and ("Профиль МП" = '57' or "Профиль МП" = '97') and "Диагноз основной (DS1)" like 'E11%' THEN '3 Терапия сахарный диабет'
           WHEN "Цель" = '3' and ("Профиль МП" = '57' or "Профиль МП" = '97') and "Диагноз основной (DS1)" like 'I%' THEN '3 Терапия БСК'  
           WHEN "Цель" = '3' and ("Профиль МП" = '57' or "Профиль МП" = '97') and "Диагноз основной (DS1)" not like any(array['I%', 'E11%'])THEN '3 Терапия другие'                                                     
           WHEN "Цель" = '3' and "Профиль МП" = '60' and "Диагноз основной (DS1)" like 'C%' and "Диагноз основной (DS1)" not like 'C44%' THEN '3 онкологии C44'
           WHEN "Цель" = '3' and "Профиль МП" = '60' and "Диагноз основной (DS1)" like 'C44%' THEN '3 онкологии C01-C96'
           WHEN "Цель" = '3' and "Профиль МП" = '60' and "Диагноз основной (DS1)" not like 'C%' THEN '3 онкологии'
           WHEN "Цель" = '3' and "Профиль МП" = '162' THEN '3 оториноларингологии'
           WHEN "Цель" = '3' and "Профиль МП" = '65' THEN '3 офтальмологии'
           WHEN "Цель" = '3' and "Профиль МП" = '100' THEN '3 травматологии и ортопедии'
           WHEN "Цель" = '3' and "Профиль МП" = '108' THEN '3 урологии'
           WHEN "Цель" = '3' and "Профиль МП" = '112' THEN '3 хирургии'
           WHEN "Цель" = '3' and "Профиль МП" = '122' THEN '3 эндокринологии'
           ELSE "Цель" 
           end
union all
select distinct "КСГ",
                COUNT(*)                        AS "К-во",
                ROUND(SUM(CAST("Тариф" AS numeric(10, 2)))::numeric, 2) as "Сумма"

from oms.oms_data
where "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  and "КСГ" is not null
  AND "Тариф" != '0'
   and "Код СМО" like '360%'
  AND "Санкции" is null
group by "КСГ"
"""
