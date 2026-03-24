from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from apps.dash_dn.sqlite_catalog.db import ensure_database

TABLES_DELETE_ORDER = [
    "dn_service_requirement",
    "dn_service_price",
    "dn_diagnosis_group_membership",
    "dn_diagnosis_specialty",
    "dn_diagnosis",
    "dn_service",
    "dn_service_price_period",
    "dn_diagnosis_group",
    "dn_specialty",
    "dn_diagnosis_category",
]

TABLES_INSERT_ORDER = list(reversed(TABLES_DELETE_ORDER))

FK_MAP = {
    "dn_diagnosis": {"category_id": "dn_diagnosis_category"},
    "dn_diagnosis_specialty": {"diagnosis_id": "dn_diagnosis", "specialty_id": "dn_specialty"},
    "dn_diagnosis_group_membership": {
        "group_id": "dn_diagnosis_group",
        "diagnosis_id": "dn_diagnosis",
    },
    "dn_service_price": {"service_id": "dn_service", "period_id": "dn_service_price_period"},
    "dn_service_requirement": {
        "service_id": "dn_service",
        "group_id": "dn_diagnosis_group",
        "specialty_id": "dn_specialty",
    },
}


def _table_columns(conn: Connection, table: str) -> list[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return [r[1] for r in rows]


def export_catalog(conn: Connection, catalog: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "format": "dash_dn_catalog",
        "version": 1,
        "catalog": catalog,
        "tables": {},
    }
    for table in TABLES_INSERT_ORDER:
        cols = _table_columns(conn, table)
        q = text(f"SELECT {', '.join(cols)} FROM {table} WHERE catalog = :c")
        rows = conn.execute(q, {"c": catalog}).mappings().all()
        payload["tables"][table] = [dict(r) for r in rows]
    return payload


def _delete_catalog(conn: Connection, catalog: str) -> None:
    for t in TABLES_DELETE_ORDER:
        conn.execute(text(f"DELETE FROM {t} WHERE catalog = :c"), {"c": catalog})


def _remap_fk(
    val: Any,
    fk_table: str,
    id_maps: dict[str, dict[int, int]],
) -> Any:
    if val is None:
        return None
    m = id_maps.get(fk_table)
    if m is None:
        return val
    return m.get(int(val), val)


def import_catalog(
    conn: Connection,
    data: Mapping[str, Any],
    *,
    target_catalog: str | None = None,
) -> None:
    if data.get("format") != "dash_dn_catalog":
        raise ValueError("Неизвестный формат JSON (ожидается dash_dn_catalog)")
    cat = target_catalog or data.get("catalog") or "global"
    tables: dict[str, list] = data.get("tables") or {}
    _delete_catalog(conn, cat)
    id_maps: dict[str, dict[int, int]] = {t: {} for t in TABLES_INSERT_ORDER}

    for table in TABLES_INSERT_ORDER:
        rows = tables.get(table) or []
        cols = _table_columns(conn, table)
        fk = FK_MAP.get(table, {})
        for row in rows:
            insert_row = {}
            for c in cols:
                if c == "id":
                    continue
                if c == "catalog":
                    insert_row[c] = cat
                    continue
                val = row.get(c)
                if c in fk:
                    val = _remap_fk(val, fk[c], id_maps)
                insert_row[c] = val
            keys = list(insert_row.keys())
            placeholders = ", ".join(f":{k}" for k in keys)
            q = text(
                f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({placeholders})"
            )
            res = conn.execute(q, insert_row)
            old_id = row.get("id")
            if old_id is not None and res.lastrowid is not None:
                id_maps.setdefault(table, {})[int(old_id)] = int(res.lastrowid)


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_diagnosis_group(conn: Connection, catalog: str, group_id: int) -> int:
    """Удалить группу диагнозов (membership и требования услуг — CASCADE). Возвращает число удалённых строк."""
    res = conn.execute(
        text("DELETE FROM dn_diagnosis_group WHERE id = :id AND catalog = :c"),
        {"id": int(group_id), "c": catalog},
    )
    return int(res.rowcount or 0)


def copy_global_to_user(engine: Engine) -> None:
    with engine.begin() as conn:
        data = export_catalog(conn, "global")
        data["catalog"] = "user"
        import_catalog(conn, data, target_catalog="user")


def seed_if_empty(engine: Engine, seed_path: Path) -> None:
    if not seed_path.is_file():
        return
    with engine.begin() as conn:
        n = conn.execute(
            text("SELECT COUNT(*) FROM dn_diagnosis_category WHERE catalog = 'global'")
        ).scalar()
        if int(n or 0) > 0:
            return
        data = load_json_file(seed_path)
        import_catalog(conn, data, target_catalog="global")


def init_app_database(engine: Engine | None = None, seed_path: Path | None = None) -> Engine:
    from apps.dash_dn.sqlite_catalog.paths import SEED_GLOBAL_JSON

    eng = ensure_database(engine)
    seed_if_empty(eng, seed_path or SEED_GLOBAL_JSON)
    return eng
