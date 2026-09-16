# apps/analytical_app/pages/economist/doctors/query.py

from apps.analytical_app.pages.SQL_query.query import base_query


def _match_filter(match_mode: str) -> str:
    if match_mode == "matched":
        return "AND doctor_id IS NOT NULL"
    if match_mode == "unmatched":
        return "AND doctor_id IS NULL"
    return ""


def _doctor_display_expr(match_mode: str) -> str:
    """Для несопоставленных показываем строку из ОМС вместо «..» из CONCAT."""
    if match_mode == "unmatched":
        return """CASE
                    WHEN NULLIF(TRIM(COALESCE(doctor_oms, '')), '') IS NOT NULL
                    THEN doctor_oms
                    ELSE 'Не в справочнике'
                  END"""
    return """CASE
                WHEN doctor_id IS NULL THEN
                    COALESCE(
                        NULLIF(TRIM(COALESCE(doctor_oms, '')), ''),
                        'Не в справочнике'
                    )
                ELSE doctor
              END"""


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
    match_mode='all',
):
    """
    Отчет по врачам. Периоды (месяцы, даты формирования, даты лечения)
    применяются ТОЛЬКО внутри base_query через переданные параметры.
    Здесь оставляем только фильтрацию по целям и группам.

    match_mode: all | matched | unmatched — сопоставление со справочником personnel.
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

    match_sql = _match_filter(match_mode)
    doctor_expr = _doctor_display_expr(match_mode)

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
    pivot_cols = ",\n        ".join(all_cols)

    code_col = ""
    code_group = ""
    if match_mode == "unmatched":
        code_col = "NULLIF(TRIM(COALESCE(doctor_code, '')), '') AS doctor_code,"
        code_group = "NULLIF(TRIM(COALESCE(doctor_code, '')), ''),"

    return f"""
        {base},
        pivot AS (
            SELECT
                {code_col}
                {doctor_expr} AS doctor,
                specialty,
                building,
                department,
            {pivot_cols}
            FROM oms
            WHERE 1=1
              {goal_filter}
              {match_sql}
            GROUP BY
                {code_group}
                {doctor_expr},
                specialty, building, department
        )
        SELECT * FROM pivot
        ORDER BY doctor, specialty, building, department;
        """


def sql_query_unmatched_doctors(
    selected_year,
    months_placeholder,
    inogorodniy,
    sanction,
    amount_null,
    goals=None,
    status_list=None,
    input_start=None,
    input_end=None,
    treatment_start=None,
    treatment_end=None,
):
    """
    Список кодов врачей из талонов, которых нет в personnel_doctorrecord
    (doctor_id IS NULL после join в base_query).
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

    return f"""
        {base}
        SELECT
            COALESCE(NULLIF(TRIM(doctor_code), ''), '—') AS "Код врача",
            COALESCE(
                NULLIF(TRIM(MAX(doctor_oms)), ''),
                '—'
            ) AS "ФИО из талона (ОМС)",
            COUNT(*) AS "Талонов",
            COUNT(DISTINCT goal) AS "Разных целей",
            STRING_AGG(DISTINCT goal, ', ' ORDER BY goal) AS "Цели"
        FROM oms
        WHERE doctor_id IS NULL
          {goal_filter}
        GROUP BY NULLIF(TRIM(doctor_code), '')
        ORDER BY COUNT(*) DESC, "Код врача";
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
