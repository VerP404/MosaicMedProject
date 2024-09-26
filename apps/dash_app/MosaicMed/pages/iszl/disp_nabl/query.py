sql_query_disp_nabl_svod = """
SELECT
    sp_mkb."Специальность совместная" as "Тип",
    COALESCE(iszl_counts."к-во в ИСЗЛ", 0) as "к-во в ИСЗЛ",
    COALESCE(oms_counts."к-во в ОМС", 0) as "выставлено",
    COALESCE(oms_status_counts."к-во в ОМС статус 3", 0) as "оплачено"
FROM (
    SELECT DISTINCT "Специальность совместная"
    FROM info.dn168n_data
) AS sp_mkb
LEFT JOIN (
    SELECT
        sp_mkb."Специальность совместная",
        COUNT(*) as "к-во в ИСЗЛ"
    FROM iszl.iszl_data
    LEFT JOIN (
        SELECT DISTINCT "Код МКБ", "Специальность совместная"
        FROM info.dn168n_data
    ) AS sp_mkb ON iszl.iszl_data."DS" = sp_mkb."Код МКБ"
    WHERE "Специальность совместная" IS NOT NULL
    GROUP BY sp_mkb."Специальность совместная"
) AS iszl_counts ON sp_mkb."Специальность совместная" = iszl_counts."Специальность совместная"
LEFT JOIN (
    SELECT
        sp_mkb."Специальность совместная",
        COUNT(*) as "к-во в ОМС"
    FROM (
            SELECT DISTINCT
                SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
                "ЕНП"
            FROM oms.oms_data
            WHERE "Цель" = '3' AND "Статус" IN ('1', '2', '3', '6', '8')
    ) AS oms
    LEFT JOIN (
        SELECT DISTINCT "Код МКБ", "Специальность совместная"
        FROM info.dn168n_data
    ) AS sp_mkb ON oms."Диагноз" = sp_mkb."Код МКБ"
    WHERE "Специальность совместная" IS NOT NULL
    GROUP BY sp_mkb."Специальность совместная"
) AS oms_counts ON sp_mkb."Специальность совместная" = oms_counts."Специальность совместная"
LEFT JOIN (
    SELECT
        sp_mkb."Специальность совместная",
        COUNT(*) as "к-во в ОМС статус 3"
    FROM (
            SELECT DISTINCT
                SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
                "ЕНП"
            FROM oms.oms_data
            WHERE "Цель" = '3' AND "Статус" = '3'
    ) AS oms_status
    LEFT JOIN (
        SELECT DISTINCT "Код МКБ", "Специальность совместная"
        FROM info.dn168n_data
    ) AS sp_mkb ON oms_status."Диагноз" = sp_mkb."Код МКБ"
    WHERE "Специальность совместная" IS NOT NULL
    GROUP BY sp_mkb."Специальность совместная"
) AS oms_status_counts ON sp_mkb."Специальность совместная" = oms_status_counts."Специальность совместная"
union all
SELECT
    '(J44) ХОБЛ' as "Тип",
    count(DISTINCT "ENP") as "к-во в ИСЗЛ",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" IN ('1', '2', '3', '6', '8') and "Диагноз основной (DS1)" like '%J44%') as "выставлено",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" = '3' and "Диагноз основной (DS1)" like '%J44%') as "оплачено"
FROM iszl.iszl_data
WHERE "DS" like '%J44%'
union all
SELECT
    '(I20-I25) ИБС' as "Тип",
    count(DISTINCT "ENP") as "к-во в ИСЗЛ",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" IN ('1', '2', '3', '6', '8') and "Диагноз основной (DS1)" like any(array['%I20%', '%I21%', '%I22%', '%I23%', '%I24%', '%I25%']) ) as "выставлено",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" = '3' and "Диагноз основной (DS1)" like any(array['%I20%', '%I21%', '%I22%', '%I23%', '%I24%', '%I25%']) ) as "оплачено"
FROM iszl.iszl_data
WHERE "DS" like any(array['%I20%', '%I21%', '%I22%', '%I23%', '%I24%', '%I25%']) 
union all
SELECT
    '(I) БСК (пациенты)' as "Тип",
    count(DISTINCT "ENP") as "к-во в ИСЗЛ",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" IN ('1', '2', '3', '6', '8') and "Диагноз основной (DS1)" like 'I%') as "выставлено",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" = '3' and "Диагноз основной (DS1)" like 'I%') as "оплачено"
FROM iszl.iszl_data
WHERE "DS" like 'I%'
union all
SELECT
    '(C) онкология (пациенты)' as "Тип",
    count(DISTINCT "ENP") as "к-во в ИСЗЛ",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" IN ('1', '2', '3', '6', '8') and "Диагноз основной (DS1)" like 'C%') as "выставлено",
    (SELECT count(DISTINCT "ЕНП") FROM oms.oms_data WHERE "Цель" = '3' AND "Статус" = '3' and "Диагноз основной (DS1)" like 'C%') as "оплачено"
FROM iszl.iszl_data
WHERE "DS" like 'C%'
order by "Тип"
"""

sql_query_disp_nabl_talon = """
select
    39869 as "План ТФОМС",
    sum(case when "Цель" = '3' and "Статус" in ('1', '2', '3', '6', '8') then 1 else 0 end ) as  "в работе",
    ROUND(SUM(CASE WHEN "Цель" = '3' AND "Статус" IN ('1', '2', '3', '6', '8') THEN 1 ELSE 0 END) / 39869.0 * 100, 2) as "% предъявленных",
    39869 - sum(case when "Цель" = '3' and "Статус" in ('1', '2', '3', '6', '8') then 1 else 0 end ) as  "остаток предъявить",
    sum(case when "Цель" = '3' and "Статус" in ('3') then 1 else 0 end ) as  "оплачено",
    ROUND(SUM(case when "Цель" = '3' and "Статус" in ('3') then 1 else 0 end ) / 39869.0 * 100, 2) as "% оплаченных",
    39869 - sum(case when "Цель" = '3' and "Статус" in ('3') then 1 else 0 end ) as  "остаток не оплачено"
from oms.oms_data
where "Цель" = '3'
"""



sql_query_disp_nabl_list = """
select DISTINCT ON ("ENP", "Специальность совместная") "FIO",
       "DR",
       "DS",
       "ENP",
       "LPUUCH",
       "Корпус",
       "Специальность совместная" as "Специальность 168н",
       TO_CHAR(TO_DATE(oms_sort."Окончание лечения", 'DD-MM-YYYY'), 'DD-MM-YY') AS "Окончание лечения (дд-мм-гг)",
              oms_sort."Врач",
       oms_sort."Цель",
       oms_sort."Тип талона",
       "Диагноз ОМС"
from (((select "FIO",
       "DR",
       "DS",
       "ENP",
       "LPUUCH",
       "Корпус"
from iszl.iszl_data left join info.area_data on iszl.iszl_data."LPUUCH" = info.area_data."Участок") as isql_korp left join (select distinct "Код МКБ",
                "Специальность совместная"
from info.dn168n_data) as sp_mkb on isql_korp."DS" = sp_mkb."Код МКБ") as iszl_168н left join oms.oms_data on
    SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) = iszl_168н."DS" and "ЕНП"="ENP") as iszl_168_3
left join (WITH ranked_data AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY "ЕНП" ORDER BY TO_DATE("Окончание лечения", 'DD-MM-YYYY') DESC) AS row_num
    FROM oms.oms_data
    WHERE "Окончание лечения" ~ '\d{2}-\d{2}-\d{4}' -- Фильтруем строки с датами
    and "Цель" != '3'
)
SELECT "Окончание лечения",
       "ЕНП",
       "Цель",
       "Тип талона",
       "Врач",
       SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз ОМС"
FROM ranked_data
WHERE row_num = 1) as oms_sort on  iszl_168_3."ENP" = oms_sort."ЕНП"
where "Специальность совместная" is not null
  and iszl_168_3."Талон" is null
  and oms_sort."Окончание лечения" is not null
order by "ENP", "Специальность совместная","FIO"
"""

sql_query_disp_nabl_list_svod = """
select distinct "Специальность 168н",
        count(*) as "К-во"
        from (select DISTINCT ON ("ENP", "Специальность совместная") "FIO",
       "DR",
       "DS",
       "ENP",
       "LPUUCH",
       "Корпус",
       "Специальность совместная" as "Специальность 168н",
       TO_CHAR(TO_DATE(oms_sort."Окончание лечения", 'DD-MM-YYYY'), 'DD-MM-YY') AS "Окончание лечения (дд-мм-гг)",
       oms_sort."Цель",
       oms_sort."Тип талона",
       "Диагноз ОМС"
from (((select "FIO",
       "DR",
       "DS",
       "ENP",
       "LPUUCH",
       "Корпус"
from iszl.iszl_data left join info.area_data on iszl.iszl_data."LPUUCH" = info.area_data."Участок") as isql_korp left join (select distinct "Код МКБ",
                "Специальность совместная"
from info.dn168n_data) as sp_mkb on isql_korp."DS" = sp_mkb."Код МКБ") as iszl_168н left join oms.oms_data on
    SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) = iszl_168н."DS" and "ЕНП"="ENP") as iszl_168_3
left join (WITH ranked_data AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY "ЕНП" ORDER BY TO_DATE("Окончание лечения", 'DD-MM-YYYY') DESC) AS row_num
    FROM oms.oms_data
    WHERE "Окончание лечения" ~ '\d{2}-\d{2}-\d{4}' -- Фильтруем строки с датами
    and "Цель" != '3'
)
SELECT "Окончание лечения",
       "ЕНП",
       "Цель",
       "Тип талона",
       "Врач",
       SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз ОМС"
FROM ranked_data
WHERE row_num = 1) as oms_sort on  iszl_168_3."ENP" = oms_sort."ЕНП"
where "Специальность совместная" is not null
  and iszl_168_3."Талон" is null
  and oms_sort."Окончание лечения" is not null
order by "ENP", "Специальность совместная","FIO") as om
group by "Специальность 168н"
"""


sql_query_disp_nabl_fgs = """
SELECT
"FIO",	"DR",	"DS" as "DS ИСЗЛ", "Корпус", "Участок", "Процедура", "Дата приема"
from ((iszl.iszl_data inner join (SELECT DISTINCT ON ("Код МКБ") * FROM info.dn168n_data) as pr on iszl.iszl_data."DS"=pr."Код МКБ")
    as iszl_168 left join info.area_data on iszl_168."LPUUCH" = info.area_data."Участок") as iszl
    left join (select DISTINCT ON ("ЕНП") *
from kvazar.obrproc_data
where "Процедура" like ANY(array['%ЭГДС%', '%Колон%'])) as obr on iszl."ENP" = obr."ЕНП"
WHERE "DS" like ANY(array['K%','D12.8'])
order by "FIO"
"""

sql_query_disp_nabl_fgs_168n = """
SELECT
    CASE
        WHEN position('.' in "DS") > 0 THEN substring("DS" from 1 for position('.' in "DS") - 1)
        ELSE "DS"
    END AS "Диагноз",
    count(*) AS "Всего",
    sum(case when "Процедура" is not null then 1 else 0 end ) as "Записано",
    sum(case when "Корпус" = 'ГП3' then 1 else 0 end ) as "ГП3",
    sum(case when "Корпус" = 'ГП3' and "Процедура" is not null then 1 else 0 end ) as "ГП3 записан",
    sum(case when "Корпус" = 'ГП11' then 1 else 0 end ) as "ГП11",
    sum(case when "Корпус" = 'ГП11' and "Процедура" is not null then 1 else 0 end ) as "ГП11 записан",
    sum(case when "Корпус" = 'ОАПП1'  then 1 else 0 end ) as "ОАПП1",
    sum(case when "Корпус" = 'ОАПП1' and "Процедура" is not null then 1 else 0 end ) as "ОАПП1 записан",
    sum(case when "Корпус" = 'ОАПП2' then 1 else 0 end ) as "ОАПП2",
    sum(case when "Корпус" = 'ОАПП2' and "Процедура" is not null then 1 else 0 end ) as "ОАПП2 записан",
    sum(case when "Корпус" not in ('ГП3', 'ГП11', 'ОАПП1', 'ОАПП2') then 1 else 0 end ) as "нет корпуса",
    sum(case when "Корпус" not in ('ГП3', 'ГП11', 'ОАПП1', 'ОАПП2') and "Процедура" is not null then 1 else 0 end ) as "нет корпуса записан"
FROM ((iszl.iszl_data
INNER JOIN (SELECT DISTINCT ON ("Код МКБ") * FROM info.dn168n_data) as pr on iszl.iszl_data."DS"=pr."Код МКБ") as iszl_168
LEFT JOIN info.area_data on iszl_168."LPUUCH" = info.area_data."Участок") as iszl
LEFT JOIN (SELECT DISTINCT ON ("ЕНП") *
            FROM kvazar.obrproc_data
            WHERE "Процедура" like ANY(array['%ЭГДС%', '%Колон%'])) as obr on iszl."ENP" = obr."ЕНП"
WHERE "DS" like ANY(array['K%','D12.8'])
GROUP BY "Диагноз"

UNION ALL
SELECT 'Итого',
    count(*),
    sum(case when "Процедура" is not null then 1 else 0 end ),
    sum(case when "Корпус" = 'ГП3' then 1 else 0 end ),
    sum(case when "Корпус" = 'ГП3' and "Процедура" is not null then 1 else 0 end ),
    sum(case when "Корпус" = 'ГП11' then 1 else 0 end ),
    sum(case when "Корпус" = 'ГП11' and "Процедура" is not null then 1 else 0 end ),
    sum(case when "Корпус" = 'ОАПП1'  then 1 else 0 end ),
    sum(case when "Корпус" = 'ОАПП1' and "Процедура" is not null then 1 else 0 end ),
    sum(case when "Корпус" = 'ОАПП2' then 1 else 0 end ),
    sum(case when "Корпус" = 'ОАПП2' and "Процедура" is not null then 1 else 0 end ),
    sum(case when "Корпус" not in ('ГП3', 'ГП11', 'ОАПП1', 'ОАПП2') then 1 else 0 end ),
    sum(case when "Корпус" not in ('ГП3', 'ГП11', 'ОАПП1', 'ОАПП2') and "Процедура" is not null then 1 else 0 end )
FROM ((iszl.iszl_data
INNER JOIN (SELECT DISTINCT ON ("Код МКБ") * FROM info.dn168n_data) as pr on iszl.iszl_data."DS"=pr."Код МКБ") as iszl_168
LEFT JOIN info.area_data on iszl_168."LPUUCH" = info.area_data."Участок") as iszl
LEFT JOIN (SELECT DISTINCT ON ("ЕНП") *
            FROM kvazar.obrproc_data
            WHERE "Процедура" like ANY(array['%ЭГДС%', '%Колон%'])) as obr on iszl."ENP" = obr."ЕНП"
WHERE "DS" like ANY(array['K%','D12.8'])
order by "Диагноз"
"""


sql_query_zap_obr = """
select "Процедура",
       count(*) as Записано
from (select DISTINCT ON ("ЕНП", "Процедура") *
from kvazar.obrproc_data
WHERE "Процедура" like ANY(array['%ЭГДС%', '%Колон%'])) as  pr
group by ROLLUP("Процедура")
order by "Процедура"
"""
sql_query_list_iszl = """
with iszl_korp as (
    select iszl.iszl_data.*,
           info.area_data."Корпус"
    from iszl.iszl_data left join info.area_data on iszl.iszl_data."LPUUCH"=info.area_data."Участок"
)
SELECT
    "ENP" as "ЕНП",
"FIO" as "ФИО",
"DR" as "ДР",
"LPUUCH" as "Участок",
"Корпус",
    STRING_AGG("DS", ', ' ORDER BY "DS") AS "Диагнозы в ИСЗЛ",
    CASE
        WHEN COUNT(DISTINCT "DS") > COUNT(DISTINCT LEFT("DS", 1))
        THEN 'да'
        ELSE 'нет'
    END AS "Диагнозы в одной группе",
    CASE
        WHEN COUNT(DISTINCT "DS") > COUNT(DISTINCT LEFT("DS", 3))
        THEN 'да'
        ELSE 'нет'
    END AS "Диагнозы в одной подгруппе"
FROM iszl_korp
GROUP BY "ENP", "FIO","DR", "LPUUCH", "Корпус"
order by "FIO"
"""

sql_query_list_oms = """
with oms_fil as (
    select          SUBSTRING("Диагноз основной (DS1)", 1,
           POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
                   *
    from oms.oms_data
    where "Статус" in ('1','2','3', '6', '8')
    and "Цель" = '3'
)

select "ЕНП",
       "Пациент" as "ФИО",
       "Дата рождения" as "ДР",
    STRING_AGG("Диагноз", ', ' ORDER BY "Диагноз") AS "Диагнозы в ОМС",
    CASE
        WHEN COUNT(DISTINCT "Диагноз") > COUNT(DISTINCT LEFT("Диагноз", 1))
        THEN 'да'
        ELSE 'нет'
    END AS "Диагнозы в одной группе",
    CASE
        WHEN COUNT(DISTINCT "Диагноз") > COUNT(DISTINCT LEFT("Диагноз", 3))
        THEN 'да'
        ELSE 'нет'
    END AS "Диагнозы в одной подгруппе"
from oms_fil
group by "ЕНП", "Пациент", "ДР"
order by "Пациент"
"""

sql_query_list_iszl_oms = """
with
    iszl_korp as (
        select iszl.iszl_data.*,
              "Корпус"
        from iszl.iszl_data left join info.area_data on iszl.iszl_data."LPUUCH"=info.area_data."Участок"
),
    uniq_168n as(
        select distinct info.dn168n_data."Код МКБ"
        from info.dn168n_data
),
    iszl_168n as (
        select iszl_korp.*
        from iszl_korp left join uniq_168n on iszl_korp."DS"=uniq_168n."Код МКБ"
        where "Код МКБ" is not null
),
    iszl_list_pacients as (
        SELECT
            "ENP" as "ЕНП",
            "FIO" as "ФИО",
            "DR" as "ДР",
            "LPUUCH" as "Участок",
            "Корпус",
            STRING_AGG("DS", ', ' ORDER BY "DS") AS "Диагнозы в ИСЗЛ"
        FROM iszl_168n
        GROUP BY "ENP", "FIO","DR", "LPUUCH", "Корпус"
        order by "FIO"
),
    oms_fil as (
        select          SUBSTRING("Диагноз основной (DS1)", 1,
               POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
                       *
        from oms.oms_data
        where "Статус" in ('1','2','3','6','8')
                    and "Цель" = '3'
),
    oms_list as (
        SELECT
            "ЕНП",
            "Пациент" AS "ФИО",
            "Дата рождения" AS "ДР",
            STRING_AGG(DISTINCT "Диагноз", ', ' ORDER BY "Диагноз") AS "Диагнозы в ОМС"
        FROM oms_fil
        GROUP BY "ЕНП", "Пациент", "ДР"
        ORDER BY "Пациент"
),
    oms_soput_dia as (
        SELECT
        "ЕНП",
        STRING_AGG(DISTINCT diagnosis, ', ' ORDER BY diagnosis) AS "Сопутствующие диагнозы"
        FROM (
            SELECT
                "ЕНП",
                "Сопутствующий диагноз (DS2)",
                regexp_matches("Сопутствующий диагноз (DS2)", '([A-Z][0-9]+\s|[A-Z][0-9]+\.[0-9])', 'g') AS matches
            FROM oms.oms_data
            where "Статус" in ('1','2','3','6','8')
                        and "Цель" = '3'
            ) AS subquery
        CROSS JOIN LATERAL UNNEST(matches) AS diagnosis
        GROUP BY "ЕНП", "Сопутствующий диагноз (DS2)"
),
    oms_vse_dia as (SELECT oms_list.*,
                    "Сопутствующие диагнозы",
                    case
                        when "Сопутствующие диагнозы" is not null then CONCAT(oms_list."Диагнозы в ОМС", ', ',
                                                                              oms_soput_dia."Сопутствующие диагнозы")
                        else oms_list."Диагнозы в ОМС"
                        end AS "Все диагнозы в ОМС"
             FROM oms_list
                      LEFT JOIN oms_soput_dia ON oms_list."ЕНП" = oms_soput_dia."ЕНП"
 ),
    oms_ as (
        SELECT "ЕНП",
               STRING_AGG(DISTINCT diagnosis, ', ' ORDER BY diagnosis) AS "ll"
        FROM (
            SELECT "ЕНП",
                   UNNEST(STRING_TO_ARRAY("Все диагнозы в ОМС", ', ')) AS diagnosis
            FROM oms_vse_dia
        ) AS subquery
        GROUP BY "ЕНП"
),
    oms_itog as (
        select oms_list."ЕНП",
               oms_list."ФИО",
               oms_list."ДР",
               oms_.ll as "Диагнозы в ОМС"
        from oms_list left join oms_ on oms_list."ЕНП"=oms_."ЕНП"
    ),table_1 as (

SELECT
    iszl_list_pacients."ЕНП",
    iszl_list_pacients."ФИО",
    iszl_list_pacients."ДР",
    iszl_list_pacients."Участок",
    iszl_list_pacients."Корпус",
    iszl_list_pacients."Диагнозы в ИСЗЛ",
    oms_itog."Диагнозы в ОМС",
    STRING_AGG(diagnosis, ', ' ORDER BY diagnosis) AS "Нет талона ОМС"
FROM iszl_list_pacients
LEFT JOIN oms_itog ON iszl_list_pacients."ЕНП" = oms_itog."ЕНП"
LEFT JOIN (
    SELECT
        iszl_168n."ENP",
        iszl_168n."DS" AS diagnosis
    FROM iszl_168n
    EXCEPT
    SELECT
        "ЕНП",
        UNNEST(STRING_TO_ARRAY(oms_itog."Диагнозы в ОМС", ', ')) AS diagnosis
    FROM oms_itog
) AS unique_iszl_diagnoses ON iszl_list_pacients."ЕНП" = unique_iszl_diagnoses."ENP"
GROUP BY iszl_list_pacients."ЕНП", iszl_list_pacients."ФИО", iszl_list_pacients."ДР",
         iszl_list_pacients."Участок", iszl_list_pacients."Корпус",
         iszl_list_pacients."Диагнозы в ИСЗЛ", oms_itog."Диагнозы в ОМС"
order by  "ФИО")
select table_1.*,
       info.naselenie_data."Телефон Квазар",
       info.naselenie_data."Телефон МИС КАУЗ"
from table_1 left join info.naselenie_data on table_1."ЕНП"=info.naselenie_data."ЕНП"
"""


sql_query_list_iszl_oms_report = """
with
    iszl_korp as (
        select iszl.iszl_data.*,
              "Корпус"
        from iszl.iszl_data left join info.area_data on iszl.iszl_data."LPUUCH"=info.area_data."Участок"
),
    uniq_168n as(
        select distinct info.dn168n_data."Код МКБ"
        from info.dn168n_data
),
    iszl_168n as (
        select iszl_korp.*
        from iszl_korp left join uniq_168n on iszl_korp."DS"=uniq_168n."Код МКБ"
        where "Код МКБ" is not null
),
    iszl_list_pacients as (
        SELECT
            "ENP" as "ЕНП",
            "FIO" as "ФИО",
            "DR" as "ДР",
            "LPUUCH" as "Участок",
            "Корпус",
            STRING_AGG("DS", ', ' ORDER BY "DS") AS "Диагнозы в ИСЗЛ"
        FROM iszl_168n
        GROUP BY "ENP", "FIO","DR", "LPUUCH", "Корпус"
        order by "FIO"
),
    oms_fil as (
        select          SUBSTRING("Диагноз основной (DS1)", 1,
               POSITION(' ' IN "Диагноз основной (DS1)") - 1) as "Диагноз",
                       *
        from oms.oms_data
        where "Статус" in ('1','2','3','6','8')
                    and "Цель" = '3'
),
    oms_list as (
        SELECT
            "ЕНП",
            "Пациент" AS "ФИО",
            "Дата рождения" AS "ДР",
            STRING_AGG(DISTINCT "Диагноз", ', ' ORDER BY "Диагноз") AS "Диагнозы в ОМС"
        FROM oms_fil
        GROUP BY "ЕНП", "Пациент", "ДР"
        ORDER BY "Пациент"
),
    oms_soput_dia as (
        SELECT
        "ЕНП",
        STRING_AGG(DISTINCT diagnosis, ', ' ORDER BY diagnosis) AS "Сопутствующие диагнозы"
        FROM (
            SELECT
                "ЕНП",
                "Сопутствующий диагноз (DS2)",
                regexp_matches("Сопутствующий диагноз (DS2)", '([A-Z][0-9]+\s|[A-Z][0-9]+\.[0-9])', 'g') AS matches
            FROM oms.oms_data
            where "Статус" in ('1','2','3','6','8')
                        and "Цель" = '3'
            ) AS subquery
        CROSS JOIN LATERAL UNNEST(matches) AS diagnosis
        GROUP BY "ЕНП", "Сопутствующий диагноз (DS2)"
),
    oms_vse_dia as (SELECT oms_list.*,
                    "Сопутствующие диагнозы",
                    case
                        when "Сопутствующие диагнозы" is not null then CONCAT(oms_list."Диагнозы в ОМС", ', ',
                                                                              oms_soput_dia."Сопутствующие диагнозы")
                        else oms_list."Диагнозы в ОМС"
                        end AS "Все диагнозы в ОМС"
             FROM oms_list
                      LEFT JOIN oms_soput_dia ON oms_list."ЕНП" = oms_soput_dia."ЕНП"
 ),
    oms_ as (
        SELECT "ЕНП",
               STRING_AGG(DISTINCT diagnosis, ', ' ORDER BY diagnosis) AS "ll"
        FROM (
            SELECT "ЕНП",
                   UNNEST(STRING_TO_ARRAY("Все диагнозы в ОМС", ', ')) AS diagnosis
            FROM oms_vse_dia
        ) AS subquery
        GROUP BY "ЕНП"
),
    oms_itog as (
        select oms_list."ЕНП",
               oms_list."ФИО",
               oms_list."ДР",
               oms_.ll as "Диагнозы в ОМС"
        from oms_list left join oms_ on oms_list."ЕНП"=oms_."ЕНП"
),
    itog as (
        SELECT
            iszl_list_pacients."ЕНП",
            iszl_list_pacients."ФИО",
            iszl_list_pacients."ДР",
            iszl_list_pacients."Участок",
            iszl_list_pacients."Корпус",
            iszl_list_pacients."Диагнозы в ИСЗЛ",
            oms_itog."Диагнозы в ОМС",
            STRING_AGG(diagnosis, ', ' ORDER BY diagnosis) AS "Нет талона ОМС"
        FROM iszl_list_pacients
        LEFT JOIN oms_itog ON iszl_list_pacients."ЕНП" = oms_itog."ЕНП"
        LEFT JOIN (
            SELECT
                iszl_168n."ENP",
                iszl_168n."DS" AS diagnosis
            FROM iszl_168n
            EXCEPT
            SELECT
                "ЕНП",
                UNNEST(STRING_TO_ARRAY(oms_itog."Диагнозы в ОМС", ', ')) AS diagnosis
            FROM oms_itog
        ) AS unique_iszl_diagnoses ON iszl_list_pacients."ЕНП" = unique_iszl_diagnoses."ENP"
        GROUP BY iszl_list_pacients."ЕНП", iszl_list_pacients."ФИО", iszl_list_pacients."ДР",
                 iszl_list_pacients."Участок", iszl_list_pacients."Корпус",
                 iszl_list_pacients."Диагнозы в ИСЗЛ", oms_itog."Диагнозы в ОМС"
        order by  "ФИО")


select "Корпус",
    count(*) as "Всего в ИСЗЛ",
    sum(case when "Нет талона ОМС" is not null then 1 else 0 end ) as "К-во не прошедших",
    sum(case when ("Диагнозы в ОМС" not like '%I%' or "Диагнозы в ОМС" is null) and "Нет талона ОМС" like '%I%' then 1 else 0 end ) as "К-во не прошедших по БСК",
    sum(case when ("Диагнозы в ОМС" not like '%I%' or "Диагнозы в ОМС" is null) and "Нет талона ОМС" like any(array['%I20%', '%I21%', '%I22%', '%I23%', '%I24%', '%I25%'])  then 1 else 0 end ) as "из них по ИБС",
    sum(case when ("Диагнозы в ОМС" not like '%C%' or "Диагнозы в ОМС" is null) and "Нет талона ОМС" like '%C%' then 1 else 0 end ) as "К-во не прошедших по онкологии"

from itog
where "Корпус" in ('ГП11', 'ГП3', 'ОАПП1', 'ОАПП2')
group by "Корпус"
union all
select '_Итого',
    count(*) as "Всего в ИСЗЛ",
    sum(case when "Нет талона ОМС" is not null then 1 else 0 end ) as "К-во не прошедших",
    sum(case when ("Диагнозы в ОМС" not like '%I%' or "Диагнозы в ОМС" is null) and "Нет талона ОМС" like '%I%' then 1 else 0 end ) as "К-во не прошедших по БСК",
    sum(case when ("Диагнозы в ОМС" not like '%I%' or "Диагнозы в ОМС" is null) and "Нет талона ОМС" like any(array['%I20%', '%I21%', '%I22%', '%I23%', '%I24%', '%I25%'])  then 1 else 0 end ) as "из них по ИБС",
    sum(case when ("Диагнозы в ОМС" not like '%C%' or "Диагнозы в ОМС" is null) and "Нет талона ОМС" like '%C%' then 1 else 0 end ) as "К-во не прошедших по онкологии"
from itog
where "Корпус" in ('ГП11', 'ГП3', 'ОАПП1', 'ОАПП2')
order by "Корпус"
"""