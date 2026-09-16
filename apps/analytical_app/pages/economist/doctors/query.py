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
    Отчет по врачам. Период:
    - month — отчётный год/месяцы;
    - initial_input / treatment — только даты (без фильтра по отчётному месяцу),
      через base_query.
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


def _sql_quote(value) -> str:
    if value is None:
        return ""
    return str(value).replace("'", "''")


def sql_query_doctors_goal_details(
    selected_year,
    months_placeholder,
    inogorodniy,
    sanction,
    amount_null,
    detail_goals=None,
    status_list=None,
    input_start=None,
    input_end=None,
    treatment_start=None,
    treatment_end=None,
    match_mode="all",
    doctor=None,
    specialty=None,
    building=None,
    department=None,
    doctor_code=None,
):
    """
    Детализация талонов по строке врача и выбранной цели/группе целей.
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

    match_sql = _match_filter(match_mode)
    doctor_expr = _doctor_display_expr(match_mode)

    conditions = []
    if match_sql:
        conditions.append(match_sql.replace("AND ", "", 1).strip())

    if detail_goals:
        quoted = ", ".join(f"'{_sql_quote(g)}'" for g in detail_goals)
        conditions.append(f"goal IN ({quoted})")

    # Сопоставление строки сводки
    conditions.append(f"COALESCE(({doctor_expr}), '') = '{_sql_quote(doctor)}'")
    conditions.append(f"COALESCE(specialty, '') = '{_sql_quote(specialty)}'")
    conditions.append(f"COALESCE(building, '') = '{_sql_quote(building)}'")
    conditions.append(f"COALESCE(department, '') = '{_sql_quote(department)}'")
    if doctor_code is not None and str(doctor_code).strip() != "":
        conditions.append(
            f"COALESCE(NULLIF(TRIM(doctor_code), ''), '') = '{_sql_quote(doctor_code)}'"
        )

    where_sql = " AND ".join(conditions) if conditions else "1=1"
    return f"""
        {base}
        SELECT
            talon AS "Талон",
            goal AS "Цель",
            status AS "Статус",
            enp AS "ЕНП",
            patient AS "Пациент",
            birth_date AS "Дата рождения",
            treatment_start AS "Дата начала",
            treatment_end AS "Дата окончания",
            gender AS "Пол",
            ({doctor_expr}) AS "Врач",
            specialty AS "Специальность",
            building AS "Корпус",
            department AS "Отделение",
            report_month AS "Отчетный месяц",
            amount_numeric AS "Сумма",
            initial_input_date AS "Дата формирования",
            account_number AS "Номер счета"
        FROM oms
        WHERE {where_sql}
        ORDER BY talon;
        """
