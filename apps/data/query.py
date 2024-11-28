def base_query_oms():
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
                     FROM data_loader_omsdata oms)
SELECT report_data.talon,
       report_data.source,
       (ARRAY ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь',
           'Октябрь', 'Ноябрь', 'Декабрь'])[report_data.report_month_number]            AS report_month,
       report_month_number,
       report_data.report_year,
       report_data.status,
       CASE
           WHEN report_data.goal = '-' AND report_data.talon_type = 'Стоматология'
               THEN report_data.talon_type
           ELSE report_data.goal
           END                                                                          AS goal,
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
       )                                                                                AS target_categories,
       report_data.patient,
       CASE
           WHEN report_data.birth_date ~ '^\d{2}-\d{2}-\d{4}$' THEN TO_DATE(report_data.birth_date, 'DD-MM-YYYY')
           END                                                                          AS birth_date_date,
       CASE
           WHEN report_data.treatment_end ~ '^\d{2}-\d{2}-\d{4}$' AND
                report_data.birth_date ~ '^\d{2}-\d{2}-\d{4}$' THEN
               CAST(SUBSTRING(report_data.treatment_end FROM 7 FOR 4) AS INTEGER) -
               CAST(SUBSTRING(report_data.birth_date FROM 7 FOR 4) AS INTEGER)
           END                                                                          AS age,
       report_data.gender,
       CASE
           WHEN report_data.enp = '-' THEN report_data.policy
           ELSE report_data.enp
           END                                                                          AS enp,
       report_data.smo_code,
       CASE
           WHEN report_data.smo_code LIKE '360%' THEN false
           ELSE true
           END                                                                          AS inogorodniy,
       CASE
           WHEN report_data.treatment_start ~ '^\d{2}-\d{2}-\d{4}$'
               THEN TO_DATE(report_data.treatment_start, 'DD-MM-YYYY')
           END                                                                          AS treatment_start,
       CASE
           WHEN report_data.treatment_end ~ '^\d{2}-\d{2}-\d{4}$' THEN TO_DATE(report_data.treatment_end, 'DD-MM-YYYY')
           END                                                                          AS treatment_end,
              CASE
           WHEN report_data.visits = '-' AND treatment_start = treatment_end THEN '1'
           WHEN report_data.visits = '-' AND treatment_start != treatment_end THEN '2'
           ELSE report_data.visits
                end                                                                          AS visits,
                              CASE
           WHEN report_data.mo_visits = '-' AND treatment_start = treatment_end THEN '1'
           WHEN report_data.mo_visits = '-' AND treatment_start != treatment_end THEN '2'
           ELSE report_data.mo_visits
                end                                                                          AS mo_visits,                              
                CASE
           WHEN report_data.home_visits = '-' THEN '0'
           ELSE report_data.home_visits
                end                                                                          AS home_visits,
       CASE
           WHEN report_data.main_diagnosis = '-' THEN NULL
           ELSE SPLIT_PART(report_data.main_diagnosis, ' ', 1)
           END                                                                          AS main_diagnosis_code,
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
           END                                                                          AS additional_diagnosis_codes,
       CASE
           WHEN report_data.initial_input_date ~ '^\d{2}-\d{2}-\d{4}$' THEN TO_DATE(report_data.initial_input_date, 'DD-MM-YYYY')
           END                                                                          AS initial_input_date,
       CASE
           WHEN report_data.last_change_date ~ '^\d{2}-\d{2}-\d{4}$' THEN TO_DATE(report_data.last_change_date, 'DD-MM-YYYY')
           END                                                                          AS last_change_date,

       CASE
           WHEN report_data.amount ~ '^[0-9]+(\\.[0-9]+)?$' THEN CAST(report_data.amount AS NUMERIC)
           END                                                                          AS amount_numeric,
       report_data.sanctions,
       report_data.ksg,
       department.id                                                                    as department_id,
       department.name                                                                  AS department,
       building.id                                                                      as building_id,
       building.name                                                                    AS building,
       SUBSTRING(report_data.doctor FROM 1 FOR POSITION(' ' IN report_data.doctor) - 1) AS doctor_code,
       pd.id                                                                            as doctor_id,
       CONCAT(person.last_name, ' ',
              SUBSTRING(person.first_name FROM 1 FOR 1), '.',
              SUBSTRING(person.patronymic FROM 1 FOR 1),
              '.')                                                                      AS doctor,
       specialty.description                                                            AS specialty,
       profile.description                                                              AS profile,
       profile.id                                                                       as profile_id

FROM report_data
         LEFT JOIN (SELECT DISTINCT ON (doctor_code) *
                    FROM personnel_doctorrecord
                    ORDER BY doctor_code, id) pd
                   ON SUBSTRING(report_data.doctor FROM 1 FOR POSITION(' ' IN report_data.doctor) - 1) = pd.doctor_code
         LEFT JOIN public.organization_department department ON department.id = pd.department_id
         LEFT JOIN public.organization_building building ON building.id = department.building_id
         LEFT JOIN public.personnel_specialty specialty ON specialty.id = pd.specialty_id
         LEFT JOIN public.personnel_profile profile ON profile.id = pd.profile_id
         LEFT JOIN public.personnel_person person ON person.id = pd.person_id
        """
