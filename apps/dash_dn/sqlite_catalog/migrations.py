"""
Миграции SQLite dash_dn: снятие CHECK catalog IN ('global','user'), реестр каталогов.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from apps.dash_dn.sqlite_catalog.catalog_ops import (
    TABLES_DELETE_ORDER,
    export_catalog,
    import_catalog,
)


def _table_has_legacy_catalog_check(conn: Connection, table: str) -> bool:
    row = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name = :t"),
        {"t": table},
    ).fetchone()
    if not row or not row[0]:
        return False
    s = row[0].upper().replace(" ", "")
    return "CHECK(CATALOGIN('GLOBAL','USER'))" in s or "CHECK(CATALOGIN(\"GLOBAL\",\"USER\"))" in s


def needs_legacy_catalog_migration(conn: Connection) -> bool:
    return _table_has_legacy_catalog_check(conn, "dn_service")


def _ensure_registry_table(conn: Connection) -> None:
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS dn_catalog_registry (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            effective_from TEXT,
            effective_to TEXT,
            read_only INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )


def _distinct_catalog_slugs(conn: Connection) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT catalog AS c FROM dn_diagnosis_category WHERE catalog IS NOT NULL AND catalog != ''
            UNION
            SELECT DISTINCT catalog FROM dn_specialty WHERE catalog IS NOT NULL AND catalog != ''
            UNION
            SELECT DISTINCT catalog FROM dn_service WHERE catalog IS NOT NULL AND catalog != ''
            """
        )
    ).fetchall()
    slugs = sorted({str(r[0]) for r in rows if r[0]})
    return slugs


def backfill_catalog_registry(conn: Connection) -> None:
    """Добавить в реестр известные slug из данных и подписи user / global (наследие)."""
    _ensure_registry_table(conn)
    defaults = [
        ("global", "Каталог global (наследие, не в навбаре)", 0),
        ("user", "Рабочая копия (ваши правки и цены)", 0),
    ]
    for slug, title, ro in defaults:
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO dn_catalog_registry (slug, title, read_only)
                VALUES (:slug, :title, :ro)
                """
            ),
            {"slug": slug, "title": title, "ro": ro},
        )
    # Подтянуть подписи, если база создана со старыми формулировками
    conn.execute(
        text(
            """
            UPDATE dn_catalog_registry SET title = 'Каталог global (наследие, не в навбаре)'
            WHERE slug = 'global' AND title IN ('Общий эталон', 'global', 'Global', 'Общий справочник (основной)')
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE dn_catalog_registry SET title = 'Рабочая копия (ваши правки и цены)'
            WHERE slug = 'user' AND title IN ('Локальный слой', 'user', 'User', 'Локальный слой — эталон не меняется')
            """
        )
    )
    for slug in _distinct_catalog_slugs(conn):
        ro = 1 if slug.startswith("matrix_") else 0
        disp = (
            "Каталог global (наследие, не в навбаре)"
            if slug == "global"
            else (
                "Рабочая копия (ваши правки и цены)"
                if slug == "user"
                else f"Снимок матрицы ({slug})"
            )
        )
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO dn_catalog_registry (slug, title, read_only)
                VALUES (:slug, :title, :ro)
                """
            ),
            {"slug": slug, "title": disp, "ro": ro},
        )
    _sync_matrix_period_labels(conn)


def _sync_matrix_period_labels(conn: Connection) -> None:
    """Подписи для двух организационных снимков (slug из DASH_DN_MATRIX_*)."""
    try:
        from apps.dash_dn.catalog_periods import matrix_catalog_after, matrix_catalog_before
    except Exception:
        return
    pairs = [
        (matrix_catalog_before(), "До 01.04.2026", 1),
        (matrix_catalog_after(), "С 01.04.2026 (действующие)", 1),
    ]
    for slug, title, ro in pairs:
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO dn_catalog_registry (slug, title, read_only)
                VALUES (:slug, :title, :ro)
                """
            ),
            {"slug": slug, "title": title, "ro": ro},
        )
        conn.execute(
            text(
                """
                UPDATE dn_catalog_registry
                SET title = :title, read_only = :ro
                WHERE slug = :slug
                """
            ),
            {"slug": slug, "title": title, "ro": ro},
        )


def upsert_catalog_registry_row(
    conn: Connection,
    *,
    slug: str,
    title: str,
    effective_from: str | None = None,
    effective_to: str | None = None,
    read_only: int | None = None,
) -> None:
    _ensure_registry_table(conn)
    ro = int(read_only) if read_only is not None else (1 if slug.startswith("matrix_") else 0)
    conn.execute(text("DELETE FROM dn_catalog_registry WHERE slug = :slug"), {"slug": slug})
    conn.execute(
        text(
            """
            INSERT INTO dn_catalog_registry (slug, title, effective_from, effective_to, read_only)
            VALUES (:slug, :title, :efrom, :eto, :ro)
            """
        ),
        {
            "slug": slug,
            "title": title,
            "efrom": effective_from,
            "eto": effective_to,
            "ro": ro,
        },
    )


def migrate_legacy_catalog_check_to_v2(conn: Connection, schema_sql: str) -> bool:
    """
    Если таблицы созданы со старым CHECK catalog — пересоздать схему и вернуть данные.
    Возвращает True, если миграция выполнена.
    """
    if not needs_legacy_catalog_migration(conn):
        _ensure_registry_table(conn)
        backfill_catalog_registry(conn)
        return False

    payloads: list[dict] = []
    for slug in _distinct_catalog_slugs(conn):
        payloads.append(export_catalog(conn, slug))

    conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        for t in TABLES_DELETE_ORDER:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
        for stmt in schema_sql.split(";"):
            s = stmt.strip()
            if not s:
                continue
            conn.exec_driver_sql(s)
    finally:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")

    for data in payloads:
        cat = data.get("catalog") or "global"
        import_catalog(conn, data, target_catalog=cat)

    conn.execute(
        text(
            "INSERT OR REPLACE INTO dn_meta(key, value) VALUES ('schema_v2_catalog', '1')"
        )
    )
    backfill_catalog_registry(conn)
    return True


def run_catalog_migrations(engine: Engine, schema_sql: str) -> None:
    with engine.begin() as conn:
        migrate_legacy_catalog_check_to_v2(conn, schema_sql)


def list_catalog_registry(conn: Connection) -> list[dict]:
    _ensure_registry_table(conn)
    rows = conn.execute(
        text(
            """
            SELECT slug, title, effective_from, effective_to, read_only
            FROM dn_catalog_registry
            ORDER BY
                CASE slug WHEN 'global' THEN 0 WHEN 'user' THEN 1 ELSE 2 END,
                COALESCE(effective_from, '') DESC,
                slug
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def catalog_nav_dropdown_options() -> list[dict]:
    """Опции выпадающего списка каталога (fallback, если реестр недоступен)."""
    from apps.dash_dn.catalog_periods import main_nav_catalog_options

    from apps.dash_dn.sqlite_catalog.db import get_engine

    try:
        with get_engine().connect() as conn:
            rows = list_catalog_registry(conn)
        if rows:
            return [{"label": r["title"], "value": r["slug"]} for r in rows]
    except Exception:
        pass
    return main_nav_catalog_options()


def catalog_quick_stats(catalog: str | None) -> dict[str, int]:
    """Сколько записей в SQLite для выбранного справочника (slug)."""
    from apps.dash_dn.catalog_periods import default_active_catalog
    from apps.dash_dn.sqlite_catalog.db import get_engine

    cat = str(catalog or default_active_catalog()).strip() or default_active_catalog()
    eng = get_engine()
    q_diag = text(
        "SELECT COUNT(*) FROM dn_diagnosis WHERE catalog = :c AND is_active = 1"
    )
    q_srv = text(
        "SELECT COUNT(*) FROM dn_service WHERE catalog = :c AND is_active = 1"
    )
    q_req = text("SELECT COUNT(*) FROM dn_service_requirement WHERE catalog = :c")
    with eng.connect() as conn:
        n_diag = int(conn.execute(q_diag, {"c": cat}).scalar() or 0)
        n_srv = int(conn.execute(q_srv, {"c": cat}).scalar() or 0)
        n_req = int(conn.execute(q_req, {"c": cat}).scalar() or 0)
    return {"diagnoses": n_diag, "services": n_srv, "matrix_rules": n_req}


def catalog_display_label(slug: str | None) -> str:
    """Подпись для UI: title из реестра или сам slug."""
    from apps.dash_dn.catalog_periods import default_active_catalog
    from apps.dash_dn.sqlite_catalog.db import get_engine

    s = str(slug or default_active_catalog()).strip() or default_active_catalog()
    try:
        with get_engine().connect() as conn:
            row = conn.execute(
                text("SELECT title FROM dn_catalog_registry WHERE slug = :slug LIMIT 1"),
                {"slug": s},
            ).fetchone()
        if row and row[0]:
            return f"{row[0]} ({s})"
    except Exception:
        pass
    return s


def delete_catalog(engine: Engine, slug: str) -> None:
    """Удалить все строки каталога slug и запись реестра."""
    if slug == "global":
        raise ValueError("Удаление каталога 'global' запрещено.")
    from apps.dash_dn.sqlite_catalog import catalog_ops as _co

    with engine.begin() as conn:
        _co._delete_catalog(conn, slug)
        conn.execute(text("DELETE FROM dn_catalog_registry WHERE slug = :s"), {"s": slug})
