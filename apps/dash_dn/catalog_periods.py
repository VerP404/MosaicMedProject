"""
Два базовых снимка матрицы (до / после 01.04.2026) + рабочая копия user.

Slug задаются через окружение, чтобы импорт и UI совпадали:
  DASH_DN_MATRIX_BEFORE  (по умолчанию matrix_before_20260401)
  DASH_DN_MATRIX_AFTER   (по умолчанию matrix_after_20260401)

Каталог global в SQLite не используется в интерфейсе; данные живут только в slug'ах
«до» и «после» (и user как копия для правок).
"""
from __future__ import annotations

import os


def _count_active_diagnoses(catalog: str) -> int:
    try:
        from sqlalchemy import text

        from apps.dash_dn.sqlite_catalog.db import get_engine

        eng = get_engine()
        with eng.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT COUNT(*) FROM dn_diagnosis WHERE catalog = :c AND is_active = 1"
                ),
                {"c": catalog},
            ).scalar()
        return int(r or 0)
    except Exception:
        return 0


def matrix_catalog_before() -> str:
    s = (os.environ.get("DASH_DN_MATRIX_BEFORE") or "matrix_before_20260401").strip()
    return s or "matrix_before_20260401"


def matrix_catalog_after() -> str:
    s = (os.environ.get("DASH_DN_MATRIX_AFTER") or "matrix_after_20260401").strip()
    return s or "matrix_after_20260401"


def default_matrix_source_for_user_copy() -> str:
    """Источник копии в user: «после», если не пусто, иначе «до»."""
    a, b = matrix_catalog_after(), matrix_catalog_before()
    if _count_active_diagnoses(a) > 0:
        return a
    return b


def default_active_catalog() -> str:
    """Первый непустой каталог: сначала «после», затем «до», затем копия правок."""
    a = matrix_catalog_after()
    b = matrix_catalog_before()
    if _count_active_diagnoses(a) > 0:
        return a
    if _count_active_diagnoses(b) > 0:
        return b
    if _count_active_diagnoses("user") > 0:
        return "user"
    return a


def main_nav_catalog_options() -> list[dict]:
    """Три пункта: до 01.04, с 01.04, рабочая копия."""
    b, a = matrix_catalog_before(), matrix_catalog_after()
    return [
        {"label": "До 01.04.2026", "value": b},
        {"label": "С 01.04.2026 (действующие)", "value": a},
        {"label": "Правки (копия)", "value": "user"},
    ]
