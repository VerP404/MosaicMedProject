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


def sql_query_adults_appointments_not_passed(selected_year: int, visit_start_date: str, visit_end_date: str, include_departments: list[str] | None = None) -> str:
    """
    Пациенты 18+ по состоянию на выбранный год, которые записаны на прием (журнал обращений)
    в интервале дат, но НЕ имеют в load_data_oms_data целей 'ДВ4' или 'ОПВ' в указанном отчетном году.

    :param selected_year: Год отчета (int)
    :param visit_start_date: Дата начала (YYYY-MM-DD)
    :param visit_end_date: Дата окончания (YYYY-MM-DD)
    :param include_departments: Если задано — только записи из этих подразделений
    """
    # Фильтр по выбранным подразделениям
    include_clause = ""
    if include_departments:
        safe_vals = [str(v).replace("'", "''") for v in include_departments if isinstance(v, str) and v.strip()]
        if safe_vals:
            include_clause = " AND ap.department IN (" + ", ".join([f"'{v}'" for v in safe_vals]) + ")"

    return f"""
WITH appointments AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        phone,
        employee_last_name,
        employee_first_name,
        employee_middle_name,
        position,
        department,
        schedule_type,
        record_source,
        no_show,
        epmz,
        COALESCE(
          /* ISO: YYYY-MM-DD[...]; берём дату */
          CASE WHEN acceptance_date LIKE '____-__-__%'
               THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
          /* RU: DD.MM.YYYY HH:MI; обрезаем до минут */
          CASE WHEN acceptance_date LIKE '__.__.____%'
               THEN to_timestamp(SUBSTRING(acceptance_date FROM 1 FOR 16), 'DD.MM.YYYY HH24:MI') END,
          /* ISO в record_date */
          CASE WHEN record_date LIKE '____-__-__%'
               THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
          /* RU в record_date */
          CASE WHEN record_date LIKE '__.__.____%'
               THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'DD.MM.YYYY')::timestamp END
        ) AS appointment_ts,
        COALESCE(
          CASE WHEN acceptance_date LIKE '____-__-__T__:%' THEN SUBSTRING(acceptance_date FROM 12 FOR 5) END,
          CASE WHEN acceptance_date LIKE '____-__-__ __:__%' THEN SUBSTRING(acceptance_date FROM 12 FOR 5) END,
          CASE WHEN acceptance_date LIKE '__.__.____ __:__%' THEN SUBSTRING(acceptance_date FROM 12 FOR 5) END,
          CASE WHEN record_date    LIKE '____-__-__T__:%' THEN SUBSTRING(record_date FROM 12 FOR 5) END,
          CASE WHEN record_date    LIKE '____-__-__ __:__%' THEN SUBSTRING(record_date FROM 12 FOR 5) END,
          CASE WHEN record_date    LIKE '__.__.____ __:__%' THEN SUBSTRING(record_date FROM 12 FOR 5) END
        ) AS appointment_time_txt
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
),
apps AS (
    SELECT *
    FROM appointments
    WHERE appointment_ts::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
),
adults AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        fio,
        dr,
        lpuuch,
        COALESCE(
          CASE WHEN dr ~ '^[0-9]{{2}}[.][0-9]{{2}}[.][0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
          CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
        ) AS dr_date,
        DATE_PART('year', AGE(make_date({selected_year}, 12, 31), COALESCE(
          CASE WHEN dr ~ '^[0-9]{{2}}[.][0-9]{{2}}[.][0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
          CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
        )))::INT AS age_years
    FROM data_loader_iszlpeople
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
)
SELECT
    a.fio AS "ФИО",
    a.dr AS "ДР",
    a.enp_norm AS "ЕНП",
    a.lpuuch AS "Участок",
    a.age_years AS "Возраст",
    CASE WHEN a.age_years IN (19,20,22,23,25,26,28,29,31,32,34,35,37,38) THEN 'ОПВ' ELSE 'ДВ4' END AS "Тип",
    ap.phone AS "Телефон",
    to_char(ap.appointment_ts::date, 'YYYY-MM-DD') AS "Дата приема",
    COALESCE(ap.appointment_time_txt, '') AS "Время приема",
    (ap.employee_last_name || ' ' || ap.employee_first_name || ' ' || ap.employee_middle_name) AS "Сотрудник",
    ap.position AS "Должность",
    ap.department AS "Подразделение",
    ap.record_source AS "Источник",
    ap.schedule_type AS "Тип расписания"
FROM adults a
JOIN apps ap ON a.enp_norm = ap.enp_norm
WHERE a.age_years >= 18
  AND NOT EXISTS (
        SELECT 1
        FROM load_data_oms_data o
        WHERE regexp_replace(o.enp, '\\D', '', 'g') = a.enp_norm
          AND o.goal IN ('ДВ4', 'ОПВ')
          AND o.report_year = {selected_year}
    )
{"" if not include_clause else include_clause}
ORDER BY ap.appointment_ts DESC, a.lpuuch, a.fio
    """


def sql_query_dispensary_organized_collectives(talon_numbers: list[str], age_group: str = None) -> str:
    """
    Сводная таблица по возрастам и типам диспансеризации для организованных коллективов.
    
    :param talon_numbers: Список номеров талонов для фильтрации
    :param age_group: '40-65', 'прочие' или None для общего итога
    """
    if not talon_numbers:
        return "SELECT 'Нет данных' AS \"Тип\", 0 AS \"1\", 0 AS \"2\", 0 AS \"3\", 0 AS \"4\", 0 AS \"5\", 0 AS \"6\", 0 AS \"7\", 0 AS \"8\", 0 AS \"12\", 0 AS \"13\", 0 AS \"0\" WHERE 1=0"
    
    # Экранируем номера талонов для SQL и приводим к строке для сравнения
    safe_talons = [f"'{str(t).replace(chr(39), chr(39)+chr(39))}'" for t in talon_numbers if t and str(t).strip()]
    if not safe_talons:
        return "SELECT 'Нет данных' AS \"Тип\", 0 AS \"1\", 0 AS \"2\", 0 AS \"3\", 0 AS \"4\", 0 AS \"5\", 0 AS \"6\", 0 AS \"7\", 0 AS \"8\", 0 AS \"12\", 0 AS \"13\", 0 AS \"0\" WHERE 1=0"
    
    talons_placeholder = ",".join(safe_talons)
    
    # Определяем фильтр по возрасту в WHERE после вычисления возраста
    age_condition = ""
    if age_group == '40-65':
        age_condition = "AND age >= 40 AND age <= 65"
    elif age_group == 'прочие':
        age_condition = "AND (age < 40 OR age > 65)"
    # Для общего итога (None) age_condition остается пустым - берём все записи
    
    return f"""
WITH filtered_data AS (
    SELECT 
        goal,
        status,
        talon,
        CASE 
            WHEN treatment_end IS NOT NULL AND birth_date IS NOT NULL THEN
                CASE
                    WHEN substring(treatment_end::text FROM '\\d{{4}}$') IS NOT NULL 
                         AND substring(birth_date::text FROM '\\d{{4}}$') IS NOT NULL THEN
                        CAST(substring(treatment_end::text FROM '\\d{{4}}$') AS INTEGER) - 
                        CAST(substring(birth_date::text FROM '\\d{{4}}$') AS INTEGER)
                    WHEN substring(treatment_end::text FROM '^\\d{{4}}') IS NOT NULL 
                         AND substring(birth_date::text FROM '^\\d{{4}}') IS NOT NULL THEN
                        CAST(substring(treatment_end::text FROM '^\\d{{4}}') AS INTEGER) - 
                        CAST(substring(birth_date::text FROM '^\\d{{4}}') AS INTEGER)
                    WHEN substring(treatment_end::text FROM '\\d{{4}}') IS NOT NULL 
                         AND substring(birth_date::text FROM '\\d{{4}}') IS NOT NULL THEN
                        CAST(substring(treatment_end::text FROM '\\d{{4}}') AS INTEGER) - 
                        CAST(substring(birth_date::text FROM '\\d{{4}}') AS INTEGER)
                    ELSE NULL
                END
            ELSE NULL
        END AS age
    FROM load_data_oms_data
    WHERE COALESCE(talon::text, '') IN ({talons_placeholder})
      AND goal IN ('ДВ4', 'ОПВ', 'УД1', 'ДР1')
      AND treatment_end IS NOT NULL
      AND birth_date IS NOT NULL
),
data_with_age AS (
    SELECT 
        goal,
        status,
        age,
        talon
    FROM filtered_data
    WHERE age IS NOT NULL
      {age_condition}
),
grouped_data AS (
    SELECT 
        goal AS "Тип",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '1'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '2'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '3'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '4'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '5'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '6'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '7'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '8'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '12'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '13'), 0) +
        COALESCE(COUNT(*) FILTER (WHERE status::text = '0'), 0) AS "Всего",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '1'), 0) AS "1",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '2'), 0) AS "2",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '3'), 0) AS "3",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '4'), 0) AS "4",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '5'), 0) AS "5",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '6'), 0) AS "6",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '7'), 0) AS "7",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '8'), 0) AS "8",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '12'), 0) AS "12",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '13'), 0) AS "13",
        COALESCE(COUNT(*) FILTER (WHERE status::text = '0'), 0) AS "0"
    FROM data_with_age
    WHERE goal IS NOT NULL AND goal != '-'
    GROUP BY goal
),
totals AS (
    SELECT 
        'Итого' AS "Тип",
        COALESCE(SUM("Всего"), 0) AS "Всего",
        COALESCE(SUM("1"), 0) AS "1",
        COALESCE(SUM("2"), 0) AS "2",
        COALESCE(SUM("3"), 0) AS "3",
        COALESCE(SUM("4"), 0) AS "4",
        COALESCE(SUM("5"), 0) AS "5",
        COALESCE(SUM("6"), 0) AS "6",
        COALESCE(SUM("7"), 0) AS "7",
        COALESCE(SUM("8"), 0) AS "8",
        COALESCE(SUM("12"), 0) AS "12",
        COALESCE(SUM("13"), 0) AS "13",
        COALESCE(SUM("0"), 0) AS "0"
    FROM grouped_data
),
result AS (
    SELECT * FROM grouped_data
    UNION ALL
    SELECT * FROM totals
)
SELECT 
    "Тип",
    "Всего",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "12",
    "13",
    "0"
FROM result
ORDER BY 
    CASE WHEN "Тип" = 'Итого' THEN 999 ELSE 1 END,
    "Тип"
    """


DISPENSARY_GOALS = ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2')
GOAL_541 = '541'
SOURCE_PREVIEW_LIMIT = 500

_DISPENSARY_GOAL_ANY_EXPR = (
    'gp."ДВ4" IS NOT NULL OR gp."ДВ2" IS NOT NULL OR gp."ОПВ" IS NOT NULL '
    'OR gp."УД1" IS NOT NULL OR gp."УД2" IS NOT NULL '
    'OR gp."ДР1" IS NOT NULL OR gp."ДР2" IS NOT NULL'
)

_APPOINTMENT_TS_EXPR = """
        COALESCE(
          CASE WHEN acceptance_date LIKE '____-__-__%'
               THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
          CASE WHEN acceptance_date LIKE '__.__.____%'
               THEN to_timestamp(SUBSTRING(acceptance_date FROM 1 FOR 16), 'DD.MM.YYYY HH24:MI') END,
          CASE WHEN record_date LIKE '____-__-__%'
               THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
          CASE WHEN record_date LIKE '__.__.____%'
               THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'DD.MM.YYYY')::timestamp END
        )
"""

_APPOINTMENT_TIME_EXPR = """
        COALESCE(
          CASE WHEN acceptance_date LIKE '____-__-__T__:%' THEN SUBSTRING(acceptance_date FROM 12 FOR 5) END,
          CASE WHEN acceptance_date LIKE '____-__-__ __:__%' THEN SUBSTRING(acceptance_date FROM 12 FOR 5) END,
          CASE WHEN acceptance_date LIKE '__.__.____ __:__%' THEN SUBSTRING(acceptance_date FROM 12 FOR 5) END,
          CASE WHEN record_date    LIKE '____-__-__T__:%' THEN SUBSTRING(record_date FROM 12 FOR 5) END,
          CASE WHEN record_date    LIKE '____-__-__ __:__%' THEN SUBSTRING(record_date FROM 12 FOR 5) END,
          CASE WHEN record_date    LIKE '__.__.____ __:__%' THEN SUBSTRING(record_date FROM 12 FOR 5) END
        )
"""

_TREATMENT_END_PARSED_EXPR = """
        COALESCE(
          CASE WHEN treatment_end::text ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
               THEN to_date(treatment_end::text, 'YYYY-MM-DD') END,
          CASE WHEN treatment_end::text ~ '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{4}$'
               THEN to_date(treatment_end::text, 'DD.MM.YYYY') END,
          CASE WHEN treatment_end::text ~ '^[0-9]{8}$'
               THEN to_date(treatment_end::text, 'YYYYMMDD') END
        )
"""

_SERVICE_DATE_PARSED_EXPR = """
        COALESCE(
          CASE WHEN service_date ~ '^[0-9]{2}-[0-9]{2}-[0-9]{4}'
               THEN to_date(service_date, 'DD-MM-YYYY') END,
          CASE WHEN service_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
               THEN to_date(service_date, 'YYYY-MM-DD') END,
          CASE WHEN service_date ~ '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{4}$'
               THEN to_date(service_date, 'DD.MM.YYYY') END
        )
"""


def _sql_escape(value: str) -> str:
    return str(value).replace("'", "''")


def _department_filter_clause(include_departments: list[str] | None, alias: str = "s") -> str:
    if not include_departments:
        return ""
    safe_vals = [_sql_escape(v) for v in include_departments if isinstance(v, str) and v.strip()]
    if not safe_vals:
        return ""
    joined = ", ".join([f"'{v}'" for v in safe_vals])
    return f" AND {alias}.department IN ({joined})"


def _procedure_filter_clause(procedures: list[str] | None, alias: str = "s") -> str:
    if not procedures:
        return ""
    safe_vals = [_sql_escape(v) for v in procedures if isinstance(v, str) and v.strip()]
    if not safe_vals:
        return ""
    joined = ", ".join([f"'{v}'" for v in safe_vals])
    return f" AND {alias}.procedure IN ({joined})"


def _service_filter_clause(services: list[str] | None) -> str:
    if not services:
        return ""
    safe_vals = [_sql_escape(v) for v in services if isinstance(v, str) and v.strip()]
    if not safe_vals:
        return ""
    joined = ", ".join([f"'{v}'" for v in safe_vals])
    return f" AND (service_name IN ({joined}) OR service_nomenclature IN ({joined}))"


def _goal_pivot_columns() -> str:
    parts = []
    for goal in DISPENSARY_GOALS:
        parts.append(
            f"MAX(CASE WHEN og.goal = '{goal}' "
            f"THEN to_char(og.goal_date, 'DD.MM.YYYY') END) AS \"{goal}\""
        )
    return ",\n    ".join(parts)


def sql_query_procedure_appointments_list(
    selected_year: int,
    visit_start_date: str,
    visit_end_date: str,
    procedures: list[str],
    service_keys: list[str],
    include_departments: list[str] | None = None,
) -> str:
    proc_clause = _procedure_filter_clause(procedures, "s")
    svc_clause = _service_filter_clause(service_keys)
    dept_clause = _department_filter_clause(include_departments, "s")
    goal_pivot = _goal_pivot_columns()

    return f"""
WITH scheduled AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        TRIM(patient_last_name || ' ' || patient_first_name || ' ' || patient_middle_name) AS patient_fio,
        birth_date,
        phone,
        procedure,
        department,
        no_show,
        schedule_type,
        record_source,
        {_APPOINTMENT_TS_EXPR} AS appointment_ts,
        {_APPOINTMENT_TIME_EXPR} AS appointment_time_txt
    FROM load_data_journal_appeals s
    WHERE COALESCE(NULLIF(s.enp, '-'), '') <> ''
      {proc_clause}
      {dept_clause}
),
scheduled_filtered AS (
    SELECT *
    FROM scheduled
    WHERE appointment_ts::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
),
service_fact AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        MAX({_SERVICE_DATE_PARSED_EXPR}) AS service_date
    FROM load_data_detailed_medical_examination
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND service_status = 'Да'
      {svc_clause}
    GROUP BY 1
),
oms_goals AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        goal,
        MAX({_TREATMENT_END_PARSED_EXPR}) AS goal_date
    FROM load_data_oms_data
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND goal IN ({", ".join([f"'{g}'" for g in DISPENSARY_GOALS])})
      AND report_year = {int(selected_year)}
    GROUP BY 1, 2
),
goal_pivot AS (
    SELECT
        og.enp_norm,
        {_goal_pivot_columns()}
    FROM oms_goals og
    GROUP BY og.enp_norm
),
goal_541_on_date AS (
    SELECT
        regexp_replace(o.enp, '\\D', '', 'g') AS enp_norm,
        {_TREATMENT_END_PARSED_EXPR} AS goal_date
    FROM load_data_oms_data o
    WHERE COALESCE(NULLIF(o.enp, '-'), '') <> ''
      AND o.goal = '{GOAL_541}'
      AND o.report_year = {int(selected_year)}
      AND {_TREATMENT_END_PARSED_EXPR} IS NOT NULL
    GROUP BY 1, 2
)
SELECT
    sf.patient_fio AS "ФИО",
    sf.birth_date AS "ДР",
    sf.enp_norm AS "ЕНП",
    sf.phone AS "Телефон",
    sf.procedure AS "Процедура",
    to_char(sf.appointment_ts::date, 'YYYY-MM-DD') AS "Дата приема",
    COALESCE(sf.appointment_time_txt, '') AS "Время приема",
    sf.department AS "Подразделение",
    sf.no_show AS "Не явился",
    sf.schedule_type AS "Тип расписания",
    sf.record_source AS "Источник",
    to_char(svc.service_date, 'DD.MM.YYYY') AS "Прошёл услугу",
    to_char(g541.goal_date, 'DD.MM.YYYY') AS "541",
    CASE
        WHEN TRIM(BOTH ', ' FROM CONCAT_WS(', ',
            CASE WHEN svc.service_date IS NOT NULL THEN 'Услуга' END,
            CASE WHEN {_DISPENSARY_GOAL_ANY_EXPR} THEN 'Диспансеризация' END,
            CASE WHEN g541.goal_date IS NOT NULL THEN '541' END
        )) = '' THEN 'Без результата'
        ELSE TRIM(BOTH ', ' FROM CONCAT_WS(', ',
            CASE WHEN svc.service_date IS NOT NULL THEN 'Услуга' END,
            CASE WHEN {_DISPENSARY_GOAL_ANY_EXPR} THEN 'Диспансеризация' END,
            CASE WHEN g541.goal_date IS NOT NULL THEN '541' END
        ))
    END AS "Результат",
    gp."ДВ4",
    gp."ДВ2",
    gp."ОПВ",
    gp."УД1",
    gp."УД2",
    gp."ДР1",
    gp."ДР2"
FROM scheduled_filtered sf
LEFT JOIN service_fact svc ON sf.enp_norm = svc.enp_norm
LEFT JOIN goal_pivot gp ON sf.enp_norm = gp.enp_norm
LEFT JOIN goal_541_on_date g541
    ON sf.enp_norm = g541.enp_norm
   AND sf.appointment_ts::date = g541.goal_date
ORDER BY sf.appointment_ts DESC, sf.patient_fio
"""


def sql_query_procedure_appointments_analytics(
    selected_year: int,
    visit_start_date: str,
    visit_end_date: str,
    procedures: list[str],
    service_keys: list[str],
    include_departments: list[str] | None = None,
) -> str:
    proc_clause = _procedure_filter_clause(procedures, "s")
    svc_clause = _service_filter_clause(service_keys)
    dept_clause = _department_filter_clause(include_departments, "s")

    disp_goals_sql = ", ".join([f"'{g}'" for g in DISPENSARY_GOALS])

    return f"""
WITH scheduled AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        {_APPOINTMENT_TS_EXPR} AS appointment_ts
    FROM load_data_journal_appeals s
    WHERE COALESCE(NULLIF(s.enp, '-'), '') <> ''
      {proc_clause}
      {dept_clause}
),
scheduled_filtered AS (
    SELECT enp_norm, appointment_ts::date AS appt_date
    FROM scheduled
    WHERE appointment_ts::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
),
scheduled_visits AS (
    SELECT DISTINCT enp_norm, appt_date FROM scheduled_filtered
),
service_fact AS (
    SELECT DISTINCT regexp_replace(enp, '\\D', '', 'g') AS enp_norm
    FROM load_data_detailed_medical_examination
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND service_status = 'Да'
      {svc_clause}
),
oms_disp AS (
    SELECT DISTINCT regexp_replace(enp, '\\D', '', 'g') AS enp_norm
    FROM load_data_oms_data
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND goal IN ({disp_goals_sql})
      AND report_year = {int(selected_year)}
),
oms_541 AS (
    SELECT
        regexp_replace(o.enp, '\\D', '', 'g') AS enp_norm,
        {_TREATMENT_END_PARSED_EXPR} AS goal_date
    FROM load_data_oms_data o
    WHERE COALESCE(NULLIF(o.enp, '-'), '') <> ''
      AND o.goal = '{GOAL_541}'
      AND o.report_year = {int(selected_year)}
      AND {_TREATMENT_END_PARSED_EXPR} IS NOT NULL
    GROUP BY 1, 2
),
visit_flags AS (
    SELECT
        sv.enp_norm,
        sv.appt_date,
        (svc.enp_norm IS NOT NULL) AS has_service,
        (disp.enp_norm IS NOT NULL) AS has_disp,
        (g541.enp_norm IS NOT NULL) AS has_541
    FROM scheduled_visits sv
    LEFT JOIN service_fact svc ON sv.enp_norm = svc.enp_norm
    LEFT JOIN oms_disp disp ON sv.enp_norm = disp.enp_norm
    LEFT JOIN oms_541 g541
        ON sv.enp_norm = g541.enp_norm
       AND sv.appt_date = g541.goal_date
),
base AS (
    SELECT
        (SELECT COUNT(*) FROM scheduled_filtered) AS scheduled_rows,
        (SELECT COUNT(DISTINCT enp_norm) FROM scheduled_filtered) AS scheduled_unique_enp,
        (SELECT COUNT(*) FROM visit_flags WHERE has_service) AS via_service,
        (SELECT COUNT(*) FROM visit_flags WHERE has_disp) AS via_disp,
        (SELECT COUNT(*) FROM visit_flags WHERE has_541) AS via_541,
        (SELECT COUNT(*) FROM visit_flags WHERE has_service OR has_disp OR has_541) AS with_any_result,
        (SELECT COUNT(*) FROM visit_flags WHERE NOT (has_service OR has_disp OR has_541)) AS without_result,
        (SELECT COUNT(*) FROM visit_flags WHERE has_service AND has_disp) AS service_and_disp,
        (SELECT COUNT(*) FROM visit_flags WHERE has_service AND has_541) AS service_and_541,
        (SELECT COUNT(*) FROM visit_flags WHERE has_disp AND has_541) AS disp_and_541,
        (SELECT COUNT(*) FROM visit_flags WHERE has_service AND has_disp AND has_541) AS all_three
)
SELECT sort_order, "Группа", "Показатель", "Значение", "Пояснение"
FROM (
    SELECT 10 AS sort_order, 'Объём' AS "Группа", 'Записей на приём' AS "Показатель",
           scheduled_rows AS "Значение", 'Строк журнала обращений за период' AS "Пояснение" FROM base
    UNION ALL SELECT 20, 'Объём', 'Уникальных пациентов', scheduled_unique_enp,
           'Уникальных ЕНП среди записей' FROM base
    UNION ALL SELECT 100, 'Результат', 'Есть результат (любой канал)', with_any_result,
           'Услуга, диспансеризация или 541 в дату приёма' FROM base
    UNION ALL SELECT 110, 'Результат', '  → Услуга (детализация)', via_service,
           'Прошёл хотя бы одну выбранную услугу' FROM base
    UNION ALL SELECT 120, 'Результат', '  → Диспансеризация (цель ОМС)', via_disp,
           'Есть цель ДВ/ОПВ/УД/ДР за год' FROM base
    UNION ALL SELECT 130, 'Результат', '  → 541 в дату приёма', via_541,
           'Окончание лечения по 541 совпало с датой записи' FROM base
    UNION ALL SELECT 200, 'Проблема', 'Без результата', without_result,
           'Ни услуги, ни диспансеризации, ни 541 в дату приёма' FROM base
    UNION ALL SELECT 300, 'Пересечения', 'Услуга + диспансеризация', service_and_disp,
           'Оба канала у одной записи' FROM base
    UNION ALL SELECT 310, 'Пересечения', 'Услуга + 541', service_and_541,
           'Оба канала у одной записи' FROM base
    UNION ALL SELECT 320, 'Пересечения', 'Диспансеризация + 541', disp_and_541,
           'Оба канала у одной записи' FROM base
    UNION ALL SELECT 330, 'Пересечения', 'Все три канала', all_three,
           'Услуга, диспансеризация и 541 одновременно' FROM base
) t
ORDER BY sort_order
"""


def sql_query_procedure_appointments_goal_breakdown(
    selected_year: int,
    visit_start_date: str,
    visit_end_date: str,
    procedures: list[str],
    include_departments: list[str] | None = None,
) -> str:
    proc_clause = _procedure_filter_clause(procedures, "s")
    dept_clause = _department_filter_clause(include_departments, "s")

    return f"""
WITH scheduled_visits AS (
    SELECT DISTINCT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        ({_APPOINTMENT_TS_EXPR})::date AS appt_date
    FROM load_data_journal_appeals s
    WHERE COALESCE(NULLIF(s.enp, '-'), '') <> ''
      {proc_clause}
      {dept_clause}
      AND ({_APPOINTMENT_TS_EXPR})::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
),
oms_disp_goals AS (
    SELECT DISTINCT
        regexp_replace(o.enp, '\\D', '', 'g') AS enp_norm,
        o.goal
    FROM load_data_oms_data o
    INNER JOIN scheduled_visits sv ON regexp_replace(o.enp, '\\D', '', 'g') = sv.enp_norm
    WHERE o.goal IN ({", ".join([f"'{g}'" for g in DISPENSARY_GOALS])})
      AND o.report_year = {int(selected_year)}
),
oms_541_matched AS (
    SELECT DISTINCT sv.enp_norm, sv.appt_date
    FROM scheduled_visits sv
    INNER JOIN load_data_oms_data o
        ON regexp_replace(o.enp, '\\D', '', 'g') = sv.enp_norm
    WHERE o.goal = '{GOAL_541}'
      AND o.report_year = {int(selected_year)}
      AND {_TREATMENT_END_PARSED_EXPR} = sv.appt_date
)
SELECT goal AS "Цель", COUNT(DISTINCT enp_norm) AS "Количество", 'Диспансеризация' AS "Тип"
FROM oms_disp_goals
GROUP BY goal
UNION ALL
SELECT '{GOAL_541}', COUNT(*), '541 в дату приёма' FROM oms_541_matched
ORDER BY "Тип", "Цель"
"""


def _scheduled_in_period_cte(
    visit_start_date: str,
    visit_end_date: str,
    proc_clause: str,
    dept_clause: str,
) -> str:
    return f"""
scheduled AS (
    SELECT
        regexp_replace(s.enp, '\\D', '', 'g') AS enp_norm,
        s.enp,
        TRIM(s.patient_last_name || ' ' || s.patient_first_name || ' ' || s.patient_middle_name) AS patient_fio,
        s.procedure,
        s.acceptance_date,
        s.record_date,
        s.department,
        s.no_show,
        {_APPOINTMENT_TS_EXPR} AS appointment_ts
    FROM load_data_journal_appeals s
    WHERE COALESCE(NULLIF(s.enp, '-'), '') <> ''
      {proc_clause}
      {dept_clause}
),
scheduled_in_period AS (
    SELECT *
    FROM scheduled
    WHERE appointment_ts::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
)"""


def sql_query_procedure_source_journal(
    visit_start_date: str,
    visit_end_date: str,
    procedures: list[str],
    include_departments: list[str] | None = None,
) -> str:
    proc_clause = _procedure_filter_clause(procedures, "s")
    dept_clause = _department_filter_clause(include_departments, "s")
    cte = _scheduled_in_period_cte(visit_start_date, visit_end_date, proc_clause, dept_clause)
    return f"""
WITH {cte}
SELECT
    patient_fio AS "ФИО",
    enp_norm AS "ЕНП",
    procedure AS "Процедура",
    to_char(appointment_ts::date, 'YYYY-MM-DD') AS "Дата приема",
    acceptance_date AS "Дата приема (сырая)",
    department AS "Подразделение",
    no_show AS "Не явился"
FROM scheduled_in_period
ORDER BY appointment_ts DESC, patient_fio
LIMIT {SOURCE_PREVIEW_LIMIT}
"""


def sql_query_procedure_source_oms(
    selected_year: int,
    visit_start_date: str,
    visit_end_date: str,
    procedures: list[str],
    include_departments: list[str] | None = None,
) -> str:
    proc_clause = _procedure_filter_clause(procedures, "s")
    dept_clause = _department_filter_clause(include_departments, "s")
    cte = _scheduled_in_period_cte(visit_start_date, visit_end_date, proc_clause, dept_clause)
    disp_goals_sql = ", ".join([f"'{g}'" for g in DISPENSARY_GOALS])
    return f"""
WITH {cte},
scheduled_enp AS (
    SELECT DISTINCT enp_norm FROM scheduled_in_period
)
SELECT
    regexp_replace(o.enp, '\\D', '', 'g') AS "ЕНП",
    o.goal AS "Цель",
    o.treatment_end AS "Окончание лечения",
    o.treatment_start AS "Начало лечения",
    o.talon AS "Талон",
    o.status AS "Статус",
    o.patient AS "Пациент"
FROM load_data_oms_data o
INNER JOIN scheduled_enp se ON regexp_replace(o.enp, '\\D', '', 'g') = se.enp_norm
WHERE o.report_year = {int(selected_year)}
  AND (o.goal IN ({disp_goals_sql}) OR o.goal = '{GOAL_541}')
ORDER BY o.enp, o.goal, o.treatment_end
LIMIT {SOURCE_PREVIEW_LIMIT}
"""


def sql_query_procedure_source_detailing(
    visit_start_date: str,
    visit_end_date: str,
    procedures: list[str],
    service_keys: list[str],
    include_departments: list[str] | None = None,
) -> str:
    proc_clause = _procedure_filter_clause(procedures, "s")
    svc_clause = _service_filter_clause(service_keys)
    dept_clause = _department_filter_clause(include_departments, "s")
    cte = _scheduled_in_period_cte(visit_start_date, visit_end_date, proc_clause, dept_clause)
    return f"""
WITH {cte},
scheduled_enp AS (
    SELECT DISTINCT enp_norm FROM scheduled_in_period
)
SELECT
    regexp_replace(d.enp, '\\D', '', 'g') AS "ЕНП",
    d.service_name AS "Услуга",
    d.service_nomenclature AS "Номенклатура",
    d.service_date AS "Дата услуги",
    d.service_status AS "Статус",
    d.talon_number AS "Талон"
FROM load_data_detailed_medical_examination d
INNER JOIN scheduled_enp se ON regexp_replace(d.enp, '\\D', '', 'g') = se.enp_norm
WHERE COALESCE(NULLIF(d.enp, '-'), '') <> ''
  AND d.service_status = 'Да'
  {svc_clause}
ORDER BY d.enp, d.service_date
LIMIT {SOURCE_PREVIEW_LIMIT}
"""


def _attached_disp_filter_clauses(
    gender_value,
    age_from,
    age_to,
    disp_type,
    lpuuch_values,
):
    gender_condition = ""
    if gender_value and gender_value != "all":
        gender_condition = f"AND a.gender = '{gender_value}'"

    age_condition = f"AND a.age_years >= {int(age_from)} AND a.age_years <= {int(age_to)}"

    disp_condition = ""
    if disp_type and disp_type != "all":
        disp_condition = f"AND o.goal = '{disp_type}'"

    lpuuch_condition = ""
    if lpuuch_values:
        safe_lpuuch = [
            f"'{lpu.replace(chr(39), chr(39) + chr(39))}'"
            for lpu in lpuuch_values
            if lpu
        ]
        if safe_lpuuch:
            lpuuch_condition = f"AND a.lpuuch IN ({', '.join(safe_lpuuch)})"

    return gender_condition, age_condition, disp_condition, lpuuch_condition


def _sql_attached_with_status_cte(
    year: int,
    gender_condition: str,
    age_condition: str,
    lpuuch_condition: str,
    disp_condition: str,
) -> str:
    return f"""
attached_patients AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        fio,
        dr,
        CASE
            WHEN LOWER("fio") LIKE '%ович%' THEN 'М'
            WHEN LOWER("fio") LIKE '%евич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%овна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%евна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ична%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%инична%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ья%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%иа%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%йя%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%инич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ус%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ия%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%джонзода%' THEN 'М'
            WHEN LOWER("fio") LIKE '%мохаммед%' THEN 'М'
            WHEN RIGHT(LOWER("fio"), 1) IN ('а', 'я', 'и', 'е', 'о', 'у', 'э', 'ю') THEN 'Ж'
            ELSE 'М'
        END AS gender,
        lpuuch,
        COALESCE(
            CASE WHEN dr ~ '^[0-9]{{2}}[.][0-9]{{2}}[.][0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
            CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
        ) AS dr_date
    FROM data_loader_iszlpeople
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND COALESCE(NULLIF(fio, '-'), '') <> ''
),
adults AS (
    SELECT
        enp_norm,
        fio,
        dr,
        gender,
        lpuuch,
        dr_date,
        DATE_PART('year', AGE(make_date({year}, 12, 31), dr_date))::INT AS age_years
    FROM attached_patients
    WHERE dr_date IS NOT NULL
),
attached_with_status AS (
    SELECT
        a.enp_norm,
        a.fio,
        a.dr,
        a.gender,
        a.lpuuch,
        a.age_years,
        CASE
            WHEN a.age_years IN (19,20,22,23,25,26,28,29,31,32,34,35,37,38) THEN 'ОПВ'
            ELSE 'ДВ4'
        END AS required_disp_type,
        EXISTS (
            SELECT 1
            FROM load_data_oms_data o
            WHERE regexp_replace(o.enp, '\\D', '', 'g') = a.enp_norm
              AND o.goal IN ('ДВ4', 'ОПВ')
              AND o.report_year = {year}
              {disp_condition}
        ) AS passed_disp
    FROM adults a
    WHERE a.age_years >= 18
      {gender_condition}
      {age_condition}
      {lpuuch_condition}
)"""


def sql_query_attached_disp_list(
    year: int,
    pass_status: str,
    gender_value=None,
    age_from: int = 18,
    age_to: int = 120,
    disp_type=None,
    lpuuch_values=None,
) -> str:
    gender_condition, age_condition, disp_condition, lpuuch_condition = _attached_disp_filter_clauses(
        gender_value, age_from, age_to, disp_type, lpuuch_values or []
    )

    pass_filter = ""
    if pass_status == "passed":
        pass_filter = "AND p.passed_disp = TRUE"
    elif pass_status == "not_passed":
        pass_filter = "AND p.passed_disp = FALSE"

    base_cte = _sql_attached_with_status_cte(
        year, gender_condition, age_condition, lpuuch_condition, disp_condition
    )

    return f"""
WITH {base_cte},
patient_phones AS (
    SELECT DISTINCT ON (regexp_replace(enp, '\\D', '', 'g'))
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        phone
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND COALESCE(NULLIF(phone, '-'), '') <> ''
    ORDER BY regexp_replace(enp, '\\D', '', 'g'),
             COALESCE(
                 CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
                      THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD') END,
                 CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}'
                      THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI')::date END,
                 CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$'
                      THEN to_date(acceptance_date, 'DD.MM.YYYY') END,
                 CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
                      THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD') END,
                 CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$'
                      THEN to_date(record_date, 'DD.MM.YYYY') END
             ) DESC NULLS LAST,
             id DESC
)
SELECT
    p.fio AS "ФИО",
    p.dr AS "ДР",
    p.enp_norm AS "ЕНП",
    p.gender AS "Пол",
    p.lpuuch AS "Участок",
    p.age_years AS "Возраст",
    p.required_disp_type AS "Требуемый тип",
    CASE WHEN p.passed_disp THEN 'Прошёл' ELSE 'Не прошёл' END AS "Статус",
    COALESCE(ph.phone, '') AS "Телефон"
FROM attached_with_status p
LEFT JOIN patient_phones ph ON p.enp_norm = ph.enp_norm
WHERE 1=1
  {pass_filter}
ORDER BY p.lpuuch, p.fio
"""


def sql_query_attached_disp_analytics(
    year: int,
    gender_value=None,
    age_from: int = 18,
    age_to: int = 120,
    disp_type=None,
    lpuuch_values=None,
) -> str:
    gender_condition, age_condition, disp_condition, lpuuch_condition = _attached_disp_filter_clauses(
        gender_value, age_from, age_to, disp_type, lpuuch_values or []
    )

    base_cte = _sql_attached_with_status_cte(
        year, gender_condition, age_condition, lpuuch_condition, disp_condition
    )

    return f"""
WITH {base_cte},
by_age AS (
    SELECT
        age_years,
        COUNT(*) AS attached_total,
        COUNT(*) FILTER (WHERE gender = 'М') AS attached_m,
        COUNT(*) FILTER (WHERE gender = 'Ж') AS attached_f,
        COUNT(*) FILTER (WHERE passed_disp) AS passed_total,
        COUNT(*) FILTER (WHERE passed_disp AND gender = 'М') AS passed_m,
        COUNT(*) FILTER (WHERE passed_disp AND gender = 'Ж') AS passed_f,
        COUNT(*) FILTER (WHERE NOT passed_disp) AS not_passed_total,
        COUNT(*) FILTER (WHERE NOT passed_disp AND gender = 'М') AS not_passed_m,
        COUNT(*) FILTER (WHERE NOT passed_disp AND gender = 'Ж') AS not_passed_f
    FROM attached_with_status
    GROUP BY age_years
),
totals AS (
    SELECT
        NULL::INT AS age_years,
        SUM(attached_total) AS attached_total,
        SUM(attached_m) AS attached_m,
        SUM(attached_f) AS attached_f,
        SUM(passed_total) AS passed_total,
        SUM(passed_m) AS passed_m,
        SUM(passed_f) AS passed_f,
        SUM(not_passed_total) AS not_passed_total,
        SUM(not_passed_m) AS not_passed_m,
        SUM(not_passed_f) AS not_passed_f
    FROM by_age
)
SELECT
    COALESCE(age_years::text, 'Итого') AS "Возраст",
    attached_total AS "Прикреплено",
    attached_m AS "Прикр. М",
    attached_f AS "Прикр. Ж",
    passed_total AS "Прошли",
    passed_m AS "Прошли М",
    passed_f AS "Прошли Ж",
    not_passed_total AS "Не прошли",
    not_passed_m AS "Не прошли М",
    not_passed_f AS "Не прошли Ж"
FROM (
    SELECT * FROM by_age
    UNION ALL
    SELECT * FROM totals
) t
ORDER BY CASE WHEN age_years IS NULL THEN 999999 ELSE age_years END
"""