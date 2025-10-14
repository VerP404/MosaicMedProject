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
    SELECT DISTINCT ON (enp)
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
    ORDER BY enp, CAST(dr AS DATE) DESC
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
LEFT JOIN talon o ON n.enp = o.enp
WHERE COALESCE(o.has_pn1, 0) = 0;

"""


query_children_list_not_pn1_summary_by_uchastok = """
WITH talon AS (
    SELECT
        enp,
        MAX(CASE WHEN goal = 'ПН1' THEN 1 ELSE 0 END) AS has_pn1
    FROM data_loader_omsdata
    WHERE goal IN ('ПН1')
    GROUP BY enp
),
naselenie AS (
    SELECT DISTINCT ON (enp)
        enp,
        lpuuch,
        DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE)))::INT AS age_years
    FROM data_loader_iszlpeople
    WHERE CAST(dr AS DATE) <= CURRENT_DATE
      AND DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) < 18
    ORDER BY enp, CAST(dr AS DATE) DESC
)
SELECT
    n.lpuuch AS "Участок",
    COUNT(*) AS "Всего",
    SUM(CASE WHEN n.age_years = 0 THEN 1 ELSE 0 END) AS "0",
    SUM(CASE WHEN n.age_years = 1 THEN 1 ELSE 0 END) AS "1",
    SUM(CASE WHEN n.age_years = 2 THEN 1 ELSE 0 END) AS "2",
    SUM(CASE WHEN n.age_years = 3 THEN 1 ELSE 0 END) AS "3",
    SUM(CASE WHEN n.age_years = 4 THEN 1 ELSE 0 END) AS "4",
    SUM(CASE WHEN n.age_years = 5 THEN 1 ELSE 0 END) AS "5",
    SUM(CASE WHEN n.age_years = 6 THEN 1 ELSE 0 END) AS "6",
    SUM(CASE WHEN n.age_years = 7 THEN 1 ELSE 0 END) AS "7",
    SUM(CASE WHEN n.age_years = 8 THEN 1 ELSE 0 END) AS "8",
    SUM(CASE WHEN n.age_years = 9 THEN 1 ELSE 0 END) AS "9",
    SUM(CASE WHEN n.age_years = 10 THEN 1 ELSE 0 END) AS "10",
    SUM(CASE WHEN n.age_years = 11 THEN 1 ELSE 0 END) AS "11",
    SUM(CASE WHEN n.age_years = 12 THEN 1 ELSE 0 END) AS "12",
    SUM(CASE WHEN n.age_years = 13 THEN 1 ELSE 0 END) AS "13",
    SUM(CASE WHEN n.age_years = 14 THEN 1 ELSE 0 END) AS "14",
    SUM(CASE WHEN n.age_years = 15 THEN 1 ELSE 0 END) AS "15",
    SUM(CASE WHEN n.age_years = 16 THEN 1 ELSE 0 END) AS "16",
    SUM(CASE WHEN n.age_years = 17 THEN 1 ELSE 0 END) AS "17"
FROM naselenie n
LEFT JOIN talon o ON n.enp = o.enp
WHERE COALESCE(o.has_pn1, 0) = 0
GROUP BY n.lpuuch
ORDER BY n.lpuuch
"""


def sql_query_children_list_not_pn1_details_by_uchastok_age(uchastok: str, age_years: int) -> str:
    safe_uch = str(uchastok).replace("'", "''")
    safe_age = int(age_years)
    return f"""
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
naselenie AS (
    SELECT DISTINCT ON (enp)
        fio,
        dr,
        CAST(dr AS DATE) AS dr_date,
        enp,
        lpuuch,
        DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) AS age_years,
        DATE_PART('month', AGE(CURRENT_DATE, CAST(dr AS DATE))) AS age_months_raw,
        (DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) * 12 + DATE_PART('month', AGE(CURRENT_DATE, CAST(dr AS DATE))))::INTEGER AS age_in_months
    FROM data_loader_iszlpeople
    WHERE CAST(dr AS DATE) <= CURRENT_DATE
      AND DATE_PART('year', AGE(CURRENT_DATE, CAST(dr AS DATE))) < 18
    ORDER BY enp, CAST(dr AS DATE) DESC
)
SELECT
    n.fio as "ФИО",
    n.dr as "ДР",
    n.enp as "ЕНП",
    n.lpuuch as "Участок",
    CAST(n.age_years AS text) AS "Возраст",
    CAST(CASE WHEN n.age_in_months >= 24 THEN 0 ELSE n.age_months_raw END  AS text) AS "Месяцев",
    CASE WHEN EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM n.dr_date) < 2 THEN 'да' ELSE 'нет' END AS "Дети до 2 лет",
    CASE WHEN o.has_pn1 = 1 THEN 'да' ELSE 'нет' END AS "ПН1",
    CASE WHEN o.has_ds1 = 1 THEN 'да' ELSE 'нет' END AS "ДС1",
    CASE WHEN o.has_ds2 = 1 THEN 'да' ELSE 'нет' END AS "ДС2",
    CAST(COALESCE(o.count_pn1, 0) AS text) AS "К-во ПН1",
    CAST(COALESCE(o.count_ds1, 0) AS text) AS "К-во ДС1",
    CAST(COALESCE(o.count_ds2, 0) AS text) AS "К-во ДС2"
FROM naselenie n
LEFT JOIN talon o ON n.enp = o.enp
WHERE COALESCE(o.has_pn1, 0) = 0
  AND n.lpuuch = '{safe_uch}'
  AND DATE_PART('year', AGE(CURRENT_DATE, n.dr_date))::INT = {safe_age}
ORDER BY n.fio
    """


def query_uniq(selected_year):
    return f"""
WITH filtered AS (
    SELECT
        status::int,
        enp,
        department,
        CASE
            WHEN report_period = '-' THEN RIGHT(treatment_end, 4)
            ELSE RIGHT(report_period, 4)
        END AS report_year,
        CASE
            WHEN report_period = '-' THEN
                CASE
                    WHEN EXTRACT(DAY FROM CURRENT_DATE)::INT <= 4 THEN
                        CASE
                            WHEN TO_NUMBER(SUBSTRING(treatment_end FROM 4 FOR 2), '99')
                                 = EXTRACT(MONTH FROM CURRENT_DATE) THEN
                                EXTRACT(MONTH FROM CURRENT_DATE)::INT
                            ELSE
                                CASE
                                    WHEN EXTRACT(MONTH FROM CURRENT_DATE)::INT = 1 THEN 12
                                    ELSE EXTRACT(MONTH FROM CURRENT_DATE)::INT - 1
                                END
                        END
                    ELSE EXTRACT(MONTH FROM CURRENT_DATE)::INT
                END
            ELSE
                CASE TRIM(SUBSTRING(report_period FROM 1 FOR POSITION(' ' IN report_period) - 1))
                    WHEN 'Января' THEN 1
                    WHEN 'Февраля' THEN 2
                    WHEN 'Марта' THEN 3
                    WHEN 'Апреля' THEN 4
                    WHEN 'Мая' THEN 5
                    WHEN 'Июня' THEN 6
                    WHEN 'Июля' THEN 7
                    WHEN 'Августа' THEN 8
                    WHEN 'Сентября' THEN 9
                    WHEN 'Октября' THEN 10
                    WHEN 'Ноября' THEN 11
                    WHEN 'Декабря' THEN 12
                    ELSE NULL
                END
        END AS month,
        EXTRACT(YEAR FROM to_date(treatment_end, 'DD-MM-YYYY')) AS year,
        COUNT(*) OVER (PARTITION BY enp) AS enp_count
    FROM data_loader_omsdata
    WHERE goal = 'ПН1'
      AND treatment_end LIKE '%{selected_year}%'
      AND enp != '-'
      AND smo_code LIKE '360%'
),
has_status_3 AS (
    SELECT enp
    FROM filtered
    WHERE status = 3
    GROUP BY enp
),
prioritized AS (
    SELECT f.*,
           CASE
               WHEN f.status = 3 THEN 0
               ELSE
                   CASE f.status
                       WHEN 2 THEN 1
                       WHEN 4 THEN 2
                       WHEN 6 THEN 3
                       WHEN 8 THEN 4
                       WHEN 1 THEN 5
                       WHEN 5 THEN 6
                       WHEN 7 THEN 7
                       WHEN 12 THEN 8
                       WHEN 13 THEN 9
                       WHEN 17 THEN 10
                       WHEN 0 THEN 11
                       ELSE 99
                   END
           END AS status_priority,
           CASE WHEN hs.enp IS NOT NULL THEN true ELSE false END AS has_status_3
    FROM filtered f
    LEFT JOIN has_status_3 hs ON f.enp = hs.enp
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY enp
               ORDER BY
                   CASE WHEN has_status_3 THEN CASE WHEN status = 3 THEN 0 ELSE 1 END ELSE 0 END,
                   month,
                   status_priority
           ) AS rank
    FROM prioritized
),
data AS (
    SELECT *
    FROM ranked
    WHERE rank = 1
)
SELECT
    month,
    department,
    SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) AS "Оплачено",
    SUM(CASE WHEN status IN (3,1,2,4,6,8) THEN 1 ELSE 0 END) AS "В работе",
    SUM(CASE WHEN status IN (5,7,12) THEN 1 ELSE 0 END) AS "Отказано",
    SUM(CASE WHEN status NOT IN (3,1,2,4,6,8,5,7,12) THEN 1 ELSE 0 END) AS "Отменено",
    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS "1",
    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) AS "2",
    SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) AS "3",
    SUM(CASE WHEN status = 4 THEN 1 ELSE 0 END) AS "4",
    SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) AS "5",
    SUM(CASE WHEN status = 6 THEN 1 ELSE 0 END) AS "6",
    SUM(CASE WHEN status = 7 THEN 1 ELSE 0 END) AS "7",
    SUM(CASE WHEN status = 8 THEN 1 ELSE 0 END) AS "8",
    SUM(CASE WHEN status = 12 THEN 1 ELSE 0 END) AS "12",
    SUM(CASE WHEN status = 13 THEN 1 ELSE 0 END) AS "13",
    SUM(CASE WHEN status = 17 THEN 1 ELSE 0 END) AS "17",
    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS "0",
    COUNT(*) AS total_count
FROM data
GROUP BY month, department
ORDER BY month, department
    """