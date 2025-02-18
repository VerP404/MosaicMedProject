import pandas as pd

from apps.analytical_app.pages.SQL_query.query import base_query
from apps.analytical_app.query_executor import engine


# Функция для генерации условий фильтрации на основе планов
def get_filter_conditions(group_ids, year):
    group_ids_str = ", ".join(map(str, group_ids))

    query = f"""
    SELECT field_name, filter_type, values
    FROM plan_filtercondition
    WHERE group_id IN ({group_ids_str}) AND year = {year}
    """
    conditions_df = pd.read_sql(query, engine)

    filter_clauses = []
    for _, row in conditions_df.iterrows():
        field_name = row['field_name']
        filter_type = row['filter_type']
        values = row['values']

        if filter_type == 'in':
            filter_clauses.append(f"{field_name} IN ({values})")
        elif filter_type == 'exact':
            filter_clauses.append(f"{field_name} = {values}")
        elif filter_type == 'like':
            filter_clauses.append(f"{field_name} LIKE {values}")
        elif filter_type == 'not_like':
            filter_clauses.append(f"{field_name} NOT LIKE {values}")

    return " AND ".join(filter_clauses)


def sql_query_rep(selected_year, group_id, months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12', inogorod=None,
                  sanction=None, amount_null=None,
                  building=None, department=None, profile=None, doctor=None, input_start=None, input_end=None,
                  treatment_start=None, treatment_end=None, filter_conditions=None, mode='finance', unique_flag=False):
    # Основной базовый запрос
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor, input_start, input_end, treatment_start, treatment_end)

    # Если включена уникальность, фильтруем данные, но сам запрос не трогаем
    if unique_flag:
        base = f"""
        {base},
        ranked_patients AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY enp, report_month_number 
                    ORDER BY 
                        CASE status 
                            WHEN '3' THEN 1
                            WHEN '2' THEN 2
                            WHEN '4' THEN 3
                            WHEN '6' THEN 4
                            WHEN '8' THEN 5
                            WHEN '1' THEN 6
                            WHEN '5' THEN 7
                            WHEN '7' THEN 8
                            WHEN '12' THEN 9
                            WHEN '13' THEN 10
                            WHEN '17' THEN 11
                            WHEN '0' THEN 12
                            ELSE 99 
                        END
                ) AS rn
            FROM oms
        ),
        oms_unique AS (
            SELECT * FROM ranked_patients WHERE rn = 1
        )
        """

    # Определяем, какую таблицу использовать
    from_table = "oms_unique" if unique_flag else "oms"

    # Начало основного запроса
    if mode == 'finance':
        query = f"""
        {base}
            SELECT
                report_month_number AS month,
                SUM(CASE WHEN status = '1' THEN amount_numeric END) AS новые,
                SUM(CASE WHEN status = '2' THEN amount_numeric END) AS в_тфомс,
                SUM(CASE WHEN status = '3' THEN amount_numeric END) AS оплачено,
                SUM(CASE WHEN status IN ('5', '7', '12') THEN amount_numeric END) AS отказано,
                SUM(CASE WHEN status IN ('6', '8', '4') THEN amount_numeric END) AS исправлено,
                SUM(CASE WHEN status IN ('0', '13', '17') THEN amount_numeric END) AS отменено
            FROM {from_table}
            """
    else:
        query = f"""
        {base}
            SELECT
                report_month_number AS month,
                COUNT(CASE WHEN status = '1' THEN 1 END) AS новые,
                COUNT(CASE WHEN status = '2' THEN 1 END) AS в_тфомс,
                COUNT(CASE WHEN status = '3' THEN 1 END) AS оплачено,
                COUNT(CASE WHEN status IN ('5', '7', '12') THEN 1 END) AS отказано,
                COUNT(CASE WHEN status IN ('6', '8', '4') THEN 1 END) AS исправлено,
                COUNT(CASE WHEN status IN ('0', '13', '17') THEN 1 END) AS отменено
            FROM {from_table}
            
        """

    # Условия WHERE
    where_conditions = [
        "inogorodniy = false",
        "sanctions = '-'",
        "amount_numeric != '0'"
    ]
    if filter_conditions:
        where_conditions.append(filter_conditions)

    # Добавляем условия WHERE в запрос, если они есть
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)

    # Завершаем запрос с группировкой и сортировкой
    query += """
    GROUP BY month
    ORDER BY month
    """

    return query
