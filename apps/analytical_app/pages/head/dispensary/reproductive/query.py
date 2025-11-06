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


def sql_query_reproductive_building_department_optimized(selected_year, months_placeholder, inogorod, sanction,
                                                         amount_null,
                                                         building=None,
                                                         department=None,
                                                         profile=None,
                                                         doctor=None,
                                                         input_start=None,
                                                         input_end=None,
                                                         treatment_start=None,
                                                         treatment_end=None,
                                                         gender=None,
                                                         dr_status=None,
                                                         attachment=None):
    """
    Оптимизированная версия запроса:
    1. Применяем фильтры по goal и age сразу в oms (до всех операций)
    2. Используем компактный lookup для DR (только enp и main_diagnosis_code)
    3. Минимизируем объем данных в промежуточных CTE
    4. Используем простой LEFT JOIN (PostgreSQL автоматически выберет hash join)
    5. Убираем лишние поля из промежуточных CTE
    """
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)

    # Формируем фильтры по полу и статусу ДР
    gender_filter = ""
    if gender and gender != '':
        if gender == 'Ж':
            gender_filter = "AND gender = 'Ж'"
        elif gender == 'М':
            gender_filter = "AND gender = 'М'"

    # Максимально оптимизированная версия
    query = f"""
    {base},
    oms_reproductive as (
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
          {gender_filter}
    ),

    DR_lookup as (
        SELECT DISTINCT ON (enp)
            enp,
            main_diagnosis_code
        FROM oms_reproductive
        WHERE goal = 'ДР1'
        ORDER BY enp, treatment_end DESC NULLS LAST
    ),

    DV_OPV as (
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
            department
        FROM oms_reproductive
        WHERE goal IN ('ДВ4', 'ОПВ')
    )
    """

    # Оптимизация: если фильтр по статусу ДР = 'да', используем INNER JOIN вместо LEFT JOIN
    # Это ускорит запрос, так как уменьшит объем данных для JOIN
    if dr_status == 'да':
        if attachment == 'да':
            query += f""",
    itog as (
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
            'да' AS "Статус ДР",
            DR_lookup.main_diagnosis_code,
            'да' AS "Прикрепление"
        FROM DV_OPV 
        INNER JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '')
    )
    """
        elif attachment == 'нет':
            query += f""",
    itog as (
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
            'да' AS "Статус ДР",
            DR_lookup.main_diagnosis_code,
            'нет' AS "Прикрепление"
        FROM DV_OPV 
        INNER JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE NOT EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '')
    )
    """
        else:
            query += f""",
    itog as (
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
            'да' AS "Статус ДР",
            DR_lookup.main_diagnosis_code,
            CASE 
                WHEN EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '') THEN 'да' 
                ELSE 'нет' 
            END AS "Прикрепление"
        FROM DV_OPV 
        INNER JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
    )
    """
    elif dr_status == 'нет':
        if attachment == 'да':
            query += f""",
    itog as (
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
            'нет' AS "Статус ДР",
            NULL AS main_diagnosis_code,
            'да' AS "Прикрепление"
        FROM DV_OPV 
        LEFT JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE DR_lookup.enp IS NULL
          AND EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '')
    )
    """
        elif attachment == 'нет':
            query += f""",
    itog as (
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
            'нет' AS "Статус ДР",
            NULL AS main_diagnosis_code,
            'нет' AS "Прикрепление"
        FROM DV_OPV 
        LEFT JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE DR_lookup.enp IS NULL
          AND NOT EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '')
    )
    """
        else:
            query += f""",
    itog as (
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
            'нет' AS "Статус ДР",
            NULL AS main_diagnosis_code,
            CASE 
                WHEN EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '') THEN 'да' 
                ELSE 'нет' 
            END AS "Прикрепление"
        FROM DV_OPV 
        LEFT JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE DR_lookup.enp IS NULL
    )
    """
    else:
        if attachment == 'да':
            query += f""",
    itog as (
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
                WHEN DR_lookup.enp IS NOT NULL THEN 'да' 
                ELSE 'нет' 
            END AS "Статус ДР",
            DR_lookup.main_diagnosis_code,
            'да' AS "Прикрепление"
        FROM DV_OPV 
        LEFT JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '')
    )
    """
        elif attachment == 'нет':
            query += f""",
    itog as (
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
                WHEN DR_lookup.enp IS NOT NULL THEN 'да' 
                ELSE 'нет' 
            END AS "Статус ДР",
            DR_lookup.main_diagnosis_code,
            'нет' AS "Прикрепление"
        FROM DV_OPV 
        LEFT JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
        WHERE NOT EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '')
    )
    """
        else:
            query += f""",
    itog as (
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
                WHEN DR_lookup.enp IS NOT NULL THEN 'да' 
                ELSE 'нет' 
            END AS "Статус ДР",
            DR_lookup.main_diagnosis_code,
            CASE 
                WHEN EXISTS (SELECT 1 FROM data_loader_iszlpeople WHERE data_loader_iszlpeople.enp = DV_OPV.enp AND COALESCE(NULLIF(data_loader_iszlpeople.enp, '-'), '') <> '') THEN 'да' 
                ELSE 'нет' 
            END AS "Прикрепление"
        FROM DV_OPV 
        LEFT JOIN DR_lookup ON DV_OPV.enp = DR_lookup.enp
    )
    """

    query += """
    SELECT *
    FROM itog
    ORDER BY patient
    """
    return query

