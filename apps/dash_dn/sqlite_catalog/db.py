from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from apps.dash_dn.sqlite_catalog.paths import get_db_path
from apps.dash_dn.sqlite_catalog.schema import SCHEMA_SQL


def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine(db_path: Path | None = None) -> Engine:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path.as_posix()}"
    eng = create_engine(url, future=True, connect_args={"check_same_thread": False})
    event.listen(eng, "connect", _set_sqlite_pragma)
    return eng


def init_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for stmt in SCHEMA_SQL.split(";"):
            s = stmt.strip()
            if s:
                conn.exec_driver_sql(s)


def ensure_database(engine: Engine | None = None) -> Engine:
    eng = engine or get_engine()
    init_schema(eng)
    return eng
