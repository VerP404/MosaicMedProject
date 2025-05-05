def sql_head_dn_job():
    return f"""
    WITH combined_diagnoses AS (
    SELECT DISTINCT
        enp,
        status,
        LOWER(LEFT(main_diagnosis, POSITION(' ' IN main_diagnosis)-1)) AS ds
    FROM data_loader_omsdata
    WHERE main_diagnosis IS NOT NULL
    and goal = '3'
    UNION ALL

    SELECT DISTINCT
        enp,
        status,
        LOWER(LEFT(additional_diagnosis, POSITION(' ' IN additional_diagnosis)-1)) AS ds
    FROM data_loader_omsdata
    WHERE additional_diagnosis IS NOT NULL
    and goal = '3'
),

job_data AS (
    SELECT
        job.id_iszl,
        job.organization,
        job.fio,
        job.birth_date,
        job.enp,
        job.ds,
        CASE
            WHEN people.enp IS NOT NULL THEN 'да'
            ELSE 'нет'
        END AS attachment,
        CASE
            WHEN COUNT(CASE WHEN diag.enp IS NOT NULL THEN 1 END) > 0 THEN 'да'
            ELSE 'нет'
        END AS oms,
        CASE
            WHEN COUNT(CASE WHEN diag.enp IS NOT NULL AND diag.status = '3' THEN 1 END) > 0 THEN 'да'
            ELSE 'нет'
        END AS oms_paid
    FROM data_loader_iszldisnabjob AS job
    LEFT JOIN data_loader_iszlpeople AS people
        ON job.enp = people.enp
    LEFT JOIN combined_diagnoses AS diag
        ON job.enp = diag.enp
        AND LOWER(job.ds) = diag.ds
    GROUP BY
        job.id_iszl,
        job.organization,
        job.fio,
        job.birth_date,
        job.enp,
        job.ds,
        people.enp
)

SELECT
    COUNT(*) AS "Всего записей в ИСЗЛ",                                             
    COUNT(CASE WHEN attachment = 'да' THEN 1 END) AS "Прикреплено (заменить)",          
    COUNT(CASE WHEN attachment = 'нет' THEN 1 END) AS "Не прикреплено",     
    COUNT(CASE WHEN attachment = 'нет' AND oms = 'да' THEN 1 END) AS "Подано",  
    COUNT(CASE WHEN attachment = 'нет' AND oms_paid = 'да' THEN 1 END) AS "Оплачено"  
FROM job_data;
    """


def sql_head_dn_job2():
    return f"""
WITH parsed AS (SELECT external_id,
                       mo_prikreplenia,
                       org_prof_m,
                       enp,
                       ds,
                       date,
                       to_timestamp(date, 'DD.MM.YYYY HH24:MI:SS') AS ts
                FROM load_data_dn_work_iszl)
SELECT external_id,
       mo_prikreplenia,
       org_prof_m,
       enp,
       UPPER(ds)              AS ds,
       date,
       EXTRACT(MONTH FROM ts) AS month,
       EXTRACT(YEAR FROM ts)  AS year,
       CASE
           WHEN ROW_NUMBER() OVER (
               PARTITION BY enp, UPPER(ds), EXTRACT(YEAR FROM ts)
               ORDER BY external_id
               ) = 1
               THEN FALSE
           ELSE TRUE
           END                AS duplicate
FROM parsed
ORDER BY enp, ds, year, external_id
    """


def sql_head_dn_job_nested(year: int) -> str:
    return f"""
WITH
  disp AS (
    SELECT
      x.enp,
      x.external_id,
      x.mo_prikreplenia,
      x.org_prof_m,
      TRIM(UPPER(x.fio)) AS fio_norm,
      TO_CHAR(TO_TIMESTAMP(x.dr, 'DD.MM.YYYY HH24:MI:SS'), 'DD-MM-YYYY') AS dr_norm,
      UPPER(x.ds) AS ds_norm,
      EXTRACT(MONTH FROM TO_TIMESTAMP(x.date, 'DD.MM.YYYY HH24:MI:SS')) AS month_d,
      EXTRACT(YEAR  FROM TO_TIMESTAMP(x.date, 'DD.MM.YYYY HH24:MI:SS')) AS year_d,
      TO_CHAR(TO_TIMESTAMP(x.date, 'DD.MM.YYYY HH24:MI:SS'), 'DD-MM-YYYY') AS disp_date,
      CASE
        WHEN ROW_NUMBER() OVER (
               PARTITION BY x.enp, UPPER(x.ds), EXTRACT(YEAR FROM TO_TIMESTAMP(x.date,'DD.MM.YYYY HH24:MI:SS'))
               ORDER BY x.external_id
             ) = 1 THEN FALSE
        ELSE TRUE
      END AS duplicate
    FROM load_data_dn_work_iszl AS x
    WHERE EXTRACT(YEAR FROM TO_TIMESTAMP(x.date, 'DD.MM.YYYY HH24:MI:SS')) = {year}
  ),

  tal AS (
    SELECT
      t.enp,
      t.patient,
      t.birth_date,
      t.talon,
      t.report_period,
      t.place_service,
      t.status,
      t.treatment_end,
      EXTRACT(MONTH FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) AS month_end,
      EXTRACT(YEAR  FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) AS year_end,
      t.doctor,
      t.doctor_profile,
      CASE WHEN t.main_diagnosis = '-' THEN NULL
           ELSE SPLIT_PART(t.main_diagnosis, ' ', 1)
      END AS ds1,
      ARRAY(
        SELECT word
        FROM unnest(string_to_array(t.additional_diagnosis, ' ')) AS word
        WHERE word ~ '^[A-ZА-Я]\d{1, 2}(\.\d{1, 2})?$'
      ) AS ds2
    FROM load_data_talons AS t
    WHERE t.goal = '3'
      AND EXTRACT(YEAR FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) = {year}
      AND (t.place_service <> '-' OR EXISTS (
             SELECT 1 FROM load_data_dn_work_iszl d_full WHERE d_full.enp = t.enp
          ))
  )

SELECT
  COALESCE(t.enp, d.enp)                                       AS enp,
  INITCAP(LOWER(COALESCE(t.patient, d.fio_norm)))             AS patient,
  COALESCE(t.birth_date, d.dr_norm)                            AS birth_date,
  t.talon,
  t.report_period,
  t.place_service,
  t.status,
  t.treatment_end,
  t.month_end,
  t.year_end,
  t.doctor,
  t.doctor_profile,
  t.ds1,
  t.ds2,
  d.external_id,
  d.mo_prikreplenia,
  d.org_prof_m,
  d.ds_norm                                                   ,
  d.disp_date,
  d.month_d,
  d.year_d,
  d.duplicate
FROM tal AS t
FULL JOIN disp AS d
  ON d.enp     = t.enp
     AND d.month_d = t.month_end
     AND d.year_d  = t.year_end
     AND (
       d.ds_norm = t.ds1
       OR d.ds_norm = ANY(t.ds2)
     )
ORDER BY enp,
         COALESCE(t.treatment_end::date, TO_DATE(d.disp_date,'DD-MM-YYYY'));
"""
