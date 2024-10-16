def sql_query_disp_rep_f1000(sql_cond=None):
    return f"""
        WITH oms AS (
    SELECT goal,
           enp
    FROM data_loader_omsdata
    WHERE data_loader_omsdata.goal IN ('ОПВ', 'ДВ4')
        and ((account_number LIKE ANY (:list_months)) {sql_cond})
  AND status IN :status_list
),
cleaned_data AS (
    SELECT
        TRIM(fio) as fio,
        dr,
        CAST(enp AS TEXT),
        lpuuch
    FROM data_loader_iszlpeople
),
data AS (
    SELECT
        cd.fio,
        cd.dr,
        cd.enp,
        cd.lpuuch,
        CASE
            WHEN LOWER(cd.fio) LIKE '%вич%' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%вна%' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%а' AND LOWER(cd.fio) NOT LIKE '%вич' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%руз' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%угли' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%дин' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%оглы' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%кызы' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%ич' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%ова%' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%ева%' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%ода %' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%ов%' AND LOWER(cd.fio) NOT LIKE '%ова%' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%ев%' AND LOWER(cd.fio) NOT LIKE '%ева%' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%кий' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%ль' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%й%' AND LOWER(cd.fio) NOT LIKE '%ой' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%илья' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%ья' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%иа' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%йя' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%инич' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%ус' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%ия' THEN 'Ж'
            WHEN LOWER(cd.fio) LIKE '%джонзода%' THEN 'М'
            WHEN LOWER(cd.fio) LIKE '%мохаммед%' THEN 'М'
            WHEN RIGHT(LOWER(cd.fio), 1) IN ('а', 'я', 'и', 'е', 'о', 'у', 'э', 'ю') THEN 'Ж'
            ELSE 'М'
        END AS Пол,
        EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM TO_DATE(dr, 'DD.MM.YYYY')) AS возраст
    FROM cleaned_data as cd
),
data_oms_people AS (
    SELECT
        data.*,
        oms.goal AS oms_цель
    FROM data
    LEFT JOIN oms ON data.enp = oms.enp
),
grouped_data AS (
    SELECT
        возраст,
        Пол,
        COUNT(*) AS численность,
        SUM(CASE WHEN oms_цель = 'ОПВ' THEN 1 ELSE 0 END) AS ПМО,
        SUM(CASE WHEN oms_цель = 'ДВ4' THEN 1 ELSE 0 END) AS ДОГВН
    FROM data_oms_people
    GROUP BY возраст, Пол
),
age_groups AS (
    SELECT
        CASE
            WHEN возраст BETWEEN 18 AND 34 THEN '18-34'
            WHEN возраст BETWEEN 35 AND 39 THEN '35-39'
            WHEN возраст BETWEEN 40 AND 54 THEN '40-54'
            WHEN возраст BETWEEN 55 AND 59 THEN '55-59'
            WHEN возраст BETWEEN 60 AND 64 THEN '60-64'
            WHEN возраст BETWEEN 65 AND 74 THEN '65-74'
            WHEN возраст >= 75 THEN '75 и старше'
        END AS "Возрастная группа",
        Пол,
        SUM(численность) AS численность,
        SUM(ПМО) AS ПМО,
        SUM(ДОГВН) AS ДОГВН
    FROM grouped_data
    WHERE возраст >= 18
    GROUP BY
        CASE
            WHEN возраст BETWEEN 18 AND 34 THEN '18-34'
            WHEN возраст BETWEEN 35 AND 39 THEN '35-39'
            WHEN возраст BETWEEN 40 AND 54 THEN '40-54'
            WHEN возраст BETWEEN 55 AND 59 THEN '55-59'
            WHEN возраст BETWEEN 60 AND 64 THEN '60-64'
            WHEN возраст BETWEEN 65 AND 74 THEN '65-74'
            WHEN возраст >= 75 THEN '75 и старше'
        END,
        Пол
),
agr_data AS (
    SELECT
        "Возрастная группа",
        SUM(численность) AS всего,
        SUM(CASE WHEN Пол = 'М' THEN численность ELSE 0 END) AS М,
        SUM(CASE WHEN Пол = 'Ж' THEN численность ELSE 0 END) AS Ж,
        SUM(CASE WHEN Пол = 'М' THEN ПМО ELSE 0 END) AS ПМО_М,
        SUM(CASE WHEN Пол = 'М' THEN ДОГВН ELSE 0 END) AS ДОГВН_М,
        SUM(CASE WHEN Пол = 'Ж' THEN ПМО ELSE 0 END) AS ПМО_Ж,
        SUM(CASE WHEN Пол = 'Ж' THEN ДОГВН ELSE 0 END) AS ДОГВН_Ж
    FROM age_groups
    GROUP BY "Возрастная группа"
    ORDER BY "Возрастная группа"
),
totals AS (
    SELECT
        'Итого' AS "Возрастная группа",
        SUM(всего) AS всего,
        SUM(М) AS М,
        SUM(Ж) AS Ж,
        SUM(ПМО_М) AS ПМО_М,
        SUM(ДОГВН_М) AS ДОГВН_М,
        SUM(ПМО_Ж) AS ПМО_Ж,
        SUM(ДОГВН_Ж) AS ДОГВН_Ж
    FROM agr_data
)
SELECT * FROM agr_data
UNION ALL
SELECT * FROM totals
    """


def sql_query_disp_rep_f1001(sql_cond=None):
    return f"""
    WITH oms AS (
    SELECT
        goal,
        enp,
        birth_date,
        gender,
        EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM TO_DATE(birth_date, 'DD.MM.YYYY')) AS возраст
    FROM data_loader_omsdata
    WHERE data_loader_omsdata.goal IN ('ОПВ', 'ДВ4')
        and ((account_number LIKE ANY (:list_months)) {sql_cond})
  AND status IN :status_list
),
working_age AS (
    SELECT
        goal,
        gender,
        COUNT(*) AS всего,
        SUM(CASE WHEN gender = 'М' AND возраст BETWEEN 18 AND 60 THEN 1 ELSE 0 END) AS М,
        SUM(CASE WHEN gender = 'Ж' AND возраст BETWEEN 18 AND 55 THEN 1 ELSE 0 END) AS Ж
    FROM oms
    WHERE (gender = 'М' AND возраст BETWEEN 18 AND 60) OR (gender = 'Ж' AND возраст BETWEEN 18 AND 55)
    GROUP BY goal, gender
),
final_table AS (
    SELECT
        goal,
        SUM(всего) AS всего,
        SUM(М) AS М,
        SUM(Ж) AS Ж
    FROM working_age
    GROUP BY goal
)

SELECT * FROM final_table
    """


def sql_query_disp_rep_f2000(sql_cond=None):
    return f"""
    WITH renamed_data AS (SELECT CASE
                                 WHEN service_name = 'Анкетирование' THEN '01 Опрос (анкетирование)'
                                 WHEN service_name = 'Антропометрия'
                                     THEN '02 Расчет на основании антропометрии (измерение роста, массы тела, окружности талии), индекса массы тела'
                                 WHEN service_name = 'Арт. давление'
                                     THEN '03 Измерение артериального давления на периферических артериях'
                                 WHEN service_name = 'Холестерин'
                                     THEN '04 Определение уровня общего холестерина в крови'
                                 WHEN service_name = 'Глюкоза' THEN '05 Определение уровня глюкозы в крови натощак'
                                 WHEN service_name = 'ССР (отн.)'
                                     THEN '06 Определение относительного сердечно-сосудистого риска'
                                 WHEN service_name = 'ССР (абс.)'
                                     THEN '07 Определение абсолютного сердечно-сосудистого риска'
                                 WHEN service_name IN
                                      ('Флюорография', 'Рентгенография легких', 'Рентгенография цифровая',
                                       'Прицельная рентгенография', 'Компьютерная томография', 'Флюорография цифр.')
                                     THEN '08 Флюорография легких или рентгенография легких'
                                 WHEN service_name = 'ЭКГ' THEN '09 Электрокардиография в покое'
                                 WHEN service_name = 'Внутриглаз. давл.'
                                     THEN '10 Измерение внутриглазного давления'
                                 WHEN service_name = 'Акушер-гинеколог'
                                     THEN '11 Осмотр фельдшером (акушеркой) или врачом акушером-гинекологом'
                                 WHEN service_name = 'Мазок/Цитология (с шейки матки)'
                                     THEN '12 Взятие мазка с поверхности шейки матки'
                                 WHEN service_name = 'Маммография'
                                     THEN '13 Маммография обеих молочных желез в двух проекциях'
                                 WHEN service_name = 'Кал на кровь'
                                     THEN '14 Исследование кала на скрытую кровь иммунохимическим методом'
                                 WHEN service_name = 'Простат-спец. антиген'
                                     THEN '15 Определение простат-специфического антигена в крови'
                                 WHEN service_name = 'Эзофагогастродуоденоскопия'
                                     THEN '16 Эзофагогастродуоденоскопия'
                                 WHEN service_name = 'Общий анализ крови' THEN '17 Общий анализ крови'
                                 WHEN service_name = 'Проф. консульт.'
                                     THEN '18 Краткое индивидуальное профилактическое консультирование'
                                 WHEN service_name IN ('Врач общей практики', 'Терапевт участковый', 'Терапевт')
                                     THEN '19 Прием фельдшером, врачом-терапевтом, ВОП или врачом по медицинской профилактике'
                                 ELSE service_name
                                 END AS service_name,
                             service_status
                      FROM data_loader_detaileddata
                      WHERE talon_type IN ('ДВ4', 'ОПВ')
                      and ((account_number LIKE ANY (:list_months)) {sql_cond}
                      AND status IN :status_list)),
     ter_data as (select CASE
                             WHEN service_name IN ('Терапевт участковый', 'Терапевт') THEN
                                 CASE
                                     WHEN
                                         CAST(regexp_replace(route, '[^0-9]', '', 'g') AS INTEGER) BETWEEN 18 AND 39 and
                                         talon_type = 'ДВ4'
                                         THEN '19.1 Прием врачом терапевтом/ВОП от 18 до 39 1 раз в 3 года'
                                     WHEN CAST(regexp_replace(route, '[^0-9]', '', 'g') AS INTEGER) >= 40 and
                                          talon_type = 'ДВ4'
                                         THEN '19.2 Прием врачом терапевтом/ВОП 40 и старше 1 раз в год'
                                     ELSE NULL
                                     END
                             ELSE NULL
                             END AS service_name,
                         service_status
                  FROM data_loader_detaileddata
                  WHERE talon_type IN ('ДВ4', 'ОПВ')
                    and service_name IN ('Врач общей практики', 'Терапевт участковый')
                      and ((account_number LIKE ANY (:list_months)) {sql_cond}
                      AND status IN :status_list)),

     aggregated_data AS (SELECT service_name,
                                COUNT(CASE WHEN service_status = 'Да' THEN 1 END)        AS "Проведено",
                                COUNT(CASE WHEN service_status = 'Перезачет' THEN 1 END) AS "Перезачет",
                                COUNT(CASE WHEN service_status = 'Отказ' THEN 1 END)     AS "Отказ"
                         FROM renamed_data
                         GROUP BY service_name),
     aggregated_data_ter AS (SELECT service_name,
                                    COUNT(CASE WHEN service_status = 'Да' THEN 1 END)        AS "Проведено",
                                    COUNT(CASE WHEN service_status = 'Перезачет' THEN 1 END) AS "Перезачет",
                                    COUNT(CASE WHEN service_status = 'Отказ' THEN 1 END)     AS "Отказ"
                             FROM ter_data
                             GROUP BY service_name),
     union_data as (select *
                    from aggregated_data
                    union all
                    select *
                    from aggregated_data_ter)
SELECT service_name,
       SUM("Проведено") AS "Проведено",
       SUM("Перезачет") AS "Перезачет",
       SUM("Отказ")     AS "Отказ"
FROM union_data
where service_name IS NOT NULL
GROUP BY service_name
ORDER BY service_name
    """


def sql_query_disp_rep_f2001(sql_cond=None):
    return f"""
                select 'направлено на 2 этап' as "Параметр" , count(*) as "к-во"
            from data_loader_detaileddata
            where health_group like 'Направлен на II этап%'
                    and ((account_number LIKE ANY (:list_months)) {sql_cond})
  AND status IN :status_list
    """


def sql_query_disp_rep_f3000(sql_cond=None):
    return f"""
    WITH renamed_data AS (
    SELECT
        CASE
            WHEN service_name = 'Невролог' THEN '01 Осмотр (консультация) врачом-неврологом '
            WHEN service_name = 'Брахицеф. арт.' THEN '02 Дуплексное сканирование брахиоцефальных артерий'
            WHEN service_name in ('Уролог', 'Хирург') THEN '03 Осмотр (консультация) врачом-хирургом или врачом-урологом'
            WHEN service_name in ('Колопроктолог') THEN '04 Осмотр (консультация) врачом-хирургом или врачом-колопроктологом, включая проведение ректороманоскопии'
            WHEN service_name in ('Колоноскопия', 'Ректороманоскопия') THEN '05 Колоноскопия'
            WHEN service_name = 'Эзофагогастродуоденоскопия' THEN '06 Эзофагогастродуоденоскопия'
            WHEN service_name = 'Рентгенография легких' THEN '07 Рентгенография легких'
            WHEN service_name = 'Томография легких' THEN '08 Компьютерная томография легких'
            WHEN service_name = 'Спирометрия' THEN '09 Спирометрия'
            WHEN service_name = 'Акушер-гинеколог' THEN '10 Осмотр (консультация) врачом-акушером-гинекологом'
            WHEN service_name = 'Оториноларинголог' THEN '11 Осмотр (консультация) врачом-оториноларингологом'
            WHEN service_name = 'Офтальмолог' THEN '12 Осмотр (консультация) врачом-офтальмологом'
            WHEN service_name in ('Углуб. проф. консультирование (перв.)', 'Углуб. проф. консультирование (повт.)') THEN '13 Индивидуальное или групповое углубленное профилактическое консультирование'
            WHEN service_name in ('Терапевт участковый', 'Врач общей практики') THEN '14 Прием (осмотр) врачом-терапевтом по результатам второго этапа диспансеризации'
            WHEN service_name = 'Онколог' THEN '15 Направление на осмотр (консультацию) врачом-онкологом при подозрении на онкологические заболевания'
            WHEN service_name = 'Гликир. гемоглобин в крови' THEN '16 Определение уровня гликированного гемоглобина в крови'
            WHEN service_name = 'Дерматолог' THEN '17 Осмотр (консультация) врачом-дерматовенерологом'
            WHEN service_name = 'Дерматоскопия' THEN '18 Проведение дерматоскопии'
            ELSE service_name
        END AS service_name,
        service_status
    FROM
        data_loader_detaileddata
    WHERE
        talon_type IN ('ДВ2')
                      and ((account_number LIKE ANY (:list_months)) {sql_cond}
                      AND status IN :status_list)),
aggregated_data AS (
    SELECT
        service_name,
        COUNT(CASE WHEN service_status = 'Да' THEN 1 END) AS "Проведено",
        COUNT(CASE WHEN service_status = 'Перезачет' THEN 1 END) AS "Перезачет",
        COUNT(CASE WHEN service_status = 'Отказ' THEN 1 END) AS "Отказ"
    FROM
        renamed_data
    GROUP BY
        service_name
)
SELECT
    service_name,
    SUM("Проведено") AS "Проведено",
    SUM("Перезачет") AS "Перезачет",
    SUM("Отказ") AS "Отказ"
FROM
    aggregated_data
GROUP BY
    service_name
ORDER BY
    service_name;
    """


def sql_query_disp_rep_f3001_3003(sql_cond):
    return f"""
        WITH data as (select distinct talon_number,
                health_group,
                talon_type
        from data_loader_detaileddata
        where talon_type in ('ДВ4', 'ДВ2')
                and ((account_number LIKE ANY (:list_months)) {sql_cond})
                AND status IN :status_list
                )
        
        select '3001 - Направлено на 2й этап' as Форма,
               sum(case when talon_type = 'ДВ4' and health_group like 'Направлен на II этап%' then 1 else 0 end ) as "к-во"
        
        from data
        union all
        select '3002 - Прошли 2й этап',
               sum(case when talon_type = 'ДВ2' then 1 else 0 end )
        from data
        union all
        select '3003 - Не прошли 2й этап',
               sum(case when talon_type = 'ДВ4' and health_group like 'Направлен на II этап%' then 1 else 0 end ) - sum(case when talon_type = 'ДВ2' then 1 else 0 end ) as "Прошли 2 этап"
        from data
    """

def sql_query_disp_rep_f4000(sql_cond):
    return f"""
WITH combined_diagnoses AS (
    SELECT
        enp,
        main_diagnosis AS diagnosis,
        gender,
        CAST(regexp_replace(route, '[^0-9]', '', 'g') AS INTEGER) as Возраст
    FROM
        data_loader_detaileddata
    WHERE
        data_loader_detaileddata.talon_type IN ('ДВ4', 'ДВ2', 'ОПВ')
         and ((data_loader_detaileddata.account_number LIKE ANY (:list_months)) {sql_cond})
         AND status IN :status_list
    UNION ALL
    SELECT
        enp,
        unnest(string_to_array(additional_diagnosis, ', ')) AS diagnosis,
        gender,
        CAST(regexp_replace(route, '[^0-9]', '', 'g') AS INTEGER) as Возраст
    FROM
        data_loader_detaileddata
    WHERE
        data_loader_detaileddata.talon_type IN ('ДВ4', 'ДВ2', 'ОПВ')
         and ((data_loader_detaileddata.account_number LIKE ANY (:list_months)) {sql_cond})
        AND status IN :status_list
),
data AS (
    SELECT
        enp,
        string_agg(DISTINCT diagnosis, ', ') AS "Диагнозы",
        gender,
        Возраст
    FROM
        combined_diagnoses
    GROUP BY
        enp, gender, Возраст
),
risk_factors AS (
    SELECT
        gender,
        CASE
            WHEN diagnosis LIKE '%E78%' THEN '01 Гиперхолестеринемия E78'
            WHEN diagnosis LIKE '%R73.9%' THEN '02 Гипергликемия R73.9'
            WHEN diagnosis LIKE '%Z72.0%' THEN '03 Курение табака Z72.0'
            WHEN diagnosis LIKE '%Z72.4%' THEN '04 Нерациональное питание Z72.4'
            WHEN diagnosis LIKE '%E63.5%' THEN '05 Избыточная масса тела R63.5'
            WHEN diagnosis LIKE '%E66%' THEN '06 Ожирение R63.5'
            WHEN diagnosis LIKE '%Z72.3%' THEN '07 Низкая физическая активность Z72.3'
            WHEN diagnosis LIKE '%Z72.1%' THEN '08 Риск пагубного потребления алкоголя Z72.1'
            WHEN diagnosis LIKE '%Z72.2%' THEN '09 Риск потребления наркотических средств Z72.2'
            WHEN diagnosis LIKE '%Z82.4%' THEN '10 Отягощённая наследственность по сердечнососудистым заболеваниям инфаркт миокарда Z82.4'
            WHEN diagnosis LIKE '%Z82.3%' THEN '11 Отягощённая наследственность по сердечнососудистым заболеваниям мозговой инсульт Z82.3'
            WHEN diagnosis LIKE '%Z80.0%' THEN '12 Отягощённая наследственность по злокачественным новообразованиям колоректальной области Z80.0'
            WHEN diagnosis LIKE '%Z80.9%' THEN '13 Отягощённая наследственность по злокачественным новообразованиям других локализаций Z80.9'
            WHEN diagnosis LIKE '%Z82.5%' THEN '14 Отягощённая наследственность по хроническим болезням нижних дыхательных путей Z82.5'
            WHEN diagnosis LIKE '%Z83.3%' THEN '15 Отягощённая наследственность по сахарному диабету Z83.3'
            WHEN diagnosis LIKE '%R54%' THEN '18 Старческая астения R54'
            ELSE 'Другие'
        END AS "Фактор риска",
        COUNT(*) AS "Количество",
        CASE
            WHEN gender = 'М' AND Возраст BETWEEN 18 AND 60 THEN 'Мужчины трудоспособного возраста'
            WHEN gender = 'М' AND Возраст > 60 THEN 'Мужчины старше трудоспособного возраста'
            WHEN gender = 'Ж' AND Возраст BETWEEN 18 AND 55 THEN 'Женщины трудоспособного возраста'
            WHEN gender = 'Ж' AND Возраст > 55 THEN 'Женщины старше трудоспособного возраста'
            ELSE 'Другие'
        END AS "Возрастная группа"
    FROM
        data, unnest(string_to_array("Диагнозы", ', ')) AS diagnosis
    GROUP BY
        gender, "Фактор риска", "Возрастная группа"
)
SELECT
    "Фактор риска",
    SUM("Количество") AS "Всего",
    SUM(CASE WHEN "Возрастная группа" IN ('Мужчины трудоспособного возраста', 'Женщины трудоспособного возраста') THEN "Количество" ELSE 0 END) AS "Трудоспособного",
    SUM(CASE WHEN "Возрастная группа" IN ('Мужчины старше трудоспособного возраста', 'Женщины старше трудоспособного возраста') THEN "Количество" ELSE 0 END) AS "Старшего",
    SUM(CASE WHEN "Возрастная группа" LIKE 'Мужчины%' THEN "Количество" ELSE 0 END) AS "М всего",
    SUM(CASE WHEN "Возрастная группа" = 'Мужчины трудоспособного возраста' THEN "Количество" ELSE 0 END) AS "М Трудоспособного",
    SUM(CASE WHEN "Возрастная группа" = 'Мужчины старше трудоспособного возраста' THEN "Количество" ELSE 0 END) AS "М Старшего",
    SUM(CASE WHEN "Возрастная группа" LIKE 'Женщины%' THEN "Количество" ELSE 0 END) AS "Ж всего",
    SUM(CASE WHEN "Возрастная группа" = 'Женщины трудоспособного возраста' THEN "Количество" ELSE 0 END) AS "Ж Трудоспособного",
    SUM(CASE WHEN "Возрастная группа" = 'Женщины старше трудоспособного возраста' THEN "Количество" ELSE 0 END) AS "Ж Старшего"
FROM
    risk_factors
where "Фактор риска" != 'Другие'
GROUP BY
    "Фактор риска"
ORDER BY
    "Фактор риска";
    """

def sql_query_disp_rep_f4001(sql_cond):
    return f"""
    WITH combined_diagnoses AS (
    SELECT
        enp as "ЕНП",
        main_diagnosis AS diagnosis,
        gender as "Пол",
        CAST(regexp_replace(route, '[^0-9]', '', 'g') AS INTEGER) as Возраст
    FROM
        data_loader_detaileddata
    WHERE
        data_loader_detaileddata.talon_type IN ('ДВ4', 'ДВ2', 'ОПВ') and
    data_loader_detaileddata.main_diagnosis not like any (array ['Z72.0', 'Z72.4 0', 'Z72.3', 'Z72.1', 'Z72.2'])
     and ((data_loader_detaileddata.account_number LIKE ANY (:list_months)) {sql_cond})
         AND "Статус" IN :status_list
    UNION ALL
    SELECT
         enp as "ЕНП",
        unnest(string_to_array(additional_diagnosis, ', ')) AS diagnosis,
        gender as "Пол",
        CAST(regexp_replace(route, '[^0-9]', '', 'g') AS INTEGER) as Возраст
    FROM
        data_loader_detaileddata
    WHERE
        data_loader_detaileddata.talon_type IN ('ДВ4', 'ДВ2', 'ОПВ') and
    data_loader_detaileddata.main_diagnosis like any (array ['Z72.0', 'Z72.4 0', 'Z72.3', 'Z72.1', 'Z72.2'])
     and ((data_loader_detaileddata.account_number LIKE ANY (:list_months)) {sql_cond})
         AND "Статус" IN :status_list
),
data AS (
    SELECT
        "ЕНП",
        string_agg(DISTINCT diagnosis, ', ') AS "Диагнозы",
        "Пол",
        Возраст
    FROM
        combined_diagnoses
    GROUP BY
        "ЕНП", "Пол", Возраст
)
select 'по строкам 03, 04, 07, 08, 09 отсутствуют факторы риска' as Параметр, count(*) as  "к-во"
from data
    """