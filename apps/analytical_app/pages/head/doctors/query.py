from apps.analytical_app.pages.SQL_query.query import base_query

def sql_query_doctors_goal(
    selected_year,
    months_placeholder,
    inogorodniy,
    sanction,
    amount_null,
    goals=None,
    status_list=None,
    with_emd=False
):
    # Сборка базового CTE (report_data, oms и т.д.)
    base = base_query(
        selected_year,
        months_placeholder,
        inogorodniy,
        sanction,
        amount_null,
        status_list=status_list
    )

    # Фильтр по целям, если задан
    filter_goals = ""
    if goals:
        quoted = ", ".join(f"'{g}'" for g in goals)
        filter_goals = f"AND goal IN ({quoted})"

    # Подключение к таблице EMD по source_id → original_epmz_id
    emd_join = ""
    if with_emd:
        emd_join = """
        LEFT JOIN load_data_emd emd
          ON oms.source_id = emd.original_epmz_id
         AND emd.sending_status = 'Документ успешно зарегистрирован'
        """

    return f"""
{base},
pivot AS (
    SELECT
        oms.doctor,
        oms.specialty,
        oms.building,
        oms.department,
        COUNT(*) FILTER (WHERE report_month_number IS NOT NULL)          AS "Итого_талоны",
        {"COUNT(emd.id) FILTER (WHERE report_month_number IS NOT NULL) AS \"Итого_РЭМД\"," if with_emd else "0 AS \"Итого_РЭМД\","}

        COUNT(*) FILTER (WHERE report_month_number = 1)                 AS "Янв_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 1) AS \"Янв_РЭМД\"," if with_emd else "0 AS \"Янв_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 2)                 AS "Фев_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 2) AS \"Фев_РЭМД\"," if with_emd else "0 AS \"Фев_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 3)                 AS "Март_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 3) AS \"Март_РЭМД\"," if with_emd else "0 AS \"Март_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 4)                 AS "Апр_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 4) AS \"Апр_РЭМД\"," if with_emd else "0 AS \"Апр_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 5)                 AS "Май_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 5) AS \"Май_РЭМД\"," if with_emd else "0 AS \"Май_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 6)                 AS "Июн_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 6) AS \"Июн_РЭМД\"," if with_emd else "0 AS \"Июн_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 7)                 AS "Июль_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 7) AS \"Июль_РЭМД\"," if with_emd else "0 AS \"Июль_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 8)                 AS "Авг_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 8) AS \"Авг_РЭМД\"," if with_emd else "0 AS \"Авг_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 9)                 AS "Сен_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 9) AS \"Сен_РЭМД\"," if with_emd else "0 AS \"Сен_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 10)                AS "Окт_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 10) AS \"Окт_РЭМД\"," if with_emd else "0 AS \"Окт_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 11)                AS "Ноя_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 11) AS \"Ноя_РЭМД\"," if with_emd else "0 AS \"Ноя_РЭМД\"," )}

        COUNT(*) FILTER (WHERE report_month_number = 12)                AS "Дек_талоны",
        {("COUNT(emd.id) FILTER (WHERE report_month_number = 12) AS \"Дек_РЭМД\"" if with_emd else "0 AS \"Дек_РЭМД\"")}

    FROM oms
    {emd_join}
    WHERE 1=1
      {filter_goals}
    GROUP BY oms.doctor, oms.specialty, oms.building, oms.department
)
SELECT *
FROM pivot
ORDER BY doctor, specialty, building, department
"""
