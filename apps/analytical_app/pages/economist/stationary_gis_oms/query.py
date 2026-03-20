"""
Отчёт «Стационарная помощь для ГИС ОМС»: КСГ × профиль врача в талоне (кол-во и сумма).
Источник: load_data_talons + привязка к personnel (как фильтры на странице врача).
"""


def _profile_case_sql():
    dp = "LOWER(COALESCE(t.doctor_profile, ''))"
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


def _talon_filters_sql(inogorodniy, sanction, amount_null):
    """Как в base_query для data_loader_omsdata, адаптировано под load_data_talons (t)."""
    parts = []
    if inogorodniy == "1":
        parts.append("AND t.smo_code LIKE '360%'")
    elif inogorodniy == "2":
        parts.append("AND (t.smo_code IS NULL OR t.smo_code NOT LIKE '360%')")
    if sanction == "1":
        parts.append("AND COALESCE(NULLIF(TRIM(t.sanctions), ''), '-') IN ('-', '0')")
    elif sanction == "2":
        parts.append("AND COALESCE(NULLIF(TRIM(t.sanctions), ''), '-') NOT IN ('-', '0')")
    if amount_null == "1":
        parts.append(
            "AND t.amount ~ '^[0-9]+(\\.[0-9]+)?$' AND (t.amount)::numeric != 0"
        )
    elif amount_null == "2":
        parts.append(
            "AND (NOT (t.amount ~ '^[0-9]+(\\.[0-9]+)?$') OR (t.amount)::numeric = 0)"
        )
    return "\n          ".join(parts)


def _personnel_filters_sql(building_ids, department_ids, profile_ids, doctor_ids):
    parts = []
    if building_ids:
        parts.append(f"AND ob.id IN ({','.join(map(str, building_ids))})")
    if department_ids:
        parts.append(f"AND od.id IN ({','.join(map(str, department_ids))})")
    if profile_ids:
        parts.append(f"AND pd.profile_id IN ({','.join(map(str, profile_ids))})")
    if doctor_ids:
        parts.append(f"AND pd.id IN ({','.join(map(str, doctor_ids))})")
    return "\n          ".join(parts)


def sql_query_stationary_gis_oms(
    months_placeholder_sql,
    selected_year,
    inogorodniy="3",
    sanction="3",
    amount_null="3",
    building_ids=None,
    department_ids=None,
    profile_ids=None,
    doctor_ids=None,
):
    """
    Биндинг: status_list, goals_list.
    Остальное — безопасные числовые списки и флаги '1'/'2'/'3'.
    """
    prof_case = _profile_case_sql().strip()
    talon_f = _talon_filters_sql(inogorodniy, sanction, amount_null)
    pers_f = _personnel_filters_sql(
        building_ids or [],
        department_ids or [],
        profile_ids or [],
        doctor_ids or [],
    )

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
    WITH raw AS (
        SELECT
            TRIM(t.ksg) AS ksg_trim,
            CASE
                WHEN t.amount ~ '^[0-9]+(\\.[0-9]+)?$' THEN t.amount::numeric
                ELSE NULL
            END AS amt,
            ({prof_case}) AS prof_key
        FROM load_data_talons t
        INNER JOIN (
            SELECT DISTINCT ON (doctor_code) id, doctor_code, department_id, profile_id
            FROM personnel_doctorrecord
            ORDER BY doctor_code, id
        ) AS pd ON SUBSTRING(TRIM(t.doctor) FROM 1 FOR POSITION(' ' IN TRIM(t.doctor)) - 1) = pd.doctor_code
        INNER JOIN organization_department od ON od.id = pd.department_id
        INNER JOIN organization_building ob ON ob.id = od.building_id
        WHERE t.ksg IS NOT NULL
          AND TRIM(t.ksg) <> ''
          AND TRIM(t.ksg) <> '-'
          AND t.report_period IN ({months_placeholder_sql})
          AND t.treatment_end LIKE '%{selected_year}%'
          AND t.status IN :status_list
          AND t.goal IN :goals_list
          {talon_f}
          {pers_f}
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
