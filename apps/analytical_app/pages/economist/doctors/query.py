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
    treatment_end=None
):
    # 1) CTE с базовыми вычислениями
    base = base_query(
        selected_year,
        months_placeholder or ", ".join(str(m) for m in range(1, 13)),
        inogorodniy,
        sanction,
        amount_null,
        status_list=status_list
    )

    # 2) Фильтр по целям
    goal_filter = ""
    if goals:
        quoted_goals = ", ".join(f"'{g}'" for g in goals)
        goal_filter = f"AND goal IN ({quoted_goals})"

    # 3) Фильтр по периоду
    period_filter = ""
    if report_type == 'month' and months_placeholder:
        period_filter = f"AND report_month_number IN ({months_placeholder})"
    elif report_type == 'initial_input' and input_start and input_end:
        period_filter = f"AND initial_input_date BETWEEN '{input_start}' AND '{input_end}'"
    elif report_type == 'treatment' and treatment_start and treatment_end:
        period_filter = f"AND treatment_start BETWEEN '{treatment_start}' AND '{treatment_end}'"

    # 4) Если нет целей и нет групп — пустой результат
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

    # 5) Генерация столбцов для групп
    group_exprs = []
    if group_mapping:
        for grp, items in group_mapping.items():
            if items:
                quoted_items = ", ".join(f"'{i}'" for i in items)
                safe_grp = grp.replace('"', '""')
                group_exprs.append(
                    f"COUNT(*) FILTER (WHERE goal IN ({quoted_items})) AS \"{safe_grp}\""
                )

    # 6) Генерация столбцов для индивидуальных целей
    goal_exprs = []
    if goals:
        for g in goals:
            safe_g = g.replace('"', '""')
            goal_exprs.append(
                f"COUNT(*) FILTER (WHERE goal = '{g}') AS \"{safe_g}\""
            )

    # 7) Итог по индивидуальным целям
    total_expr = ""
    if goal_exprs:
        sum_expr = " + ".join(expr.split(' AS ')[0] for expr in goal_exprs)
        total_expr = f"({sum_expr}) AS \"Итого\""

    # 8) Собираем все столбцы
    all_cols = group_exprs + goal_exprs
    if total_expr:
        all_cols.append(total_expr)
    pivot_cols = ",\n        ".join(all_cols)

    # 9) Собираем финальный SQL
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
              {period_filter}
            GROUP BY doctor, specialty, building, department
        )
        SELECT * FROM pivot
        ORDER BY doctor, specialty, building, department;
        """