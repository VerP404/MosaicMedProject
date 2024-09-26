sql_gen_invoices = """SELECT "Первоначальная дата ввода" AS "дата ввода",
       sum(case when "Цель" = '1' then 1 end)                                                     as "1",
       sum(case when "Цель" = '3' then 1 end)                                                     as "3",
       sum(case when "Цель" = '305' or "Цель" = '307' then 1 end)                                 as "305, 307 D",
       sum(case when "Цель" = '13' or "Цель" = '14' or "Цель" = '140' then 1 end)                 as "13,14,140 Z",
       sum(case when "Цель" = '64' or "Цель" = '640' then 1 end)                                  as "64 G",
       sum(case when "Цель" = '541' or "Цель" = '561' then 1 end)                                 as "541,561 E",
       sum(case when "Цель" = '22' then 1 end)                                                    as "22 N",
       sum(case when "Цель" = '30' or "Цель" = '301' then 1 end)                                  as "30,301 O",
       sum(case when "Диагноз основной (DS1)" like 'C%' and "Тип талона" like '%Амб%' then 1 end) as "онко C",
       sum(case
               when "Цель" = '5' or "Цель" = '7' or "Цель" = '9' or "Цель" = '10' or "Цель" = '32' then 1
               end)                                                                               as "5,7,9,10,32 P",
       sum(case
               when "Цель" = 'В дневном стационаре' or "Цель" = 'На дому' then 1
               end)                                                                               as "ст SD",
       sum(case when "Цель" = 'ДВ4' then 1 end)                                                   as "ДВ4 V",
       sum(case when "Цель" = 'ДВ2' then 1 end)                                                   as "ДВ2 T",
       sum(case when "Цель" = 'ОПВ' then 1 end)                                                   as "ОПВ P",
       sum(case when "Цель" = 'УД1' then 1 end)                                                   as "УД1 U",
       sum(case when "Цель" = 'УД2' then 1 end)                                                   as "УД2 Y",
       sum(case when "Цель" = 'ДР1' then 1 end)                                                   as "ДР1 R",
       sum(case when "Цель" = 'ДР2' then 1 end)                                                   as "ДР2 Q",
       sum(case when "Цель" = 'ПН1' then 1 end)                                                   as "ПН1 N",
       sum(case when "Цель" = 'ДС2' then 1 end)                                                   as "ДС2 S",
       sum(case
               when "Цель" IN
                    ('1', '3', '305', '307', '7', '13', '14', '140', '64', '640', '541', '561', '22',
                   '30', '301', '5', '6', '9', '10', '32', 'В дневном стационаре', 'На дому', 'ДВ4',
                   'ДВ2', 'ОПВ', 'ДР1', 'ДР2', 'УД1', 'УД2', 'ПН1', 'ДС2') THEN 1
               end)                                                                               as "Всего"
FROM oms.oms_data
WHERE "Статус" = '1'
  AND "Тариф" != '0'
    AND ("Цель" IN ('1', '3', '305', '307', '7', '13', '14', '140', '64', '640', '541', '561', '22',
                   '30', '301', '5', '6', '9', '10', '32', 'В дневном стационаре', 'На дому', 'ДВ4',
                   'ДВ2', 'ОПВ', 'ДР1', 'ДР2', 'УД1', 'УД2', 'ПН1', 'ДС2'))
                   AND "Код СМО" IN ('36071', '36065')
GROUP BY "Первоначальная дата ввода"
ORDER BY TO_DATE("Первоначальная дата ввода", 'DD-MM-YYYY')"""

sql_gen_invoices_povt = """SELECT "Первоначальная дата ввода" AS "дата ввода",
       sum(case when "Цель" = '1' then 1 end)                                                     as "1",
       sum(case when "Цель" = '3' then 1 end)                                                     as "3",
       sum(case when "Цель" = '305' or "Цель" = '307' then 1 end)                                 as "305, 307 D",
       sum(case when "Цель" = '13' or "Цель" = '14' or "Цель" = '140' then 1 end)                 as "13,14,140 Z",
       sum(case when "Цель" = '64' or "Цель" = '640' then 1 end)                                  as "64 G",
       sum(case when "Цель" = '541' or "Цель" = '561' then 1 end)                                 as "541,561 E",
       sum(case when "Цель" = '22' then 1 end)                                                    as "22 N",
       sum(case when "Цель" = '30' or "Цель" = '301' then 1 end)                                  as "30,301 O",
       sum(case when "Диагноз основной (DS1)" like 'C%' and "Тип талона" like '%Амб%' then 1 end) as "онко C",
       sum(case
               when "Цель" = '5' or "Цель" = '7' or "Цель" = '9' or "Цель" = '10' or "Цель" = '32' then 1
               end)                                                                               as "5,7,9,10,32 P",
       sum(case
               when "Цель" = 'В дневном стационаре' or "Цель" = 'На дому' then 1
               end)                                                                               as "ст SD",
       sum(case when "Цель" = 'ДВ4' then 1 end)                                                   as "ДВ4 V",
       sum(case when "Цель" = 'ДВ2' then 1 end)                                                   as "ДВ2 T",
       sum(case when "Цель" = 'ОПВ' then 1 end)                                                   as "ОПВ P",
       sum(case when "Цель" = 'УД1' then 1 end)                                                   as "УД1 U",
       sum(case when "Цель" = 'УД2' then 1 end)                                                   as "УД2 Y",
       sum(case when "Цель" = 'ДР1' then 1 end)                                                   as "ДР1 R",
       sum(case when "Цель" = 'ДР2' then 1 end)                                                   as "ДР2 Q",
       sum(case when "Цель" = 'ПН1' then 1 end)                                                   as "ПН1 N",
       sum(case when "Цель" = 'ДС2' then 1 end)                                                   as "ДС2 S",
       sum(case
               when "Цель" IN
                    ('1', '3', '305', '307', '7', '13', '14', '140', '64', '640', '541', '561', '22',
                   '30', '301', '5', '6', '9', '10', '32', 'В дневном стационаре', 'На дому', 'ДВ4',
                   'ДВ2', 'ОПВ', 'ДР1', 'ДР2', 'УД1', 'УД2', 'ПН1', 'ДС2') THEN 1
               end)                                                                               as "Всего"
FROM oms.oms_data
WHERE ("Статус" = '6' or "Статус" = '8' or "Статус" = '4')
 AND "Код СМО" IN ('36071', '36065')
  AND "Тариф" != '0'
      AND ("Цель" IN ('1', '3', '305', '307', '7', '13', '14', '140', '64', '640', '541', '561', '22',
                   '30', '301', '5', '6', '9', '10', '32', 'В дневном стационаре', 'На дому', 'ДВ4',
                   'ДВ2', 'ОПВ', 'ДР1', 'ДР2', 'УД1', 'УД2', 'ПН1', 'ДС2'))
GROUP BY "Первоначальная дата ввода"
ORDER BY TO_DATE("Первоначальная дата ввода", 'DD-MM-YYYY')"""


sql_gen_name_check = """
SELECT
    "Номер счёта",
    count(*) AS "Количество",
           sum(case when "Статус" = '3' then 1 else 0 end)                                   as Оплачено,
       sum(case when "Статус" = '2' or "Статус" = '1' or "Статус" = '4'or "Статус" = '6' or "Статус" = '8' 
       then 1 else 0 end)                                   as "В ТФОМС",
       sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
       sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end) as "Отменен",
       sum(case when "Статус" = '1' then 1 else 0 end)                                   as "1",
       sum(case when "Статус" = '2' then 1 else 0 end)                                   as "2",
       sum(case when "Статус" = '3' then 1 else 0 end)                                   as "3",
       sum(case when "Статус" = '4' then 1 else 0 end)                                   as "4",
       sum(case when "Статус" = '5' then 1 else 0 end)                                   as "5",
       sum(case when "Статус" = '6' then 1 else 0 end)                                   as "6",
       sum(case when "Статус" = '7' then 1 else 0 end)                                   as "7",
       sum(case when "Статус" = '8' then 1 else 0 end)                                   as "8",
       sum(case when "Статус" = '12' then 1 else 0 end)                                  as "12",
       sum(case when "Статус" = '13' then 1 else 0 end)                                  as "13",
       sum(case when "Статус" = '17' then 1 else 0 end)                                  as "17",
       sum(case when "Статус" = '0' then 1 else 0 end)                                   as "0"
FROM oms.oms_data
WHERE "Отчетный период выгрузки" != '-' and "Санкции" is null
GROUP BY "Номер счёта"
ORDER BY "Номер счёта"
"""