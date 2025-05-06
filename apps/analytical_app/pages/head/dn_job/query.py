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
            WHERE word ~ '^[A-ZА-Я][0-9]{{1,2}}(\\.[0-9]{{1,2}})?$'
          ) AS ds2
    FROM load_data_talons AS t
    WHERE t.goal = '3'
      AND EXTRACT(YEAR FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) = {year}
      AND (
        t.place_service <> '-'
        OR EXISTS (
          SELECT 1 FROM load_data_dn_work_iszl d_full WHERE d_full.enp = t.enp
        )
      )
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
