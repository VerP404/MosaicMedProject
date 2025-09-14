# Оптимизированные SQL-запросы для ускорения работы
from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms


def sql_query_reproductive_building_department_optimized(selected_year, months_placeholder, inogorod, sanction, amount_null,
                                                       building=None,
                                                       department=None,
                                                       profile=None,
                                                       doctor=None,
                                                       input_start=None,
                                                       input_end=None,
                                                       treatment_start=None,
                                                       treatment_end=None):
    """
    Оптимизированная версия запроса - используем оригинальную структуру с улучшениями
    """
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    
    # Используем оригинальную структуру из query.py, но с оптимизациями
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
    LIMIT 10000
    """
    return query


def sql_query_reproductive_building_department_cached(selected_year, months_placeholder, inogorod, sanction, amount_null,
                                                     building=None,
                                                     department=None,
                                                     profile=None,
                                                     doctor=None,
                                                     input_start=None,
                                                     input_end=None,
                                                     treatment_start=None,
                                                     treatment_end=None):
    """
    Версия запроса с кэшированием промежуточных результатов
    """
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    
    query = f"""
    -- Создаем временную таблицу для кэширования
    CREATE TEMP TABLE IF NOT EXISTS temp_oms_filter AS
    SELECT  
        age, 
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
    WHERE goal IN ('ДР1', 'ДВ4', 'ОПВ')
      AND age > 17 
      AND age < 50
      AND report_year = '{selected_year}';
    
    -- Создаем индексы для ускорения
    CREATE INDEX IF NOT EXISTS idx_temp_oms_goal ON temp_oms_filter(goal);
    CREATE INDEX IF NOT EXISTS idx_temp_oms_enp ON temp_oms_filter(enp);
    
    -- Основной запрос
    WITH DR AS (
        SELECT *
        FROM temp_oms_filter
        WHERE goal = 'ДР1'
    ),
    DV_OPV AS (
        SELECT *
        FROM temp_oms_filter
        WHERE goal IN ('ДВ4', 'ОПВ')
    ),
    itog AS (
        SELECT 
            DV_OPV.patient,
            DV_OPV.birth_date,
            DV_OPV.age,
            DV_OPV.enp,
            DV_OPV.gender,
            DV_OPV.goal,
            DV_OPV.treatment_end,
            DV_OPV.doctor,
            DV_OPV.building,
            DV_OPV.department,
            CASE 
                WHEN DR.goal = 'ДР1' THEN 'да' 
                ELSE 'нет' 
            END AS "Статус ДР",
            DR.main_diagnosis_code
        FROM DV_OPV 
        LEFT JOIN DR ON DV_OPV.enp = DR.enp
    )
    SELECT *
    FROM itog
    ORDER BY patient;
    
    -- Очищаем временную таблицу
    DROP TABLE IF EXISTS temp_oms_filter;
    """
    return query
