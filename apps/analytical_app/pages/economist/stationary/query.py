def sql_query_stac(sql_cond, selected_year, selected_buildings):
    # Включаем фильтрацию по выбранным корпусам
    building_filter = " AND ob.name_kvazar IN :building_list"

    dynamic_columns = []
    dynamic_column_names = []
    dynamic_column_sums = []

    # Генерация столбцов только для выбранных корпусов
    for building in selected_buildings:
        dynamic_columns.append(
            f"SUM(CASE WHEN ob.name_kvazar = '{building}' AND dlo.gender = 'М' THEN 1 ELSE 0 END) AS \"М {building}\"")
        dynamic_columns.append(
            f"ROUND(SUM(CASE WHEN ob.name_kvazar = '{building}' AND dlo.gender = 'М' THEN ROUND(CAST(dlo.amount AS numeric(15, 2)):: numeric, 2) ELSE 0 END):: numeric, 2) AS \"М {building} Сумма\"")
        dynamic_columns.append(
            f"SUM(CASE WHEN ob.name_kvazar = '{building}' AND dlo.gender = 'Ж' THEN 1 ELSE 0 END) AS \"Ж {building}\"")
        dynamic_columns.append(
            f"ROUND(SUM(CASE WHEN ob.name_kvazar = '{building}' AND dlo.gender = 'Ж' THEN ROUND(CAST(dlo.amount AS numeric(15, 2)):: numeric, 2) ELSE 0 END):: numeric, 2) AS \"Ж {building} Сумма\"")

        dynamic_column_names.append(f"\"М {building}\"")
        dynamic_column_names.append(f"\"М {building} Сумма\"")
        dynamic_column_names.append(f"\"Ж {building}\"")
        dynamic_column_names.append(f"\"Ж {building} Сумма\"")

        dynamic_column_sums.append(f"SUM(\"М {building}\")")
        dynamic_column_sums.append(f"SUM(\"М {building} Сумма\")")
        dynamic_column_sums.append(f"SUM(\"Ж {building}\")")
        dynamic_column_sums.append(f"SUM(\"Ж {building} Сумма\")")

    dynamic_columns_sql = ',\n    '.join(dynamic_columns)
    dynamic_column_names_sql = ',\n       '.join(dynamic_column_names)
    dynamic_column_sums_sql = ',\n       '.join(dynamic_column_sums)

    query = f"""
    WITH data AS (
        SELECT
            ksg,
            COUNT(*) AS "Всего",
            ROUND(SUM(CAST(dlo.amount AS numeric(15, 2))):: numeric, 2) AS "Сумма",
            SUM(CASE WHEN dlo.gender = 'М' THEN 1 ELSE 0 END) AS "М",
            ROUND(SUM(CASE WHEN dlo.gender = 'М' THEN ROUND(CAST(dlo.amount AS numeric(15, 2)):: numeric, 2) ELSE 0 END):: numeric, 2) AS "М Сумма",
            SUM(CASE WHEN dlo.gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж",
            ROUND(SUM(CASE WHEN dlo.gender = 'Ж' THEN ROUND(CAST(dlo.amount AS numeric(15, 2)):: numeric, 2) ELSE 0 END):: numeric, 2) AS "Ж Сумма",
            {dynamic_columns_sql}  
        FROM
            data_loader_omsdata dlo
        JOIN
            personnel_doctorrecord pd
            ON SUBSTRING(dlo.doctor, 1, POSITION(' ' IN dlo.doctor) - 1) = pd.doctor_code
        JOIN
            personnel_person pp
            ON pd.person_id = pp.id
        JOIN
            organization_department od
            ON pd.department_id = od.id
        JOIN
            organization_building ob
            ON od.building_id = ob.id
        WHERE
            report_period IN ({sql_cond})
            AND status IN :status_list
            {building_filter}  
            AND tariff != '0'
            AND dlo.treatment_end LIKE '%{selected_year}%'
            AND goal IN :dv
        GROUP BY ksg
    )

    SELECT
        CASE WHEN ksg IS NULL THEN 'Итого' ELSE ksg::text END AS ksg,
        "Всего",
        "Сумма",
        "М",
        "М Сумма",
        "Ж",
        "Ж Сумма",
        {dynamic_column_names_sql}  
    FROM data
    UNION ALL
    SELECT 'Итого' AS ksg,
        SUM("Всего"),
        SUM("Сумма"),
        SUM("М"),
        SUM("М Сумма"),
        SUM("Ж"),
        SUM("Ж Сумма"),
        {dynamic_column_sums_sql} 
    FROM data
    """
    print(query)
    return query
