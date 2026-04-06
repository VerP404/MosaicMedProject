def sql_query_financial_indicators(
    selected_year,
    selected_months=None,
    building_ids=None,
    department_ids=None,
    profile_ids=None,
    inogorodniy='3',
    amount_null='3',
    doctor_ids=None,
    report_type='month',
    input_start=None,
    input_end=None,
    treatment_start=None,
    treatment_end=None,
    status_list=None
):
    """
    SQL-запрос для финансовых показателей по целям и СМО
    """
    # Формируем фильтры по корпусу и отделению
    building_filter = ""
    department_filter = ""
    profile_filter = ""
    doctor_filter = ""
    inogorod_filter = ""
    amount_filter = ""
    report_type_filter = ""
    status_filter = ""
    
    if building_ids:
        building_ids_str = ', '.join(map(str, building_ids))
        building_filter = f"AND building.id IN ({building_ids_str})"
    
    if department_ids:
        department_ids_str = ', '.join(map(str, department_ids))
        department_filter = f"AND department.id IN ({department_ids_str})"

    if profile_ids:
        profile_ids_str = ', '.join(map(str, profile_ids))
        profile_filter = f"AND pd.profile_id IN ({profile_ids_str})"

    if doctor_ids:
        doctor_ids_str = ', '.join(map(str, doctor_ids))
        doctor_filter = f"AND pd.id IN ({doctor_ids_str})"

    if inogorodniy == '1':
        inogorod_filter = "AND report_data.smo_code IN ('36065', '36071', '36079')"
    elif inogorodniy == '2':
        inogorod_filter = "AND report_data.smo_code NOT IN ('36065', '36071', '36079')"

    amount_numeric_expr = (
        "COALESCE(CASE "
        "WHEN report_data.amount ~ '^[0-9]+(\\.[0-9]+)?$' "
        "THEN CAST(report_data.amount AS NUMERIC) "
        "ELSE NULL END, 0)"
    )
    if amount_null == '1':
        amount_filter = f"AND {amount_numeric_expr} <> 0"
    elif amount_null == '2':
        amount_filter = f"AND {amount_numeric_expr} = 0"

    if status_list:
        safe_statuses = [str(s).strip() for s in status_list if str(s).strip().isdigit()]
        if safe_statuses:
            statuses_str = ', '.join(f"'{s}'" for s in safe_statuses)
            status_filter = f"AND report_data.status IN ({statuses_str})"

    if report_type == 'initial_input' and input_start and input_end:
        report_type_filter = (
            "AND report_data.initial_input_date_parsed BETWEEN "
            f"TO_DATE('{input_start}', 'DD-MM-YYYY') AND TO_DATE('{input_end}', 'DD-MM-YYYY')"
        )
    elif report_type == 'treatment' and treatment_start and treatment_end:
        report_type_filter = (
            "AND report_data.treatment_end_date_parsed BETWEEN "
            f"TO_DATE('{treatment_start}', 'DD-MM-YYYY') AND TO_DATE('{treatment_end}', 'DD-MM-YYYY')"
        )
    else:
        selected_month_start = 1
        selected_month_end = 12
        if selected_months and isinstance(selected_months, (list, tuple)) and len(selected_months) == 2:
            selected_month_start = int(selected_months[0])
            selected_month_end = int(selected_months[1])
        report_type_filter = (
            f"AND report_data.report_year = '{selected_year}' "
            f"AND report_data.report_month_number BETWEEN {selected_month_start} AND {selected_month_end}"
        )
    
    # Адаптация вашего рабочего запроса с правильной фильтрацией по месяцам
    query = f"""
    WITH report_data AS (
        SELECT oms.*,
               CASE
                   WHEN oms.report_period = '-' THEN RIGHT(oms.treatment_end, 4)
                   ELSE RIGHT(oms.report_period, 4)
                   END AS report_year,
               CASE
                   WHEN oms.report_period = '-' THEN
                       CASE
                           WHEN EXTRACT(DAY FROM CURRENT_DATE)::INT <= 4 THEN
                               CASE
                                   WHEN TO_NUMBER(SUBSTRING(oms.treatment_end FROM 4 FOR 2), '99') = EXTRACT(MONTH FROM CURRENT_DATE)
                                   THEN EXTRACT(MONTH FROM CURRENT_DATE)::INT
                                   ELSE CASE
                                       WHEN EXTRACT(MONTH FROM CURRENT_DATE)::INT = 1 THEN 12
                                       ELSE EXTRACT(MONTH FROM CURRENT_DATE)::INT - 1
                                       END
                                   END
                           ELSE EXTRACT(MONTH FROM CURRENT_DATE)::INT
                           END
                   ELSE
                       CASE TRIM(SUBSTRING(oms.report_period FROM 1 FOR POSITION(' ' IN oms.report_period) - 1))
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
                   END AS report_month_number,
               CASE
                   WHEN oms.initial_input_date ~ '^\\d{2}-\\d{2}-\\d{4}$'
                       THEN TO_DATE(oms.initial_input_date, 'DD-MM-YYYY')
                   ELSE NULL
               END AS initial_input_date_parsed,
               CASE
                   WHEN oms.treatment_end ~ '^\\d{2}-\\d{2}-\\d{4}$'
                       THEN TO_DATE(oms.treatment_end, 'DD-MM-YYYY')
                   ELSE NULL
               END AS treatment_end_date_parsed
        FROM data_loader_omsdata oms
    ),
    oms_data AS (
        SELECT 
            report_data.goal,
            report_data.smo_code,
            CASE
                WHEN report_data.amount ~ '^[0-9]+(\\.[0-9]+)?$' THEN CAST(report_data.amount AS NUMERIC)
                ELSE NULL
                END AS amount_numeric,
            report_data.status,
            report_data.report_year,
            report_data.report_month_number,
            pd.id as doctor_id,
            department.id as department_id,
            building.id as building_id
        FROM report_data
        LEFT JOIN (
            SELECT DISTINCT ON (doctor_code) * 
            FROM personnel_doctorrecord
            ORDER BY doctor_code, id 
        ) pd ON SUBSTRING(report_data.doctor FROM 1 FOR POSITION(' ' IN report_data.doctor) - 1) = pd.doctor_code
        LEFT JOIN public.organization_department department ON department.id = pd.department_id
        LEFT JOIN public.organization_building building ON building.id = department.building_id
        WHERE 1=1
          {status_filter}
          {report_type_filter}
          {inogorod_filter}
          {building_filter}
          {department_filter}
          {profile_filter}
          {doctor_filter}
          {amount_filter}
    )
    SELECT *
    FROM (
        SELECT
            COALESCE(goal, 'Без цели') AS goal,
            COUNT(*) FILTER (WHERE smo_code IN ('36065', '36071', '36079')) AS count_records,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code IN ('36065', '36071', '36079')), 0) AS total_amount,
            COUNT(*) FILTER (WHERE smo_code = '36065') AS count_inkomed,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code = '36065'), 0) AS sum_inkomed,
            COUNT(*) FILTER (WHERE smo_code IN ('36071', '36079')) AS count_sogaz,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code IN ('36071', '36079')), 0) AS sum_sogaz,
            COUNT(*) FILTER (WHERE smo_code NOT IN ('36065', '36071', '36079')) AS count_inogor,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code NOT IN ('36065', '36071', '36079')), 0) AS sum_inogor
        FROM oms_data
        GROUP BY goal

        UNION ALL

        SELECT
            'Сверхподушевик' AS goal,
            COUNT(*) FILTER (WHERE smo_code IN ('36065', '36071', '36079')) AS count_records,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code IN ('36065', '36071', '36079')), 0) AS total_amount,
            COUNT(*) FILTER (WHERE smo_code = '36065') AS count_inkomed,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code = '36065'), 0) AS sum_inkomed,
            COUNT(*) FILTER (WHERE smo_code IN ('36071', '36079')) AS count_sogaz,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code IN ('36071', '36079')), 0) AS sum_sogaz,
            COUNT(*) FILTER (WHERE smo_code NOT IN ('36065', '36071', '36079')) AS count_inogor,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code NOT IN ('36065', '36071', '36079')), 0) AS sum_inogor
        FROM oms_data
        WHERE goal IN ('ДВ4', 'ДВ2', 'ОПВ', 'ДР1', 'ДР2', 'УД1', 'УД2',
                       'ПН1', 'ДС2', '3', '113', '307', '22', '541',
                       '64', '301', '305', '14', 'В дневном стационаре', 'На дому')

        UNION ALL

        SELECT
            'ИТОГО' AS goal,
            COUNT(*) FILTER (WHERE smo_code IN ('36065', '36071', '36079')) AS count_records,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code IN ('36065', '36071', '36079')), 0) AS total_amount,
            COUNT(*) FILTER (WHERE smo_code = '36065') AS count_inkomed,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code = '36065'), 0) AS sum_inkomed,
            COUNT(*) FILTER (WHERE smo_code IN ('36071', '36079')) AS count_sogaz,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code IN ('36071', '36079')), 0) AS sum_sogaz,
            COUNT(*) FILTER (WHERE smo_code NOT IN ('36065', '36071', '36079')) AS count_inogor,
            COALESCE(SUM(amount_numeric) FILTER (WHERE smo_code NOT IN ('36065', '36071', '36079')), 0) AS sum_inogor
        FROM oms_data
    ) t
    ORDER BY
        CASE
            WHEN goal = 'ИТОГО' THEN 2
            WHEN goal = 'Сверхподушевик' THEN 1
            ELSE 0
        END,
        goal;
    """
    
    return query

