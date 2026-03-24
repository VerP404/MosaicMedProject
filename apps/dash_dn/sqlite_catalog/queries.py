from __future__ import annotations

from sqlalchemy import bindparam, text


SPECIALTIES_OPTIONS_SQL = text(
    """
    SELECT DISTINCT s.name AS value, s.name AS label
    FROM dn_specialty s
    JOIN dn_service_requirement sr
      ON sr.specialty_id = s.id AND sr.catalog = :catalog AND sr.is_required = 1
    WHERE s.catalog = :catalog AND s.is_active = 1
    ORDER BY s.name
    """
)


DIAGNOSES_OPTIONS_SQL = text(
    """
    SELECT DISTINCT
        d.code AS value,
        d.code || COALESCE(' [' || c.name || ']', '') AS label
    FROM dn_diagnosis d
    LEFT JOIN dn_diagnosis_category c
      ON c.id = d.category_id AND c.catalog = :catalog
    WHERE d.catalog = :catalog AND d.is_active = 1
    ORDER BY d.code
    """
)


SPECIALTIES_FOR_DIAGNOSIS_SQL = text(
    """
    SELECT DISTINCT s.name AS value, s.name AS label
    FROM dn_diagnosis_specialty ds
    JOIN dn_specialty s ON s.id = ds.specialty_id AND s.catalog = :catalog
    JOIN dn_diagnosis d ON d.id = ds.diagnosis_id AND d.catalog = :catalog
    JOIN dn_diagnosis_group_membership gm
      ON gm.diagnosis_id = d.id AND gm.catalog = :catalog AND gm.is_active = 1
    JOIN dn_service_requirement sr
      ON sr.group_id = gm.group_id AND sr.catalog = :catalog
     AND sr.specialty_id = s.id AND sr.is_required = 1
    WHERE d.code = :diagnosis_code AND s.is_active = 1 AND d.is_active = 1
    ORDER BY s.name
    """
)


DIAGNOSES_FOR_SPECIALTY_SQL = text(
    """
    SELECT DISTINCT
        d.code AS value,
        d.code || COALESCE(' [' || c.name || ']', '') AS label
    FROM dn_diagnosis_specialty ds
    JOIN dn_specialty s ON s.id = ds.specialty_id AND s.catalog = :catalog
    JOIN dn_diagnosis d ON d.id = ds.diagnosis_id AND d.catalog = :catalog
    LEFT JOIN dn_diagnosis_category c
      ON c.id = d.category_id AND c.catalog = :catalog
    JOIN dn_diagnosis_group_membership gm
      ON gm.diagnosis_id = d.id AND gm.catalog = :catalog AND gm.is_active = 1
    JOIN dn_service_requirement sr
      ON sr.group_id = gm.group_id AND sr.catalog = :catalog
     AND sr.specialty_id = s.id AND sr.is_required = 1
    WHERE s.name = :specialty_name AND s.is_active = 1 AND d.is_active = 1
    ORDER BY d.code
    """
)


SERVICES_FOR_DIAGNOSES_FLAT_SQL = text(
    """
    WITH actual_prices AS (
        SELECT sp.service_id, sp.price,
               ROW_NUMBER() OVER (
                   PARTITION BY sp.service_id
                   ORDER BY pp.date_start DESC, pp.id DESC
               ) AS rn
        FROM dn_service_price sp
        JOIN dn_service_price_period pp ON pp.id = sp.period_id AND pp.catalog = :catalog
        WHERE date(pp.date_start) <= date('now')
          AND (pp.date_end IS NULL OR date(pp.date_end) >= date('now'))
    )
    SELECT
        srv.code AS code,
        srv.name AS name,
        ap.price AS price,
        d.code AS diagnosis_code,
        grp.title AS group_title
    FROM dn_service_requirement sr
    JOIN dn_service srv ON srv.id = sr.service_id AND srv.catalog = :catalog
    LEFT JOIN actual_prices ap ON ap.service_id = srv.id AND ap.rn = 1
    JOIN dn_diagnosis_group grp ON grp.id = sr.group_id AND grp.catalog = :catalog
    JOIN dn_diagnosis_group_membership gm
      ON gm.group_id = grp.id AND gm.catalog = :catalog AND gm.is_active = 1
    JOIN dn_diagnosis d ON d.id = gm.diagnosis_id AND d.catalog = :catalog
    JOIN dn_specialty s ON s.id = sr.specialty_id AND s.catalog = :catalog
    WHERE s.name = :specialty_name
      AND d.code IN :diagnosis_codes
      AND sr.is_required = 1
      AND srv.is_active = 1
      AND sr.catalog = :catalog
    ORDER BY srv.name, srv.code, d.code
    """
).bindparams(bindparam("diagnosis_codes", expanding=True))


SERVICES_CATALOG_LIST_WITH_PRICE_SQL = text(
    """
    WITH actual_prices AS (
        SELECT sp.service_id, sp.price,
               ROW_NUMBER() OVER (
                   PARTITION BY sp.service_id
                   ORDER BY pp.date_start DESC, pp.id DESC
               ) AS rn
        FROM dn_service_price sp
        JOIN dn_service_price_period pp ON pp.id = sp.period_id AND pp.catalog = :catalog
        WHERE date(pp.date_start) <= date('now')
          AND (pp.date_end IS NULL OR date(pp.date_end) >= date('now'))
    )
    SELECT srv.id, srv.code, srv.name, ap.price
    FROM dn_service srv
    LEFT JOIN actual_prices ap ON ap.service_id = srv.id AND ap.rn = 1
    WHERE srv.catalog = :catalog AND srv.is_active = 1
    ORDER BY srv.code
    """
)


SERVICE_CODE_PRICE_BY_ID_SQL = text(
    """
    WITH actual_prices AS (
        SELECT sp.service_id, sp.price,
               ROW_NUMBER() OVER (
                   PARTITION BY sp.service_id
                   ORDER BY pp.date_start DESC, pp.id DESC
               ) AS rn
        FROM dn_service_price sp
        JOIN dn_service_price_period pp ON pp.id = sp.period_id AND pp.catalog = :catalog
        WHERE date(pp.date_start) <= date('now')
          AND (pp.date_end IS NULL OR date(pp.date_end) >= date('now'))
    )
    SELECT srv.code, ap.price
    FROM dn_service srv
    LEFT JOIN actual_prices ap ON ap.service_id = srv.id AND ap.rn = 1
    WHERE srv.id = :service_id AND srv.catalog = :catalog
    """
)
