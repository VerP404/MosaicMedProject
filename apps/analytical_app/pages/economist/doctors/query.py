# apps/analytical_app/pages/economist/doctors/query.py

from apps.analytical_app.pages.SQL_query.query import base_query


def sql_query_doctors_goal_stat(
    selected_year,
    months_placeholder,
    inogorodniy,
    sanction,
    amount_null,
    group_mapping=None,
    goals=None,
    status_list=None,
    report_type='month',
    input_start=None,
    input_end=None,
    treatment_start=None,
    treatment_end=None,
):
    """
    Отчет по врачам. Периоды (месяцы, даты формирования, даты лечения)
    применяются ТОЛЬКО внутри base_query через переданные параметры.
    Здесь оставляем только фильтрацию по целям и группам.
    """
    base = base_query(
        selected_year,
        months_placeholder or ", ".join(str(m) for m in range(1, 12 + 1)),
        inogorodniy,
        sanction,
        amount_null,
        initial_input_date_start=input_start,
        initial_input_date_end=input_end,
        treatment_start=treatment_start,
        treatment_end=treatment_end,
        status_list=status_list,
    )

    # Фильтр по целям
    goal_filter = ""
    if goals:
        quoted_goals = ", ".join(f"'{g}'" for g in goals)
        goal_filter = f"AND goal IN ({quoted_goals})"

    # Если нет ни целей, ни групп — возвращаем пустую выборку
    if not goals and not group_mapping:
        return f"""
        {base},
        pivot AS (
            SELECT doctor, specialty, building, department
            FROM oms
            WHERE 1=0
        )
        SELECT * FROM pivot;
        """

    # Динамические столбцы для групп
    group_exprs = []
    if group_mapping:
        for grp, items in group_mapping.items():
            if items:
                quoted_items = ", ".join(f"'{i}'" for i in items)
                safe_grp = grp.replace('"', '""')
                group_exprs.append(
                    f"COUNT(*) FILTER (WHERE goal IN ({quoted_items})) AS \"{safe_grp}\""
                )

    # Динамические столбцы для индивидуальных целей
    goal_exprs = []
    if goals:
        for g in goals:
            safe_g = g.replace('"', '""')
            goal_exprs.append(
                f"COUNT(*) FILTER (WHERE goal = '{g}') AS \"{safe_g}\""
            )

    # Итог по индивидуальным целям
    total_expr = ""
    if goal_exprs:
        sum_expr = " + ".join(expr.split(' AS ')[0] for expr in goal_exprs)
        total_expr = f"({sum_expr}) AS \"Итого\""

    all_cols = group_exprs + goal_exprs
    if total_expr:
        all_cols.append(total_expr)
    pivot_cols = ",\n        ".join(all_cols)

    return f"""
        {base},
        pivot AS (
            SELECT
                doctor,
                specialty,
                building,
                department,
            {pivot_cols}
            FROM oms
            WHERE 1=1
              {goal_filter}
            GROUP BY doctor, specialty, building, department
        )
        SELECT * FROM pivot
        ORDER BY doctor, specialty, building, department;
        """


def sql_query_buildings_goal_stat(
    selected_year,
    months_placeholder,
    inogorodniy,
    sanction,
    amount_null,
    group_mapping=None,
    goals=None,
    status_list=None,
    report_type='month',
    input_start=None,
    input_end=None,
    treatment_start=None,
    treatment_end=None,
):
    """
    Отчет по корпусам. Аналогично, периоды применяются внутри base_query.
    """
    base = base_query(
        selected_year,
        months_placeholder or ", ".join(str(m) for m in range(1, 12 + 1)),
        inogorodniy,
        sanction,
        amount_null,
        initial_input_date_start=input_start,
        initial_input_date_end=input_end,
        treatment_start=treatment_start,
        treatment_end=treatment_end,
        status_list=status_list,
    )

    goal_filter = ""
    if goals:
        quoted_goals = ", ".join(f"'{g}'" for g in goals)
        goal_filter = f"AND goal IN ({quoted_goals})"

    if not goals and not group_mapping:
        return f"""
        {base},
        pivot AS (
            SELECT building
            FROM oms
            WHERE 1=0
        )
        SELECT * FROM pivot;
        """

    group_exprs = []
    if group_mapping:
        for grp, items in group_mapping.items():
            if items:
                quoted_items = ", ".join(f"'{i}'" for i in items)
                safe_grp = grp.replace('"', '""')
                group_exprs.append(
                    f"COUNT(*) FILTER (WHERE goal IN ({quoted_items})) AS \"{safe_grp}\""
                )

    goal_exprs = []
    if goals:
        for g in goals:
            safe_g = g.replace('"', '""')
            goal_exprs.append(
                f"COUNT(*) FILTER (WHERE goal = '{g}') AS \"{safe_g}\""
            )

    total_expr = ""
    if goal_exprs:
        sum_expr = " + ".join(expr.split(' AS ')[0] for expr in goal_exprs)
        total_expr = f"({sum_expr}) AS \"Итого\""

    all_cols = group_exprs + goal_exprs
    if total_expr:
        all_cols.append(total_expr)
    pivot_cols = ",\n        ".join(all_cols) if all_cols else "COUNT(*) AS \"Итого\""

    return f"""
        {base},
        pivot AS (
            SELECT
                building,
            {pivot_cols}
            FROM oms
            WHERE 1=1
              {goal_filter}
            GROUP BY building
        )
        SELECT * FROM pivot
        ORDER BY building;
        """