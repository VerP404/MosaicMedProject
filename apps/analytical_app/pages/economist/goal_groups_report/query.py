# apps/analytical_app/pages/economist/goal_groups_report/query.py

from apps.analytical_app.pages.SQL_query.query import base_query


def sql_query_goal_groups_report(
    selected_year,
    current_reporting_month,
    group_mapping,
    inogorodniy=None,
    sanction=None,
    show_goals_detail=False,
):
    """
    Отчет по группам целей, подразделениям и месяцам.
    Для текущего отчетного месяца фильтр по статусу 2,3
    Для всех предыдущих месяцев фильтр по статусу 3
    """
    
    # Формируем список месяцев от 1 до текущего отчетного месяца
    months_list = list(range(1, current_reporting_month + 1))
    months_placeholder = ", ".join(str(m) for m in months_list)
    
    # Формируем условия для групп целей
    goal_conditions = []
    all_goals = []
    for group_name, goals in group_mapping.items():
        if goals:
            quoted_goals = ", ".join(f"'{g}'" for g in goals)
            goal_conditions.append(f"goal IN ({quoted_goals})")
            all_goals.extend(goals)
    
    if not goal_conditions:
        return """
        SELECT 
            'Нет данных' AS group_name,
            'Нет данных' AS building,
            0 AS "Январь", 0 AS "Февраль", 0 AS "Март", 0 AS "Апрель",
            0 AS "Май", 0 AS "Июнь", 0 AS "Июль", 0 AS "Август",
            0 AS "Сентябрь", 0 AS "Октябрь", 0 AS "Ноябрь", 0 AS "Декабрь",
            0 AS "Общий итог"
        WHERE 1=0
        """
    
    goal_filter = " OR ".join(goal_conditions)
    
    # Базовый запрос без фильтрации по статусам (добавим позже)
    # base_query требует строку для months, а не список
    base = base_query(
        selected_year,
        months_placeholder,
        inogorodniy=inogorodniy,
        sanction=sanction,
        amount_null=None,
        initial_input_date_start=None,
        initial_input_date_end=None,
        treatment_start=None,
        treatment_end=None,
        status_list=None,  # Не передаем статусы в base_query, фильтруем отдельно
    )
    
    # Формируем столбцы для месяцев
    month_columns = []
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
        7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    for month in range(1, 13):
        month_name = month_names[month]
        if month <= current_reporting_month:
            # Для текущего месяца фильтр по статусу 2,3, для предыдущих - 3
            if month == current_reporting_month:
                status_filter = "status IN ('2', '3')"
            else:
                status_filter = "status = '3'"
            
            month_columns.append(
                f"COUNT(*) FILTER (WHERE report_month_number = {month} AND {status_filter}) AS \"{month_name}\""
            )
        else:
            # Для будущих месяцев - 0
            month_columns.append(f"0 AS \"{month_name}\"")
    
    month_cols_str = ",\n                ".join(month_columns)
    
    # Формируем итоговую колонку
    total_parts = []
    for month in range(1, current_reporting_month + 1):
        if month == current_reporting_month:
            status_filter = "status IN ('2', '3')"
        else:
            status_filter = "status = '3'"
        total_parts.append(
            f"COUNT(*) FILTER (WHERE report_month_number = {month} AND {status_filter})"
        )
    
    total_expr = " + ".join(total_parts) if total_parts else "0"
    
    # Формируем CASE для определения группы целей
    group_case_parts = []
    for group_name, goals in group_mapping.items():
        if goals:
            quoted_goals = ", ".join(f"'{g}'" for g in goals)
            safe_group_name = group_name.replace("'", "''")
            group_case_parts.append(f"WHEN goal IN ({quoted_goals}) THEN '{safe_group_name}'")
    
    group_case = "\n                    ".join(group_case_parts)
    if not group_case:
        group_case = "ELSE 'Прочее'"
    else:
        group_case += "\n                    ELSE 'Прочее'"
    
    # Формируем запрос с группировкой по группам целей и подразделениям
    if show_goals_detail:
        # Детализация по целям внутри групп
        return f"""
            {base},
            filtered_oms AS (
                SELECT *
                FROM oms
                WHERE ({goal_filter})
            ),
            grouped_data AS (
                SELECT
                    CASE
                        {group_case}
                    END AS group_name,
                    goal,
                    building,
                    {month_cols_str},
                    ({total_expr}) AS "Общий итог"
                FROM filtered_oms
                WHERE building IS NOT NULL
                GROUP BY 
                    CASE
                        {group_case}
                    END,
                    goal,
                    building
            )
            SELECT * FROM grouped_data
            ORDER BY group_name, goal, building
        """
    else:
        # Без детализации по целям
        return f"""
            {base},
            filtered_oms AS (
                SELECT *
                FROM oms
                WHERE ({goal_filter})
            ),
            grouped_data AS (
                SELECT
                    CASE
                        {group_case}
                    END AS group_name,
                    building,
                    {month_cols_str},
                    ({total_expr}) AS "Общий итог"
                FROM filtered_oms
                WHERE building IS NOT NULL
                GROUP BY 
                    CASE
                        {group_case}
                    END,
                    building
            )
            SELECT * FROM grouped_data
            ORDER BY group_name, building
        """

