from typing import List, Optional


def sql_query_oms_dispensary(
    selected_year: int,
    selected_month: int,
    status_list: List[str]
) -> str:
    """SQL запрос для ОМС диспансеризации"""
    
    if status_list:
        statuses = ', '.join([f"'{s}'" for s in status_list])
        status_filter = f"AND t.status IN ({statuses})"
    else:
        status_filter = ""
    
    return f"""
    SELECT
        t.talon,
        t.source_id,
        t.status,
        t.goal,
        t.patient,
        t.birth_date,
        t.gender,
        t.enp,
        t.treatment_end,
        t.treatment_start,
        CONCAT(
            d.last_name, ' ',
            LEFT(d.first_name, 1), '.',
            LEFT(d.middle_name, 1), '. / ',
            TRIM(regexp_replace(d.medical_profile_code, '\\s*\\(.*?\\)', '', 'g'))
        ) AS doctor,
        t.department,
        REPLACE(CAST(CAST(t.amount AS NUMERIC) AS TEXT), '.', ',') AS amount,
        e.sending_status,
        CASE
            WHEN e.id IS NOT NULL THEN 'Да'
            ELSE 'Нет'
        END AS emd
    FROM load_data_talons t
    LEFT JOIN data_loader_doctordata d
        ON SPLIT_PART(t.doctor, ' ', 1) = d.doctor_code
    LEFT JOIN load_data_emd e
        ON t.id = e.talon_id
    WHERE t.goal IN ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1')
          AND t.report_year = '{selected_year}'
          AND t.report_month = {selected_month}
          AND t.sanctions IN ('0', '-')
          {status_filter}
    ORDER BY t.talon
    """


def sql_query_detailed_dispensary(
    selected_year: int,
    selected_month: int,
    status_list: List[str]
) -> str:
    """SQL запрос для детализации услуг диспансеризации"""
    
    if status_list:
        statuses = ', '.join([f"'{s}'" for s in status_list])
        status_filter = f"AND o.status IN ({statuses})"
    else:
        status_filter = ""
    
    return f"""
    SELECT
        d.talon_number,
        d.talon_type,
        d.gender,
        d.service_name,
        t.department,
        d.doctor_services_code,
        CONCAT(
            doc.last_name, ' ',
            LEFT(doc.first_name, 1), '.',
            LEFT(doc.middle_name, 1), '. / ',
            TRIM(regexp_replace(doc.medical_profile_code, '\\s*\\(.*?\\)', '', 'g'))
        ) AS service_doctor,
        d.service_status,
        e.sending_status,
        CASE WHEN e.id IS NOT NULL THEN 'Да' ELSE 'Нет' END AS emd
    FROM
        load_data_detailed_medical_examination d
        LEFT JOIN data_loader_doctordata doc
            ON d.doctor_services_code = doc.doctor_code
        LEFT JOIN load_data_talons t
            ON d.talon_number = t.talon
        LEFT JOIN load_data_emd e
            ON d.talon_number = (
                SELECT o.talon
                FROM load_data_talons o
                WHERE o.id = e.talon_id
                LIMIT 1
            )
    WHERE
        d.service_status = 'Да'
        AND d.talon_number IN (
            SELECT o.talon
            FROM load_data_talons o
            WHERE o.goal IN ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1')
              AND o.report_year = '{selected_year}'
              AND o.report_month = {selected_month}
              AND o.sanctions IN ('0', '-')
              {status_filter}
        )
    ORDER BY d.talon_number, d.service_name
    """
