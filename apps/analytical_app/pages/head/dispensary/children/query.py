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
