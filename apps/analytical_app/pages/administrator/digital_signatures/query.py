from datetime import date


def sql_query_digital_signatures(
    show_only_latest=True,
    show_working_only=True,
    filter_expiring=None,  # None, 'expiring_60', 'expiring_30', 'expiring_7', 'expired', 'all'
    filter_category=None,  # None, 'doctor', 'staff', 'all'
    filter_department_name=None  # None или название подразделения (для структурных подразделений или департментов)
):
    """
    SQL-запрос для получения списка ЭЦП с информацией о сотрудниках
    
    Параметры:
    - show_only_latest: показывать только последние ЭЦП для каждого сотрудника
    - show_working_only: показывать только работающих сотрудников
    - filter_expiring: фильтр по статусу ЭЦП
        - None: все
        - 'expiring_30': заканчиваются в течение 30 дней
        - 'expiring_7': заканчиваются в течение 7 дней
        - 'expired': просроченные
        - 'all': все
    - filter_category: фильтр по категории
        - None или 'all': все
        - 'doctor': только врачи
        - 'staff': только сотрудники
    - filter_department_name: фильтр по названию подразделения (structural_unit или department.name)
    """
    today = date.today()
    
    # Базовый запрос
    query = f"""
    WITH working_persons AS (
        SELECT DISTINCT p.id as person_id
        FROM personnel_person p
        WHERE 1=1
    """
    
    if show_working_only:
        query += """
            AND (
                EXISTS (
                    SELECT 1 
                    FROM personnel_doctorrecord dr
                    WHERE dr.person_id = p.id
                    AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                )
                OR
                EXISTS (
                    SELECT 1 
                    FROM personnel_staffrecord sr
                    WHERE sr.person_id = p.id
                    AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                )
            )
        """
    
    query += """
    ),
    person_categories AS (
        SELECT DISTINCT
            p.id as person_id,
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_doctorrecord dr
                    WHERE dr.person_id = p.id
                    AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                ) AND EXISTS (
                    SELECT 1 
                    FROM personnel_staffrecord sr
                    WHERE sr.person_id = p.id
                    AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                ) THEN 'both'
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_doctorrecord dr
                    WHERE dr.person_id = p.id
                    AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                ) THEN 'doctor'
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_staffrecord sr
                    WHERE sr.person_id = p.id
                    AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                ) THEN 'staff'
                ELSE 'none'
            END as category
        FROM personnel_person p
        WHERE p.id IN (SELECT person_id FROM working_persons)
    ),
    person_departments AS (
        SELECT DISTINCT
            p.id as person_id,
            COALESCE(
                (SELECT dr.structural_unit 
                 FROM personnel_doctorrecord dr
                 WHERE dr.person_id = p.id
                 AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                 ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                 LIMIT 1),
                (SELECT dept.name 
                 FROM personnel_doctorrecord dr
                 INNER JOIN organization_department dept ON dept.id = dr.department_id
                 WHERE dr.person_id = p.id
                 AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                 ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                 LIMIT 1),
                (SELECT dept.name 
                 FROM personnel_staffrecord sr
                 INNER JOIN organization_department dept ON dept.id = sr.department_id
                 WHERE sr.person_id = p.id
                 AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                 ORDER BY sr.end_date DESC NULLS FIRST, sr.start_date DESC
                 LIMIT 1)
            ) as department_name,
            COALESCE(
                (SELECT dept.id 
                 FROM personnel_doctorrecord dr
                 INNER JOIN organization_department dept ON dept.id = dr.department_id
                 WHERE dr.person_id = p.id
                 AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                 ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                 LIMIT 1),
                (SELECT dept.id 
                 FROM personnel_staffrecord sr
                 INNER JOIN organization_department dept ON dept.id = sr.department_id
                 WHERE sr.person_id = p.id
                 AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                 ORDER BY sr.end_date DESC NULLS FIRST, sr.start_date DESC
                 LIMIT 1)
            ) as department_id
        FROM personnel_person p
        WHERE p.id IN (SELECT person_id FROM working_persons)
    ),
    digital_signatures_with_status AS (
        SELECT 
            ds.id,
            ds.person_id,
            p.last_name || ' ' || p.first_name || COALESCE(' ' || p.patronymic, '') as fio,
            p.snils,
            p.inn,
            p.phone_number,
            p.email,
            p.telegram,
            ds.certificate_serial,
            ds.valid_from,
            ds.valid_to,
            ds.issued_date,
            ds.revoked_date,
            ds.application_date,
            ds.scan,
            ds.scan_uploaded_at,
            ds.added_at,
            pos.description as position_name,
            pos.code as position_code,
            ds.position_id,
            COALESCE(pc.category, 'none') as category,
            COALESCE(pd.department_name, '-') as department_name,
            pd.department_id,
            CASE 
                WHEN ds.revoked_date IS NOT NULL THEN 'revoked'
                WHEN ds.valid_to IS NULL THEN 'no_end_date'
                WHEN ds.valid_to < CURRENT_DATE THEN 'expired'
                WHEN ds.valid_to <= CURRENT_DATE + INTERVAL '7 days' THEN 'expiring_7'
                WHEN ds.valid_to <= CURRENT_DATE + INTERVAL '30 days' THEN 'expiring_30'
                WHEN ds.valid_to <= CURRENT_DATE + INTERVAL '60 days' THEN 'expiring_60'
                ELSE 'active'
            END as status,
            CASE
                WHEN ds.scan IS NULL AND ds.application_date IS NULL THEN 'no_actions'
                WHEN ds.scan IS NOT NULL AND ds.application_date IS NULL THEN 'notification_uploaded'
                WHEN ds.application_date IS NOT NULL AND (ds.valid_from IS NULL OR ds.valid_to IS NULL) THEN 'application_created'
                WHEN ds.valid_from IS NOT NULL AND ds.valid_to IS NOT NULL AND ds.valid_from > CURRENT_DATE THEN 'new_certificate_ready'
                WHEN ds.valid_from IS NOT NULL AND ds.valid_to IS NOT NULL AND ds.valid_to >= CURRENT_DATE THEN 'active_certificate'
                ELSE 'no_actions'
            END as process_status,
            CASE 
                WHEN ds.valid_to IS NOT NULL THEN 
                    (ds.valid_to - CURRENT_DATE)::INTEGER
                ELSE NULL
            END as days_until_expiration,
            ROW_NUMBER() OVER (
                PARTITION BY ds.person_id 
                ORDER BY 
                    CASE WHEN ds.revoked_date IS NULL THEN 0 ELSE 1 END,
                    ds.valid_to DESC NULLS LAST,
                    ds.valid_from DESC NULLS LAST,
                    ds.id DESC
            ) as signature_rank,
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_digitalsignature ds2
                    WHERE ds2.person_id = ds.person_id
                    AND ds2.id != ds.id
                    AND (
                        ds2.valid_to > ds.valid_to 
                        OR (ds2.valid_to IS NULL AND ds.valid_to IS NOT NULL)
                        OR (
                            ds2.valid_to = ds.valid_to 
                            AND ds2.valid_from > ds.valid_from
                        )
                        OR (
                            ds2.valid_to = ds.valid_to 
                            AND ds2.valid_from = ds.valid_from
                            AND ds2.id > ds.id
                        )
                    )
                    AND (ds2.revoked_date IS NULL OR ds2.revoked_date > ds.valid_to)
                ) THEN true
                ELSE false
            END as is_replaced
        FROM personnel_digitalsignature ds
        INNER JOIN personnel_person p ON p.id = ds.person_id
        LEFT JOIN personnel_postrg014 pos ON pos.id = ds.position_id
        LEFT JOIN person_categories pc ON pc.person_id = p.id
        LEFT JOIN person_departments pd ON pd.person_id = p.id
        WHERE p.id IN (SELECT person_id FROM working_persons)
    )
    SELECT 
        id,
        person_id,
        fio,
        snils,
        inn,
        phone_number,
        email,
        telegram,
        certificate_serial,
        valid_from,
        valid_to,
        issued_date,
        revoked_date,
        application_date,
        scan,
        scan_uploaded_at,
        added_at,
        position_name,
        position_code,
        position_id,
        category,
        department_name,
        department_id,
        status,
        process_status,
        days_until_expiration,
        signature_rank,
        is_replaced
    FROM digital_signatures_with_status
    WHERE 1=1
    """
    
    # Фильтр по последним ЭЦП
    if show_only_latest:
        query += " AND signature_rank = 1"
    
    # Фильтр по категории
    if filter_category == 'doctor':
        query += " AND (category = 'doctor' OR category = 'both')"
    elif filter_category == 'staff':
        query += " AND (category = 'staff' OR category = 'both')"
    # 'all' или None - показываем все
    
    # Фильтр по подразделению
    if filter_department_name:
        # Экранируем одинарные кавычки в названии для SQL
        escaped_name = filter_department_name.replace("'", "''")
        query += f" AND department_name = '{escaped_name}'"
    
    # Фильтр по статусу
    if filter_expiring == 'expiring_60':
        query += " AND status IN ('expiring_60', 'expiring_30', 'expiring_7')"
    elif filter_expiring == 'expiring_30':
        query += " AND status IN ('expiring_30', 'expiring_7')"
    elif filter_expiring == 'expiring_7':
        query += " AND status = 'expiring_7'"
    elif filter_expiring == 'expired':
        query += " AND status = 'expired'"
    # 'all' или None - показываем все
    
    query += """
    ORDER BY 
        CASE status
            WHEN 'expired' THEN 1
            WHEN 'expiring_7' THEN 2
            WHEN 'expiring_30' THEN 3
            WHEN 'expiring_60' THEN 4
            WHEN 'revoked' THEN 5
            ELSE 6
        END,
        days_until_expiration ASC NULLS LAST,
        fio,
        valid_to DESC NULLS LAST;
    """
    
    return query


def sql_query_doctors_without_signature(
    filter_department_name=None,
):
    """
    Возвращает SQL-запрос, который выбирает активных врачей без каких-либо ЭЦП.
    """

    # Оставлено для совместимости: используем общий запрос по всем категориям
    return sql_query_persons_without_signature(
        filter_department_name=filter_department_name,
        filter_category='doctor',
        show_working_only=True,
    )


def sql_query_persons_without_signature(
    filter_department_name=None,
    filter_category=None,  # None/all, 'doctor', 'staff'
    show_working_only=True,
):
    """
    Возвращает SQL-запрос, который выбирает активных сотрудников (врачей и/или сотрудников)
    без каких-либо ЭЦП.
    """

    query = """
    WITH working_persons AS (
        SELECT DISTINCT p.id as person_id
        FROM personnel_person p
        WHERE 1=1
    """

    if show_working_only:
        query += """
            AND (
                EXISTS (
                    SELECT 1 
                    FROM personnel_doctorrecord dr
                    WHERE dr.person_id = p.id
                    AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                )
                OR
                EXISTS (
                    SELECT 1 
                    FROM personnel_staffrecord sr
                    WHERE sr.person_id = p.id
                    AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                )
            )
        """

    query += """
    ),
    person_categories AS (
        SELECT DISTINCT
            p.id as person_id,
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_doctorrecord dr
                    WHERE dr.person_id = p.id
                    AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                ) AND EXISTS (
                    SELECT 1 
                    FROM personnel_staffrecord sr
                    WHERE sr.person_id = p.id
                    AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                ) THEN 'both'
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_doctorrecord dr
                    WHERE dr.person_id = p.id
                    AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                ) THEN 'doctor'
                WHEN EXISTS (
                    SELECT 1 
                    FROM personnel_staffrecord sr
                    WHERE sr.person_id = p.id
                    AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                ) THEN 'staff'
                ELSE 'none'
            END as category
        FROM personnel_person p
        WHERE p.id IN (SELECT person_id FROM working_persons)
    ),
    person_departments AS (
        SELECT DISTINCT
            p.id as person_id,
            COALESCE(
                (SELECT dr.structural_unit 
                 FROM personnel_doctorrecord dr
                 WHERE dr.person_id = p.id
                 AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                 ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                 LIMIT 1),
                (SELECT dept.name 
                 FROM personnel_doctorrecord dr
                 INNER JOIN organization_department dept ON dept.id = dr.department_id
                 WHERE dr.person_id = p.id
                 AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                 ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                 LIMIT 1),
                (SELECT dept.name 
                 FROM personnel_staffrecord sr
                 INNER JOIN organization_department dept ON dept.id = sr.department_id
                 WHERE sr.person_id = p.id
                 AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                 ORDER BY sr.end_date DESC NULLS FIRST, sr.start_date DESC
                 LIMIT 1)
            ) as department_name,
            COALESCE(
                (SELECT dept.id 
                 FROM personnel_doctorrecord dr
                 INNER JOIN organization_department dept ON dept.id = dr.department_id
                 WHERE dr.person_id = p.id
                 AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                 ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                 LIMIT 1),
                (SELECT dept.id 
                 FROM personnel_staffrecord sr
                 INNER JOIN organization_department dept ON dept.id = sr.department_id
                 WHERE sr.person_id = p.id
                 AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                 ORDER BY sr.end_date DESC NULLS FIRST, sr.start_date DESC
                 LIMIT 1)
            ) as department_id
        FROM personnel_person p
        WHERE p.id IN (SELECT person_id FROM working_persons)
    )
    SELECT
        NULL::integer as id,
        p.id as person_id,
        p.last_name || ' ' || p.first_name || COALESCE(' ' || p.patronymic, '') as fio,
        p.snils,
        p.inn,
        p.phone_number,
        p.email,
        p.telegram,
        NULL::text as certificate_serial,
        NULL::date as valid_from,
        NULL::date as valid_to,
        NULL::date as issued_date,
        NULL::date as revoked_date,
        NULL::date as application_date,
        NULL::text as scan,
        NULL::timestamp as scan_uploaded_at,
        NULL::timestamp as added_at,
        NULL::text as position_name,
        NULL::text as position_code,
        NULL::integer as position_id,
        COALESCE(pc.category, 'none') as category,
        COALESCE(pd.department_name, '-') as department_name,
        pd.department_id,
        'no_signature' as status,
        'no_signature' as process_status,
        NULL::integer as days_until_expiration,
        1 as signature_rank,
        false as is_replaced
    FROM working_persons wp
    INNER JOIN personnel_person p ON p.id = wp.person_id
    LEFT JOIN person_categories pc ON pc.person_id = p.id
    LEFT JOIN person_departments pd ON pd.person_id = p.id
    WHERE NOT EXISTS (
        SELECT 1
        FROM personnel_digitalsignature ds
        WHERE ds.person_id = p.id
    )
    """

    if filter_category == 'doctor':
        query += """
    AND (pc.category = 'doctor' OR pc.category = 'both')
        """
    elif filter_category == 'staff':
        query += """
    AND (pc.category = 'staff' OR pc.category = 'both')
        """

    if filter_department_name:
        escaped_department = filter_department_name.replace("'", "''")
        query += f"\n    AND COALESCE(pd.department_name, '-') = '{escaped_department}'"

    query += "\n    ORDER BY fio"

    return query

