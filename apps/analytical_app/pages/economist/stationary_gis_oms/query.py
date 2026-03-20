"""
Отчёт «Стационарная помощь для ГИС ОМС»: КСГ × профиль врача в талоне (кол-во и сумма).
Источник: load_data_talons (как вкладка «Стационары» в для ГИС ОМС).
"""


def _profile_case_sql():
    dp = "LOWER(COALESCE(doctor_profile, ''))"
    return f"""
    CASE
        WHEN {dp} LIKE '%общей врачебной%' OR {dp} LIKE '%семейной медицине%' THEN 'opp'
        WHEN {dp} LIKE '%педиатр%' THEN 'ped'
        WHEN {dp} LIKE '%невролог%' THEN 'nev'
        WHEN {dp} LIKE '%травматолог%' OR {dp} LIKE '%ортопед%' THEN 'trav'
        WHEN {dp} LIKE '%эндокринолог%' THEN 'endo'
        WHEN {dp} LIKE '%хирург%' THEN 'surg'
        WHEN {dp} LIKE '%терап%' AND {dp} NOT LIKE '%психотерап%' THEN 'ther'
        ELSE 'oth'
    END
    """


# Ключ CASE → заголовки столбцов (кол-во / сумма)
_PROFILES = [
    ("opp", "общая врачебная практика"),
    ("ther", "терапия"),
    ("nev", "неврология"),
    ("ped", "педиатрия"),
    ("trav", "травматология и ортопедия"),
    ("surg", "хирургия"),
    ("endo", "эндокринология"),
    ("oth", "прочие профили"),
]


def sql_query_stationary_gis_oms(months_placeholder_sql, selected_year):
    """
    months_placeholder_sql: строка вида "'Января 2025', 'Февраля 2025'" (как в gis_oms).
    Биндинг: status_list, goals_list (кортежи для IN).
    """
    prof_case = _profile_case_sql().strip()

    agg_count_parts = []
    agg_sum_parts = []
    total_parts = []
    numbered_select_profile = []
    for key, title in _PROFILES:
        tq = title.replace('"', '""')
        agg_count_parts.append(
            f"COUNT(*) FILTER (WHERE prof_key = '{key}') AS \"{tq} — сл.\""
        )
        agg_sum_parts.append(
            f"ROUND(COALESCE(SUM(amt) FILTER (WHERE prof_key = '{key}'), 0)::numeric, 2) AS \"{tq} — руб.\""
        )
        total_parts.append(f"SUM(\"{tq} — сл.\") AS \"{tq} — сл.\"")
        total_parts.append(f"SUM(\"{tq} — руб.\") AS \"{tq} — руб.\"")
        numbered_select_profile.append(f'"{tq} — сл."')
        numbered_select_profile.append(f'"{tq} — руб."')

    agg_count_sql = ",\n            ".join(agg_count_parts)
    agg_sum_sql = ",\n            ".join(agg_sum_parts)
    total_profiles_sql = ",\n        ".join(total_parts)
    prof_list_sql = ",\n            ".join(numbered_select_profile)

    query = f"""
    WITH     raw AS (
        SELECT
            TRIM(ksg) AS ksg_trim,
            CASE
                WHEN amount ~ '^[0-9]+(\\.[0-9]+)?$' THEN amount::numeric
                ELSE NULL
            END AS amt,
            ({prof_case}) AS prof_key
        FROM load_data_talons
        WHERE ksg IS NOT NULL
          AND TRIM(ksg) <> ''
          AND TRIM(ksg) <> '-'
          AND report_period IN ({months_placeholder_sql})
          AND treatment_end LIKE '%{selected_year}%'
          AND status IN :status_list
          AND goal IN :goals_list
    ),
    norm AS (
        SELECT
            CASE
                WHEN POSITION(' ' IN ksg_trim) > 0
                THEN SPLIT_PART(ksg_trim, ' ', 1)
                ELSE ksg_trim
            END AS ksg_code,
            amt,
            prof_key
        FROM raw
    ),
    agg AS (
        SELECT
            ksg_code,
            COUNT(*) AS cnt_all,
            ROUND(COALESCE(SUM(amt), 0)::numeric, 2) AS sum_all,
            {agg_count_sql},
            {agg_sum_sql}
        FROM norm
        GROUP BY ksg_code
    ),
    numbered AS (
        SELECT
            ksg_code AS "Код КСГ",
            cnt_all AS "случаев лечения, ед.",
            sum_all AS "объем финансирования, руб.",
            {prof_list_sql}
        FROM agg
    )
    SELECT * FROM (
        SELECT * FROM numbered
        UNION ALL
        SELECT
            'Всего' AS "Код КСГ",
            SUM("случаев лечения, ед.") AS "случаев лечения, ед.",
            ROUND(SUM("объем финансирования, руб.")::numeric, 2) AS "объем финансирования, руб.",
            {total_profiles_sql}
        FROM numbered
    ) AS report
    ORDER BY CASE WHEN "Код КСГ" = 'Всего' THEN 1 ELSE 0 END, "Код КСГ"
    """
    return query.strip()
