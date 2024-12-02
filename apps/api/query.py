def base_query(year, months, inogorodniy=1, sanction=1, amount_null=1,
               building_ids=None,
               department_ids=None,
               profile_ids=None,
               doctor_ids=None,
               initial_input_date_start=None, initial_input_date_end=None,
               treatment_start=None, treatment_end=None,
               cel_list=None, status_list=None):

    if months == '0':
        months = ','.join(map(str, range(1, 13)))

    filters = []

    if building_ids:
        filters.append(f"building_id IN ({','.join(map(str, building_ids))})")
    if department_ids:
        filters.append(f"department_id IN ({','.join(map(str, department_ids))})")
    if profile_ids:
        filters.append(f"profile_id IN ({','.join(map(str, profile_ids))})")
    if doctor_ids:
        filters.append(f"doctor_id IN ({','.join(map(str, doctor_ids))})")

    if inogorodniy == '1':
        filters.append("inogorodniy = false")
    elif inogorodniy == '2':
        filters.append("inogorodniy = true")

    if sanction == '1':
        filters.append("sanctions = '-'")
    elif sanction == '2':
        filters.append("sanctions != '-'")

    if amount_null == '1':
        filters.append("amount_numeric != '0'")
    elif amount_null == '2':
        filters.append("amount_numeric = '0'")

    if treatment_start and treatment_end:
        filters.append(f"to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date('{treatment_start}', 'DD-MM-YYYY') "
                       f"AND to_date('{treatment_end}', 'DD-MM-YYYY')")

    if initial_input_date_start and initial_input_date_end:
        filters.append(f"to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN "
                       f"to_date('{initial_input_date_start}', 'DD-MM-YYYY') AND to_date('{initial_input_date_end}', 'DD-MM-YYYY')")

    if cel_list:
        filters.append("status IN (" + ",".join(f"'{cel}'" for cel in cel_list) + ")")
    if status_list:
        filters.append("status IN (" + ",".join(f"'{stat}'" for stat in status_list) + ")")

    filters_query = " AND ".join(filters)

    return f"""
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
                                            WHERE SPLIT_PART(TRIM(s), ' ', 1) ~ '^[A-Z]\\d{2}(\\.\\d)?$'
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
     )
            select *
                    from oms_data
        WHERE report_year = '{year}' 
          AND report_month_number IN ({months})
          {(' AND ' + filters_query) if filters_query else ''}
                               
        """


def query_api_month(year, months, inogorodniy=1, sanction=1, amount_null=1,
               building_ids=None,
               department_ids=None,
               profile_ids=None,
               doctor_ids=None,
               initial_input_date_start=None, initial_input_date_end=None,
               treatment_start=None, treatment_end=None,
               cel_list=None, status_list=None):
    if months == '0':
        months = ','.join(map(str, range(1, 13)))

    filters = []

    if building_ids:
        filters.append(f"building_id IN ({','.join(map(str, building_ids))})")
    if department_ids:
        filters.append(f"department_id IN ({','.join(map(str, department_ids))})")
    if profile_ids:
        filters.append(f"profile_id IN ({','.join(map(str, profile_ids))})")
    if doctor_ids:
        filters.append(f"doctor_id IN ({','.join(map(str, doctor_ids))})")

    if inogorodniy == '1':
        filters.append("inogorodniy = false")
    elif inogorodniy == '2':
        filters.append("inogorodniy = true")

    if sanction == '1':
        filters.append("sanctions = '-'")
    elif sanction == '2':
        filters.append("sanctions != '-'")

    if amount_null == '1':
        filters.append("amount_numeric != '0'")
    elif amount_null == '2':
        filters.append("amount_numeric = '0'")

    if treatment_start and treatment_end:
        filters.append(f"to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date('{treatment_start}', 'DD-MM-YYYY') "
                       f"AND to_date('{treatment_end}', 'DD-MM-YYYY')")

    if initial_input_date_start and initial_input_date_end:
        filters.append(f"to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN "
                       f"to_date('{initial_input_date_start}', 'DD-MM-YYYY') AND to_date('{initial_input_date_end}', 'DD-MM-YYYY')")

    if cel_list:
        filters.append("status IN (" + ",".join(f"'{cel}'" for cel in cel_list) + ")")
    if status_list:
        filters.append("status IN (" + ",".join(f"'{stat}'" for stat in status_list) + ")")


    return f"""
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
                                            WHERE SPLIT_PART(TRIM(s), ' ', 1) ~ '^[A-Z]\\d{2}(\\.\\d)?$'
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
            oms as (select *
                    from oms_data
        WHERE report_year = '{year}' 
          AND report_month_number IN ({months})
          AND inogorodniy = false
          AND sanctions = '-'
          AND amount_numeric != '0'),
          aggregated_data AS (SELECT report_month_number,
                                COUNT(DISTINCT talon) AS patient_count,
                                SUM(amount_numeric)     AS total_amount
                         FROM oms
                         GROUP BY report_month_number
                         ORDER BY report_month_number)
SELECT report_month_number,
       patient_count AS "Количество пациентов",
       total_amount  AS "Сумма"
FROM aggregated_data
order by report_month_number desc

        """


def query_api_dd(year, months, inogorodniy=1, sanction=1, amount_null=1,
               building_ids=None,
               department_ids=None,
               profile_ids=None,
               doctor_ids=None,
               initial_input_date_start=None, initial_input_date_end=None,
               treatment_start=None, treatment_end=None,
               cel_list=None, status_list=None):
    if months == '0':
        months = ','.join(map(str, range(1, 13)))

    filters = []

    if building_ids:
        filters.append(f"building_id IN ({','.join(map(str, building_ids))})")
    if department_ids:
        filters.append(f"department_id IN ({','.join(map(str, department_ids))})")
    if profile_ids:
        filters.append(f"profile_id IN ({','.join(map(str, profile_ids))})")
    if doctor_ids:
        filters.append(f"doctor_id IN ({','.join(map(str, doctor_ids))})")

    if inogorodniy == '1':
        filters.append("inogorodniy = false")
    elif inogorodniy == '2':
        filters.append("inogorodniy = true")

    if sanction == '1':
        filters.append("sanctions = '-'")
    elif sanction == '2':
        filters.append("sanctions != '-'")

    if amount_null == '1':
        filters.append("amount_numeric != '0'")
    elif amount_null == '2':
        filters.append("amount_numeric = '0'")

    if treatment_start and treatment_end:
        filters.append(f"to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date('{treatment_start}', 'DD-MM-YYYY') "
                       f"AND to_date('{treatment_end}', 'DD-MM-YYYY')")

    if initial_input_date_start and initial_input_date_end:
        filters.append(f"to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN "
                       f"to_date('{initial_input_date_start}', 'DD-MM-YYYY') AND to_date('{initial_input_date_end}', 'DD-MM-YYYY')")

    if cel_list:
        filters.append("status IN (" + ",".join(f"'{cel}'" for cel in cel_list) + ")")
    if status_list:
        filters.append("status IN (" + ",".join(f"'{stat}'" for stat in status_list) + ")")


    return f"""
        WITH oms as (select 
                        report_month_number,
                        goal,
                        COUNT(*) AS count
                    from data_oms
        WHERE report_year = '{year}' 
          AND report_month_number IN ({months})
          AND status IN ('1', '2', '3', '4', '6', '8')
          AND inogorodniy = false
          AND sanctions = '-'
          AND amount_numeric != '0'
          AND goal IN ('ДВ2', 'ДВ4', 'ДР1', 'ДР2', 'ОПВ', 'ПН1', 'УД1', 'УД2')
        GROUP BY report_month_number, goal),
pivoted_data AS (
    SELECT
        goal,
        SUM(count) AS "Итого",
        SUM(CASE WHEN report_month_number = 1 THEN count ELSE 0 END) AS "1",
        SUM(CASE WHEN report_month_number = 2 THEN count ELSE 0 END) AS "2",
        SUM(CASE WHEN report_month_number = 3 THEN count ELSE 0 END) AS "3",
        SUM(CASE WHEN report_month_number = 4 THEN count ELSE 0 END) AS "4",
        SUM(CASE WHEN report_month_number = 5 THEN count ELSE 0 END) AS "5",
        SUM(CASE WHEN report_month_number = 6 THEN count ELSE 0 END) AS "6",
        SUM(CASE WHEN report_month_number = 7 THEN count ELSE 0 END) AS "7",
        SUM(CASE WHEN report_month_number = 8 THEN count ELSE 0 END) AS "8",
        SUM(CASE WHEN report_month_number = 9 THEN count ELSE 0 END) AS "9",
        SUM(CASE WHEN report_month_number = 10 THEN count ELSE 0 END) AS "10",
        SUM(CASE WHEN report_month_number = 11 THEN count ELSE 0 END) AS "11",
        SUM(CASE WHEN report_month_number = 12 THEN count ELSE 0 END) AS "12"
    FROM oms
    GROUP BY goal
)
SELECT p.goal,
       case when plan_table.plan is not null then plan_table.plan else 0 end AS "План",
       p."Итого",
       p."1",
       p."2",
       p."3",
       p."4",
       p."5",
       p."6",
       p."7",
       p."8",
       p."9",
       p."10",
       p."11",
       p."12"
FROM pivoted_data p
         LEFT JOIN plan_chiefdashboard plan_table
                   ON p.goal = plan_table.goal
                       AND plan_table.year = '{year}'
                       AND plan_table.name = 'Диспансеризация'
ORDER BY p.goal
        """

