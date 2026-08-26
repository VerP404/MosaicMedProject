"""
Быстрый bulk-sync load_data_dispansery_iszl → dn_app (Person + DnLine) + факты ОМС.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from django.db import connection, transaction
from django.utils import timezone
from psycopg2.extras import execute_values

from apps.dn_app.models import DataImport, DnFact, DnLine, Person
from apps.dn_reference.specialty_clusters import specialty_to_cluster


def extract_mkb(raw) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().upper()
    if not s or s in ("-", "NONE", "NAN"):
        return ""
    m = re.match(r"([A-Z]\d{2}(?:\.\d{1,2})?)", s)
    return m.group(1) if m else s.split()[0]


def plan_year_counts() -> dict[int, int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT CAST(SPLIT_PART(TRIM(plan_year), '.', 1) AS INT) AS y,
                   COUNT(*) AS n
            FROM load_data_dispansery_iszl
            WHERE TRIM(COALESCE(plan_year, '')) ~ '^[0-9]+'
            GROUP BY 1 ORDER BY 1
            """
        )
        return {int(y): int(n) for y, n in cursor.fetchall()}


def resolve_plan_years(requested: int | None = None) -> list[int]:
    counts = plan_year_counts()
    if not counts:
        raise ValueError(
            "load_data_dispansery_iszl пуста — сначала load_iszl_dn_years или iszl_job_dn"
        )
    if requested and int(requested) > 0:
        y = int(requested)
        if y not in counts:
            raise ValueError(f"Нет строк за PlanYear={y}. Есть: {sorted(counts)}")
        return [y]
    return sorted(counts.keys())


def resolve_plan_year(requested: int | None = None) -> int:
    years = resolve_plan_years(requested if requested and int(requested) > 0 else None)
    if requested and int(requested) > 0:
        return years[0]
    cal = datetime.now().year
    if cal in years:
        return cal
    return years[-1]


def _load_168n_maps() -> tuple[dict[str, str], dict[str, str]]:
    """code -> category name; code -> primary specialty name."""
    cat_map: dict[str, str] = {}
    spec_map: dict[str, str] = {}
    with connection.cursor() as c:
        c.execute(
            """
            SELECT d.code, COALESCE(cat.name, '')
            FROM dn_reference_dndiagnosis d
            LEFT JOIN dn_reference_dndiagnosiscategory cat ON cat.id = d.category_id
            WHERE d.is_active = TRUE
            """
        )
        for code, cat in c.fetchall():
            cat_map[str(code).upper()] = cat or ""
        c.execute(
            """
            SELECT d.code, s.name
            FROM dn_reference_dndiagnosisspecialty ds
            JOIN dn_reference_dndiagnosis d ON d.id = ds.diagnosis_id
            JOIN dn_reference_dnspecialty s ON s.id = ds.specialty_id
            WHERE ds.source = 'primary'
            """
        )
        for code, name in c.fetchall():
            spec_map.setdefault(str(code).upper(), name or "")
    return cat_map, spec_map


def _parse_date_sql_expr(col: str) -> str:
    """Try common date formats from ISZL char fields → date."""
    return f"""
    CASE
      WHEN NULLIF(TRIM({col}), '') IS NULL OR TRIM({col}) IN ('-', 'None', 'nan') THEN NULL
      WHEN TRIM({col}) ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}'
        THEN TO_DATE(SUBSTRING(TRIM({col}) FROM 1 FOR 10), 'DD.MM.YYYY')
      WHEN TRIM({col}) ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
        THEN TO_DATE(SUBSTRING(TRIM({col}) FROM 1 FOR 10), 'YYYY-MM-DD')
      WHEN TRIM({col}) ~ '^[0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}}'
        THEN TO_DATE(SUBSTRING(TRIM({col}) FROM 1 FOR 10), 'DD-MM-YYYY')
      ELSE NULL
    END
    """


class DNBulkSync:
    """Sync one PlanYear from bronze into Person + DnLine (+ OMS facts)."""

    def __init__(self, year: int):
        self.year = int(year)
        self.import_batch: Optional[DataImport] = None
        self.stats = {
            "total_rows": 0,
            "persons_upserted": 0,
            "lines_upserted": 0,
            "detached": 0,
            "facts_oms": 0,
            "matched_lines": 0,
            "errors": [],
        }

    def process(self) -> tuple[bool, str]:
        try:
            self.import_batch = DataImport.objects.create(
                year=self.year,
                file_name="load_data_dispansery_iszl",
                file_path=f"db://bulk?plan_year={self.year}",
                status="processing",
            )
            cat_map, spec_map = _load_168n_maps()
            with transaction.atomic():
                n = self._upsert_persons_and_lines(cat_map, spec_map)
                self.stats["total_rows"] = n
                self.stats["lines_upserted"] = n
                self._detach_missing()
                self._match_oms_and_update_lines()
            self.import_batch.total_rows = self.stats["total_rows"]
            self.import_batch.processed_rows = self.stats["total_rows"]
            self.import_batch.created_persons = self.stats["persons_upserted"]
            self.import_batch.created_observations = self.stats["lines_upserted"]
            self.import_batch.detached_patients = self.stats["detached"]
            self.import_batch.status = "completed"
            self.import_batch.save()
            return True, f"Bulk sync PlanYear={self.year} OK"
        except Exception as e:
            if self.import_batch:
                self.import_batch.status = "error"
                self.import_batch.error_message = str(e)
                self.import_batch.save()
            self.stats["errors"].append(str(e))
            return False, f"Ошибка bulk sync: {e}"

    def _upsert_persons_and_lines(self, cat_map: dict, spec_map: dict) -> int:
        with connection.cursor() as c:
            c.execute(
                f"""
                SELECT
                    REPLACE(TRIM(enp), '`', '') AS enp,
                    COALESCE(NULLIF(TRIM(fio), ''), REPLACE(TRIM(enp), '`', '')) AS fio,
                    {_parse_date_sql_expr('dr')} AS dr,
                    COALESCE(TRIM(lpuuch), '') AS lpuuch,
                    TRIM(pdwid) AS pdwid,
                    COALESCE(TRIM(pid), '') AS pid,
                    COALESCE(TRIM(ldwid), '') AS ldwid,
                    COALESCE(TRIM(ds), '') AS ds,
                    UPPER(SPLIT_PART(TRIM(ds), ' ', 1)) AS ds_code,
                    {_parse_date_sql_expr('date_begin')} AS date_begin,
                    {_parse_date_sql_expr('date_end')} AS date_end,
                    COALESCE(NULLIF(TRIM(name_reason), ''), COALESCE(TRIM(id_reason), '')) AS reason,
                    CAST(SPLIT_PART(TRIM(plan_year), '.', 1) AS INT) AS plan_year,
                    COALESCE(TRIM(plan_month), '') AS plan_month,
                    COALESCE(TRIM(fio_doctor), '') AS doctor,
                    COALESCE(TRIM(spec_d), '') AS specialty_raw
                FROM load_data_dispansery_iszl
                WHERE plan_year ~ '^[0-9]'
                  AND CAST(SPLIT_PART(TRIM(plan_year), '.', 1) AS INT) = %s
                  AND REPLACE(TRIM(enp), '`', '') NOT IN ('', '-', 'None', 'nan')
                  AND TRIM(COALESCE(pdwid, '')) NOT IN ('', '-')
                """,
                [self.year],
            )
            cols = [d[0] for d in c.description]
            rows = [dict(zip(cols, r)) for r in c.fetchall()]

        if not rows:
            raise ValueError(f"Нет строк bronze за PlanYear={self.year}")

        # persons
        person_map: dict[str, int] = {}
        person_rows = {}
        for r in rows:
            enp = r["enp"]
            if enp not in person_rows:
                person_rows[enp] = (enp, r["fio"], r["dr"], r["lpuuch"] or "")

        now = timezone.now()
        with connection.cursor() as c:
            execute_values(
                c,
                """
                INSERT INTO dn_app_person
                    (enp, fio, dr, lpuuch, is_detached, detached_date, last_import_date)
                VALUES %s
                ON CONFLICT (enp) DO UPDATE SET
                    fio = EXCLUDED.fio,
                    dr = COALESCE(EXCLUDED.dr, dn_app_person.dr),
                    lpuuch = CASE WHEN EXCLUDED.lpuuch <> '' THEN EXCLUDED.lpuuch
                                 ELSE dn_app_person.lpuuch END,
                    is_detached = FALSE,
                    detached_date = NULL,
                    last_import_date = EXCLUDED.last_import_date
                """,
                [
                    (enp, fio, dr, lpuuch, False, None, now)
                    for enp, fio, dr, lpuuch in person_rows.values()
                ],
                page_size=2000,
            )
            self.stats["persons_upserted"] = len(person_rows)
            c.execute(
                "SELECT id, enp FROM dn_app_person WHERE enp = ANY(%s)",
                [list(person_rows.keys())],
            )
            person_map = {enp: pid for pid, enp in c.fetchall()}

        batch_id = self.import_batch.id if self.import_batch else None
        line_tuples = []
        for r in rows:
            code = extract_mkb(r["ds_code"] or r["ds"])
            cat = cat_map.get(code, "")
            out = code not in cat_map if code else True
            spec_raw = r["specialty_raw"] or spec_map.get(code, "")
            cluster = specialty_to_cluster(spec_raw) if spec_raw else specialty_to_cluster(
                spec_map.get(code, "")
            )
            if not cat and not out:
                cat = ""
            person_id = person_map.get(r["enp"])
            if not person_id:
                continue
            line_tuples.append(
                (
                    person_id,
                    r["pdwid"],
                    r["pid"] or "",
                    r["ldwid"] or "",
                    (r["ds"] or "")[:255],
                    code[:32],
                    r["date_begin"],
                    r["date_end"],
                    (r["reason"] or "")[:255],
                    self.year,
                    (r["plan_month"] or "")[:10],
                    (r["doctor"] or "")[:255],
                    (spec_raw or "")[:255],
                    (cat or "")[:64],
                    (cluster or "")[:128],
                    out,
                    "planned",
                    True,
                    "",
                    None,
                    batch_id,
                    now,
                )
            )

        with connection.cursor() as c:
            execute_values(
                c,
                """
                INSERT INTO dn_app_dnline (
                    person_id, pdwid, pid, ldwid, ds, ds_code,
                    date_begin, date_end, reason, plan_year, plan_month,
                    doctor, specialty_raw, category_168n, profile_cluster,
                    out_of_168n, status, is_current, talon_number, actual_date,
                    import_batch_id, updated_at
                ) VALUES %s
                ON CONFLICT (pdwid) DO UPDATE SET
                    person_id = EXCLUDED.person_id,
                    pid = EXCLUDED.pid,
                    ldwid = EXCLUDED.ldwid,
                    ds = EXCLUDED.ds,
                    ds_code = EXCLUDED.ds_code,
                    date_begin = EXCLUDED.date_begin,
                    date_end = EXCLUDED.date_end,
                    reason = EXCLUDED.reason,
                    plan_year = EXCLUDED.plan_year,
                    plan_month = EXCLUDED.plan_month,
                    doctor = EXCLUDED.doctor,
                    specialty_raw = EXCLUDED.specialty_raw,
                    category_168n = EXCLUDED.category_168n,
                    profile_cluster = EXCLUDED.profile_cluster,
                    out_of_168n = EXCLUDED.out_of_168n,
                    is_current = TRUE,
                    status = CASE
                        WHEN dn_app_dnline.status = 'completed' THEN 'completed'
                        ELSE 'planned'
                    END,
                    import_batch_id = EXCLUDED.import_batch_id,
                    updated_at = EXCLUDED.updated_at
                """,
                line_tuples,
                page_size=2000,
            )
        return len(line_tuples)

    def _detach_missing(self):
        """Линии года, которых нет в текущем batch → detached."""
        if not self.import_batch:
            return
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE dn_app_dnline
                SET is_current = FALSE,
                    status = 'detached',
                    updated_at = %s
                WHERE plan_year = %s
                  AND is_current = TRUE
                  AND (import_batch_id IS DISTINCT FROM %s)
                """,
                [timezone.now(), self.year, self.import_batch.id],
            )
            detached_lines = c.rowcount
            # Person detached if no current lines this year
            c.execute(
                """
                UPDATE dn_app_person p
                SET is_detached = TRUE, detached_date = %s
                WHERE EXISTS (
                    SELECT 1 FROM dn_app_dnline l
                    WHERE l.person_id = p.id AND l.plan_year = %s
                )
                AND NOT EXISTS (
                    SELECT 1 FROM dn_app_dnline l
                    WHERE l.person_id = p.id AND l.plan_year = %s AND l.is_current = TRUE
                )
                """,
                [timezone.now(), self.year, self.year],
            )
            self.stats["detached"] = c.rowcount
            self.stats["errors"].append(f"detached_lines={detached_lines}")

    def _match_oms_and_update_lines(self):
        """Загрузить факты ОМС (цель 3 и 305) и проставить completed на линиях."""
        with connection.cursor() as c:
            c.execute(
                """
                SELECT
                    CASE WHEN t.enp = '-' THEN t.policy ELSE t.enp END AS enp,
                    CASE WHEN t.main_diagnosis = '-' THEN NULL
                         ELSE UPPER(SPLIT_PART(t.main_diagnosis, ' ', 1)) END AS ds1,
                    t.additional_diagnosis,
                    t.talon,
                    COALESCE(t.goal, '') AS goal,
                    COALESCE(t.treatment_end, '') AS treatment_end,
                    COALESCE(t.status, '') AS status,
                    COALESCE(t.doctor, '') AS doctor
                FROM load_data_talons t
                WHERE t.goal IN ('3', '305')
                  AND (
                        (t.report_year ~ '^[0-9]+$' AND t.report_year::int = %s)
                        OR (
                            COALESCE(NULLIF(t.report_year, '-'), '') !~ '^[0-9]+$'
                            AND t.treatment_end ~ '^[0-9]{2}-[0-9]{2}-[0-9]{4}$'
                            AND EXTRACT(YEAR FROM TO_DATE(t.treatment_end, 'DD-MM-YYYY')) = %s
                        )
                      )
                """,
                [self.year, self.year],
            )
            oms_rows = c.fetchall()

        if not oms_rows:
            with connection.cursor() as c:
                c.execute(
                    """
                    UPDATE dn_app_dnline
                    SET status = 'not_completed', updated_at = %s
                    WHERE plan_year = %s
                      AND is_current = TRUE
                      AND status = 'planned'
                      AND out_of_168n = FALSE
                    """,
                    [timezone.now(), self.year],
                )
            return

        # person ids
        enps = list({r[0] for r in oms_rows if r[0]})
        with connection.cursor() as c:
            c.execute("SELECT id, enp FROM dn_app_person WHERE enp = ANY(%s)", [enps])
            person_by_enp = {e: i for i, e in c.fetchall()}

        fact_tuples = []
        for enp, ds1, add, talon, goal, tend, status, doctor in oms_rows:
            codes = set()
            if ds1:
                codes.add(extract_mkb(ds1))
            if add and str(add) not in ("-", "", "None"):
                for part in re.split(r"[,;]", str(add)):
                    code = extract_mkb(part)
                    if code:
                        codes.add(code)
                    for tok in str(part).upper().split():
                        c2 = extract_mkb(tok)
                        if c2:
                            codes.add(c2)
            if not codes:
                codes.add("")
            pid = person_by_enp.get(enp)
            if not pid:
                # create stub person for fact-only
                Person.objects.get_or_create(
                    enp=enp, defaults={"fio": enp, "dr": None}
                )
                pid = Person.objects.filter(enp=enp).values_list("id", flat=True).first()
            for code in codes:
                fact_tuples.append(
                    (
                        pid,
                        enp,
                        code[:32],
                        self.year,
                        DnFact.SOURCE_OMS,
                        (talon or "")[:64],
                        (goal or "")[:32],
                        (tend or "")[:32],
                        (status or "")[:64],
                        (doctor or "")[:255],
                        "",
                        timezone.now(),
                    )
                )

        if fact_tuples:
            with connection.cursor() as c:
                # delete old oms facts for year then insert (simpler than complex unique)
                c.execute(
                    """
                    DELETE FROM dn_app_dnfact
                    WHERE source = %s AND report_year = %s
                    """,
                    [DnFact.SOURCE_OMS, self.year],
                )
                execute_values(
                    c,
                    """
                    INSERT INTO dn_app_dnfact (
                        person_id, enp, ds_code, report_year, source,
                        talon, goal, treatment_end, status, doctor, raw_diagnosis, created_at
                    ) VALUES %s
                    ON CONFLICT ON CONSTRAINT dn_fact_uniq_source_enp_ds_year_talon DO NOTHING
                    """,
                    fact_tuples,
                    page_size=2000,
                )
                self.stats["facts_oms"] = len(fact_tuples)

        # Update lines: completed if goal=3 fact matches ds_code for same enp
        # PostgreSQL: UPDATE target alias cannot be referenced inside FROM…JOIN ON —
        # join person via WHERE (p.id = l.person_id).
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE dn_app_dnline AS l
                SET status = 'completed',
                    talon_number = f.talon,
                    actual_date = CASE
                        WHEN f.treatment_end ~ '^[0-9]{2}-[0-9]{2}-[0-9]{4}$'
                          THEN TO_DATE(f.treatment_end, 'DD-MM-YYYY')
                        WHEN f.treatment_end ~ '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{4}'
                          THEN TO_DATE(SUBSTRING(f.treatment_end FROM 1 FOR 10), 'DD.MM.YYYY')
                        ELSE l.actual_date
                    END,
                    updated_at = %s
                FROM dn_app_dnfact AS f
                JOIN dn_app_person AS p ON p.enp = f.enp
                WHERE l.person_id = p.id
                  AND l.plan_year = %s
                  AND l.is_current = TRUE
                  AND l.status <> 'detached'
                  AND f.source = %s
                  AND f.report_year = %s
                  AND f.goal = '3'
                  AND f.ds_code <> ''
                  AND (
                    f.ds_code = l.ds_code
                    OR f.ds_code LIKE l.ds_code || '%%'
                    OR l.ds_code LIKE f.ds_code || '%%'
                  )
                """,
                [timezone.now(), self.year, DnFact.SOURCE_OMS, self.year],
            )
            matched = c.rowcount
            c.execute(
                """
                UPDATE dn_app_dnline
                SET status = 'not_completed', updated_at = %s
                WHERE plan_year = %s
                  AND is_current = TRUE
                  AND status = 'planned'
                  AND out_of_168n = FALSE
                """,
                [timezone.now(), self.year],
            )
            self.stats["matched_lines"] = matched


# backward-compatible aliases used by management commands
DNIszlSync = DNBulkSync
