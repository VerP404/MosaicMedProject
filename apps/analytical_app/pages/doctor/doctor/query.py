from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms


def sql_query_amb_def(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                      department=None,
                      profile=None,
                      doctor=None,
                      input_start=None, input_end=None,
                      treatment_start=None,
                      treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
    SELECT case when target_categories like '%Диспансерное наблюдение%' then 'Диспансерное наблюдение' 
        when target_categories like '%Дневной стационар, Стационар%' then 'Стационар - дневной'
        when target_categories like '%Стационарно, Стационар%' then 'Стационар - стационарно'
        when target_categories like '%Стационар на дому, Стационар%' then 'Стационар - на дому'
    else target_categories end as target_categories,
           {columns_by_status_oms()}
           FROM oms
           WHERE target_categories LIKE any(array['Посещения', 'Обращения', 'Неотложка', '%Диспансерное наблюдение%', 
           '%Стационарно%', '%Дневной стационар%', '%Стационар на дому%',
           'Стоматология'])
           group by target_categories;
    """
    return query


def sql_query_dd_def(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                     department=None,
                     profile=None,
                     doctor=None,
                     input_start=None, input_end=None,
                     treatment_start=None,
                     treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
    SELECT goal,
           {columns_by_status_oms()}
           FROM oms
           group by goal;
    """
    return query


def sql_query_stac_def(months_placeholder):
    return f"""
 SELECT goal,
               COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               sum(case when status = '4' then 1 else 0 end)  as "4",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
        FROM (SELECT *,
                     department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
                     '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
                     CASE
                         WHEN doctor_profile ~ '\\(.*\\)' THEN
                             substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
                         ELSE
                             doctor_profile
                         END AS "Корпус Врач"
              FROM data_loader_omsdata) as oms
        WHERE goal IN ('В дневном стационаре', 'На дому', 'Стационарно')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})
        GROUP BY goal
        ORDER BY CASE goal
                     WHEN 'На дому' THEN 1
                     WHEN 'В дневном стационаре' THEN 2
                     WHEN 'Стационарно' THEN 3
                     END
        """

