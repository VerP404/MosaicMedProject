# отчет по диспансеризации
from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms


def sql_query_dispensary(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
           WHERE target_categories like '%Диспансеризация взрослых%'
           group by goal;
    """
    return query


def sql_query_dispensary_building(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
           WHERE target_categories like '%Диспансеризация взрослых%'
           group by building, goal;
    """
    return query


def sql_query_dispensary_building_department(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
           WHERE target_categories like '%Диспансеризация взрослых%'
           group by building, department, goal;
    """
    return query


def sql_query_dispensary_age(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
           WHERE target_categories like '%Диспансеризация взрослых%'
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
           WHERE target_categories like '%Диспансеризация взрослых%'
           group by "-";
    """
    return query


def sql_query_dispensary_remd(selected_year):
    return f"""
    SELECT
        doctor,
        branch,
COALESCE(SUM(1) FILTER(WHERE mon = 1 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "янв_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 1 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "янв_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 1), 0)                                                   AS "янв_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 2 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "фев_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 2 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "фев_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 2), 0)                                                   AS "фев_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 3 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "мар_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 3 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "мар_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 3), 0)                                                   AS "мар_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 4 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "апр_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 4 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "апр_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 4), 0)                                                   AS "апр_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 5 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "май_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 5 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "май_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 5), 0)                                                   AS "май_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 6 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "июн_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 6 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "июн_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 6), 0)                                                   AS "июн_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 7 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "июл_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 7 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "июл_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 7), 0)                                                   AS "июл_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 8 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "авг_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 8 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "авг_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 8), 0)                                                   AS "авг_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 9 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "сен_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 9 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "сен_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 9), 0)                                                   AS "сен_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 10 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "окт_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 10 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "окт_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 10), 0)                                                  AS "окт_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 11 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "ноя_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 11 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "ноя_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 11), 0)                                                  AS "ноя_итого",
    COALESCE(SUM(1) FILTER(WHERE mon = 12 AND sending_status = 'Документ успешно зарегистрирован'), 0) AS "дек_да",
    COALESCE(SUM(1) FILTER(WHERE mon = 12 AND sending_status <> 'Документ успешно зарегистрирован'), 0) AS "дек_нет",
    COALESCE(SUM(1) FILTER(WHERE mon = 12), 0) AS "дек_итого"

    FROM (
        SELECT
            doctor,
            branch,
            sending_status,
            EXTRACT(MONTH FROM to_timestamp(document_date, 'DD.MM.YYYY HH24:MI')) AS mon,
            EXTRACT(YEAR  FROM to_timestamp(document_date, 'DD.MM.YYYY HH24:MI')) AS yr
        FROM load_data_emd
        WHERE document_type = 'Диспансеризация взрослого населения'
    ) sub
    WHERE yr = {selected_year}
    GROUP BY doctor, branch
    ORDER BY doctor, branch
    """
