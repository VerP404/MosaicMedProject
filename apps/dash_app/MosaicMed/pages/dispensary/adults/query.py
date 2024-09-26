# отчет по диспансеризации
def sql_query_dispensary():
    return """
    SELECT
        coalesce("Подразделение", 'Итого')              as Корпус,
        sum(case when "Цель" = 'ДВ4' then 1 else 0 end) as ДВ4,
        sum(case when "Цель" = 'ДВ2' then 1 else 0 end) as ДВ2,
        sum(case when "Цель" = 'ОПВ' then 1 else 0 end) as ОПВ,
        sum(case when "Цель" = 'УД1' then 1 else 0 end) as УД1,
        sum(case when "Цель" = 'УД2' then 1 else 0 end) as УД2
    from oms.oms_data
    where to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') 
    and to_date(:end_date, 'DD-MM-YYYY')
      AND "Подразделение" NOT LIKE '%ДП%'
      and "Подразделение" NOT LIKE '%ЖК%'
    group by rollup ("Подразделение")
"""


def sql_query_do_korpus_dd(sql_cond):
    return f"""
        select COALESCE("Подразделение", 'Итого') AS "Подразделение",
        count(*) as "Всего",
        sum(case when "Статус" = '3' then 1 else 0 end)  as Оплачено,
        sum(case when "Статус" = '2' or "Статус" = '1' then 1 else 0 end)  as "В ТФОМС",
        sum(case when "Статус" = '5' or "Статус" = '7' or "Статус" = '12' then 1 else 0 end)  as "Отказано",
        sum(case when "Статус" = '0' or "Статус" = '13' or "Статус" = '17' then 1 else 0 end)  as "Отменен",
        sum(case when "Статус" = '1' then 1 else 0 end)  as "1",
        sum(case when "Статус" = '2' then 1 else 0 end)  as "2",
        sum(case when "Статус" = '3' then 1 else 0 end)  as "3",
        sum(case when "Статус" = '5' then 1 else 0 end)  as "5",
        sum(case when "Статус" = '6' then 1 else 0 end)  as "6",
        sum(case when "Статус" = '7' then 1 else 0 end)  as "7",
        sum(case when "Статус" = '8' then 1 else 0 end)  as "8",
        sum(case when "Статус" = '12' then 1 else 0 end) as "12",
        sum(case when "Статус" = '13' then 1 else 0 end) as "13",
        sum(case when "Статус" = '17' then 1 else 0 end) as "17",
        sum(case when "Статус" = '0' then 1 else 0 end)  as "0"
from oms.oms_data
where "Цель" = :text_1
    and "Тариф" != '0'
and "Подразделение" not like '%ДП%'
AND "Отчетный период выгрузки" IN ({sql_cond})
GROUP BY ROLLUP("Подразделение")
    """


sql_query_adults_age_dispensary = """
WITH data AS (SELECT 2024 - CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer)                        as Возраст,
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN "Пол" = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
              FROM oms.oms_data
              WHERE "Цель" IN ('ДВ4', 'ОПВ')
                and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                AND "Статус" IN :status_list
              GROUP BY Возраст)
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
        "Всего",
        "М",
        "Ж",
        "М ГП3",
        "Ж ГП3",
        "ГП3",
        "М ГП11",
        "Ж ГП11",
        "ГП11",
        "М ОАПП1",
        "Ж ОАПП1",
        "ОАПП1",
        "М ОАПП2",
        "Ж ОАПП2",
        "ОАПП2"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
        SUM("М ГП3"),  
        SUM("М ГП3"),  
        SUM("ГП3"),
        SUM("М ГП11"),
        SUM("Ж ГП11"),
        SUM("ГП11"),
        SUM("М ОАПП1"),
        SUM("Ж ОАПП1"),
        SUM("ОАПП1"),
        SUM("М ОАПП2"),
        SUM("Ж ОАПП2"),
        SUM("ОАПП2")
      FROM data) d
"""

sql_query_adults_age_dispensary_dv4 = """
WITH data AS (SELECT 2024 - CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer)                        as Возраст,
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN "Пол" = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
              FROM oms.oms_data
              WHERE "Цель" IN ('ДВ4')
                and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                AND "Статус" IN :status_list
              GROUP BY Возраст)
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
        "Всего",
        "М",
        "Ж",
        "М ГП3",
        "Ж ГП3",
        "ГП3",
        "М ГП11",
        "Ж ГП11",
        "ГП11",
        "М ОАПП1",
        "Ж ОАПП1",
        "ОАПП1",
        "М ОАПП2",
        "Ж ОАПП2",
        "ОАПП2"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
        SUM("М ГП3"),  
        SUM("М ГП3"),  
        SUM("ГП3"),
        SUM("М ГП11"),
        SUM("Ж ГП11"),
        SUM("ГП11"),
        SUM("М ОАПП1"),
        SUM("Ж ОАПП1"),
        SUM("ОАПП1"),
        SUM("М ОАПП2"),
        SUM("Ж ОАПП2"),
        SUM("ОАПП2")
      FROM data) d
"""


def sql_query_adults_age_dispensary():
    return f"""
            WITH data AS (SELECT 2024 - CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer)                        as Возраст,
                                 COUNT(*)                                                                   AS "Всего",
                                 SUM(CASE WHEN "Пол" = 'М' THEN 1 ELSE 0 END) AS "М",
                                 SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                                 SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                                 SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                                 SUM(CASE WHEN "Подразделение" = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                                 SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                                 SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                                 SUM(CASE WHEN "Подразделение" = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                                 SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                                 SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                                 SUM(CASE WHEN "Подразделение" = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                                 SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                                 SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                                 SUM(CASE WHEN "Подразделение" = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
                          FROM oms.oms_data
                          WHERE "Цель" IN ('ОПВ', 'ДВ4')
                            and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
                            AND "Статус" IN :status_list
                          GROUP BY Возраст)
            SELECT CASE
                       WHEN Возраст IS NULL THEN 'Итого'
                       ELSE Возраст::text
                       END AS Возраст,
                    "Всего",
                    "М",
                    "Ж",
                    "М ГП3",
                    "Ж ГП3",
                    "ГП3",
                    "М ГП11",
                    "Ж ГП11",
                    "ГП11",
                    "М ОАПП1",
                    "Ж ОАПП1",
                    "ОАПП1",
                    "М ОАПП2",
                    "Ж ОАПП2",
                    "ОАПП2"
            FROM data
            UNION ALL
            select *
            from (SELECT 'Итого' as Возраст,
                         SUM("Всего"),
                         SUM("М"),
                         SUM("Ж"),
                    SUM("М ГП3"),  
                    SUM("М ГП3"),  
                    SUM("ГП3"),
                    SUM("М ГП11"),
                    SUM("Ж ГП11"),
                    SUM("ГП11"),
                    SUM("М ОАПП1"),
                    SUM("Ж ОАПП1"),
                    SUM("ОАПП1"),
                    SUM("М ОАПП2"),
                    SUM("Ж ОАПП2"),
                    SUM("ОАПП2")
                  FROM data) d
            """


def query_age_dispensary(sql_cond):
    return f"""
    WITH data AS (SELECT 2024 - CAST(substring("Дата рождения" FROM LENGTH("Дата рождения") - 3) AS integer) as "Возраст",
                     COUNT(*)                                                                   AS "Всего",
                     SUM(CASE WHEN "Пол" = 'М' THEN 1 ELSE 0 END) AS "М",
                     SUM(CASE WHEN "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж",                     
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №3' THEN 1 ELSE 0 END)                 AS "ГП3",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ГП №11' THEN 1 ELSE 0 END)                 AS "ГП11",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП1",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП1",                  
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №1' THEN 1 ELSE 0 END)              AS "ОАПП1",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'М' THEN 1 ELSE 0 END) AS "М ОАПП2",
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' and "Пол" = 'Ж' THEN 1 ELSE 0 END) AS "Ж ОАПП2",                  
                     SUM(CASE WHEN "Подразделение" = 'ОАПП №2' THEN 1 ELSE 0 END)              AS "ОАПП2"
              FROM oms.oms_data
              WHERE "Цель" = :cel
                and "Отчетный период выгрузки" IN ({sql_cond})
                AND "Статус" IN :status_list
                AND "Тариф" != '0'
                and "Код СМО" like '360%'
                AND "Санкции" is null
              GROUP BY "Возраст")
SELECT CASE
           WHEN Возраст IS NULL THEN 'Итого'
           ELSE Возраст::text
           END AS Возраст,
        "Всего",
        "М",
        "Ж",
        "М ГП3",
        "Ж ГП3",
        "ГП3",
        "М ГП11",
        "Ж ГП11",
        "ГП11",
        "М ОАПП1",
        "Ж ОАПП1",
        "ОАПП1",
        "М ОАПП2",
        "Ж ОАПП2",
        "ОАПП2"
FROM data
UNION ALL
select *
from (SELECT 'Итого' as Возраст,
             SUM("Всего"),
             SUM("М"),
             SUM("Ж"),
        SUM("М ГП3"),  
        SUM("М ГП3"),  
        SUM("ГП3"),
        SUM("М ГП11"),
        SUM("Ж ГП11"),
        SUM("ГП11"),
        SUM("М ОАПП1"),
        SUM("Ж ОАПП1"),
        SUM("ОАПП1"),
        SUM("М ОАПП2"),
        SUM("Ж ОАПП2"),
        SUM("ОАПП2")
      FROM data) d
"""


sql_query_flu_list = """
with flu as (select *,
                    LOWER(concat(replace("Пациент", ' ', ''), "ДР"))                                as "ФИОДР",
                    ROW_NUMBER()
                    OVER (PARTITION BY "Пациент", "ДР" ORDER BY to_date("Дата", 'DD-MM-YYYY') DESC) AS row_num
             from kvazar.flu_data),
     fl_uniq as (SELECT *
                 FROM flu
                 WHERE row_num = 1),
     nas_vse as (select LOWER(concat("Фамилия", "Имя", "Отчество", "Дата рождения")) AS "ФИО_ДР",
                        "ЕНП"
                 from info.naselenie_data),
     flu_nas_vse as (select "Пациент",
                            "ДР",
                            "Дата",
                            "ЕНП"
                     from fl_uniq
                              left join nas_vse on fl_uniq."ФИОДР" = nas_vse."ФИО_ДР"),
     itog as (select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     oms.detaildd_data."ЕНП",
                     "Доктор (ФИО)",
                     "Доктор (Код)",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     flu_nas_vse."Дата" as "Дата флюры"


              from oms.detaildd_data
                       left join flu_nas_vse on oms.detaildd_data."ЕНП" = flu_nas_vse."ЕНП"
              where "Название услуги" like 'Флюоро%')

select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     "ЕНП",
                     "Доктор (ФИО)",
                     "Структурное подразделение:" as "Корпус",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     "Дата флюры"
from itog left join oms.doctors_oms_data on itog."Доктор (Код)"=  oms.doctors_oms_data."Код врача:"
"""

sql_query_flu_list2 = """
with flu as (select *,
                    LOWER(concat(replace("Пациент", ' ', ''), "ДР"))                                as "ФИОДР",
                    ROW_NUMBER()
                    OVER (PARTITION BY "Пациент", "ДР" ORDER BY to_date("Дата", 'DD-MM-YYYY') DESC) AS row_num
             from kvazar.flu_data),
     fl_uniq as (SELECT *
                 FROM flu
                 WHERE row_num = 1),
     nas_vse as (select LOWER(concat("Фамилия", "Имя", "Отчество", "Дата рождения")) AS "ФИО_ДР",
                        "ЕНП"
                 from info.naselenie_data),
     flu_nas_vse as (select "Пациент",
                            "ДР",
                            "Дата",
                            "ЕНП"
                     from fl_uniq
                              left join nas_vse on fl_uniq."ФИОДР" = nas_vse."ФИО_ДР"),
     itog as (select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     oms.detaildd_data."ЕНП",
                     "Доктор (ФИО)",
                     "Доктор (Код)",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     flu_nas_vse."Дата" as "Дата флюры"


              from oms.detaildd_data
                       left join flu_nas_vse on oms.detaildd_data."ЕНП" = flu_nas_vse."ЕНП"
              where "Название услуги" like 'Флюоро%')

select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     "ЕНП",
                     "Доктор (ФИО)",
                     "Структурное подразделение:" as "Корпус",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     "Дата флюры"
from itog left join oms.doctors_oms_data on itog."Доктор (Код)"=  oms.doctors_oms_data."Код врача:"
where "Дата флюры" is null 
"""

sql_query_flu_list3 = """
with flu as (select *,
                    LOWER(concat(replace("Пациент", ' ', ''), "ДР"))                                as "ФИОДР",
                    ROW_NUMBER()
                    OVER (PARTITION BY "Пациент", "ДР" ORDER BY to_date("Дата", 'DD-MM-YYYY') DESC) AS row_num
             from kvazar.flu_data),
     fl_uniq as (SELECT *
                 FROM flu
                 WHERE row_num = 1),
     nas_vse as (select LOWER(concat("Фамилия", "Имя", "Отчество", "Дата рождения")) AS "ФИО_ДР",
                        "ЕНП"
                 from info.naselenie_data),
     flu_nas_vse as (select "Пациент",
                            "ДР",
                            "Дата",
                            "ЕНП"
                     from fl_uniq
                              left join nas_vse on fl_uniq."ФИОДР" = nas_vse."ФИО_ДР"),
     itog as (select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     oms.detaildd_data."ЕНП",
                     "Доктор (ФИО)",
                     "Доктор (Код)",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     flu_nas_vse."Дата" as "Дата флюры"


              from oms.detaildd_data
                       left join flu_nas_vse on oms.detaildd_data."ЕНП" = flu_nas_vse."ЕНП"
              where "Название услуги" like 'Флюоро%')

select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     "ЕНП",
                     "Доктор (ФИО)",
                     "Структурное подразделение:" as "Корпус",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     "Дата флюры"
from itog left join oms.doctors_oms_data on itog."Доктор (Код)"=  oms.doctors_oms_data."Код врача:"
where right("Дата флюры",4)  < right("Дата-Услуги",4)
"""

sql_query_flu_report = """
with flu as (select *,
                    LOWER(concat(replace("Пациент", ' ', ''), "ДР"))                                as "ФИОДР",
                    ROW_NUMBER()
                    OVER (PARTITION BY "Пациент", "ДР" ORDER BY to_date("Дата", 'DD-MM-YYYY') DESC) AS row_num
             from kvazar.flu_data),
     fl_uniq as (SELECT *
                 FROM flu
                 WHERE row_num = 1),
     nas_vse as (select LOWER(concat("Фамилия", "Имя", "Отчество", "Дата рождения")) AS "ФИО_ДР",
                        "ЕНП"
                 from info.naselenie_data),
     flu_nas_vse as (select "Пациент",
                            "ДР",
                            "Дата",
                            "ЕНП"
                     from fl_uniq
                              left join nas_vse on fl_uniq."ФИОДР" = nas_vse."ФИО_ДР"),
     count as (select count(*)                                    as "Всего",
                      sum(case when "ЕНП" is null then 1 end)     as "Не найден ЕНП",
                      sum(case when "ЕНП" is not null then 1 end) as "Найден ЕНП"

               from flu_nas_vse),
     itog as (select "Номер талона",
                     "Тип талона",
                     "Статус",
                     "Фамилия",
                     "Имя",
                     "Отчество",
                     "Дата рождения",
                     detaildd_data."ЕНП",
                     "Доктор (ФИО)",
                     "Доктор (Код)",
                     "Дата начала",
                     "Дата окончания",
                     "Название услуги",
                     "Дата-Услуги",
                     "Статус-Услуги",
                     flu_nas_vse."Дата" as "Дата флюры"


              from oms.detaildd_data
                       left join flu_nas_vse on oms.detaildd_data."ЕНП" = flu_nas_vse."ЕНП"
              where "Название услуги" like 'Флюоро%'),
    it2 as (


    select "Номер талона",
                         "Тип талона",
                         "Статус",
                         "Фамилия",
                         "Имя",
                         "Отчество",
                         "Дата рождения",
                         "ЕНП",
                         "Доктор (ФИО)",
                         "Структурное подразделение:" as "Корпус",
                         "Дата начала",
                         "Дата окончания",
                         "Название услуги",
                         "Дата-Услуги",
                         "Статус-Услуги",
                         "Дата флюры"
    from itog left join oms.doctors_oms_data on itog."Доктор (Код)"=  oms.doctors_oms_data."Код врача:"
    )
select COALESCE("Корпус", 'Итого') AS "Корпус",
       count(*)as "Всего",
       sum(case when "Дата флюры" is null then 1 else 0 end ) as "Нет флюры в флюоромониторинге",
       sum(case when right("Дата флюры",4)  < right("Дата-Услуги",4) then 1 else 0 end ) as "Год флюры меньше года услуги "
from it2
GROUP BY ROLLUP("Корпус")
"""

sql_query_list_of_failed = """
with
    sel_nas as (
        select iszl.people_data."FIO",
               iszl.people_data."DR",
               2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as  "Возраст",
               iszl.people_data."ENP",
               iszl.people_data."LPUUCH",
               info.area_data."Корпус"
        from iszl.people_data left join info.area_data on people_data."LPUUCH" = info.area_data."Участок"
        where 2024 - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) >= 18
),
    itog as     (
        select *,
               case when sel_nas."ENP" in (select "ЕНП" from oms.oms_data where "Цель" in ('ДВ4', 'ОПВ')) then 'да' else 'нет' end as "Есть ДВ4/ОПВ",
               case when "Возраст" in ('19', '20', '22', '23', '25', '26', '28', '29', '31', '32', '34', '35', '37', '38') then 'ОПВ' else 'ДВ4' end as "Тип"
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
where "Есть ДВ4/ОПВ" = 'нет'
order by "FIO"
"""


def query_dv4_price(sql_cond=None):
    return f"""
select "Подразделение",
       count(*) as "Всего",
       sum(case when CAST("Сумма" AS numeric(15, 2)) < 2000 then 1 else 0 end) as "<2000",
       sum(case when CAST("Сумма" AS numeric(15, 2)) >= 2000 and CAST("Сумма" AS numeric(15, 2)) < 3000 then 1 else 0 end) as "2000-3000",
       sum(case when CAST("Сумма" AS numeric(15, 2)) >= 3000 and CAST("Сумма" AS numeric(15, 2)) < 4000 then 1 else 0 end) as "3000-4000",
       sum(case when CAST("Сумма" AS numeric(15, 2)) >= 4000 and CAST("Сумма" AS numeric(15, 2)) < 5000 then 1 else 0 end) as "4000-5000",
       sum(case when CAST("Сумма" AS numeric(15, 2)) >= 5000  then 1 else 0 end) as ">5000"
from oms.oms_data
              WHERE "Цель" = :cel
                and "Отчетный период выгрузки" IN ({sql_cond})
                AND "Статус" IN :status_list
                AND "Тариф" != '0'
                and "Код СМО" like '360%'
                AND "Санкции" is null
    group by ROLLUP ("Подразделение")

"""
