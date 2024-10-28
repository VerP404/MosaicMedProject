def base_query(year, months, inogorodniy, sanction, amount_null,
               building_ids=None,
               department_ids=None,
               profile_ids=None,
               doctor_ids=None,
               initial_input_date_start=None, initial_input_date_end=None,
               treatment_start=None, treatment_end=None,
               ):
    building_filter = ""
    department_filter = ""
    profile_filter = ""
    doctor_filter = ""
    inogorodniy_filter = ""
    status_filter = ""
    amount_null_filter = ""
    treatment = ""
    initial_input = ""

    if building_ids:
        building_filter = f"AND building_id IN ({','.join(map(str, building_ids))})"

    if department_ids:
        department_filter = f"AND department_id IN ({','.join(map(str, department_ids))})"

    if profile_ids:
        profile_filter = f"AND profile_id IN ({','.join(map(str, profile_ids))})"

    if doctor_ids:
        doctor_filter = f"AND doctor_id IN ({','.join(map(str, doctor_ids))})"

    if inogorodniy == '1':
        inogorodniy_filter = f"AND inogorodniy = false"
    if inogorodniy == '2':
        inogorodniy_filter = f"AND inogorodniy = true"

    if sanction == '1':
        status_filter = f"AND sanctions = '-'"
    if sanction == '2':
        status_filter = f"AND sanctions != '-'"

    if amount_null == '1':
        amount_null_filter = f"AND amount_numeric != '0'"
    if amount_null == '2':
        amount_null_filter = f"AND amount_numeric = '0'"



    if treatment_start and treatment_end:
        treatment = (f"AND to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date('{treatment_start}', "
                     f"'DD-MM-YYYY') and to_date('{treatment_end}', 'DD-MM-YYYY')")

    if initial_input_date_start and initial_input_date_end:
        initial_input = (f"AND to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date('{initial_input_date_start}', "
                         f"'DD-MM-YYYY') and to_date('{initial_input_date_end}', 'DD-MM-YYYY')")




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
                        WHEN report_data.treatment_end ~ '^\\d{2}-\\d{2}-\\d{4}$' AND
                             report_data.birth_date ~ '^\\d{2}-\\d{2}-\\d{4}$' THEN
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
                                WHERE report_data.report_year = '{year}' 
                                AND report_data.report_month_number IN ({months})
     ),
            oms as (select *
                    from oms_data
                    where talon notnull
                               {inogorodniy_filter}
                               {status_filter}
                               {amount_null_filter}
                               {building_filter}
                               {department_filter}
                               {profile_filter}
                               {doctor_filter}
                               {treatment}
                               {initial_input}
                               )
        """


def columns_by_status_oms():
    return """
                   COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3 )",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '4' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,4,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
    """


def sql_query_amb_def(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                      department=None,
                      profile=None,
                      doctor=None,
                      input_start=None, input_end=None,
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
           group by oms.goal;
    """
    return query


# def sql_query_amb_def(months_placeholder):
#     return f"""
# SELECT goal,
#                COUNT(*)                                       AS Всего,
#                SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
#                SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '4' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,4,6,8)",
#                SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
#                SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
#                SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
#                SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",
#                SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
#                SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
#                SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
#                SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
#                SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
#                SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
#                SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
#                SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
#                SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
#                SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
#                SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
#         FROM (SELECT *,
#                      department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
#                      '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
#                      CASE
#                          WHEN doctor_profile ~ '\\(.*\\)' THEN
#                              substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
#                          ELSE
#                              doctor_profile
#                          END AS "Корпус Врач"
#               FROM data_loader_omsdata) as oms
#         WHERE goal IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '32', '64', '640', '301', '305',
#                         '307', '541', '561')
#           AND "Корпус Врач" = :value_doctor
#           AND report_period IN ({months_placeholder})
#
#         GROUP BY goal
#
#         UNION ALL
#
#         SELECT
#     CASE
#         WHEN goal IN ('1', '5', '7', '9', '10', '32') THEN 'Посещения(1, 5, 7, 9, 10, 32)'
#         WHEN goal IN ('30', '301', '305', '307') THEN 'Обращения(30, 301, 305, 307)'
#         WHEN goal IN ('22') THEN 'Неотложка(22)'
#         WHEN goal IN ('3') THEN 'Диспансерное набл.(3)'
#         ELSE 'Другая цель'
#     END AS "Тип",
#     COUNT(*) AS Всего,
#     SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END) AS "Оплачен(3)",
#     SUM(CASE WHEN status IN ('1', '2', '3', '4', '6', '8') THEN 1 ELSE 0 END) AS "В работе(1,2,3,4,6,8)",
#     SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS "Выставлен(2)",
#     SUM(CASE WHEN status IN ('0', '13', '17') THEN 1 ELSE 0 END) AS "Отменен(0,13,17)",
#     SUM(CASE WHEN status IN ('5', '7', '12') THEN 1 ELSE 0 END) AS "Отказан(5,7,12)",
#     SUM(CASE WHEN status IN ('6', '8') THEN 1 ELSE 0 END) AS "Исправлен(6,8)",
#     SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END) AS "0",
#     SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS "1",
#     SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS "2",
#     SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END) AS "3",
#     SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END) AS "5",
#     SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END) AS "6",
#     SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END) AS "7",
#     SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END) AS "8",
#     SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
#     SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
#     SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
# FROM (
#     SELECT *,
#            department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
#            '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
#            CASE
#                WHEN doctor_profile ~ '\\(.*\\)' THEN
#                    substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
#                ELSE
#                    doctor_profile
#            END AS "Корпус Врач"
#     FROM data_loader_omsdata
# ) AS oms
# WHERE
#     goal IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '32', '64', '640', '301', '305',
#                 '307', '541', '561')
#           AND "Корпус Врач" = :value_doctor
#           AND report_period IN ({months_placeholder})
# GROUP BY "Тип"
#     """


def sql_query_stac_def(months_placeholder):
    return f"""
 SELECT goal,
               COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
        FROM (SELECT *,
                     department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
                     '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
                     CASE
                         WHEN doctor_profile ~ '\\(.*\\)' THEN
                             substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
                         ELSE
                             doctor_profile
                         END AS "Корпус Врач"
              FROM data_loader_omsdata) as oms
        WHERE goal IN ('В дневном стационаре', 'На дому', 'Стационарно')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})
        GROUP BY goal
        ORDER BY CASE goal
                     WHEN 'На дому' THEN 1
                     WHEN 'В дневном стационаре' THEN 2
                     WHEN 'Стационарно' THEN 3
                     END
        """


def sql_query_dd_def(months_placeholder):
    return f"""
 SELECT goal,
               COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",               
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
        FROM (SELECT *,
                     department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
                     '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
                     CASE
                         WHEN doctor_profile ~ '\\(.*\\)' THEN
                             substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
                         ELSE
                             doctor_profile
                         END AS "Корпус Врач"
              FROM data_loader_omsdata) as oms

        WHERE amount != '0'
          AND goal IN ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1', 'ДС2')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})

        GROUP BY goal
        ORDER BY CASE goal
                     WHEN 'ДВ4' THEN 1
                     WHEN 'ДВ2' THEN 2
                     WHEN 'ОПВ' THEN 3
                     WHEN 'УД1' THEN 4
                     WHEN 'УД2' THEN 5
                     WHEN 'ДР1' THEN 5
                     WHEN 'ДР2' THEN 5
                     WHEN 'ПН1' THEN 6
                     WHEN 'ДС2' THEN 7
                     END
        """
