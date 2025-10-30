import pandas as pd
from sqlalchemy import text
from apps.analytical_app.query_executor import engine


def sql_query_financial_indicators(selected_year, selected_month, building_ids=None, department_ids=None):
    """
    SQL-запрос для финансовых показателей по целям и СМО
    """
    # Формируем фильтры по корпусу и отделению
    building_filter = ""
    department_filter = ""
    
    if building_ids:
        building_ids_str = ', '.join(map(str, building_ids))
        building_filter = f"AND building.id IN ({building_ids_str})"
    
    if department_ids:
        department_ids_str = ', '.join(map(str, department_ids))
        department_filter = f"AND department.id IN ({department_ids_str})"
    
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
                   END AS report_month_number
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
        WHERE report_data.status = '3'
          AND report_data.report_year = '{selected_year}'
          AND report_data.report_month_number = {selected_month}
          {building_filter}
          {department_filter}
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

