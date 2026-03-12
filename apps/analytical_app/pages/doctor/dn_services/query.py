from sqlalchemy import bindparam, text


def specialties_options_query():
    return text(
        """
        SELECT DISTINCT
            s.name AS value,
            s.name AS label
        FROM dn_reference_dnspecialty s
        JOIN dn_reference_dnservicerequirement sr
            ON sr.specialty_id = s.id
           AND sr.is_required = TRUE
        WHERE s.is_active = TRUE
        ORDER BY s.name
        """
    )


def diagnoses_options_query():
    return text(
        """
        SELECT DISTINCT
            d.code AS value,
            d.code || COALESCE(' [' || c.name || ']', '') AS label
        FROM dn_reference_dndiagnosis d
        LEFT JOIN dn_reference_dndiagnosiscategory c
            ON c.id = d.category_id
        WHERE d.is_active = TRUE
        ORDER BY d.code
        """
    )


def specialties_for_diagnosis_query():
    return text(
        """
        SELECT DISTINCT
            s.name AS value,
            s.name AS label
        FROM dn_reference_dndiagnosisspecialty ds
        JOIN dn_reference_dnspecialty s
            ON s.id = ds.specialty_id
        JOIN dn_reference_dndiagnosis d
            ON d.id = ds.diagnosis_id
        JOIN dn_reference_dndiagnosisgroupmembership gm
            ON gm.diagnosis_id = d.id AND gm.is_active = TRUE
        JOIN dn_reference_dnservicerequirement sr
            ON sr.group_id = gm.group_id
           AND sr.specialty_id = s.id
           AND sr.is_required = TRUE
        WHERE d.code = :diagnosis_code
          AND s.is_active = TRUE
          AND d.is_active = TRUE
        ORDER BY s.name
        """
    )


def diagnoses_for_specialty_query():
    return text(
        """
        SELECT DISTINCT
            d.code AS value,
            d.code || COALESCE(' [' || c.name || ']', '') AS label
        FROM dn_reference_dndiagnosisspecialty ds
        JOIN dn_reference_dnspecialty s
            ON s.id = ds.specialty_id
        JOIN dn_reference_dndiagnosis d
            ON d.id = ds.diagnosis_id
        LEFT JOIN dn_reference_dndiagnosiscategory c
            ON c.id = d.category_id
        JOIN dn_reference_dndiagnosisgroupmembership gm
            ON gm.diagnosis_id = d.id AND gm.is_active = TRUE
        JOIN dn_reference_dnservicerequirement sr
            ON sr.group_id = gm.group_id
           AND sr.specialty_id = s.id
           AND sr.is_required = TRUE
        WHERE s.name = :specialty_name
          AND s.is_active = TRUE
          AND d.is_active = TRUE
        ORDER BY d.code
        """
    )


def services_for_diagnoses_query():
    return text(
        """
        WITH actual_prices AS (
            SELECT
                sp.service_id,
                sp.price,
                ROW_NUMBER() OVER (
                    PARTITION BY sp.service_id
                    ORDER BY pp.date_start DESC, pp.id DESC
                ) AS rn
            FROM dn_reference_dnserviceprice sp
            JOIN dn_reference_dnservicepriceperiod pp
                ON pp.id = sp.period_id
            WHERE pp.date_start <= CURRENT_DATE
              AND (pp.date_end IS NULL OR pp.date_end >= CURRENT_DATE)
        )
        SELECT
            srv.code AS "Код услуги",
            srv.name AS "Наименование услуги",
            ap.price AS "Актуальная стоимость",
            STRING_AGG(DISTINCT d.code, ', ' ORDER BY d.code) AS "Диагнозы",
            STRING_AGG(DISTINCT grp.title, '; ' ORDER BY grp.title) AS "Группы диагнозов"
        FROM dn_reference_dnservicerequirement sr
        JOIN dn_reference_dnservice srv
            ON srv.id = sr.service_id
        LEFT JOIN actual_prices ap
            ON ap.service_id = srv.id
           AND ap.rn = 1
        JOIN dn_reference_dndiagnosisgroup grp
            ON grp.id = sr.group_id
        JOIN dn_reference_dndiagnosisgroupmembership gm
            ON gm.group_id = grp.id AND gm.is_active = TRUE
        JOIN dn_reference_dndiagnosis d
            ON d.id = gm.diagnosis_id
        JOIN dn_reference_dnspecialty s
            ON s.id = sr.specialty_id
        WHERE s.name = :specialty_name
          AND d.code IN :diagnosis_codes
          AND sr.is_required = TRUE
          AND srv.is_active = TRUE
        GROUP BY srv.code, srv.name, ap.price
        ORDER BY srv.name, srv.code
        """
    ).bindparams(bindparam("diagnosis_codes", expanding=True))

