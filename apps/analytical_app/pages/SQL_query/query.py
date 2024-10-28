def base_query(year, months, inogorodniy, sanction, amount_null,
               building_ids=None,
               department_ids=None,
               profile_ids=None,
               doctor_ids=None,
               initial_input_date_start=None, initial_input_date_end=None,
               treatment_start=None, treatment_end=None,
               cel_list=None, status_list=None):
    building_filter = ""
    department_filter = ""
    profile_filter = ""
    doctor_filter = ""
    inogorodniy_filter = ""
    status_filter = ""
    amount_null_filter = ""
    treatment = ""
    initial_input = ""
    cels = ""
    status = ""

    if cel_list:
        cels = f"AND goal IN ({','.join(f'\'{cel}\'' for cel in cel_list)})"
    if status_list:
        status = f"AND status IN ({','.join(f'\'{cel}\'' for cel in status_list)})"

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
                               {cels}
                               {status}
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


def columns_by_department(selected_buildings):
    dynamic_columns = []
    dynamic_column_names = []
    dynamic_column_sums = []

    # Генерация столбцов только для выбранных корпусов
    for department in selected_buildings:
        dynamic_columns.append(
            f"SUM(CASE WHEN ob.name = '{department}' AND dlo.gender = 'М' THEN 1 ELSE 0 END) AS \"М {department}\"")
        dynamic_columns.append(
            f"ROUND(SUM(CASE WHEN ob.name = '{department}' AND dlo.gender = 'М' THEN ROUND(CAST(dlo.amount AS numeric(15, 2)):: numeric, 2) ELSE 0 END):: numeric, 2) AS \"М {building} Сумма\"")
        dynamic_columns.append(
            f"SUM(CASE WHEN ob.name = '{department}' AND dlo.gender = 'Ж' THEN 1 ELSE 0 END) AS \"Ж {department}\"")
        dynamic_columns.append(
            f"ROUND(SUM(CASE WHEN ob.name = '{department}' AND dlo.gender = 'Ж' THEN ROUND(CAST(dlo.amount AS numeric(15, 2)):: numeric, 2) ELSE 0 END):: numeric, 2) AS \"Ж {building} Сумма\"")

        dynamic_column_names.append(f"\"М {department}\"")
        dynamic_column_names.append(f"\"М {department} Сумма\"")
        dynamic_column_names.append(f"\"Ж {department}\"")
        dynamic_column_names.append(f"\"Ж {department} Сумма\"")

        dynamic_column_sums.append(f"SUM(\"М {department}\")")
        dynamic_column_sums.append(f"SUM(\"М {department} Сумма\")")
        dynamic_column_sums.append(f"SUM(\"Ж {department}\")")
        dynamic_column_sums.append(f"SUM(\"Ж {department} Сумма\")")

    dynamic_columns_sql = ',\n    '.join(dynamic_columns)
    dynamic_column_names_sql = ',\n       '.join(dynamic_column_names)
    dynamic_column_sums_sql = ',\n       '.join(dynamic_column_sums)
    return dynamic_columns_sql, dynamic_column_names_sql, dynamic_column_sums_sql
