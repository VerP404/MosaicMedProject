def sql_dn_job_disp(year: int) -> str:
    return f"""
WITH disp_raw AS (
    SELECT
        x.enp,
        x.external_id,
        x.mo_prikreplenia,
        x.org_prof_m,
        TRIM(UPPER(x.fio)) AS fio_norm,
        TO_TIMESTAMP(x.dr, 'DD.MM.YYYY HH24:MI:SS') AS dr_ts,
        TO_TIMESTAMP(x.date, 'DD.MM.YYYY HH24:MI:SS') AS disp_ts,
        UPPER(x.ds) AS ds_norm
    FROM load_data_dn_work_iszl AS x
    WHERE EXTRACT(YEAR FROM TO_TIMESTAMP(x.date, 'DD.MM.YYYY HH24:MI:SS')) = {int(year)}
)
SELECT
    enp,
    external_id,
    mo_prikreplenia,
    org_prof_m,
    fio_norm,
    TO_CHAR(dr_ts, 'DD-MM-YYYY') AS dr_norm,
    ds_norm,
    EXTRACT(MONTH FROM disp_ts) AS month_d,
    EXTRACT(YEAR FROM disp_ts) AS year_d,
    TO_CHAR(disp_ts, 'DD-MM-YYYY') AS disp_date,
    CASE
        WHEN ROW_NUMBER() OVER (
            PARTITION BY enp, ds_norm, EXTRACT(YEAR FROM disp_ts)
            ORDER BY external_id
        ) = 1 THEN FALSE
        ELSE TRUE
    END AS duplicate
FROM disp_raw
"""


def sql_dn_job_tal(year: int) -> str:
    year = int(year)
    return f"""
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
    EXTRACT(YEAR FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) AS year_end,
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
  AND (
        (t.report_year ~ '^[0-9]+$' AND t.report_year::int = {year})
        OR (
            COALESCE(NULLIF(t.report_year, '-'), '') !~ '^[0-9]+$'
            AND EXTRACT(YEAR FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) = {year}
        )
      )
  AND (
        t.place_service <> '-'
        OR EXISTS (
            SELECT 1
            FROM load_data_dn_work_iszl d
            WHERE d.enp = t.enp
              AND EXTRACT(YEAR FROM TO_TIMESTAMP(d.date, 'DD.MM.YYYY HH24:MI:SS')) = {year}
        )
      )
"""


def sql_dn_job_orgs(year: int) -> str:
    return f"""
SELECT DISTINCT org_prof_m
FROM load_data_dn_work_iszl
WHERE org_prof_m IS NOT NULL
  AND org_prof_m <> ''
  AND EXTRACT(YEAR FROM TO_TIMESTAMP(date, 'DD.MM.YYYY HH24:MI:SS')) = {int(year)}
ORDER BY org_prof_m
"""


def sql_dn_job_coverage(year: int) -> str:
    year = int(year)
    return f"""
WITH tal_year AS (
    SELECT
        enp,
        place_service,
        status,
        gender,
        {year} - EXTRACT(YEAR FROM to_date(birth_date, 'DD-MM-YYYY')) AS age
    FROM load_data_talons
    WHERE goal = '3'
      AND (
            (report_year ~ '^[0-9]+$' AND report_year::int = {year})
            OR (
                COALESCE(NULLIF(report_year, '-'), '') !~ '^[0-9]+$'
                AND EXTRACT(YEAR FROM TO_DATE(treatment_end, 'DD-MM-YYYY')) = {year}
            )
          )
),
iszl AS (
    SELECT COUNT(DISTINCT enp) AS cnt
    FROM load_data_dn_work_iszl
    WHERE EXTRACT(YEAR FROM TO_TIMESTAMP(date, 'DD.MM.YYYY HH24:MI:SS')) = {year}
)
SELECT
    (SELECT COUNT(DISTINCT enp) FROM tal_year
     WHERE (gender = 'М' AND age < 65) OR (gender = 'Ж' AND age < 60)) AS cov_count,
    (SELECT cnt FROM iszl) AS iszl_count,
    (SELECT COUNT(DISTINCT enp) FROM tal_year WHERE place_service = '17') AS work_count,
    (SELECT COUNT(DISTINCT enp) FROM tal_year WHERE place_service = '17' AND status = '3') AS work_paid_count
"""


def sql_head_dn_job_nested(year: int) -> str:
    """Совместимость: плоский join для отчётов, если нужен напрямую."""
    return f"""
WITH
  disp AS ({sql_dn_job_disp(year)}),
  tal AS ({sql_dn_job_tal(year)})
SELECT
  COALESCE(t.enp, d.enp) AS enp,
  INITCAP(LOWER(COALESCE(t.patient, d.fio_norm))) AS patient,
  COALESCE(t.birth_date, d.dr_norm) AS birth_date,
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
  d.ds_norm,
  d.disp_date,
  d.month_d,
  d.year_d,
  d.duplicate
FROM tal AS t
FULL JOIN disp AS d
  ON d.enp = t.enp
     AND d.month_d = t.month_end
     AND d.year_d = t.year_end
     AND (
       d.ds_norm = t.ds1
       OR d.ds_norm = ANY(t.ds2)
     )
ORDER BY enp,
         COALESCE(t.treatment_end::date, TO_DATE(d.disp_date, 'DD-MM-YYYY'))
"""
