import pandas as pd
from sqlalchemy import text

from apps.analytical_app.pages.SQL_query.query import base_query
from apps.analytical_app.query_executor import engine
from datetime import datetime


# Функция для генерации условий фильтрации на основе планов
def get_filter_conditions(group_ids, year):
    group_ids_str = ", ".join(map(str, group_ids))

    query = f"""
    SELECT field_name, filter_type, values
    FROM plan_filtercondition
    WHERE group_id IN ({group_ids_str}) AND year = {year}
    """
    conditions_df = pd.read_sql(query, engine)

    filter_clauses = []
    for _, row in conditions_df.iterrows():
        field_name = row['field_name']
        filter_type = row['filter_type']
        values = row['values']

        if filter_type == 'in':
            filter_clauses.append(f"{field_name} IN ({values})")
        elif filter_type == 'exact':
            filter_clauses.append(f"{field_name} = {values}")
        elif filter_type == 'like':
            filter_clauses.append(f"{field_name} LIKE {values}")
        elif filter_type == 'not_like':
            filter_clauses.append(f"{field_name} NOT LIKE {values}")

    return " AND ".join(filter_clauses)


def sql_query_rep(selected_year, group_id,
                  months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
                  inogorod=None, sanction=None, amount_null=None,
                  building=None, department=None, profile=None, doctor=None,
                  input_start=None, input_end=None, treatment_start=None, treatment_end=None,
                  filter_conditions=None, mode='finance', unique_flag=False):
    """
    Формирует SQL запрос с учетом базовых фильтров и, опционально, рассчета уникальных записей.

    Параметры:
      selected_year: выбранный год
      group_id: идентификатор группы (при необходимости, можно использовать в base_query)
      months_placeholder: строка с номерами месяцев
      inogorod, sanction, amount_null, building, department, profile, doctor,
      input_start, input_end, treatment_start, treatment_end: дополнительные фильтры,
        передаваемые в base_query
      filter_conditions: дополнительные условия для WHERE
      mode: 'finance' или иное – влияет на тип агрегации (суммы или количества)
      unique_flag: если True, происходит выборка уникальных записей с применением оконной функции.

    Возвращает:
      Итоговый SQL запрос (строка)
    """

    # Получаем базовую часть запроса (например, с привязкой к году, периодам и т.п.)
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null,
                      building, department, profile, doctor, input_start, input_end, treatment_start, treatment_end)

    # Формируем базовый набор условий
    where_conditions = [
        "inogorodniy = false",
        "sanctions IN ('-', '0')",  # Включаем как '-' так и '0'
        "amount_numeric != '0'"
    ]
    if filter_conditions:
        where_conditions.append(filter_conditions)

    # Если есть условия – формируем WHERE-клаузулу
    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

    # В зависимости от режима (finance или нет) выбираем агрегирующие столбцы
    if mode == 'finance':
        agg_columns = f"""
                SUM(CASE WHEN status = '1' THEN amount_numeric END) AS новые,
                SUM(CASE WHEN status = '2' THEN amount_numeric END) AS в_тфомс,
                SUM(CASE WHEN status = '3' THEN amount_numeric END) AS оплачено,
                SUM(CASE WHEN status IN ('5', '7', '12') THEN amount_numeric END) AS отказано,
                SUM(CASE WHEN status IN ('6', '8', '4') THEN amount_numeric END) AS исправлено,
                SUM(CASE WHEN status IN ('0', '13', '17') THEN amount_numeric END) AS отменено
        """
    else:
        agg_columns = f"""
                COUNT(CASE WHEN status = '1' THEN 1 END) AS новые,
                COUNT(CASE WHEN status = '2' THEN 1 END) AS в_тфомс,
                COUNT(CASE WHEN status = '3' THEN 1 END) AS оплачено,
                COUNT(CASE WHEN status IN ('5', '7', '12') THEN 1 END) AS отказано,
                COUNT(CASE WHEN status IN ('6', '8', '4') THEN 1 END) AS исправлено,
                COUNT(CASE WHEN status IN ('0', '13', '17') THEN 1 END) AS отменено
        """

    if unique_flag:
        # Формируем запрос с уникальностью через оконную функцию и CTE
        # Используем логику приоритизации статусов как в tab4.py
        query = f"""
WITH filtered AS (
    {base}
    SELECT *
    FROM oms
    {where_clause}
),
has_status_3 AS (
    SELECT enp
    FROM filtered
    WHERE status = '3'
    GROUP BY enp
),
prioritized AS (
    SELECT f.*,
           CASE 
             WHEN f.status = '3' THEN 0
             ELSE
               CASE f.status
                 WHEN '2' THEN 1
                 WHEN '4' THEN 2
                 WHEN '6' THEN 3
                 WHEN '8' THEN 4
                 WHEN '1' THEN 5
                 WHEN '5' THEN 6
                 WHEN '7' THEN 7
                 WHEN '12' THEN 8
                 WHEN '13' THEN 9
                 WHEN '17' THEN 10
                 WHEN '0' THEN 11
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
                   CASE WHEN has_status_3 THEN CASE WHEN status = '3' THEN 0 ELSE 1 END ELSE 0 END,
                   report_month_number,
                   status_priority
           ) AS rn
    FROM prioritized
),
unique_oms AS (
    SELECT *
    FROM ranked
    WHERE rn = 1
)
SELECT report_month_number AS month,
       {agg_columns},
       COUNT(*) AS total_count
FROM unique_oms
GROUP BY month
ORDER BY month;
        """
    else:
        # Стандартный запрос без уникальности
        query = f"""
{base}
SELECT report_month_number AS month,
       {agg_columns},
       COUNT(*) AS total_count
FROM oms
{where_clause}
GROUP BY month
ORDER BY month
        """
    return query


def sql_query_svpod_details(selected_year, selected_month, group_ids, filter_conditions, status_filter=None):
    """
    SQL-запрос для детализации svpod по талонам
    Возвращает детальную информацию по талонам для выбранной группы показателей
    """
    # Формируем условия фильтрации
    where_conditions = []
    
    # Добавляем условия по группе показателей (filter_conditions - это строка)
    if filter_conditions:
        where_conditions.append(filter_conditions)
    
    # Добавляем условия по году и месяцу
    if selected_year:
        where_conditions.append(f"report_year = '{selected_year}'")
    
    if selected_month:
        where_conditions.append(f"report_month_number = {selected_month}")
    
    # Добавляем фильтр по статусам, если указан
    if status_filter:
        if isinstance(status_filter, str) and status_filter.startswith("COMPLEX_LOGIC:"):
            # Обрабатываем сложную логику для нарастающих показателей
            complex_conditions = status_filter.replace("COMPLEX_LOGIC:", "").split(":")
            # Объединяем условия через OR
            complex_where = " OR ".join(complex_conditions)
            where_conditions.append(f"({complex_where})")
        else:
            # Обычная логика для простых статусов
            status_values = "', '".join(status_filter)
            where_conditions.append(f"status IN ('{status_values}')")
    
    # Базовые фильтры (как в основном запросе)
    where_conditions.extend([
        "inogorodniy = false",
        "amount_numeric != '0'",
        "sanctions IN ('-', '0')"
    ])
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
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
     oms as (select * from oms_data WHERE {where_clause})
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


def get_all_end_groups():
    """
    Получает все конечные группы показателей (те, у которых нет дочерних групп).
    Это группы, которые используются для формирования отчетов.
    Устарело: используйте get_groups_for_cumulative_report(selected_year) вместо этого.
    """
    query = """
    SELECT DISTINCT g.id, g.name
    FROM plan_groupindicators g
    WHERE NOT EXISTS (
        SELECT 1 
        FROM plan_groupindicators child 
        WHERE child.parent_id = g.id
    )
    ORDER BY g.name
    """
    groups = pd.read_sql(query, engine)
    return groups


def get_groups_for_cumulative_report(selected_year):
    """
    Получает группы показателей, которые нужно отображать в отчете нарастающе.
    Выбираются группы, у которых AnnualPlan.show_in_cumulative_report = True для указанного года.
    Может быть любой уровень вложенности (не только конечные группы).
    Возвращает полную иерархию групп через обратный слэш (\\).
    """
    from sqlalchemy import text
    
    query = text("""
    WITH RECURSIVE group_paths AS (
        SELECT 
            g.id,
            g.name,
            g.parent_id,
            g.name::text as full_path,
            0 as level
        FROM plan_groupindicators g
        INNER JOIN plan_annualplan ap ON ap.group_id = g.id
        WHERE ap.year = :selected_year 
        AND ap.show_in_cumulative_report = true
        
        UNION ALL
        
        SELECT 
            gp.id,
            p.name,
            p.parent_id,
            p.name || ' \\ ' || gp.full_path as full_path,
            gp.level + 1
        FROM plan_groupindicators p
        INNER JOIN group_paths gp ON gp.parent_id = p.id
    )
    SELECT DISTINCT ON (id)
        id,
        full_path as name
    FROM group_paths
    ORDER BY id, level DESC
    """)
    groups = pd.read_sql(query, engine, params={"selected_year": selected_year})
    return groups


def get_groups_for_indicators_report(selected_year):
    """
    Получает группы показателей, которые нужно отображать в отчете индикаторов.
    Выбираются группы, у которых AnnualPlan.show_in_indicators_report = True для указанного года.
    Может быть любой уровень вложенности (не только конечные группы).
    Возвращает полную иерархию групп через обратный слэш (\\).
    """
    from sqlalchemy import text
    
    query = text("""
    WITH RECURSIVE group_paths AS (
        SELECT 
            g.id,
            g.name,
            g.parent_id,
            g.name::text as full_path,
            0 as level
        FROM plan_groupindicators g
        INNER JOIN plan_annualplan ap ON ap.group_id = g.id
        WHERE ap.year = :selected_year 
        AND ap.show_in_indicators_report = true
        
        UNION ALL
        
        SELECT 
            gp.id,
            p.name,
            p.parent_id,
            p.name || ' \\ ' || gp.full_path as full_path,
            gp.level + 1
        FROM plan_groupindicators p
        INNER JOIN group_paths gp ON gp.parent_id = p.id
    )
    SELECT DISTINCT ON (id)
        id,
        full_path as name
    FROM group_paths
    ORDER BY id, level DESC
    """)
    groups = pd.read_sql(query, engine, params={"selected_year": selected_year})
    return groups


def get_cumulative_report_for_all_groups(selected_year, mode='volumes', unique_flag=False, reporting_month=None, payment_type='presented'):
    """
    Формирует отчет нарастающе по всем группам показателей.
    Для каждой группы рассчитывает нарастающий итог за год.
    
    Возвращает DataFrame с колонками:
    - Группа показателей (название)
    - План 1/12 (сумма за год)
    - Факт (нарастающий итог)
    - Остаток
    - % выполнения
    - новые, в_тфомс, оплачено, исправлено, отказано, отменено (суммы)
    """
    from apps.analytical_app.callback import TableUpdater
    from sqlalchemy import text
    
    # Получаем группы, помеченные для отображения в отчете нарастающе
    groups = get_groups_for_cumulative_report(selected_year)
    
    if groups.empty:
        return pd.DataFrame()
    
    # Определяем текущий месяц и день
    today = datetime.today()
    default_month = today.month - 1 if today.day <= 5 else today.month
    current_day = today.day
    current_month = reporting_month if reporting_month is not None else default_month
    
    results = []

    for _, group_row in groups.iterrows():
        group_id = group_row['id']
        group_name = group_row['name']
        
        # Получаем условия фильтрации для группы
        filter_conditions = get_filter_conditions([group_id], selected_year)
        
        # Получаем фактические данные по месяцам
        fact_columns, fact_data_list = TableUpdater.query_to_df(
            engine,
            sql_query_rep(selected_year,
                          group_id=[group_id],
                          filter_conditions=filter_conditions,
                          mode=mode,
                          unique_flag=unique_flag)
        )
        
        # Преобразуем в словарь по месяцам
        fact_dict = {}
        for row in fact_data_list:
            m = row["month"]
            fact_dict[m] = row
        
        # Получаем плановые данные
        plan_field = "quantity" if mode == 'volumes' else "amount"
        plan_query = text(f"""
            SELECT mp.month, SUM(mp.{plan_field}) AS plan
            FROM plan_monthlyplan AS mp
            INNER JOIN plan_annualplan AS ap ON mp.annual_plan_id = ap.id
            WHERE ap.group_id = :group_id AND ap.year = :year
            GROUP BY mp.month
            ORDER BY mp.month
        """)
        with engine.connect() as connection:
            result = connection.execute(plan_query, {"group_id": group_id, "year": selected_year}).mappings()
            plan_data = {row["month"]: row["plan"] for row in result}
        
        # Рассчитываем общую сумму "исправлено" за все месяцы
        total_ispravleno_all_months = sum(row.get("исправлено", 0) or 0 for row in fact_data_list)
        
        # Собираем данные по месяцам
        cumulative_fact = 0
        cumulative_new = 0
        cumulative_tfoms = 0
        cumulative_oplacheno = 0
        cumulative_ispravleno = 0
        cumulative_otkazano = 0
        cumulative_otmeneno = 0
        cumulative_plan_12 = 0  # Сумма планов за отображаемые месяцы (от 1 до current_month)
        incoming_balance = 0
        
        # Проходим по всем месяцам от 1 до current_month для расчета остатка
        for m in range(1, current_month + 1):
            month_data = fact_dict.get(m, {})
            
            # Рассчитываем Факт в зависимости от режима и отчетного месяца
            if payment_type == 'paid':
                # Режим "Оплаченные" - только оплаченные (status = '3')
                month_fact = month_data.get("оплачено", 0) or 0
            elif payment_type == 'presented_2_3':
                # Режим "Предъявленные 2,3" - статусы 2 и 3 (только для отчетного месяца)
                if m == current_month:
                    # Для отчетного месяца: статусы 2 (в_тфомс) и 3 (оплачено)
                    month_fact = (month_data.get("в_тфомс", 0) or 0) + (month_data.get("оплачено", 0) or 0)
                else:
                    # Для других месяцев: только оплаченные (статус 3)
                    month_fact = month_data.get("оплачено", 0) or 0
            else:
                # Режим "Предъявленные" - текущая логика
                if m < current_month:
                    # Для месяцев < отчетного: только оплаченные (статус 3)
                    month_fact = month_data.get("оплачено", 0) or 0
                elif m == current_month:
                    # Для отчетного месяца: новые+в_тфомс+оплачено+исправлено
                    month_fact = (
                        (month_data.get("новые", 0) or 0) +
                        (month_data.get("в_тфомс", 0) or 0) +
                        (month_data.get("оплачено", 0) or 0) +
                        total_ispravleno_all_months
                    )
                else:
                    month_fact = 0
            
            # Рассчитываем план на месяц
            month_plan_12 = plan_data.get(m, 0) or 0
            month_plan = month_plan_12 + incoming_balance
            
            # Накапливаем сумму планов за отображаемые месяцы
            cumulative_plan_12 += month_plan_12
            
            # Остаток
            month_remainder = month_plan - month_fact
            incoming_balance = month_remainder
            
            # Накапливаем суммы
            cumulative_fact += month_fact
            cumulative_new += (month_data.get("новые", 0) or 0)
            cumulative_tfoms += (month_data.get("в_тфомс", 0) or 0)
            cumulative_oplacheno += (month_data.get("оплачено", 0) or 0)
            cumulative_ispravleno += (month_data.get("исправлено", 0) or 0)
            cumulative_otkazano += (month_data.get("отказано", 0) or 0)
            cumulative_otmeneno += (month_data.get("отменено", 0) or 0)
        
        # Формируем строку результата
        percent = round(cumulative_fact / cumulative_plan_12 * 100, 1) if cumulative_plan_12 > 0 else 0
        
        results.append({
            "Группа показателей": group_name,
            "План 1/12": cumulative_plan_12,
            "Факт": cumulative_fact,
            "Остаток": incoming_balance,
            "%": percent,
            "новые": cumulative_new,
            "в_тфомс": cumulative_tfoms,
            "оплачено": cumulative_oplacheno,
            "исправлено": cumulative_ispravleno,
            "отказано": cumulative_otkazano,
            "отменено": cumulative_otmeneno,
        })
    
    return pd.DataFrame(results)


# ========== Функции для вкладки "Выбранные индикаторы" ==========

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


def get_plan_by_months_for_group(group_id, selected_year, months_list):
    """
    Получает план для группы по месяцам (помесячно).
    Возвращает словарь: {month: (quantity, amount)}
    """
    if not months_list:
        return {}
    
    months_str = ', '.join(map(str, months_list))
    query = text(f"""
        SELECT 
            mp.month,
            COALESCE(SUM(mp.quantity), 0) AS plan_quantity,
            COALESCE(SUM(mp.amount), 0) AS plan_amount
        FROM plan_monthlyplan AS mp
        INNER JOIN plan_annualplan AS ap ON mp.annual_plan_id = ap.id
        WHERE ap.group_id = :group_id 
        AND ap.year = :year
        AND mp.month IN ({months_str})
        GROUP BY mp.month
        ORDER BY mp.month
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"group_id": group_id, "year": selected_year}).mappings()
        plan_by_months = {}
        for row in result:
            plan_by_months[row["month"]] = (row["plan_quantity"] or 0, float(row["plan_amount"] or 0.0))
        return plan_by_months


def sql_query_indicators(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
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
                   {plan_quantity} AS "План 1/12 (количество)",
                   ROUND({plan_amount}::numeric, 2) AS "План 1/12 (сумма)",
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
        final_query = f"{base}\nSELECT 'no_data' AS type, 0 AS \"План 1/12 (количество)\", 0.00 AS \"План 1/12 (сумма)\", 0 AS \"К-во\", 0.00 AS \"Сумма\", 'Нет данных' AS \"Условия фильтра\" FROM oms WHERE 1=0\nLIMIT 10000"

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


def sql_query_plans(selected_year):
    """
    Возвращает SQL-запрос для получения планов по объемам и финансам.
    Принимает год (число) и возвращает строку SQL-запроса.
    """
    return f"""
    WITH RECURSIVE group_hierarchy AS (
        SELECT
            g.id,
            g.name,
            g.parent_id,
            g.name::text AS full_path
        FROM plan_groupindicators g
        WHERE g.parent_id IS NULL
        
        UNION ALL
        
        SELECT
            g.id,
            g.name,
            g.parent_id,
            gh.full_path || ' \\ ' || g.name AS full_path
        FROM plan_groupindicators g
        INNER JOIN group_hierarchy gh ON g.parent_id = gh.id
    ),
    base_data AS (
        SELECT
            gh.full_path AS name,
            mp.month,
            mp.quantity,
            mp.amount
        FROM plan_annualplan ap
        JOIN plan_monthlyplan mp ON mp.annual_plan_id = ap.id
        JOIN plan_groupindicators g ON g.id = ap.group_id
        JOIN group_hierarchy gh ON gh.id = ap.group_id
        WHERE ap.year = {selected_year}
    )
    SELECT
        name || ' - Объемы' AS "Показатель",
        (SUM(CASE WHEN month = 1 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 2 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 3 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 4 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 5 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 6 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 7 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 8 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 9 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 10 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 11 THEN quantity ELSE 0 END) +
         SUM(CASE WHEN month = 12 THEN quantity ELSE 0 END))::INTEGER AS "Итого",
        SUM(CASE WHEN month = 1 THEN quantity ELSE 0 END)::INTEGER AS "1",
        SUM(CASE WHEN month = 2 THEN quantity ELSE 0 END)::INTEGER AS "2",
        SUM(CASE WHEN month = 3 THEN quantity ELSE 0 END)::INTEGER AS "3",
        SUM(CASE WHEN month = 4 THEN quantity ELSE 0 END)::INTEGER AS "4",
        SUM(CASE WHEN month = 5 THEN quantity ELSE 0 END)::INTEGER AS "5",
        SUM(CASE WHEN month = 6 THEN quantity ELSE 0 END)::INTEGER AS "6",
        SUM(CASE WHEN month = 7 THEN quantity ELSE 0 END)::INTEGER AS "7",
        SUM(CASE WHEN month = 8 THEN quantity ELSE 0 END)::INTEGER AS "8",
        SUM(CASE WHEN month = 9 THEN quantity ELSE 0 END)::INTEGER AS "9",
        SUM(CASE WHEN month = 10 THEN quantity ELSE 0 END)::INTEGER AS "10",
        SUM(CASE WHEN month = 11 THEN quantity ELSE 0 END)::INTEGER AS "11",
        SUM(CASE WHEN month = 12 THEN quantity ELSE 0 END)::INTEGER AS "12"
    FROM base_data
    GROUP BY name
    
    UNION ALL
    
    SELECT
        name || ' - Финансы' AS "Показатель",
        (SUM(CASE WHEN month = 1 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 2 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 3 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 4 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 5 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 6 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 7 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 8 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 9 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 10 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 11 THEN amount ELSE 0 END) +
         SUM(CASE WHEN month = 12 THEN amount ELSE 0 END))::NUMERIC(15,2) AS "Итого",
        SUM(CASE WHEN month = 1 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "1",
        SUM(CASE WHEN month = 2 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "2",
        SUM(CASE WHEN month = 3 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "3",
        SUM(CASE WHEN month = 4 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "4",
        SUM(CASE WHEN month = 5 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "5",
        SUM(CASE WHEN month = 6 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "6",
        SUM(CASE WHEN month = 7 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "7",
        SUM(CASE WHEN month = 8 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "8",
        SUM(CASE WHEN month = 9 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "9",
        SUM(CASE WHEN month = 10 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "10",
        SUM(CASE WHEN month = 11 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "11",
        SUM(CASE WHEN month = 12 THEN amount ELSE 0 END)::NUMERIC(15,2) AS "12"
    FROM base_data
    GROUP BY name
    
    ORDER BY "Показатель"
    """


def clear_cache():
    """Очищает кэш для обновления условий"""
    # Кэширование убрано из get_dynamic_conditions, поэтому функция всегда возвращает актуальные данные
    # Оставляем функцию для обратной совместимости на случай, если в будущем понадобится кэширование
    pass