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
    procedure: str,
    service_key: str,
    include_departments: list[str] | None = None,
) -> str:
    safe_procedure = _sql_escape(procedure)
    safe_service = _sql_escape(service_key)
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
      AND s.procedure = '{safe_procedure}'
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
      AND (service_name = '{safe_service}' OR service_nomenclature = '{safe_service}')
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
ORDER BY sf.appointment_ts DESC, sf.patient_fio
"""


def sql_query_procedure_appointments_analytics(
    selected_year: int,
    visit_start_date: str,
    visit_end_date: str,
    procedure: str,
    service_key: str,
    include_departments: list[str] | None = None,
) -> str:
    safe_procedure = _sql_escape(procedure)
    safe_service = _sql_escape(service_key)
    dept_clause = _department_filter_clause(include_departments, "s")

    return f"""
WITH scheduled AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        {_APPOINTMENT_TS_EXPR} AS appointment_ts
    FROM load_data_journal_appeals s
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND procedure = '{safe_procedure}'
      {dept_clause}
),
scheduled_filtered AS (
    SELECT enp_norm
    FROM scheduled
    WHERE appointment_ts::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
),
scheduled_unique AS (
    SELECT DISTINCT enp_norm FROM scheduled_filtered
),
service_fact AS (
    SELECT DISTINCT regexp_replace(enp, '\\D', '', 'g') AS enp_norm
    FROM load_data_detailed_medical_examination
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND service_status = 'Да'
      AND (service_name = '{safe_service}' OR service_nomenclature = '{safe_service}')
),
oms_any_goal AS (
    SELECT DISTINCT regexp_replace(enp, '\\D', '', 'g') AS enp_norm
    FROM load_data_oms_data
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND goal IN ({", ".join([f"'{g}'" for g in DISPENSARY_GOALS])})
      AND report_year = {int(selected_year)}
),
oms_dv4_opv AS (
    SELECT DISTINCT regexp_replace(enp, '\\D', '', 'g') AS enp_norm
    FROM load_data_oms_data
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND goal IN ('ДВ4', 'ОПВ')
      AND report_year = {int(selected_year)}
),
base AS (
    SELECT
        (SELECT COUNT(*) FROM scheduled_filtered) AS scheduled_rows,
        (SELECT COUNT(*) FROM scheduled_unique) AS scheduled_unique_enp,
        (SELECT COUNT(*) FROM scheduled_unique su INNER JOIN service_fact svc ON su.enp_norm = svc.enp_norm) AS passed_service,
        (SELECT COUNT(*) FROM scheduled_unique su INNER JOIN oms_any_goal og ON su.enp_norm = og.enp_norm) AS has_any_goal,
        (SELECT COUNT(*) FROM scheduled_unique su
            INNER JOIN service_fact svc ON su.enp_norm = svc.enp_norm
            INNER JOIN oms_any_goal og ON su.enp_norm = og.enp_norm) AS overlap_service_and_goal,
        (SELECT COUNT(*) FROM scheduled_unique su INNER JOIN oms_dv4_opv dv ON su.enp_norm = dv.enp_norm) AS passed_dv4_opv,
        (SELECT COUNT(*) FROM scheduled_unique su LEFT JOIN oms_dv4_opv dv ON su.enp_norm = dv.enp_norm WHERE dv.enp_norm IS NULL) AS scheduled_not_dv4_opv
)
SELECT
    'Сводка' AS "Показатель",
    scheduled_rows AS "Значение"
FROM base
UNION ALL SELECT 'Уникальных ЕНП', scheduled_unique_enp FROM base
UNION ALL SELECT 'Прошли выбранную услугу', passed_service FROM base
UNION ALL SELECT 'Не прошли услугу', scheduled_unique_enp - passed_service FROM base
UNION ALL SELECT 'Есть хотя бы одна цель (ОМС)', has_any_goal FROM base
UNION ALL SELECT 'Нет ни одной цели', scheduled_unique_enp - has_any_goal FROM base
UNION ALL SELECT 'Прошли ДВ4 или ОПВ', passed_dv4_opv FROM base
UNION ALL SELECT 'Записаны, не прошли ДВ4/ОПВ', scheduled_not_dv4_opv FROM base
UNION ALL SELECT 'Пересечение: услуга + цель', overlap_service_and_goal FROM base
"""


def sql_query_procedure_appointments_goal_breakdown(
    selected_year: int,
    visit_start_date: str,
    visit_end_date: str,
    procedure: str,
    include_departments: list[str] | None = None,
) -> str:
    safe_procedure = _sql_escape(procedure)
    dept_clause = _department_filter_clause(include_departments, "s")

    return f"""
WITH scheduled AS (
    SELECT
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        {_APPOINTMENT_TS_EXPR} AS appointment_ts
    FROM load_data_journal_appeals s
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND procedure = '{safe_procedure}'
      {dept_clause}
),
scheduled_unique AS (
    SELECT DISTINCT enp_norm
    FROM scheduled
    WHERE appointment_ts::date BETWEEN DATE '{visit_start_date}' AND DATE '{visit_end_date}'
),
oms_goals AS (
    SELECT DISTINCT
        regexp_replace(o.enp, '\\D', '', 'g') AS enp_norm,
        o.goal
    FROM load_data_oms_data o
    INNER JOIN scheduled_unique sf ON regexp_replace(o.enp, '\\D', '', 'g') = sf.enp_norm
    WHERE o.goal IN ({", ".join([f"'{g}'" for g in DISPENSARY_GOALS])})
      AND o.report_year = {int(selected_year)}
)
SELECT goal AS "Цель", COUNT(DISTINCT enp_norm) AS "Количество"
FROM oms_goals
GROUP BY goal
ORDER BY goal
"""