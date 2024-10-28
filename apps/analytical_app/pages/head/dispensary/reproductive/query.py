# отчет по диспансеризации
from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms


def sql_query_reproductive(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
    SELECT goal, gender,
           {columns_by_status_oms()}
           FROM oms
           WHERE goal in ('ДР1', 'ДР2')
           group by goal, gender;
    """
    return query


def sql_query_reproductive_building(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
            goal, gender,
           {columns_by_status_oms()}
           FROM oms
           WHERE goal in ('ДР1', 'ДР2')
           group by building, goal, gender;
    """
    return query


def sql_query_reproductive_building_department(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
            goal, gender,
           {columns_by_status_oms()}
           FROM oms
           WHERE goal in ('ДР1', 'ДР2')
           group by building, department, goal, gender;
    """
    return query


def sql_query_reproductive_building_department(selected_year, months_placeholder, inogorod, sanction, amount_null,
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
    {base},
    oms_filter as (
        SELECT  age, 
                patient,
                birth_date,
                gender,
                goal, 
                enp,
                treatment_end,
                doctor,
                building,
                department,
                main_diagnosis_code
                FROM oms
                WHERE goal in ('ДР1', 'ДВ4', 'ОПВ')
                and age > 17 and age < 50
    ),
    
    DR as (SELECT  *
            FROM oms_filter
            WHERE goal in ('ДР1')
            ),
    DV_OPV as (SELECT  *
            FROM oms_filter
            WHERE goal in ('ДВ4', 'ОПВ')
            ),
    itog as (
    select DV_OPV.patient,
           DV_OPV.birth_date,
           DV_OPV.age,
           DV_OPV.enp,
           DV_OPV.gender,
           DV_OPV.goal,
           DV_OPV.treatment_end,
           DV_OPV.doctor,
           DV_OPV.building,
           DV_OPV.department,
           case when DR.goal = 'ДР1' then 'да' else 'нет' end as "Статус ДР",
           DR.main_diagnosis_code
    from DV_OPV left join DR on DV_OPV.enp = DR.enp
    )        
            
    select *
    from itog
    order by patient
            ;
    """
    return query
