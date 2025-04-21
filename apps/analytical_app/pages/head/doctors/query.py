from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms


def sql_query_doctors_goal(selected_year, months_placeholder,
                           inogorodniy, sanction, amount_null,
                           goals=None, status_list=None):
    # Базовый CTE
    base = base_query(
        selected_year, months_placeholder,
        inogorodniy, sanction, amount_null,
        status_list=status_list
    )
    # Фильтр по целям
    filter_goals = ''
    if goals:
        quoted = ", ".join(f"'{g}'" for g in goals)
        filter_goals = f"AND goal IN ({quoted})"

    return f"""
    {base},
    pivot AS (
        SELECT
            doctor,
            specialty,
            building,
            department,
            COUNT(*) FILTER (WHERE report_month_number IS NOT NULL) AS "Итого",
            COUNT(*) FILTER (WHERE report_month_number = 1)  AS "Янв",
            COUNT(*) FILTER (WHERE report_month_number = 2)  AS "Фев",
            COUNT(*) FILTER (WHERE report_month_number = 3)  AS "Март",
            COUNT(*) FILTER (WHERE report_month_number = 4)  AS "Апр",
            COUNT(*) FILTER (WHERE report_month_number = 5)  AS "Май",
            COUNT(*) FILTER (WHERE report_month_number = 6)  AS "Июн",
            COUNT(*) FILTER (WHERE report_month_number = 7)  AS "Июль",
            COUNT(*) FILTER (WHERE report_month_number = 8)  AS "Авг",
            COUNT(*) FILTER (WHERE report_month_number = 9)  AS "Сен",
            COUNT(*) FILTER (WHERE report_month_number = 10) AS "Окт",
            COUNT(*) FILTER (WHERE report_month_number = 11) AS "Ноя",
            COUNT(*) FILTER (WHERE report_month_number = 12) AS "Дек"
        FROM oms
        WHERE 1=1
        {filter_goals}
        GROUP BY doctor, specialty, building, department
    )
    SELECT *
    FROM pivot
    ORDER BY doctor, specialty, building, department;
    """


def sql_query_doctors_goal_with_emd(
    selected_year,
    months_placeholder,
    inogorodniy,
    sanction,
    amount_null,
    goals=None,
    status_list=None
):
    # базовый CTE (report_data, oms и т.д.)
    base = base_query(
        selected_year,
        months_placeholder,
        inogorodniy,
        sanction,
        amount_null,
        status_list=status_list
    )

    # фильтр по целям, если задан
    filter_goals = ""
    if goals:
        quoted = ", ".join(f"'{g}'" for g in goals)
        filter_goals = f"AND goal IN ({quoted})"

    return f"""
{base}
, pivot AS (
    SELECT
        oms.doctor,
        oms.specialty,
        oms.building,
        oms.department,

        COUNT(*) FILTER (WHERE report_month_number IS NOT NULL)        AS "Итого_талоны",
        COUNT(emd.id)   FILTER (WHERE report_month_number IS NOT NULL) AS "Итого_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 1)              AS "Янв_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 1)         AS "Янв_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 2)              AS "Фев_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 2)         AS "Фев_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 3)              AS "Март_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 3)         AS "Март_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 4)              AS "Апр_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 4)         AS "Апр_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 5)              AS "Май_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 5)         AS "Май_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 6)              AS "Июн_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 6)         AS "Июн_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 7)              AS "Июль_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 7)         AS "Июль_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 8)              AS "Авг_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 8)         AS "Авг_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 9)              AS "Сен_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 9)         AS "Сен_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 10)             AS "Окт_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 10)        AS "Окт_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 11)             AS "Ноя_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 11)        AS "Ноя_РЭМД",

        COUNT(*) FILTER (WHERE report_month_number = 12)             AS "Дек_талоны",
        COUNT(emd.id) FILTER (WHERE report_month_number = 12)        AS "Дек_РЭМД"

    FROM oms
    LEFT JOIN load_data_emd emd
      ON oms.source_id = emd.original_epmz_id
     AND emd.sending_status = 'Документ успешно зарегистрирован'
    WHERE 1=1
      {filter_goals}
    GROUP BY
      oms.doctor, oms.specialty, oms.building, oms.department
)
SELECT *
FROM pivot
ORDER BY doctor, specialty, building, department
"""