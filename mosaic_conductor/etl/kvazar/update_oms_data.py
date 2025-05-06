from dagster import op
from sqlalchemy import text

from mosaic_conductor.etl.common.connect_db import connect_to_db


@op
def update_oms_data_op(context, load_result):
    """
    Вставляет или обновляет сводные данные OMS в таблицу load_data_oms_data
    на основе CTE oms_data.
    """
    engine, _ = connect_to_db(context=context)

    sql = """
    WITH oms_data AS (
      /* ваш CTE без изменений */
      SELECT
        talons.talon,
        (ARRAY[
          'Январь','Февраль','Март','Апрель','Май','Июнь',
          'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'
        ])[report_month]                             AS month,
        report_month,
        report_year::int AS report_year,
        COALESCE(source_id,   '-') as source_id,
        place_service,
        talons.status,
        CASE
          WHEN goal = '-' AND talons.talon_type = 'Стоматология'
          THEN talons.talon_type ELSE goal END         AS goal,
        patient,
        to_date(talons.birth_date,      'DD-MM-YYYY') AS birth_date,
        to_date(talons.treatment_start, 'DD-MM-YYYY') AS treatment_start,
        to_date(talons.treatment_end,   'DD-MM-YYYY') AS treatment_end,
        CAST(RIGHT(talons.treatment_end,4) AS INT)
          - CAST(RIGHT(talons.birth_date,4) AS INT)    AS age,
        talons.gender,
        CASE WHEN talons.enp = '-' THEN talons.policy ELSE talons.enp END AS enp,
        smo_code,
        CASE WHEN smo_code LIKE '360%' THEN FALSE ELSE TRUE END            AS inogorodniy,
        CASE WHEN visits IN ('0','-')
             THEN (to_date(talons.treatment_end,'DD-MM-YYYY')
                   - to_date(talons.treatment_start,'DD-MM-YYYY')+1)::int
             ELSE visits::int END                                        AS visits,
        COALESCE(NULLIF(mo_visits,'-'),'0')::int                         AS mo_visits,
        COALESCE(NULLIF(home_visits,'-'),'0')::int                       AS home_visits,
        CASE WHEN talons.main_diagnosis = '-' THEN NULL
             ELSE split_part(talons.main_diagnosis,' ',1) END            AS main_diagnosis_code,
        array_to_string(
          (SELECT array_agg(split_part(trim(s),' ',1))
           FROM unnest(string_to_array(talons.additional_diagnosis,',')) AS s),
          ','
        )                                                                AS additional_diagnosis_codes,
        to_date(initial_input_date,'DD-MM-YYYY')                         AS initial_input_date,
        to_date(last_change_date,    'DD-MM-YYYY')                       AS last_change_date,
        amount::numeric                                                  AS amount_numeric,
        sanctions,
        ksg,
        COALESCE(department.id,   0)                                                     AS department_id,
        COALESCE(department.name, '-')                                                   AS department,
        COALESCE(building.id,     0)                                                       AS building_id,
        COALESCE(building.name,   '-')                                                     AS building,
        split_part(doctor,' ',1)                                          AS doctor_code,
        COALESCE(pd.id, 0)::int                                                             AS doctor_id,
        concat(
          person.last_name,' ',
          substr(person.first_name,1,1),'.',
          substr(person.patronymic,1,1),'.'
        )                                                                AS doctor,
        COALESCE(specialty.description, '-')                                              AS specialty,
        COALESCE(profile.description, '-')                                               AS profile,
        COALESCE(profile.id  , 0)::int                                                      AS profile_id,
        COALESCE(dme.health_group, '-')                                   AS health_group,
        talons.created_at                      AS created_at,
        talons.updated_at                      AS updated_at
      FROM load_data_talons talons
      LEFT JOIN (
        SELECT DISTINCT ON (tde.talon_number)
          tde.talon_number, tde.health_group
        FROM load_data_detailed_medical_examination tde
        ORDER BY tde.talon_number
      ) AS dme ON talons.talon = dme.talon_number
      LEFT JOIN (
        SELECT DISTINCT ON (doctor_code) *
        FROM personnel_doctorrecord
        ORDER BY doctor_code, id
      ) pd ON split_part(doctor,' ',1) = pd.doctor_code
      LEFT JOIN public.organization_department  department ON department.id = pd.department_id
      LEFT JOIN public.organization_building    building   ON building.id   = department.building_id
      LEFT JOIN public.personnel_specialty      specialty  ON specialty.id  = pd.specialty_id
      LEFT JOIN public.personnel_profile        profile    ON profile.id    = pd.profile_id
      LEFT JOIN public.personnel_person         person     ON person.id     = pd.person_id
    )
    INSERT INTO load_data_oms_data (
      talon, month, report_month, report_year, source_id,
      place_service, status, goal, patient,
      birth_date, treatment_start, treatment_end, age,
      gender, enp, smo_code, inogorodniy,
      visits, mo_visits, home_visits,
      main_diagnosis_code, additional_diagnosis_codes,
      initial_input_date, last_change_date, amount_numeric,
      sanctions, ksg, department_id, department,
      building_id, building, doctor_code, doctor_id,
      doctor, specialty, profile, profile_id, health_group,
      attached, created_at, updated_at
    )
    SELECT
      talon, month, report_month, report_year, source_id,
      place_service, status, goal, patient,
      birth_date, treatment_start, treatment_end, age,
      gender, enp, smo_code, inogorodniy,
      visits, mo_visits, home_visits,
      main_diagnosis_code, additional_diagnosis_codes,
      initial_input_date, last_change_date, amount_numeric,
      sanctions, ksg, department_id, department,
      building_id, building, doctor_code, doctor_id,
      doctor, specialty, profile, profile_id, health_group,
      TRUE AS attached, created_at, updated_at
    FROM oms_data
    ON CONFLICT (talon, source_id, doctor_code)
    DO UPDATE SET
      month                       = EXCLUDED.month,
      report_month                = EXCLUDED.report_month,
      report_year                 = EXCLUDED.report_year,
      place_service               = EXCLUDED.place_service,
      status                      = EXCLUDED.status,
      goal                        = EXCLUDED.goal,
      patient                     = EXCLUDED.patient,
      birth_date                  = EXCLUDED.birth_date,
      treatment_start             = EXCLUDED.treatment_start,
      treatment_end               = EXCLUDED.treatment_end,
      age                         = EXCLUDED.age,
      gender                      = EXCLUDED.gender,
      enp                         = EXCLUDED.enp,
      smo_code                    = EXCLUDED.smo_code,
      inogorodniy                 = EXCLUDED.inogorodniy,
      visits                      = EXCLUDED.visits,
      mo_visits                   = EXCLUDED.mo_visits,
      home_visits                 = EXCLUDED.home_visits,
      main_diagnosis_code         = EXCLUDED.main_diagnosis_code,
      additional_diagnosis_codes  = EXCLUDED.additional_diagnosis_codes,
      initial_input_date          = EXCLUDED.initial_input_date,
      last_change_date            = EXCLUDED.last_change_date,
      amount_numeric              = EXCLUDED.amount_numeric,
      sanctions                   = EXCLUDED.sanctions,
      ksg                         = EXCLUDED.ksg,
      department_id               = EXCLUDED.department_id,
      department                  = EXCLUDED.department,
      building_id                 = EXCLUDED.building_id,
      building                    = EXCLUDED.building,
      doctor_id                   = EXCLUDED.doctor_id,
      doctor                      = EXCLUDED.doctor,
      specialty                   = EXCLUDED.specialty,
      profile                     = EXCLUDED.profile,
      profile_id                  = EXCLUDED.profile_id,
      health_group                = EXCLUDED.health_group,
      attached                    = EXCLUDED.attached,
      updated_at                  = EXCLUDED.updated_at;
    """

    with engine.begin() as conn:
        before = conn.execute(text(
            "SELECT COUNT(*) FROM load_data_oms_data"
        )).scalar_one()
        context.log.info(f"🔄 До обновления OMS: {before}")
        result = conn.execute(text(sql))
        context.log.info(f"✅ Вставлено/обновлено строк OMS: {result.rowcount}")
        after = conn.execute(text(
            "SELECT COUNT(*) FROM load_data_oms_data"
        )).scalar_one()
        context.log.info(f"🔍 После обновления OMS: {after}")

    # возвращаем load_result, чтобы DAG дальше продолжился
    return load_result
