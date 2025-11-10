def sql_query_gis_oms_research(selected_months, selected_year, status_list=None):
    """
    Запрос для исследований (ГИС ОМС)
    Группировка по возрастным группам с детализацией по исследованиям
    """
    months_placeholder = ', '.join([f"'{month}'" for month in selected_months])
    
    # Формируем фильтр по статусу
    if status_list:
        status_placeholders = ', '.join([f"'{s}'" for s in status_list])
        status_filter = f"AND status IN ({status_placeholders})"
    else:
        status_filter = "AND status = '3'"
    
    query = f"""
    SELECT
        COALESCE(age_group, 'Итого') AS "Группа",
        COUNT(*) AS "Количество",
        SUM(ROUND(amount::NUMERIC, 2)) AS "Сумма",
        COUNT(*) FILTER (WHERE goal = '541') AS "к-во: исследования",
        SUM(ROUND((CASE WHEN goal = '541' THEN amount::NUMERIC ELSE 0 END), 2)) AS "сумма: исследования",
        COUNT(*) FILTER (WHERE goal = '541' AND amount IN ('589.82', '1179.64', '1769.46', '2359.28', '1387.58', '2081.37', '2775.16', '693.79')) AS "к-во: УЗИ",
        SUM(ROUND((CASE WHEN goal = '541' AND amount IN ('589.82', '1179.64', '1769.46', '2359.28', '1387.58', '2081.37', '2775.16', '693.79') THEN amount::NUMERIC ELSE 0 END), 2)) AS "сумма: УЗИ",
        COUNT(*) FILTER (WHERE goal = '541' AND amount IN ('1059.57', '1404.98', '2077.79', '2387.07', '2972.81', '895.02', '994.23')) AS "к-во: эндоскопия",
        SUM(ROUND((CASE WHEN goal = '541' AND amount IN ('1059.57', '1404.98', '2077.79', '2387.07', '2972.81', '895.02', '994.23') THEN amount::NUMERIC ELSE 0 END), 2)) AS "сумма: эндоскопия",
        COUNT(*) FILTER (WHERE goal = '561') AS "к-во: COVID",
        SUM(ROUND((CASE WHEN goal = '561' THEN amount::NUMERIC ELSE 0 END), 2)) AS "сумма: COVID"
    FROM (
        SELECT
            *,
            CASE
                WHEN EXTRACT(YEAR FROM AGE(TO_DATE(birth_date, 'DD-MM-YYYY'))) < 18 THEN 'Дети'
                ELSE 'Взрослые'
            END AS age_group
        FROM load_data_talons
        WHERE treatment_end LIKE '%{selected_year}%'
          AND report_period IN ({months_placeholder})
          AND goal IN ('541', '561')
          {status_filter}
    ) AS subquery
    GROUP BY GROUPING SETS ((age_group), ())
    ORDER BY CASE WHEN age_group IS NULL THEN 1 ELSE 0 END, age_group
    """
    return query.strip()


def sql_query_gis_oms_ambulatory(selected_months, selected_year, status_list=None):
    """
    Запрос для амбулаторной помощи (ГИС ОМС)
    Группировка по профилю врача с детализацией по целям
    """
    months_placeholder = ', '.join([f"'{month}'" for month in selected_months])
    
    # Формируем фильтр по статусу
    if status_list:
        status_placeholders = ', '.join([f"'{s}'" for s in status_list])
        status_filter = f"AND status IN ({status_placeholders})"
    else:
        status_filter = "AND status = '3'"
    
    query = f"""
    SELECT doctor_profile,
           SUM(CASE WHEN goal IN ('1', '3', '5', '7', '9', '10', '113', '114', '22', '32', '64', '541', '561',
                                  'ДВ4', 'ОПВ', 'УД1', 'ДР1', 'ПН1', 'ДР1') THEN 1 ELSE 0 END) AS "Посещений всего",
           0 as "Паллиатив",
           0 as "Патронаж",
           0 as "Без патронажа",
           COUNT(*) AS "Посещений с иными целями",
           SUM(CASE WHEN goal IN ('22') THEN 1 ELSE 0 END) AS "Неотложная помощь",
           0 AS "Гемодиализ",
           0 AS "Иные цели",
           SUM(CASE WHEN goal IN ('30', '301', '305', '307') THEN 1 ELSE 0 END) AS "Обращения",
           SUM(amount::numeric) AS "Сумма оплаты"
    FROM load_data_talons
    WHERE report_period IN ({months_placeholder})
      {status_filter}
      AND goal IN ('1', '3', '5', '7', '9', '10', '113', '114', '22', '32', '64', '541', '561',
                   'ДВ4', 'ОПВ', 'УД1', 'ДР1', 'ПН1', 'ДР1',
                   '30', '301', '305', '307')
    GROUP BY doctor_profile
    ORDER BY "Посещений всего" DESC
    """
    return query.strip()


def sql_query_gis_oms_stationary(selected_months, selected_year, status_list=None):
    """
    Запрос для стационаров (ГИС ОМС)
    Группировка по KSG и профилю врача
    """
    months_placeholder = ', '.join([f"'{month}'" for month in selected_months])
    
    # Формируем фильтр по статусу
    if status_list:
        status_placeholders = ', '.join([f"'{s}'" for s in status_list])
        status_filter = f"AND status IN ({status_placeholders})"
    else:
        status_filter = "AND status = '3'"
    
    query = f"""
    SELECT 
        ksg,
        doctor_profile,
        COUNT(*) AS "количество",
        SUM(amount::numeric) AS "Сумма",
        SUM(CASE WHEN gender = 'М' THEN 1 ELSE 0 END) AS "М количество",
        SUM(CASE WHEN gender = 'М' THEN amount::numeric ELSE 0 END) AS "М сумма",
        SUM(CASE WHEN gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж количество",
        SUM(CASE WHEN gender = 'Ж' THEN amount::numeric ELSE 0 END) AS "Ж сумма"
    FROM load_data_talons
    WHERE ksg != '-'
      AND report_period IN ({months_placeholder})
      AND treatment_end LIKE '%{selected_year}%'
      {status_filter}
    GROUP BY ksg, doctor_profile
    ORDER BY ksg, doctor_profile
    """
    return query.strip()

