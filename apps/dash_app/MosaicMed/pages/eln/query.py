sql_query_eln_often = """
with
--     "Журнал обращений" - добавляем столбец для сравнения и унифицируем дату приема
obr as (select concat("Фамилия", ' ', "Имя", ' ', "Отчество", ' ',
                      "Дата рождения")                                                 AS "ФИО_ДР_обр",
               case
                   when "Дата приема" is not null then TO_DATE("Дата приема"::text, 'YYYY-MM-DD"T"HH24:MI')::date
                   else TO_DATE("Дата записи"::text, 'YYYY-MM-DD"T"HH24:MI')::date end as "Прием",
               *
        from kvazar.obrdoc_data),
--     "ЭЛН" - фильтруем: первичные, не по уходу, действующие, за нужный период
eln as (select concat("Фамилия пациента", ' ', "Имя пациента", ' ', "Отчество пациента", ' ',
                      "Дата рождения") AS "ФИО_ДР_элн",
               *
        from kvazar.ln_data
        where "Первичный" = 'да'
          and "Статус" not in ('Действия прекращены', 'Отклонен председателем ВК')
          and "Уход за больными" is null
          and to_date("Дата выдачи", 'YYYY-MM-DD') BETWEEN DATE_TRUNC('MONTH', :date_in ::date - INTERVAL '6 months')::date and to_date(:date_in, 'DD-MM-YYYY')),

-- группируем все больничные
eln_in_table as (select "ФИО_ДР_элн",
                        count(*) as "К-во"
                 from eln
                 group by "ФИО_ДР_элн"),
-- получаем список больничных, которые открыты и продлены
eln_not_table as (select distinct "ФИО_ДР_элн"
                  from eln
                  where "Статус" in ('Открыт', 'Продлен')
                  group by "ФИО_ДР_элн"),
-- в общем списке помечаем те что нужно удалить из дальнейшей обработки, так как они придут закрывать больничный
eln_f as (select eln_in_table."ФИО_ДР_элн"  as "ФИО",
                 "К-во",
                 eln_not_table."ФИО_ДР_элн" as "Удалить"
          from eln_in_table
                   left join eln_not_table on eln_in_table."ФИО_ДР_элн" = eln_not_table."ФИО_ДР_элн"),
-- Удаляем тех кто придет закрывать и оставляем с больше 4 больничными
filt_eln as (select "ФИО",
                    "К-во"
             from eln_f
             where "Удалить" isnull
               and "К-во" >= 4
             order by "К-во" desc, "ФИО"),
-- в обращениях добавляем столбец с к-вом больничных для пациентов на требуемую дату
join_table as (select filt_eln."К-во" as "К-во больничных",
                      "Прием",
                      "ФИО_ДР_обр"    as ФИО,
                      "ЕНП",
                      "Телефон",
                      "Прикрепление",
                      "Фамилия.1" as "Врач",
                      "Должность",
                      "Тип расписания",
                      "Источник записи" as "Источник",
                      "Подразделение",
                      "Создавший"
               from obr
                        left join filt_eln on obr."ФИО_ДР_обр" = filt_eln."ФИО"
               where "Прием" = to_date(:date_in, 'DD-MM-YYYY')),
-- Получаем список записанных пациентов с отметкой о количестве больничных за последние 6 месяцев
itog as (select *
         from join_table
         where "К-во больничных" is not null
         order by "К-во больничных" desc, ФИО)
select *
from itog
"""

sql_query_eln_often_list = """
with
--     "Журнал обращений" - добавляем столбец для сравнения и унифицируем дату приема
obr as (select concat("Фамилия", ' ', "Имя", ' ', "Отчество", ' ',
                      "Дата рождения")                                                 AS "ФИО_ДР_обр",
               case
                   when "Дата приема" is not null then TO_DATE("Дата приема"::text, 'YYYY-MM-DD"T"HH24:MI')::date
                   else TO_DATE("Дата записи"::text, 'YYYY-MM-DD"T"HH24:MI')::date end as "Прием",
               *
        from kvazar.obrdoc_data),
--     "ЭЛН" - фильтруем: первичные, не по уходу, действующие, за нужный период
eln as (select concat("Фамилия пациента", ' ', "Имя пациента", ' ', "Отчество пациента", ' ',
                      "Дата рождения") AS "ФИО_ДР_элн",
               *
        from kvazar.ln_data
        where "Первичный" = 'да'
          and "Статус" not in ('Действия прекращены', 'Отклонен председателем ВК')
          and "Уход за больными" is null
          and to_date("Дата выдачи", 'YYYY-MM-DD') BETWEEN DATE_TRUNC('MONTH', :date_in ::date - INTERVAL '6 months')::date and to_date(:date_in, 'DD-MM-YYYY')),

-- группируем все больничные
eln_in_table as (select "ФИО_ДР_элн",
                        count(*) as "К-во"
                 from eln
                 group by "ФИО_ДР_элн"),
filt_eln as (select "ФИО_ДР_элн" as  "ФИО",
                    "К-во"
             from eln_in_table
             where "К-во" >= 4
             order by "К-во" desc, "ФИО")
select *
from filt_eln
"""


sql_query_eln_zapis = """
with
--     "Журнал обращений" - добавляем столбец для сравнения и унифицируем дату приема
obr as (select concat("Фамилия", ' ', "Имя", ' ', "Отчество", ' ',
                      "Дата рождения")                                                 AS "ФИО_обр",
               case
                   when "Дата приема" is not null then TO_DATE("Дата приема"::text, 'YYYY-MM-DD"T"HH24:MI')::date
                   else TO_DATE("Дата записи"::text, 'YYYY-MM-DD"T"HH24:MI')::date end as "Прием",
               *
        from kvazar.obrdoc_data),
odr_fil as (select *
            from obr
            where "Прием" >= to_date(:date_in, 'DD-MM-YYYY')),
eln as (select concat("Фамилия пациента", ' ', "Имя пациента", ' ', "Отчество пациента", ' ',
                      "Дата рождения") as "ФИО_ЛН", *
        from kvazar.ln_data
        where to_date("Дата выдачи", 'YYYY-MM-DD') BETWEEN DATE_TRUNC('DAY', :date_in ::date - INTERVAL '14 days')::date and DATE_TRUNC('DAY', :date_in ::date + INTERVAL '14 days')::date
          and "Статус" in ('Открыт', 'Продлен')
          and "Уход за больными" is null),
itog as (
         select case when "Прием" is null then 'нет' else 'да' end as "Записан","ФИО_ЛН", "Статус", "Дата выдачи", "Выдавший врач","ТВСП", "Период нетрудоспособности: дата о" as "нетрудоспособность по",
         "Прием", "Фамилия.1" as "Врач", "Должность", "Тип расписания", "Источник записи", "Подразделение",
         "Создавший"
        from eln left join odr_fil on eln."ФИО_ЛН" = odr_fil."ФИО_обр"
        order by "ФИО_ЛН"
    )
    
select *
from itog
"""

sql_query_eln_zapis_list = """
with
--     "Журнал обращений" - добавляем столбец для сравнения и унифицируем дату приема
obr as (select concat("Фамилия", ' ', "Имя", ' ', "Отчество", ' ',
                      "Дата рождения")                                                 AS "ФИО_обр",
               case
                   when "Дата приема" is not null then TO_DATE("Дата приема"::text, 'YYYY-MM-DD"T"HH24:MI')::date
                   else TO_DATE("Дата записи"::text, 'YYYY-MM-DD"T"HH24:MI')::date end as "Прием",
               *
        from kvazar.obrdoc_data),
odr_fil as (select *
            from obr
            where "Прием" >= to_date(:date_in, 'DD-MM-YYYY')),
eln as (select concat("Фамилия пациента", ' ', "Имя пациента", ' ', "Отчество пациента", ' ',
                      "Дата рождения") as "ФИО_ЛН", *
        from kvazar.ln_data
        where to_date("Дата выдачи", 'YYYY-MM-DD') BETWEEN DATE_TRUNC('DAY', :date_in ::date - INTERVAL '14 days')::date and DATE_TRUNC('DAY', :date_in ::date + INTERVAL '14 days')::date
          and "Статус" in ('Открыт', 'Продлен')
          and "Уход за больными" is null),
itog as (
         select case when "Прием" is null then 'нет' else 'да' end as "Записан","ФИО_ЛН", "Статус", "Дата выдачи", "Выдавший врач","ТВСП", "Период нетрудоспособности: дата о" as "нетрудоспособность по",
         "Прием", "Фамилия.1" as "Врач", "Должность", "Тип расписания", "Источник записи", "Подразделение",
         "Создавший"
        from eln left join odr_fil on eln."ФИО_ЛН" = odr_fil."ФИО_обр"
        order by "ФИО_ЛН"
    ),
    svod as (
        select distinct "Выдавший врач",
                "ТВСП",
                "Записан"
from itog
    )

select "ТВСП",
       "Выдавший врач",
       count(*) as Всего,
       sum(case when "Записан" = 'да' then 1 else 0 end ) as Записано,
       sum(case when "Записан" = 'нет' then 1 else 0 end ) as "Не записано"
from svod
group by "ТВСП","Выдавший врач"
"""


sql_query_eln_zapis_svod = """
with
--     "Журнал обращений" - добавляем столбец для сравнения и унифицируем дату приема
obr as (select concat("Фамилия", ' ', "Имя", ' ', "Отчество", ' ',
                      "Дата рождения")                                                 AS "ФИО_обр",
               case
                   when "Дата приема" is not null then TO_DATE("Дата приема"::text, 'YYYY-MM-DD"T"HH24:MI')::date
                   else TO_DATE("Дата записи"::text, 'YYYY-MM-DD"T"HH24:MI')::date end as "Прием",
               *
        from kvazar.obrdoc_data),
odr_fil as (select *
            from obr
            where "Прием" >= to_date(:date_in, 'DD-MM-YYYY')),
eln as (select concat("Фамилия пациента", ' ', "Имя пациента", ' ', "Отчество пациента", ' ',
                      "Дата рождения") as "ФИО_ЛН", *
        from kvazar.ln_data
        where to_date("Дата выдачи", 'YYYY-MM-DD') BETWEEN DATE_TRUNC('DAY', :date_in ::date - INTERVAL '14 days')::date and DATE_TRUNC('DAY', :date_in ::date + INTERVAL '14 days')::date
          and "Статус" in ('Открыт', 'Продлен')
          and "Уход за больными" is null),
itog as (
         select case when "Прием" is null then 'нет' else 'да' end as "Записан","ФИО_ЛН", "Статус", "Дата выдачи", "Выдавший врач","ТВСП", "Период нетрудоспособности: дата о" as "нетрудоспособность по",
         "Прием", "Фамилия.1" as "Врач", "Должность", "Тип расписания", "Источник записи", "Подразделение",
         "Создавший"
        from eln left join odr_fil on eln."ФИО_ЛН" = odr_fil."ФИО_обр"
        order by "ФИО_ЛН"
    ),
    svod as (
        select distinct "Выдавший врач",
                "ТВСП",
                "Записан"
from itog
    )

select "ТВСП",
       count(*) as Всего,
       sum(case when "Записан" = 'да' then 1 else 0 end ) as Записано,
       sum(case when "Записан" = 'нет' then 1 else 0 end ) as "Не записано"
from svod
GROUP BY "ТВСП"
UNION ALL
SELECT
    ' Итого' AS "ТВСП",
    COUNT(*) AS "Всего",
    SUM(CASE WHEN "Записан" = 'да' THEN 1 ELSE 0 END) AS "Записано",
    SUM(CASE WHEN "Записан" <> 'да' THEN 1 ELSE 0 END) AS "Не записано"
FROM svod
order by "ТВСП"
"""