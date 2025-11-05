from sqlalchemy import text
import time
import pandas as pd
from apps.analytical_app.pages.SQL_query.query import base_query
from apps.analytical_app.query_executor import engine
from apps.analytical_app.pages.economist.svpod.query import get_groups_for_indicators_report, get_filter_conditions


def get_dynamic_conditions(year):
    """
    Получает условия фильтрации из groupindicators через FilterCondition.
    Используется для обратной совместимости со старым кодом.
    Кэширование убрано, чтобы данные всегда были актуальными.
    """
    # Получаем группы для отчета индикаторов
    groups = get_groups_for_indicators_report(year)
    
    if groups.empty:
        return []
    
    group_ids = groups['id'].tolist()
    
    # Получаем условия фильтрации для каждой группы
    conditions = []
    for group_id in group_ids:
        filter_conditions = get_filter_conditions([group_id], year)
        if filter_conditions:
            # Используем имя группы как type
            group_name = groups[groups['id'] == group_id]['name'].iloc[0]
            conditions.append((group_name, filter_conditions, "AND"))
    
    return conditions


def get_plan_for_group(group_id, selected_year, months_list, mode='both'):
    """
    Получает план для группы за выбранные месяцы.
    mode: 'both' - возвращает (quantity, amount), 'quantity' - только количество, 'amount' - только сумму
    """
    if not months_list:
        return 0, 0.0
    
    months_str = ', '.join(map(str, months_list))
    query = text(f"""
        SELECT 
            COALESCE(SUM(mp.quantity), 0) AS plan_quantity,
            COALESCE(SUM(mp.amount), 0) AS plan_amount
        FROM plan_monthlyplan AS mp
        INNER JOIN plan_annualplan AS ap ON mp.annual_plan_id = ap.id
        WHERE ap.group_id = :group_id 
        AND ap.year = :year
        AND mp.month IN ({months_str})
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"group_id": group_id, "year": selected_year}).fetchone()
        if result:
            return result[0] or 0, float(result[1] or 0.0)
        return 0, 0.0


def sql_query_indicators(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                         department=None,
                         profile=None,
                         doctor=None,
                         input_start=None, input_end=None,
                         treatment_start=None,
                         treatment_end=None,
                         status_list=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end, status_list)
    # Получаем динамические условия из groupindicators
    dynamic_conditions = get_dynamic_conditions(selected_year)
    
    # Получаем группы для получения планов
    groups = get_groups_for_indicators_report(selected_year)
    group_name_to_id = {}
    if not groups.empty:
        group_name_to_id = dict(zip(groups['name'], groups['id']))
    
    # Парсим список месяцев из months_placeholder
    try:
        months_list = [int(m.strip()) for m in months_placeholder.split(',') if m.strip().isdigit()]
        if not months_list:
            months_list = list(range(1, 13))  # По умолчанию все месяцы
    except:
        months_list = list(range(1, 13))  # По умолчанию все месяцы
    
    # Создаем список для объединенных запросов
    union_queries = []

    # Создаем запросы для каждой группы
    for condition_type, where_clause, operator in dynamic_conditions:
        # Экранируем одинарные кавычки для SQL
        escaped_filter_description = where_clause.replace("'", "''")
        
        # Получаем план для этой группы
        group_id = group_name_to_id.get(condition_type)
        plan_quantity = 0
        plan_amount = 0.0
        if group_id:
            plan_quantity, plan_amount = get_plan_for_group(group_id, selected_year, months_list)
        
        # Используем правильную логику группировки статусов как в svpod
        union_query = f"""
            SELECT '{condition_type}' AS type,
                   {plan_quantity} AS "План (количество)",
                   ROUND({plan_amount}::numeric, 2) AS "План (сумма)",
                   COUNT(*) AS "К-во",
                   ROUND(COALESCE(SUM(CAST(amount_numeric AS numeric(10, 2))), 0)::numeric, 2) AS "Сумма",
                   '{escaped_filter_description}' AS "Условия фильтра"
            FROM oms
            WHERE {where_clause}
            AND inogorodniy = false
            AND sanctions IN ('-', '0')
            AND amount_numeric != '0'
        """
        union_queries.append(union_query)

    # Объединяем основной запрос с динамическими условиями
    if union_queries:
        # Объединяем только динамические запросы без base
        final_query = f"{base}\n" + " UNION ALL ".join(union_queries) + "\nLIMIT 10000"
    else:
        # Если нет динамических условий, возвращаем пустой результат
        final_query = f"{base}\nSELECT 'no_data' AS type, 0 AS \"План (количество)\", 0.00 AS \"План (сумма)\", 0 AS \"К-во\", 0.00 AS \"Сумма\", 'Нет данных' AS \"Условия фильтра\" FROM oms WHERE 1=0\nLIMIT 10000"

    return final_query


def sql_query_indicators_details(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
                                 department=None, profile=None, doctor=None,
                                 input_start=None, input_end=None,
                                 treatment_start=None, treatment_end=None,
                                 indicator_type=None, status_list=None):
    """
    SQL-запрос для детализации индикаторов по талонам
    Возвращает детальную информацию по талонам для выбранного индикатора
    """
    # Получаем динамические условия для фильтрации
    dynamic_conditions = get_dynamic_conditions(selected_year)
    
    # Находим условие для выбранного типа индикатора
    indicator_filter = ""
    if indicator_type:
        for condition_type, where_clause, operator in dynamic_conditions:
            if condition_type == indicator_type:
                indicator_filter = f"AND ({where_clause})"
                break
    
    # Формируем дополнительные фильтры
    building_filter = ""
    department_filter = ""
    profile_filter = ""
    doctor_filter = ""
    inogorodniy_filter = ""
    sanction_filter = ""
    amount_null_filter = ""
    treatment = ""
    initial_input = ""
    status = ""
    
    if building:
        building_filter = f"AND building_id IN ({','.join(map(str, building))})"
    if department:
        department_filter = f"AND department_id IN ({','.join(map(str, department))})"
    if profile:
        profile_filter = f"AND profile_id IN ({','.join(map(str, profile))})"
    if doctor:
        doctor_filter = f"AND doctor_id IN ({','.join(map(str, doctor))})"
    
    if inogorod == '1':
        inogorodniy_filter = f"AND inogorodniy = false"
    if inogorod == '2':
        inogorodniy_filter = f"AND inogorodniy = true"
    
    if sanction == '1':
        sanction_filter = f"AND sanctions IN ('-', '0')"
    if sanction == '2':
        sanction_filter = f"AND sanctions NOT IN ('-', '0')"
    
    if amount_null == '1':
        amount_null_filter = f"AND amount_numeric != '0'"
    if amount_null == '2':
        amount_null_filter = f"AND amount_numeric = '0'"
    
    if treatment_start and treatment_end:
        treatment = (f"AND to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date('{treatment_start}', "
                     f"'DD-MM-YYYY') and to_date('{treatment_end}', 'DD-MM-YYYY')")
    
    if input_start and input_end:
        initial_input = (f"AND to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date('{input_start}', "
                         f"'DD-MM-YYYY') and to_date('{input_end}', 'DD-MM-YYYY')")
    
    if status_list:
        status = "AND status IN (" + ",".join(f"'{cel}'" for cel in status_list) + ")"
    
    query = f"""
    WITH report_data AS (SELECT oms.*,
                            CASE
                                WHEN oms.report_period = '-' THEN RIGHT(oms.treatment_end, 4)
                                ELSE RIGHT(oms.report_period, 4)
                                END AS report_year,
                            CASE
                                WHEN oms.report_period = '-' THEN
                                    CASE
                                        WHEN EXTRACT(DAY FROM CURRENT_DATE)::INT <= 4 THEN
                                            CASE
                                                WHEN TO_NUMBER(SUBSTRING(oms.treatment_end FROM 4 FOR 2), '99') =
                                                     EXTRACT(MONTH FROM CURRENT_DATE) THEN
                                                    EXTRACT(MONTH FROM CURRENT_DATE)::INT
                                                ELSE
                                                    CASE
                                                        WHEN EXTRACT(MONTH FROM CURRENT_DATE)::INT = 1 THEN 12
                                                        ELSE EXTRACT(MONTH FROM CURRENT_DATE)::INT - 1
                                                        END
                                                END
                                        ELSE
                                            EXTRACT(MONTH FROM CURRENT_DATE)::INT
                                        END
                                ELSE
                                    CASE TRIM(SUBSTRING(oms.report_period FROM 1 FOR
                                                        POSITION(' ' IN oms.report_period) - 1))
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
                                END AS report_month_number
                     FROM data_loader_omsdata oms),
     oms_data as (SELECT report_data.talon,
                    (ARRAY ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 
                    'Октябрь', 'Ноябрь', 'Декабрь'])[report_data.report_month_number] AS report_month,
                    report_month_number,
                    report_data.report_year,
                    report_data.source_id,
                    report_data.status,
                    CASE
                        WHEN report_data.goal = '-' AND report_data.talon_type = 'Стоматология'
                            THEN report_data.talon_type
                        ELSE report_data.goal
                        END                                                 AS goal,
                    COALESCE(
                            ARRAY_TO_STRING(
                                    ARRAY(
                            SELECT otc.name
                            FROM oms_reference_generalomstarget og
                                     LEFT JOIN oms_reference_medicalorganizationomstarget mo
                                               ON mo.general_target_id = og.id
                                     LEFT JOIN oms_reference_medicalorganizationomstarget_categories moc
                                               ON moc.medicalorganizationomstarget_id = mo.id
                                     LEFT JOIN oms_reference_omstargetcategory otc ON otc.id = moc.omstargetcategory_id
                            WHERE og.code = report_data.goal
                                    ),
                                    ', '
                            ),
                            '-'
                    )                                                          AS target_categories,
                    report_data.patient,
                    report_data.birth_date,
                    CASE
                        WHEN report_data.treatment_end ~ '^\\d{{2}}-\\d{{2}}-\\d{{4}}$' AND
                             report_data.birth_date ~ '^\\d{{2}}-\\d{{2}}-\\d{{4}}$' THEN
                            CAST(SUBSTRING(report_data.treatment_end FROM 7 FOR 4) AS INTEGER) -
                            CAST(SUBSTRING(report_data.birth_date FROM 7 FOR 4) AS INTEGER)
                        ELSE NULL
                        END                                                    AS age,
                    report_data.gender,
                    CASE
                        WHEN report_data.enp = '-' THEN report_data.policy
                        ELSE report_data.enp
                        END                                                                  AS enp,
                    report_data.smo_code,
                    CASE
                        WHEN report_data.smo_code LIKE '360%' THEN false
                        ELSE true
                        END                                                        AS inogorodniy,
                    report_data.treatment_start,
                    report_data.treatment_end,
                    report_data.visits,
                    report_data.mo_visits,
                    report_data.home_visits,
                    CASE
                        WHEN report_data.main_diagnosis = '-' THEN NULL
                        ELSE SPLIT_PART(report_data.main_diagnosis, ' ', 1)
                        END                                                           AS main_diagnosis_code,
                    CASE
                        WHEN report_data.additional_diagnosis = '-' THEN report_data.additional_diagnosis
                        ELSE
                            ARRAY_TO_STRING(
                                    ARRAY(
                                            SELECT SPLIT_PART(TRIM(s), ' ', 1)
                                            FROM UNNEST(STRING_TO_ARRAY(report_data.additional_diagnosis, ',')) AS s
                                            WHERE SPLIT_PART(TRIM(s), ' ', 1) ~ '^[A-Z]\\d{{2}}(\\.\\d)?$'
                                    ),
                                    ','
                            )
                        END        AS additional_diagnosis_codes,
                    report_data.initial_input_date,
                    report_data.last_change_date,
                    CASE
                        WHEN report_data.amount ~ '^[0-9]+(\\.[0-9]+)?$' THEN CAST(report_data.amount AS NUMERIC)
                        ELSE NULL
                        END                                                      AS amount_numeric,
                    report_data.sanctions,
                    report_data.ksg,
                    department.id as department_id,                
                    department.name                                                    AS department,
                    building.id as building_id,
                    building.name      AS building,
                    SUBSTRING(report_data.doctor FROM 1 FOR POSITION(' ' IN report_data.doctor) - 1)   AS doctor_code,
                    pd.id as doctor_id,
                    CONCAT(person.last_name, ' ',
                           SUBSTRING(person.first_name FROM 1 FOR 1), '.',
                           SUBSTRING(person.patronymic FROM 1 FOR 1),
                           '.')                                                    AS doctor,
                    specialty.description                 AS specialty,
                    profile.description               AS profile,
                    profile.id as profile_id

             FROM report_data
                      LEFT JOIN (SELECT DISTINCT ON (doctor_code) * 
                                 FROM personnel_doctorrecord
                                 ORDER BY doctor_code, id 
             ) pd ON SUBSTRING(report_data.doctor FROM 1 FOR POSITION(' ' IN report_data.doctor) - 1) = pd.doctor_code
                      LEFT JOIN public.organization_department department ON department.id = pd.department_id
                      LEFT JOIN public.organization_building building ON building.id = department.building_id
                      LEFT JOIN public.personnel_specialty specialty ON specialty.id = pd.specialty_id
                      LEFT JOIN public.personnel_profile profile ON profile.id = pd.profile_id
                      LEFT JOIN public.personnel_person person ON person.id = pd.person_id
             ),
     oms as (select * from oms_data 
             WHERE report_year = '{selected_year}' 
                   AND report_month_number IN ({months_placeholder})
                   {inogorodniy_filter}
                   {sanction_filter}
                   {amount_null_filter}
                   {building_filter}
                   {department_filter}
                   {profile_filter}
                   {doctor_filter}
                   {treatment}
                   {initial_input}
                   {status}
                   {indicator_filter}
             )
    SELECT talon                               AS "Талон",
           goal                                AS "Цель", 
           status                              AS "Статус",
           enp                                 AS "ЕНП",
           patient                             AS "Пациент",
           birth_date                          AS "Дата рождения",
           treatment_start                     AS "Дата начала",
           treatment_end                       AS "Дата окончания",
           gender                              AS "Пол",
           doctor                              AS "Врач",
           specialty                           AS "Специальность",
           building                            AS "Корпус",
           department                          AS "Отделение",
           report_month                        AS "Отчетный месяц"
    FROM oms
    ORDER BY talon
    """
    
    return query


def clear_cache():
    """Очищает кэш для обновления условий"""
    # Кэширование убрано из get_dynamic_conditions, поэтому функция всегда возвращает актуальные данные
    # Оставляем функцию для обратной совместимости на случай, если в будущем понадобится кэширование
    pass
