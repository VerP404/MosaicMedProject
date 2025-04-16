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


def sql_query_rep(selected_year, group_id,
                  months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
                  inogorod=None, sanction=None, amount_null=None,
                  building=None, department=None, profile=None, doctor=None,
                  input_start=None, input_end=None, treatment_start=None, treatment_end=None,
                  filter_conditions=None, mode='finance', unique_flag=False):
    """
    Формирует SQL запрос с учетом базовых фильтров и, опционально, рассчета уникальных записей.

    Параметры:
      selected_year: выбранный год
      group_id: идентификатор группы (при необходимости, можно использовать в base_query)
      months_placeholder: строка с номерами месяцев
      inogorod, sanction, amount_null, building, department, profile, doctor,
      input_start, input_end, treatment_start, treatment_end: дополнительные фильтры,
        передаваемые в base_query
      filter_conditions: дополнительные условия для WHERE
      mode: 'finance' или иное – влияет на тип агрегации (суммы или количества)
      unique_flag: если True, происходит выборка уникальных записей с применением оконной функции.

    Возвращает:
      Итоговый SQL запрос (строка)
    """

    # Получаем базовую часть запроса (например, с привязкой к году, периодам и т.п.)
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null,
                      building, department, profile, doctor, input_start, input_end, treatment_start, treatment_end)

    # Формируем базовый набор условий
    where_conditions = [
        "inogorodniy = false",
        "sanctions = '-'",
        "amount_numeric != '0'"
    ]
    if filter_conditions:
        where_conditions.append(filter_conditions)

    # Если есть условия – формируем WHERE-клаузулу
    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

    # В зависимости от режима (finance или нет) выбираем агрегирующие столбцы
    if mode == 'finance':
        agg_columns = f"""
                SUM(CASE WHEN status = '1' THEN amount_numeric END) AS новые,
                SUM(CASE WHEN status = '2' THEN amount_numeric END) AS в_тфомс,
                SUM(CASE WHEN status = '3' THEN amount_numeric END) AS оплачено,
                SUM(CASE WHEN status IN ('5', '7', '12') THEN amount_numeric END) AS отказано,
                SUM(CASE WHEN status IN ('6', '8', '4') THEN amount_numeric END) AS исправлено,
                SUM(CASE WHEN status IN ('0', '13', '17') THEN amount_numeric END) AS отменено
        """
    else:
        agg_columns = f"""
                COUNT(CASE WHEN status = '1' THEN 1 END) AS новые,
                COUNT(CASE WHEN status = '2' THEN 1 END) AS в_тфомс,
                COUNT(CASE WHEN status = '3' THEN 1 END) AS оплачено,
                COUNT(CASE WHEN status IN ('5', '7', '12') THEN 1 END) AS отказано,
                COUNT(CASE WHEN status IN ('6', '8', '4') THEN 1 END) AS исправлено,
                COUNT(CASE WHEN status IN ('0', '13', '17') THEN 1 END) AS отменено
        """

    if unique_flag:
        # Формируем запрос с уникальностью через оконную функцию и CTE
        query = f"""
WITH filtered AS (
    {base}
    SELECT *
    FROM oms
    {where_clause}
),
has_status_3 AS (
    SELECT enp
    FROM filtered
    WHERE status = '3'
    GROUP BY enp
),
prioritized AS (
    SELECT f.*,
           CASE 
             WHEN f.status = '3' THEN 0
             ELSE
               CASE f.status
                 WHEN '2' THEN 1
                 WHEN '4' THEN 2
                 WHEN '6' THEN 3
                 WHEN '8' THEN 4
                 WHEN '1' THEN 5
                 WHEN '5' THEN 6
                 WHEN '7' THEN 7
                 WHEN '12' THEN 8
                 WHEN '13' THEN 9
                 WHEN '17' THEN 10
                 WHEN '0' THEN 11
                 ELSE 99
               END
           END AS status_priority,
           CASE WHEN hs.enp IS NOT NULL THEN true ELSE false END AS has_status_3
    FROM filtered f
    LEFT JOIN has_status_3 hs ON f.enp = hs.enp
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY enp, report_month_number
               ORDER BY 
                   CASE WHEN has_status_3 THEN CASE WHEN status = '3' THEN 0 ELSE 1 END ELSE 0 END,
                   report_month_number,
                   status_priority
           ) AS rn
    FROM prioritized
),
unique_oms AS (
    SELECT *
    FROM ranked
    WHERE rn = 1
)
SELECT report_month_number AS month,
       {agg_columns},
       COUNT(*) AS total_count
FROM unique_oms
GROUP BY month
ORDER BY month;
        """
    else:
        # Стандартный запрос без уникальности
        query = f"""
{base}
SELECT report_month_number AS month,
       {agg_columns},
       COUNT(*) AS total_count
FROM oms
{where_clause}
GROUP BY month
ORDER BY month
        """
    return query

