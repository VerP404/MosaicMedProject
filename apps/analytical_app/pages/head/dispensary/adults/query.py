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


def sql_query_adults_appointments_not_passed(selected_year: int, visit_start_date: str, visit_end_date: str, exclude_departments: list[str] | None = None) -> str:
    """
    Пациенты 18+ по состоянию на выбранный год, которые записаны на прием (журнал обращений)
    в интервале дат, но НЕ имеют в load_data_oms_data целей 'ДВ4' или 'ОПВ' в указанном отчетном году.

    :param selected_year: Год отчета (int)
    :param visit_start_date: Дата начала (YYYY-MM-DD)
    :param visit_end_date: Дата окончания (YYYY-MM-DD)
    """
    # Исключение подразделений
    exclude_clause = ""
    if exclude_departments:
        safe_vals = [str(v).replace("'", "''") for v in exclude_departments if isinstance(v, str) and v.strip()]
        if safe_vals:
            exclude_clause = " AND ap.department NOT IN (" + ", ".join([f"'{v}'" for v in safe_vals]) + ")"

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
{"" if not exclude_clause else exclude_clause}
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
    
    # Экранируем номера талонов для SQL
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
        CASE 
            WHEN treatment_end IS NOT NULL AND birth_date IS NOT NULL AND
                 treatment_end::text ~ '^\\d{{2}}-\\d{{2}}-\\d{{4}}$' AND
                 birth_date::text ~ '^\\d{{2}}-\\d{{2}}-\\d{{4}}$' THEN
                CAST(SUBSTRING(treatment_end::text FROM 7 FOR 4) AS INTEGER) -
                CAST(SUBSTRING(birth_date::text FROM 7 FOR 4) AS INTEGER)
            ELSE NULL
        END AS age
    FROM load_data_oms_data
    WHERE talon IN ({talons_placeholder})
      AND goal IS NOT NULL
      AND goal != '-'
),
data_with_age AS (
    SELECT 
        goal,
        status,
        age
    FROM filtered_data
    WHERE age IS NOT NULL
      {age_condition}
),
grouped_data AS (
    SELECT 
        COALESCE(goal, '-') AS "Тип",
        COUNT(*) FILTER (WHERE status = '1' OR status::text = '1') AS "1",
        COUNT(*) FILTER (WHERE status = '2' OR status::text = '2') AS "2",
        COUNT(*) FILTER (WHERE status = '3' OR status::text = '3') AS "3",
        COUNT(*) FILTER (WHERE status = '4' OR status::text = '4') AS "4",
        COUNT(*) FILTER (WHERE status = '5' OR status::text = '5') AS "5",
        COUNT(*) FILTER (WHERE status = '6' OR status::text = '6') AS "6",
        COUNT(*) FILTER (WHERE status = '7' OR status::text = '7') AS "7",
        COUNT(*) FILTER (WHERE status = '8' OR status::text = '8') AS "8",
        COUNT(*) FILTER (WHERE status = '12' OR status::text = '12') AS "12",
        COUNT(*) FILTER (WHERE status = '13' OR status::text = '13') AS "13",
        COUNT(*) FILTER (WHERE status = '0' OR status::text = '0') AS "0"
    FROM data_with_age
    WHERE goal IS NOT NULL AND goal != '-'
    GROUP BY goal
),
totals AS (
    SELECT 
        'Итого' AS "Тип",
        SUM("1") AS "1",
        SUM("2") AS "2",
        SUM("3") AS "3",
        SUM("4") AS "4",
        SUM("5") AS "5",
        SUM("6") AS "6",
        SUM("7") AS "7",
        SUM("8") AS "8",
        SUM("12") AS "12",
        SUM("13") AS "13",
        SUM("0") AS "0"
    FROM grouped_data
),
result AS (
    SELECT * FROM grouped_data
    UNION ALL
    SELECT * FROM totals
)
SELECT 
    "Тип",
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