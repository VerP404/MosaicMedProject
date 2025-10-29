import pandas as pd

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
    Возвращает полную иерархию групп через обратный слэш (\).
    """
    from sqlalchemy import text
    
    query = text("""
    WITH RECURSIVE group_paths AS (
        -- Базовый случай: группы с show_in_cumulative_report = true
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
        
        -- Рекурсивный случай: поднимаемся по иерархии вверх к родителю
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


def get_cumulative_report_for_all_groups(selected_year, mode='volumes', unique_flag=False):
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
    current_month = default_month
    
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
            
            # Рассчитываем Факт по текущему дню (логика аналогична основной странице)
            if m < current_month - 1:
                month_fact = month_data.get("оплачено", 0) or 0
            elif m == current_month - 1:
                if current_day <= 10:
                    month_fact = (
                        (month_data.get("новые", 0) or 0) +
                        (month_data.get("в_тфомс", 0) or 0) +
                        (month_data.get("оплачено", 0) or 0) +
                        total_ispravleno_all_months
                    )
                else:
                    month_fact = month_data.get("оплачено", 0) or 0
            elif m == current_month:
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