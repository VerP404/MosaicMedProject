# -*- coding: utf-8 -*-
"""
Детализация ПН1/ДС2: load_data_oms_data + маршрут из load_data_detailed_medical_examination.

Колонки как у «Диспансеризация по возрастам»: Всего, Сумма, М, М Сумма, Ж, Ж Сумма и по каждому
выбранному корпусу — М {корпус}, М {корпус} Сумма, Ж {корпус}, Ж {корпус} Сумма.
Строки отчёта — группировка по тексту маршрута; сортировка по возрасту в месяцах из текста
(0 месяцев, затем по возрастанию), в конце — «нет маршрута» / «нет в детализации», затем «Итого».
"""


def sql_child_prof_exams_detail(selected_buildings):
    if not selected_buildings:
        selected_buildings = ['ГП1']

    dynamic_columns = []
    dynamic_column_names = []
    dynamic_column_sums = []

    for building in selected_buildings:
        b_esc = str(building).replace("'", "''")
        dynamic_columns.append(
            f'SUM(CASE WHEN TRIM(BOTH FROM COALESCE(j.building, \'\')) = \'{b_esc}\' '
            f"AND j.gender = 'М' THEN 1 ELSE 0 END) AS \"М {building}\""
        )
        dynamic_columns.append(
            f'ROUND(SUM(CASE WHEN TRIM(BOTH FROM COALESCE(j.building, \'\')) = \'{b_esc}\' '
            f"AND j.gender = 'М' THEN ROUND(COALESCE(j.amount_numeric, 0)::numeric(15, 2), 2) "
            f"ELSE 0 END)::numeric, 2) AS \"М {building} Сумма\""
        )
        dynamic_columns.append(
            f'SUM(CASE WHEN TRIM(BOTH FROM COALESCE(j.building, \'\')) = \'{b_esc}\' '
            f"AND j.gender = 'Ж' THEN 1 ELSE 0 END) AS \"Ж {building}\""
        )
        dynamic_columns.append(
            f'ROUND(SUM(CASE WHEN TRIM(BOTH FROM COALESCE(j.building, \'\')) = \'{b_esc}\' '
            f"AND j.gender = 'Ж' THEN ROUND(COALESCE(j.amount_numeric, 0)::numeric(15, 2), 2) "
            f"ELSE 0 END)::numeric, 2) AS \"Ж {building} Сумма\""
        )

        dynamic_column_names.append(f"\"М {building}\"")
        dynamic_column_names.append(f"\"М {building} Сумма\"")
        dynamic_column_names.append(f"\"Ж {building}\"")
        dynamic_column_names.append(f"\"Ж {building} Сумма\"")

        dynamic_column_sums.append(f'SUM("М {building}")')
        dynamic_column_sums.append(f'SUM("М {building} Сумма")')
        dynamic_column_sums.append(f'SUM("Ж {building}")')
        dynamic_column_sums.append(f'SUM("Ж {building} Сумма")')

    dynamic_columns_sql = ",\n        ".join(dynamic_columns)
    dynamic_column_names_sql = ",\n        ".join(dynamic_column_names)
    dynamic_column_sums_sql = ",\n        ".join(dynamic_column_sums)
    dynamic_select_outer = ",\n    ".join(f"t.{n}" for n in dynamic_column_names)

    return f"""
WITH oms_f AS (
    SELECT
        oms.talon,
        oms.goal,
        oms.gender,
        oms.building,
        oms.amount_numeric
    FROM load_data_oms_data oms
    WHERE oms.goal IN :goal_list
      AND oms.report_year = :report_year
      AND oms.report_month IN :report_months
      AND oms.status IN :status_list
      AND oms.building IN :building_list
),
talons AS (
    SELECT DISTINCT TRIM(BOTH FROM COALESCE(talon, '')) AS tnn
    FROM oms_f
    WHERE TRIM(BOTH FROM COALESCE(talon, '')) <> ''
),
dme_unique_talon_route AS (
    SELECT
        TRIM(BOTH FROM COALESCE(d.talon_number, '')) AS tnn,
        CASE
            WHEN d.route IS NULL
                 OR TRIM(BOTH FROM COALESCE(d.route, '')) = ''
                 OR TRIM(BOTH FROM COALESCE(d.route, '')) = '-'
            THEN '(нет маршрута)'
            ELSE TRIM(BOTH FROM d.route)
        END AS route_label,
        MAX(d.updated_at) AS last_at
    FROM load_data_detailed_medical_examination d
    INNER JOIN talons t ON TRIM(BOTH FROM COALESCE(d.talon_number, '')) = t.tnn
    WHERE TRIM(BOTH FROM COALESCE(d.talon_number, '')) <> ''
    GROUP BY
        TRIM(BOTH FROM COALESCE(d.talon_number, '')),
        CASE
            WHEN d.route IS NULL
                 OR TRIM(BOTH FROM COALESCE(d.route, '')) = ''
                 OR TRIM(BOTH FROM COALESCE(d.route, '')) = '-'
            THEN '(нет маршрута)'
            ELSE TRIM(BOTH FROM d.route)
        END
),
dme_pick AS (
    SELECT DISTINCT ON (tnn)
        tnn,
        route_label
    FROM dme_unique_talon_route
    ORDER BY
        tnn,
        CASE WHEN route_label = '(нет маршрута)' THEN 1 ELSE 0 END,
        last_at DESC NULLS LAST
),
joined AS (
    SELECT
        COALESCE(d.route_label, '(нет в детализации)') AS route_label,
        oms.gender,
        oms.building,
        oms.amount_numeric
    FROM oms_f oms
    LEFT JOIN dme_pick d ON TRIM(BOTH FROM COALESCE(oms.talon, '')) = d.tnn
),
data AS (
    SELECT
        j.route_label AS "Маршрут",
        MIN(
            CASE
                WHEN j.route_label IN ('(нет в детализации)', '(нет маршрута)') THEN 999998
                ELSE (
                    COALESCE((regexp_match(COALESCE(j.route_label, ''), '([0-9]{{1,2}})\\s*(год|года|лет|г\\.)', 'i'))[1]::text, '0')::int * 12
                    + COALESCE((regexp_match(COALESCE(j.route_label, ''), '([0-9]{{1,3}})\\s*(месяц|месяцев|мес\\.?)', 'i'))[1]::text, '0')::int
                )
            END
        ) AS _sort_mos,
        COUNT(*) AS "Всего",
        ROUND(SUM(COALESCE(j.amount_numeric, 0))::numeric, 2) AS "Сумма",
        SUM(CASE WHEN j.gender = 'М' THEN 1 ELSE 0 END) AS "М",
        ROUND(SUM(CASE WHEN j.gender = 'М' THEN ROUND(COALESCE(j.amount_numeric, 0)::numeric(15, 2), 2) ELSE 0 END)::numeric, 2) AS "М Сумма",
        SUM(CASE WHEN j.gender = 'Ж' THEN 1 ELSE 0 END) AS "Ж",
        ROUND(SUM(CASE WHEN j.gender = 'Ж' THEN ROUND(COALESCE(j.amount_numeric, 0)::numeric(15, 2), 2) ELSE 0 END)::numeric, 2) AS "Ж Сумма",
        {dynamic_columns_sql}
    FROM joined j
    GROUP BY j.route_label
)
SELECT
    t."Маршрут",
    t."Всего",
    t."Сумма",
    t."М",
    t."М Сумма",
    t."Ж",
    t."Ж Сумма",
    {dynamic_select_outer}
FROM (
    SELECT
        "Маршрут",
        _sort_mos,
        "Всего",
        "Сумма",
        "М",
        "М Сумма",
        "Ж",
        "Ж Сумма",
        {dynamic_column_names_sql}
    FROM data
    UNION ALL
    SELECT
        'Итого' AS "Маршрут",
        999999 AS _sort_mos,
        SUM("Всего"),
        SUM("Сумма"),
        SUM("М"),
        SUM("М Сумма"),
        SUM("Ж"),
        SUM("Ж Сумма"),
        {dynamic_column_sums_sql}
    FROM data
) t
ORDER BY
    CASE WHEN t."Маршрут" = 'Итого' THEN 1 ELSE 0 END,
    t._sort_mos ASC NULLS LAST,
    t."Маршрут"
"""
