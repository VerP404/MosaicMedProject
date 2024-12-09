# отчет по диспансеризации
from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms


def sql_query_dispensary_children(selected_year, months_placeholder, inogorod, sanction, amount_null,
                                  building=None,
                                  department=None,
                                  profile=None,
                                  doctor=None,
                                  input_start=None,
                                  input_end=None,
                                  treatment_start=None,
                                  treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
    SELECT goal,
           {columns_by_status_oms()}
           FROM oms
           WHERE target_categories like '%Диспансеризация детей%'
           group by goal;
    """
    return query


def sql_query_dispensary_building_children(selected_year, months_placeholder, inogorod, sanction, amount_null,
                                           building=None,
                                           department=None,
                                           profile=None,
                                           doctor=None,
                                           input_start=None,
                                           input_end=None,
                                           treatment_start=None,
                                           treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
    SELECT building, 
            goal,
           {columns_by_status_oms()}
           FROM oms
           WHERE target_categories like '%Диспансеризация детей%'
           group by building, goal;
    """
    return query


def sql_query_dispensary_building_department_children(selected_year, months_placeholder, inogorod, sanction,
                                                      amount_null,
                                                      building=None,
                                                      department=None,
                                                      profile=None,
                                                      doctor=None,
                                                      input_start=None,
                                                      input_end=None,
                                                      treatment_start=None,
                                                      treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
    SELECT building, department, 
            goal,
           {columns_by_status_oms()}
           FROM oms
           WHERE target_categories like '%Диспансеризация детей%'
           group by building, department, goal;
    """
    return query


def sql_query_dispensary_age_children(selected_year, months_placeholder, inogorod, sanction, amount_null,
                                      building=None,
                                      department=None,
                                      profile=None,
                                      doctor=None,
                                      input_start=None,
                                      input_end=None,
                                      treatment_start=None,
                                      treatment_end=None,
                                      cel_list=None,
                                      status_list=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end, cel_list, status_list)
    query = f"""
    {base}
    SELECT age "Возраст",
           COUNT(*)                                                                   AS "Всего",
           SUM(CASE WHEN gender = 'М' THEN 1 ELSE 0 END) AS "М",
           SUM(CASE WHEN gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж"              
           FROM oms
           WHERE target_categories like '%Диспансеризация детей%'
           group by age
           order by age;
    """
    return query


def sql_query_dispensary_amount_group(selected_year, months_placeholder, inogorod, sanction, amount_null,
                                      building=None,
                                      department=None,
                                      profile=None,
                                      doctor=None,
                                      input_start=None,
                                      input_end=None,
                                      treatment_start=None,
                                      treatment_end=None,
                                      cel_list=None,
                                      status_list=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end, cel_list, status_list)
    query = f"""
    {base}
    SELECT '-' "-",
       count(*) as "Всего",
       sum(case when amount_numeric < 2000 then 1 else 0 end) as "<2000",
       sum(case when amount_numeric >= 2000 and amount_numeric < 3000 then 1 else 0 end) as "2000-3000",
       sum(case when amount_numeric >= 3000 and amount_numeric < 4000 then 1 else 0 end) as "3000-4000",
       sum(case when amount_numeric >= 4000 and amount_numeric < 5000 then 1 else 0 end) as "4000-5000",
       sum(case when amount_numeric >= 5000  then 1 else 0 end) as ">5000"         
           FROM oms
           WHERE target_categories like '%Диспансеризация детей%'
           group by "-";
    """
    return query


def sql_query_dispensary_uniq(selected_year, months_placeholder, inogorod, sanction, amount_null,
                              building=None,
                              department=None,
                              profile=None,
                              doctor=None,
                              input_start=None,
                              input_end=None,
                              treatment_start=None,
                              treatment_end=None,
                              cel_list=None,
                              status_list=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end, cel_list, status_list)
    query = f"""
    {base}
    , 
    oms_order_filter as (
        select * 
        from oms 
        where target_categories like '%Диспансеризация детей%'
        order by report_month_number, enp),
    oms_distinct_filter as (
        select distinct(enp),
         *
        from oms_order_filter)
    SELECT building, department, 
            goal,
           {columns_by_status_oms()}
           FROM oms_distinct_filter
           group by building, department, goal;
    """
    return query


query_download_children_list_not_pn1 = """
WITH talon AS (
    SELECT
        enp,
        MAX(CASE WHEN goal = 'ПН1' THEN 1 ELSE 0 END) AS has_pn1,
        MAX(CASE WHEN goal = 'ДС1' THEN 1 ELSE 0 END) AS has_ds1,
        MAX(CASE WHEN goal = 'ДС2' THEN 1 ELSE 0 END) AS has_ds2,
        SUM(CASE WHEN goal = 'ПН1' THEN 1 ELSE 0 END) AS count_pn1,
        SUM(CASE WHEN goal = 'ДС1' THEN 1 ELSE 0 END) AS count_ds1,
        SUM(CASE WHEN goal = 'ДС2' THEN 1 ELSE 0 END) AS count_ds2
    FROM data_loader_omsdata
    WHERE goal IN ('ПН1', 'ДС1', 'ДС2')
    GROUP BY enp
),
age_requirements AS (
    SELECT unnest(ARRAY[
        0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 18, 24,
        36, 48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168, 180, 192
    ]) AS required_age_months
),
naselenie AS (
    SELECT
        DISTINCT
        fio,
        dr,
        CAST(dr AS DATE) AS dr_date,
        enp,
        lpuuch,
        DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) AS age_years,
        DATE_PART('month', AGE(CURRENT_DATE, CAST(dr AS DATE))) AS age_months_raw,
        (DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) * 12 + DATE_PART('month', AGE(CURRENT_DATE, CAST(dr AS DATE))))::INTEGER AS age_in_months,
        CASE
            WHEN LOWER("fio") LIKE '%вич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%вна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%а' AND LOWER("fio") NOT LIKE '%вич' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%руз' THEN 'М'
            WHEN LOWER("fio") LIKE '%угли' THEN 'М'
            WHEN LOWER("fio") LIKE '%дин' THEN 'М'
            WHEN LOWER("fio") LIKE '%оглы' THEN 'М'
            WHEN LOWER("fio") LIKE '%кызы' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ич' THEN 'М'
            WHEN LOWER("fio") LIKE '%ова%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ева%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ода %' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ов%' AND LOWER("fio") NOT LIKE '%ова%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ев%' AND LOWER("fio") NOT LIKE '%ева%' THEN 'М'
            WHEN LOWER("fio") LIKE '%кий' THEN 'М'
            WHEN LOWER("fio") LIKE '%ль' THEN 'М'
            WHEN LOWER("fio") LIKE '%й%' AND LOWER("fio") NOT LIKE '%ой' THEN 'М'
            WHEN LOWER("fio") LIKE '%илья' THEN 'М'
            WHEN LOWER("fio") LIKE '%ья' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%иа' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%йя' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%инич' THEN 'М'
            WHEN LOWER("fio") LIKE '%ус' THEN 'М'
            WHEN LOWER("fio") LIKE '%ия' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%джонзода%' THEN 'М'
            WHEN LOWER("fio") LIKE '%мохаммед%' THEN 'М'
            WHEN RIGHT(LOWER("fio"), 1) IN ('а', 'я', 'и', 'е', 'о', 'у', 'э', 'ю') THEN 'Ж'
            ELSE 'М'
        END AS gender
    FROM data_loader_iszlpeople
    WHERE CAST(dr AS DATE) <= CURRENT_DATE
      AND DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) < 18
)
SELECT
    n.fio as "ФИО",
    n.dr as "ДР",
    n.enp as "ЕНП",
    n.lpuuch as "Участок",
    CAST(n.age_years AS text) AS "Возраст",
    CAST(CASE WHEN n.age_in_months >= 24 THEN 0 ELSE n.age_months_raw END  AS text) AS "Месяцев",
    n.gender as "Пол",
    CASE WHEN EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM n.dr_date) < 2 THEN 'да' ELSE 'нет' END AS "Дети до 2 лет",
    CASE WHEN o.has_pn1 = 1 THEN 'да' ELSE 'нет' END AS "ПН1",
    CASE WHEN o.has_ds1 = 1 THEN 'да' ELSE 'нет' END AS "ДС1",
    CASE WHEN o.has_ds2 = 1 THEN 'да' ELSE 'нет' END AS "ДС2",
    CAST(COALESCE(o.count_pn1, 0) AS text) AS "К-во ПН1",
    CAST(COALESCE(o.count_ds1, 0) AS text) AS "К-во ДС1",
    CAST(COALESCE(o.count_ds2, 0) AS text) AS "К-во ДС2",
CAST(
    (
        SELECT COUNT(*)
        FROM age_requirements ar
        WHERE
            n.dr_date + (ar.required_age_months || ' months')::INTERVAL <= CURRENT_DATE
            AND n.dr_date + (ar.required_age_months || ' months')::INTERVAL >= DATE '2024-01-01'
            AND n.dr_date + (ar.required_age_months || ' months')::INTERVAL >= n.dr_date
    ) AS text
) AS "План осмотров на сегодня"
FROM naselenie n
LEFT JOIN talon o ON n.enp = o.enp;

"""
