"""SQL-отчёты модуля ДН (silver). Ключ диагноза — ldwid; pdwid — строка плана год/месяц."""

STATUS_RU = {
    "planned": "Запланирован",
    "completed": "Выполнен",
    "not_completed": "Не выполнен",
    "detached": "Откреплён / снят",
}


def _month_num(alias: str = "l") -> str:
    """Число месяца из plan_month ('1'..'12')."""
    return f"""
    CASE
      WHEN TRIM(COALESCE({alias}.plan_month, '')) ~ '^[0-9]+$'
        THEN CAST(TRIM({alias}.plan_month) AS INT)
      ELSE 0
    END
    """


def _latest_plan_rows(year: int) -> str:
    """Одна актуальная строка плана на ldwid (последний месяц в году)."""
    y = int(year)
    return f"""
    SELECT DISTINCT ON (NULLIF(TRIM(l.ldwid), ''), l.person_id, l.ds_code)
        l.*,
        {_month_num('l')} AS plan_month_num
    FROM dn_app_dnline l
    WHERE l.plan_year = {y}
      AND l.is_current = TRUE
    ORDER BY
        NULLIF(TRIM(l.ldwid), ''),
        l.person_id,
        l.ds_code,
        {_month_num('l')} DESC,
        l.pdwid DESC
    """


def sql_line_summary(year: int) -> str:
    y = int(year)
    return f"""
WITH latest AS (
{_latest_plan_rows(y)}
)
SELECT
    COUNT(*) AS iszl_diag_rows,
    COUNT(DISTINCT person_id) AS iszl_enp,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed,
    COUNT(*) FILTER (WHERE status = 'not_completed' AND out_of_168n = FALSE) AS not_passed,
    COUNT(*) FILTER (WHERE out_of_168n) AS out_of_168n,
    COUNT(*) FILTER (WHERE status = 'detached') AS detached
FROM latest
"""


def sql_by_category(year: int) -> str:
    y = int(year)
    return f"""
WITH latest AS (
{_latest_plan_rows(y)}
)
SELECT
    COALESCE(NULLIF(category_168n, ''), '(вне 168н)') AS category_168n,
    COUNT(*) AS iszl_diag_rows,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed,
    COUNT(*) FILTER (WHERE status = 'not_completed' AND out_of_168n = FALSE) AS not_passed
FROM latest
GROUP BY 1
ORDER BY iszl_diag_rows DESC
    """


def _sql_latest_phones_cte(alias: str = "phones") -> str:
    """Последний непустой телефон из журнала обращений на ЕНП (как в ДВ tab12/tab13)."""
    return f"""
{alias} AS (
    SELECT DISTINCT ON (regexp_replace(enp, '\\D', '', 'g'))
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        phone
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND COALESCE(NULLIF(phone, '-'), '') <> ''
    ORDER BY regexp_replace(enp, '\\D', '', 'g'),
             COALESCE(
                 CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
                      THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD') END,
                 CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}'
                      THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI')::date END,
                 CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$'
                      THEN to_date(acceptance_date, 'DD.MM.YYYY') END,
                 CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
                      THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD') END,
                 CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$'
                      THEN to_date(record_date, 'DD.MM.YYYY') END
             ) DESC NULLS LAST,
             id DESC
)
"""


def sql_not_passed(year: int, category: str = "", profile: str = "", limit: int = 5000) -> str:
    """Детальный список. ds в bronze = код МКБ, колонку «Диагноз» не дублируем."""
    y = int(year)
    extra = ""
    if category:
        extra += f" AND x.category_168n = '{category.replace(chr(39), '')}'"
    if profile:
        extra += f" AND x.profile_cluster = '{profile.replace(chr(39), '')}'"
    lim = f"LIMIT {int(limit)}" if limit and int(limit) > 0 else ""
    return f"""
WITH latest AS (
{_latest_plan_rows(y)}
),
{_sql_latest_phones_cte("phones")}
SELECT
    p.enp,
    p.fio,
    p.dr,
    COALESCE(ph.phone, '') AS phone,
    p.lpuuch,
    x.ldwid,
    x.ds_code,
    x.plan_month,
    x.doctor,
    x.category_168n,
    x.profile_cluster,
    x.status,
    x.pdwid
FROM latest x
JOIN dn_app_person p ON p.id = x.person_id
LEFT JOIN phones ph ON regexp_replace(COALESCE(p.enp, ''), '\\D', '', 'g') = ph.enp_norm
WHERE x.status = 'not_completed'
  AND x.out_of_168n = FALSE
  {extra}
ORDER BY x.plan_month_num, p.fio
{lim}
"""


def _enp_in_sql(enps: list[str] | None) -> str:
    if not enps:
        return ""
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in enps:
        digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
        if not digits or digits in seen:
            continue
        seen.add(digits)
        cleaned.append(digits)
        if len(cleaned) >= 5000:
            break
    if not cleaned:
        return ""
    listed = ", ".join("'" + e + "'" for e in cleaned)
    return f" AND regexp_replace(COALESCE(p.enp, ''), '\\D', '', 'g') IN ({listed})"


def sql_not_passed_grouped(year: int, category: str = "", profile: str = "", enps: list[str] | None = None) -> str:
    """
    Режим «по пациенту + профилю»: одна строка на человека и профиль.
    Основной МКБ — по приоритету группы: БСК > ОНКО > СД > Прочие.
    Сопутствующие — остальные МКБ того же профиля, через запятую рядом с основным.
    Другой профиль (напр. Эндокринология) = отдельная строка того же пациента.
    """
    y = int(year)
    extra = ""
    if category:
        extra += f" AND x.category_168n = '{category.replace(chr(39), '')}'"
    if profile:
        extra += f" AND x.profile_cluster = '{profile.replace(chr(39), '')}'"
    extra += _enp_in_sql(enps)
    return f"""
WITH latest AS (
{_latest_plan_rows(y)}
),
base AS (
    SELECT
        p.enp,
        p.fio,
        p.dr,
        p.lpuuch,
        x.ldwid,
        UPPER(NULLIF(TRIM(x.ds_code), '')) AS ds_code,
        x.plan_month,
        x.plan_month_num,
        x.doctor,
        COALESCE(NULLIF(TRIM(x.category_168n), ''), 'Прочие') AS category_168n,
        COALESCE(NULLIF(TRIM(x.profile_cluster), ''), '—') AS profile_cluster,
        CASE COALESCE(NULLIF(TRIM(x.category_168n), ''), 'Прочие')
            WHEN 'БСК' THEN 4
            WHEN 'ОНКО' THEN 3
            WHEN 'СД' THEN 2
            WHEN 'Прочие' THEN 1
            ELSE 0
        END AS cat_prio
    FROM latest x
    JOIN dn_app_person p ON p.id = x.person_id
    WHERE x.status = 'not_completed'
      AND x.out_of_168n = FALSE
      AND NULLIF(TRIM(x.ds_code), '') IS NOT NULL
      {extra}
),
ranked AS (
    SELECT
        b.*,
        ROW_NUMBER() OVER (
            PARTITION BY b.enp, b.profile_cluster
            ORDER BY b.cat_prio DESC, b.plan_month_num DESC, b.ds_code
        ) AS rn
    FROM base b
),
main AS (
    SELECT * FROM ranked WHERE rn = 1
),
acc AS (
    SELECT
        r.enp,
        r.profile_cluster,
        STRING_AGG(r.ds_code, ', ' ORDER BY r.cat_prio DESC, r.ds_code) AS accompanying
    FROM ranked r
    WHERE r.rn > 1
    GROUP BY r.enp, r.profile_cluster
),
cnt AS (
    SELECT enp, profile_cluster, COUNT(*) AS diag_count
    FROM base
    GROUP BY enp, profile_cluster
),
{_sql_latest_phones_cte("phones")}
SELECT
    m.enp,
    m.fio,
    m.dr,
    COALESCE(ph.phone, '') AS phone,
    m.lpuuch,
    m.profile_cluster AS main_profile,
    m.category_168n AS main_category,
    m.ds_code AS main_mkb,
    COALESCE(a.accompanying, '') AS accompanying,
    m.plan_month AS main_plan_month,
    m.doctor AS main_doctor,
    m.ldwid AS main_ldwid,
    c.diag_count
FROM main m
JOIN cnt c ON c.enp = m.enp AND c.profile_cluster = m.profile_cluster
LEFT JOIN acc a ON a.enp = m.enp AND a.profile_cluster = m.profile_cluster
LEFT JOIN phones ph ON regexp_replace(COALESCE(m.enp, ''), '\\D', '', 'g') = ph.enp_norm
ORDER BY m.fio, m.profile_cluster
LIMIT 20000
"""


def sql_out_of_168n(year: int) -> str:
    y = int(year)
    return f"""
WITH latest AS (
{_latest_plan_rows(y)}
)
SELECT
    p.enp,
    p.fio,
    p.dr,
    p.lpuuch,
    x.ldwid,
    x.ds_code,
    x.ds,
    x.plan_month,
    x.doctor,
    x.status,
    x.pdwid,
    '305' AS suggested_goal
FROM latest x
JOIN dn_app_person p ON p.id = x.person_id
WHERE x.out_of_168n = TRUE
ORDER BY p.fio
LIMIT 5000
"""


def sql_missing_prior(year: int) -> str:
    """ЕНП были в предыдущие годы, нет в выбранном году (по факту присутствия в ИСЗЛ)."""
    y = int(year)
    return f"""
WITH prior AS (
    SELECT DISTINCT ON (NULLIF(TRIM(l.ldwid), ''), p.enp, l.ds_code)
        p.enp, p.fio, p.dr, p.lpuuch,
        l.ldwid, l.ds_code, l.ds, l.plan_year AS prior_year,
        l.doctor, l.category_168n, l.pdwid
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE l.plan_year < {y}
    ORDER BY
        NULLIF(TRIM(l.ldwid), ''),
        p.enp,
        l.ds_code,
        l.plan_year DESC,
        {_month_num('l')} DESC
),
curr_enp AS (
    SELECT DISTINCT p.enp
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE l.plan_year = {y} AND l.is_current = TRUE
)
SELECT pr.*
FROM prior pr
WHERE pr.enp NOT IN (SELECT enp FROM curr_enp)
ORDER BY pr.prior_year DESC, pr.fio
LIMIT 5000
"""


def sql_dropped_diagnoses(year: int) -> str:
    """Диагнозы (ldwid) были в предыдущие годы; пациент есть в текущем, диагноза нет — снять/внести."""
    y = int(year)
    return f"""
WITH prior AS (
    SELECT DISTINCT ON (NULLIF(TRIM(l.ldwid), ''), p.enp, l.ds_code)
        p.enp, p.fio, p.lpuuch,
        l.ldwid, l.ds_code, l.ds, l.plan_year AS prior_year,
        l.category_168n, l.doctor, l.pdwid
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE l.plan_year < {y}
      AND NULLIF(TRIM(l.ldwid), '') IS NOT NULL
    ORDER BY
        NULLIF(TRIM(l.ldwid), ''),
        p.enp,
        l.ds_code,
        l.plan_year DESC,
        {_month_num('l')} DESC
),
curr AS (
    SELECT DISTINCT
        p.enp,
        NULLIF(TRIM(l.ldwid), '') AS ldwid,
        UPPER(l.ds_code) AS ds_code
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE l.plan_year = {y} AND l.is_current = TRUE
),
curr_enp AS (
    SELECT DISTINCT enp FROM curr
)
SELECT
    pr.enp, pr.fio, pr.lpuuch, pr.ldwid, pr.ds_code, pr.ds,
    pr.prior_year, pr.category_168n, pr.doctor,
    'снять / внести' AS action
FROM prior pr
WHERE pr.enp IN (SELECT enp FROM curr_enp)
  AND NOT EXISTS (
      SELECT 1 FROM curr c
      WHERE c.enp = pr.enp
        AND (
            (pr.ldwid <> '' AND c.ldwid = pr.ldwid)
            OR c.ds_code = UPPER(pr.ds_code)
        )
  )
ORDER BY pr.fio
LIMIT 5000
"""


def sql_patient_search(q: str) -> str:
    safe = q.replace("'", "").strip()
    return f"""
SELECT enp, fio, dr, lpuuch, is_detached
FROM dn_app_person
WHERE enp ILIKE '%%{safe}%%' OR fio ILIKE '%%{safe}%%'
ORDER BY fio
LIMIT 50
"""


def sql_patient_card(enp: str, year: int) -> str:
    """Карточка: диагнозы по ldwid, периоды, группа, ИСЗЛ/Квазар, талоны года, незакрытые."""
    safe = enp.replace("'", "")
    y = int(year)
    return f"""
WITH lines AS (
    SELECT
        l.ldwid, l.pdwid, l.ds_code, l.ds,
        l.date_begin, l.date_end, l.reason,
        l.plan_year, l.plan_month, l.doctor,
        l.specialty_raw, l.category_168n, l.profile_cluster,
        l.out_of_168n, l.status, l.talon_number, l.actual_date, l.is_current,
        {_month_num('l')} AS plan_month_num,
        COALESCE(NULLIF(TRIM(l.ldwid), ''), p.enp || ':' || UPPER(l.ds_code)) AS diag_key
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE p.enp = '{safe}'
),
bounds AS (
    SELECT
        diag_key,
        MIN(plan_year) AS year_from,
        MAX(plan_year) AS year_to,
        MIN(date_begin) AS date_begin,
        MAX(date_end) AS date_end_any
    FROM lines
    GROUP BY diag_key
),
latest_any AS (
    SELECT DISTINCT ON (diag_key)
        diag_key, ldwid, ds_code, ds, date_begin, date_end, reason,
        category_168n, profile_cluster, out_of_168n
    FROM lines
    ORDER BY diag_key, plan_year DESC, plan_month_num DESC, pdwid DESC
),
cur AS (
    SELECT DISTINCT ON (diag_key)
        diag_key, status, plan_month, talon_number, actual_date, doctor, pdwid
    FROM lines
    WHERE plan_year = {y} AND is_current = TRUE
    ORDER BY diag_key, plan_month_num DESC, pdwid DESC
),
talons AS (
    SELECT
        UPPER(NULLIF(TRIM(f.ds_code), '')) AS ds_code,
        STRING_AGG(DISTINCT f.goal, ', ') AS goals,
        STRING_AGG(DISTINCT NULLIF(f.talon, ''), ', ') AS talons
    FROM dn_app_dnfact f
    WHERE f.enp = '{safe}'
      AND f.report_year = {y}
      AND f.source = 'oms'
    GROUP BY 1
),
kv AS (
    SELECT DISTINCT UPPER(NULLIF(TRIM(ds_code), '')) AS ds_code
    FROM load_data_dn_kvazar
    WHERE REPLACE(TRIM(enp), '`', '') = '{safe}'
),
joined AS (
    SELECT
        d.diag_key,
        d.ldwid,
        d.ds_code,
        d.date_begin,
        d.date_end,
        d.reason,
        d.category_168n,
        d.profile_cluster,
        d.out_of_168n,
        b.year_from,
        b.year_to,
        b.date_begin AS bound_begin,
        c.diag_key AS in_year_key,
        c.status AS year_status,
        c.plan_month,
        c.talon_number AS line_talon,
        t.talons AS oms_talons,
        t.goals AS oms_goals,
        k.ds_code AS kv_ds,
        CASE
          WHEN NULLIF(TRIM(COALESCE(c.talon_number, '')), '') IS NOT NULL THEN TRUE
          WHEN NULLIF(TRIM(COALESCE(t.talons, '')), '') IS NOT NULL THEN TRUE
          ELSE FALSE
        END AS has_talon
    FROM latest_any d
    JOIN bounds b ON b.diag_key = d.diag_key
    LEFT JOIN cur c ON c.diag_key = d.diag_key
    LEFT JOIN talons t ON t.ds_code = UPPER(d.ds_code)
    LEFT JOIN kv k ON k.ds_code = UPPER(d.ds_code)
)
SELECT
    ldwid AS "ldwID (диагноз)",
    ds_code AS "МКБ",
    COALESCE(date_begin, bound_begin) AS "Поставлен на ДН",
    date_end AS "Снят с ДН",
    reason AS "Причина снятия",
    category_168n AS "Группа 168н",
    profile_cluster AS "Профиль",
    year_from AS "Годы с",
    year_to AS "Годы по",
    CASE WHEN out_of_168n THEN 'нет' ELSE 'да' END AS "В 168н",
    CASE WHEN in_year_key IS NOT NULL THEN 'да' ELSE 'нет' END AS "В ИСЗЛ (год)",
    CASE WHEN kv_ds IS NOT NULL THEN 'да' ELSE 'нет' END AS "В Квазар",
    CASE WHEN has_talon THEN 'да' ELSE 'нет' END AS "Есть талон",
    CASE
      WHEN in_year_key IS NULL AND has_talon THEN
        'Нет в ИСЗЛ за год; талон есть'
      WHEN in_year_key IS NULL THEN
        'Нет в ИСЗЛ за год; талона нет'
      WHEN year_status = 'completed' OR has_talon THEN
        'В ИСЗЛ; талон есть; пройден'
      WHEN year_status = 'not_completed' THEN
        'В ИСЗЛ; талона нет; не пройден'
      WHEN year_status = 'planned' AND out_of_168n THEN
        'В ИСЗЛ; талона нет; вне 168н (контроль 305)'
      WHEN year_status = 'planned' THEN
        'В ИСЗЛ; талона нет; в плане'
      WHEN year_status = 'detached' THEN
        'В ИСЗЛ; откреплён / снят'
      ELSE
        'В ИСЗЛ; ' || COALESCE(year_status, '—')
    END AS "Статус",
    plan_month AS "Месяц плана",
    COALESCE(line_talon, '') AS "Талон в линии",
    COALESCE(oms_talons, '') AS "Талоны ОМС года",
    COALESCE(oms_goals, '') AS "Цели ОМС",
    CASE
      WHEN date_end IS NULL AND (in_year_key IS NULL OR year_status IN ('not_completed', 'planned'))
        THEN 'да'
      ELSE 'нет'
    END AS "Не закрыт"
FROM joined
ORDER BY year_to DESC, ds_code
"""


def sql_patient_meta(enp: str, year: int) -> str:
    safe = enp.replace("'", "")
    y = int(year)
    return f"""
SELECT
    p.enp, p.fio, p.dr, p.lpuuch,
    EXISTS (
        SELECT 1 FROM dn_app_dnline l
        WHERE l.person_id = p.id AND l.plan_year = {y} AND l.is_current
    ) AS in_iszl_year,
    EXISTS (
        SELECT 1 FROM dn_app_dnline l WHERE l.person_id = p.id
    ) AS in_iszl_any,
    EXISTS (
        SELECT 1 FROM load_data_dn_kvazar k
        WHERE REPLACE(TRIM(k.enp), '`', '') = p.enp
    ) AS in_kvazar,
    (
        SELECT COUNT(DISTINCT f.talon)
        FROM dn_app_dnfact f
        WHERE f.enp = p.enp AND f.report_year = {y} AND f.source = 'oms' AND f.talon <> ''
    ) AS talons_year
FROM dn_app_person p
WHERE p.enp = '{safe}'
LIMIT 1
"""


def sql_etl_status() -> str:
    return """
SELECT table_name, start_time, end_time, count_before, count_after,
       duration, error_occurred
FROM load_data_loadlog
WHERE table_name LIKE '%%dispansery%%' OR table_name LIKE '%%dn%%'
ORDER BY start_time DESC
LIMIT 20
"""


def sql_kvazar_stats(year: int) -> str:
    """Индикаторы схожести ИСЗЛ ↔ Квазар (пары ЕНП+МКБ)."""
    _ = int(year)
    return """
WITH iszl AS (
    SELECT DISTINCT p.enp, UPPER(l.ds_code) AS ds_code, p.lpuuch, l.category_168n
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE NULLIF(TRIM(l.ds_code), '') IS NOT NULL
),
kv AS (
    SELECT DISTINCT
        REPLACE(TRIM(enp), '`', '') AS enp,
        UPPER(NULLIF(TRIM(ds_code), '')) AS ds_code,
        MAX(lpuuch) AS lpuuch
    FROM load_data_dn_kvazar
    WHERE REPLACE(TRIM(enp), '`', '') NOT IN ('', '-')
      AND NULLIF(TRIM(ds_code), '') IS NOT NULL
    GROUP BY 1, 2
),
both_pairs AS (
    SELECT i.enp, i.ds_code
    FROM iszl i
    INNER JOIN kv k ON k.enp = i.enp AND k.ds_code = i.ds_code
)
SELECT
    (SELECT COUNT(*) FROM iszl) AS iszl_pairs,
    (SELECT COUNT(*) FROM kv) AS kvazar_pairs,
    (SELECT COUNT(*) FROM both_pairs) AS both_pairs,
    (SELECT COUNT(DISTINCT enp) FROM iszl) AS iszl_enp,
    (SELECT COUNT(DISTINCT enp) FROM kv) AS kvazar_enp,
    (SELECT COUNT(DISTINCT i.enp) FROM iszl i INNER JOIN kv k ON k.enp = i.enp) AS both_enp
"""


def sql_kvazar_not_in_iszl(year: int) -> str:
    _ = int(year)
    return """
WITH iszl AS (
    SELECT DISTINCT p.enp, UPPER(l.ds_code) AS ds_code
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE NULLIF(TRIM(l.ds_code), '') IS NOT NULL
),
iszl_enp AS (SELECT DISTINCT enp FROM iszl),
kv AS (
    SELECT
        REPLACE(TRIM(enp), '`', '') AS enp,
        UPPER(NULLIF(TRIM(ds_code), '')) AS ds_code,
        MAX(fio) AS fio,
        MAX(ds) AS ds_raw,
        MAX(lpuuch) AS lpuuch
    FROM load_data_dn_kvazar
    WHERE REPLACE(TRIM(enp), '`', '') NOT IN ('', '-')
      AND NULLIF(TRIM(ds_code), '') IS NOT NULL
    GROUP BY 1, 2
)
SELECT
    k.enp,
    k.fio,
    k.lpuuch,
    k.ds_code,
    k.ds_raw,
    CASE WHEN e.enp IS NULL THEN 'ЕНП нет в ИСЗЛ' ELSE 'Пара нет в ИСЗЛ' END AS issue
FROM kv k
LEFT JOIN iszl_enp e ON e.enp = k.enp
LEFT JOIN iszl i ON i.enp = k.enp AND i.ds_code = k.ds_code
WHERE i.enp IS NULL
ORDER BY issue, k.fio
LIMIT 5000
"""


def sql_iszl_not_in_kvazar(year: int) -> str:
    """Есть в ИСЗЛ (последний снимок по ldwid в любом году / текущие линии), нет в Квазар."""
    y = int(year)
    return f"""
WITH latest AS (
{_latest_plan_rows(y)}
),
iszl AS (
    SELECT
        p.enp, p.fio, p.lpuuch,
        x.ldwid, UPPER(x.ds_code) AS ds_code, x.ds,
        x.category_168n, x.doctor, x.plan_month
    FROM latest x
    JOIN dn_app_person p ON p.id = x.person_id
    WHERE NULLIF(TRIM(x.ds_code), '') IS NOT NULL
),
kv AS (
    SELECT DISTINCT
        REPLACE(TRIM(enp), '`', '') AS enp,
        UPPER(NULLIF(TRIM(ds_code), '')) AS ds_code
    FROM load_data_dn_kvazar
    WHERE REPLACE(TRIM(enp), '`', '') NOT IN ('', '-')
      AND NULLIF(TRIM(ds_code), '') IS NOT NULL
),
kv_enp AS (SELECT DISTINCT enp FROM kv)
SELECT
    i.enp,
    i.fio,
    i.lpuuch,
    i.category_168n,
    i.ldwid,
    i.ds_code,
    i.ds,
    i.doctor,
    i.plan_month,
    CASE WHEN ke.enp IS NULL THEN 'ЕНП нет в Квазар' ELSE 'Пара нет в Квазар' END AS issue
FROM iszl i
LEFT JOIN kv_enp ke ON ke.enp = i.enp
LEFT JOIN kv k ON k.enp = i.enp AND k.ds_code = i.ds_code
WHERE k.enp IS NULL
ORDER BY issue, i.fio
LIMIT 5000
"""


GOAL3_ACTIVE_STATUSES = ("1", "2", "3", "4", "5", "6", "7", "8", "12", "18", "19")

# LIKE с %% — pandas/psycopg воспринимают одиночный % как плейсхолдер (immutabledict is not a sequence).

_JOURNAL_APPOINTMENT_TS = """
        COALESCE(
          CASE WHEN j.acceptance_date LIKE '____-__-__%%'
               THEN to_date(SUBSTRING(j.acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
          CASE WHEN j.acceptance_date LIKE '__.__.____%%'
               THEN to_timestamp(SUBSTRING(j.acceptance_date FROM 1 FOR 16), 'DD.MM.YYYY HH24:MI') END,
          CASE WHEN j.record_date LIKE '____-__-__%%'
               THEN to_date(SUBSTRING(j.record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
          CASE WHEN j.record_date LIKE '__.__.____%%'
               THEN to_date(SUBSTRING(j.record_date FROM 1 FOR 10), 'DD.MM.YYYY')::timestamp END
        )
"""

_JOURNAL_NO_SHOW_SQL = """
      AND NOT (
        LOWER(TRIM(COALESCE(j.no_show, ''))) IN ('да', 'true', '1', 'yes', '+')
        OR LOWER(COALESCE(j.no_show, '')) LIKE '%%не явил%%'
      )
"""


def _iso_date_sql(value) -> str:
    text = str(value or "")[:10]
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        raise ValueError("Ожидается дата YYYY-MM-DD.")
    return text


def _departments_sql(departments: list[str] | None) -> str:
    if not departments:
        return ""
    safe = []
    for raw in departments:
        name = str(raw or "").strip()
        if not name:
            continue
        safe.append("'" + name.replace("'", "''") + "'")
    if not safe:
        return ""
    return " AND j.department IN (" + ", ".join(safe) + ")"


def sql_journal_departments() -> str:
    return """
    SELECT DISTINCT department
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(department, '-'), '') <> ''
    ORDER BY department
    """


def sql_journal_visits_in_period(
    date_from,
    date_to,
    departments: list[str] | None = None,
) -> str:
    """Посещения поликлиники: номер (серия/номер полиса журнала), ЕНП, дата, врач, подразделение."""
    start = _iso_date_sql(date_from)
    end = _iso_date_sql(date_to)
    dept = _departments_sql(departments)
    return f"""
    SELECT
        regexp_replace(COALESCE(j.enp, ''), '\\D', '', 'g') AS enp_norm,
        j.enp,
        TRIM(COALESCE(j.patient_last_name, '') || ' ' || COALESCE(j.patient_first_name, '') || ' ' || COALESCE(j.patient_middle_name, '')) AS fio,
        j.birth_date,
        j.department,
        j.employee_last_name,
        j.employee_first_name,
        j.employee_middle_name,
        COALESCE(NULLIF(TRIM(j.number), ''), NULLIF(TRIM(j.series), ''), '') AS journal_number,
        ({_JOURNAL_APPOINTMENT_TS})::date AS visit_date
    FROM load_data_journal_appeals j
    WHERE COALESCE(NULLIF(j.enp, '-'), '') <> ''
      {_JOURNAL_NO_SHOW_SQL}
      {dept}
      AND ({_JOURNAL_APPOINTMENT_TS})::date BETWEEN DATE '{start}' AND DATE '{end}'
    ORDER BY visit_date, j.enp
    """


def sql_journal_blocked_dates(enps: list[str], date_from, date_to) -> str:
    """Все даты журнала по ЕНП в расширенном окне (чтобы явки ДН не пересеклись)."""
    start = _iso_date_sql(date_from)
    end = _iso_date_sql(date_to)
    extra = _enp_in_sql(enps).replace("p.enp", "j.enp")
    if not extra:
        return "SELECT NULL::text AS enp_norm, NULL::date AS visit_date WHERE FALSE"
    return f"""
    SELECT
        regexp_replace(COALESCE(j.enp, ''), '\\D', '', 'g') AS enp_norm,
        ({_JOURNAL_APPOINTMENT_TS})::date AS visit_date
    FROM load_data_journal_appeals j
    WHERE COALESCE(NULLIF(j.enp, '-'), '') <> ''
      {_JOURNAL_NO_SHOW_SQL}
      {extra}
      AND ({_JOURNAL_APPOINTMENT_TS})::date BETWEEN DATE '{start}' - INTERVAL '14 days'
          AND DATE '{end}' + INTERVAL '90 days'
    """


def sql_goal3_active_by_group(year: int, enps: list[str] | None = None) -> str:
    """Талоны цели 3 в рабочих статусах: ЕНП + группа 168н по коду МКБ."""
    y = int(year)
    statuses = ", ".join("'" + s + "'" for s in GOAL3_ACTIVE_STATUSES)
    extra = _enp_in_sql(enps).replace("p.enp", "o.enp")
    return f"""
    WITH latest AS (
    {_latest_plan_rows(y)}
    ),
    mkb_cat AS (
        SELECT DISTINCT ON (UPPER(TRIM(ds_code)))
            UPPER(TRIM(ds_code)) AS mkb,
            COALESCE(NULLIF(TRIM(category_168n), ''), 'Прочие') AS category_168n
        FROM latest
        WHERE NULLIF(TRIM(ds_code), '') IS NOT NULL
        ORDER BY UPPER(TRIM(ds_code)), category_168n
    )
    SELECT DISTINCT
        regexp_replace(COALESCE(o.enp, ''), '\\D', '', 'g') AS enp_norm,
        UPPER(NULLIF(TRIM(o.main_diagnosis_code), '')) AS mkb,
        COALESCE(c.category_168n, 'Прочие') AS category_168n
    FROM load_data_oms_data o
    LEFT JOIN mkb_cat c ON c.mkb = UPPER(NULLIF(TRIM(o.main_diagnosis_code), ''))
    WHERE o.report_year = {y}
      AND TRIM(COALESCE(o.goal, '')) IN ('3', '03')
      AND TRIM(COALESCE(o.status, '')) IN ({statuses})
      {extra}
    """


def sql_doctor_codes_by_name() -> str:
    return """
    SELECT DISTINCT ON (LOWER(TRIM(last_name)), LOWER(TRIM(first_name)))
        LOWER(TRIM(last_name)) AS last_name,
        LOWER(TRIM(first_name)) AS first_name,
        doctor_code
    FROM load_data_doctor
    WHERE COALESCE(NULLIF(TRIM(doctor_code), '-'), '') <> ''
      AND COALESCE(NULLIF(TRIM(last_name), '-'), '') <> ''
    ORDER BY LOWER(TRIM(last_name)), LOWER(TRIM(first_name)), id DESC
    """


_TALON_END_DATE_SQL = """
COALESCE(
  CASE WHEN t.treatment_end ~ '^\\d{4}-\\d{2}-\\d{2}'
       THEN to_date(SUBSTRING(t.treatment_end FROM 1 FOR 10), 'YYYY-MM-DD') END,
  CASE WHEN t.treatment_end ~ '^\\d{2}-\\d{2}-\\d{4}'
       THEN to_date(SUBSTRING(t.treatment_end FROM 1 FOR 10), 'DD-MM-YYYY') END,
  CASE WHEN t.treatment_end ~ '^\\d{2}\\.\\d{2}\\.\\d{4}'
       THEN to_date(SUBSTRING(t.treatment_end FROM 1 FOR 10), 'DD.MM.YYYY') END
)
"""


def _status_in_sql(statuses: list[str] | None) -> str:
    if not statuses:
        return ""
    safe = []
    for raw in statuses:
        code = str(raw or "").strip()
        if not code:
            continue
        safe.append("'" + code.replace("'", "''") + "'")
    if not safe:
        return ""
    return (
        " AND regexp_replace(TRIM(COALESCE(t.status, '')), '\\.0$', '') IN ("
        + ", ".join(safe)
        + ")"
    )


def sql_goal3_talon_departments(year: int) -> str:
    y = int(year)
    return f"""
    SELECT DISTINCT department
    FROM (
        SELECT department, goal, report_year FROM load_data_talons
        UNION ALL
        SELECT department, goal, report_year FROM load_data_complex_talons
    ) t
    WHERE TRIM(COALESCE(t.goal, '')) IN ('3', '03')
      AND TRIM(COALESCE(t.report_year, '')) IN ('{y}', '{y}.0')
      AND COALESCE(NULLIF(TRIM(t.department), '-'), '') <> ''
    ORDER BY department
    """


def sql_goal3_journal_talons(
    year: int,
    date_from,
    date_to,
    departments: list[str] | None = None,
    statuses: list[str] | None = None,
) -> str:
    """Талоны цели 3 из журнала WEB.ОМС (обычные + комплексные)."""
    y = int(year)
    start = _iso_date_sql(date_from)
    end = _iso_date_sql(date_to)
    dept = ""
    if departments:
        names = []
        for raw in departments:
            name = str(raw or "").strip()
            if name:
                names.append("'" + name.replace("'", "''") + "'")
        if names:
            dept = " AND t.department IN (" + ", ".join(names) + ")"
    status_sql = _status_in_sql(statuses)
    return f"""
    SELECT DISTINCT ON (t.talon)
        t.talon,
        t.enp,
        t.status,
        t.goal,
        t.patient,
        t.gender,
        t.birth_date,
        t.treatment_start,
        t.treatment_end,
        t.doctor,
        t.doctor_profile,
        t.specialty,
        t.department,
        t.main_diagnosis,
        t.additional_diagnosis,
        t.visits,
        t.mo_visits,
        t.case_code,
        t.talon_type,
        t.result,
        t.outcome,
        t.main_disease_character,
        t.dispensary_monitoring,
        t.care_conditions
    FROM (
        SELECT talon, enp, status, goal, patient, gender, birth_date,
               treatment_start, treatment_end, doctor, doctor_profile, specialty,
               department, main_diagnosis, additional_diagnosis, visits, mo_visits,
               case_code, talon_type, result, outcome, main_disease_character,
               dispensary_monitoring, care_conditions, report_year
        FROM load_data_talons
        UNION ALL
        SELECT talon, enp, status, goal, patient, gender, birth_date,
               treatment_start, treatment_end, doctor, doctor_profile, specialty,
               department, main_diagnosis, additional_diagnosis, visits, mo_visits,
               case_code, talon_type, result, outcome, main_disease_character,
               dispensary_monitoring, care_conditions, report_year
        FROM load_data_complex_talons
    ) t
    WHERE TRIM(COALESCE(t.goal, '')) IN ('3', '03')
      AND TRIM(COALESCE(t.report_year, '')) IN ('{y}', '{y}.0')
      AND ({_TALON_END_DATE_SQL}) BETWEEN DATE '{start}' AND DATE '{end}'
      {dept}
      {status_sql}
    ORDER BY t.talon, ({_TALON_END_DATE_SQL}) DESC NULLS LAST
    """


def sql_iszl_mkb_by_enp(year: int, enps: list[str] | None = None) -> str:
    y = int(year)
    extra = _enp_in_sql(enps)
    return f"""
    SELECT
        regexp_replace(COALESCE(p.enp, ''), '\\D', '', 'g') AS enp_norm,
        UPPER(NULLIF(TRIM(l.ds_code), '')) AS mkb
    FROM dn_app_dnline l
    JOIN dn_app_person p ON p.id = l.person_id
    WHERE l.plan_year = {y}
      AND l.is_current = TRUE
      AND COALESCE(l.out_of_168n, FALSE) = FALSE
      AND NULLIF(TRIM(l.ds_code), '') IS NOT NULL
      {extra}
    """


