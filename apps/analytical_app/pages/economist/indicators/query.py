from sqlalchemy import text
from apps.analytical_app.pages.SQL_query.query import base_query
from apps.analytical_app.query_executor import engine


def get_dynamic_conditions(year):
    query = text("""
        SELECT type, field_name, filter_type, values 
        FROM plan_unifiedfilter uf
        JOIN plan_unifiedfiltercondition ufc ON uf.id = ufc.filter_id
        WHERE uf.year = :year
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"year": year}).fetchall()

    conditions = []
    for row in result:
        type, field_name, filter_type, values = row
        if filter_type == 'in':
            clause = f"{field_name} IN ({values})"
        elif filter_type == 'exact':
            clause = f"{field_name} = '{values}'"
        elif filter_type == 'like':
            clause = f"{field_name} LIKE '{values}'"
        elif filter_type == 'not_like':
            clause = f"{field_name} NOT LIKE '{values}'"
        conditions.append((type, clause))

    return conditions


def sql_query_indicators(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                         department=None,
                         profile=None,
                         doctor=None,
                         input_start=None, input_end=None,
                         treatment_start=None,
                         treatment_end=None,
                         status_list=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end, status_list)
    # Получаем динамические условия
    dynamic_conditions = get_dynamic_conditions(selected_year)
    # Создаем список для объединенных запросов
    union_queries = []

    # Группируем условия по типу и объединяем их в один WHERE
    conditions_by_type = {}
    for condition_type, where_clause in dynamic_conditions:
        if condition_type not in conditions_by_type:
            conditions_by_type[condition_type] = []
        conditions_by_type[condition_type].append(where_clause)

    # Создаем запрос для каждого типа, объединяя все условия через AND
    for condition_type, conditions in conditions_by_type.items():
        combined_where_clause = " AND ".join(conditions)
        union_query = f"""
            SELECT '{condition_type}' AS type,
                   COUNT(*) AS "К-во",
                   ROUND(SUM(CAST(amount_numeric AS numeric(10, 2)))::numeric, 2) AS "Сумма"
            FROM oms
            WHERE {combined_where_clause}
            GROUP BY type
            """
        union_queries.append(union_query)

    # Объединяем все запросы через UNION ALL
    final_query = base + " UNION ALL ".join(union_queries)

    return final_query
