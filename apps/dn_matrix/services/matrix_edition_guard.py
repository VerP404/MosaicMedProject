"""Правила кодов редакций матрицы ДН — только dn_* вне тестов."""

from __future__ import annotations

import re
import sys

from django.conf import settings
from django.core.exceptions import ValidationError

PRODUCTION_CODE_RE = re.compile(r"^dn_[a-z0-9_]+$")

JUNK_CODE_PREFIXES = (
    "dup-",
    "dup_",
    "test-",
    "test_",
    "tmp-",
    "tmp_",
    "debug-",
    "debug_",
)


def matrix_edition_guard_enabled() -> bool:
    if not getattr(settings, "MATRIX_EDITION_CODE_GUARD", True):
        return False
    argv = " ".join(sys.argv).lower()
    if "pytest" in argv or " test" in f" {argv} " or argv.endswith(" test"):
        return False
    if getattr(settings, "TESTING", False):
        return False
    return True


def is_production_matrix_edition_code(code: str) -> bool:
    return bool(PRODUCTION_CODE_RE.match((code or "").strip()))


def is_junk_matrix_edition_code(code: str) -> bool:
    normalized = (code or "").strip()
    if not normalized:
        return True
    return not is_production_matrix_edition_code(normalized)


def validate_matrix_edition_code(code: str) -> None:
    if not matrix_edition_guard_enabled():
        return
    normalized = (code or "").strip()
    if not normalized:
        raise ValidationError({"code": "Укажите код редакции."})
    lower = normalized.lower()
    for prefix in JUNK_CODE_PREFIXES:
        if lower.startswith(prefix):
            raise ValidationError(
                {
                    "code": (
                        f"Код «{normalized}» зарезервирован для отладки/тестов и не может быть создан "
                        "в рабочей базе. Удалите лишние редакции и используйте импорт bundle (dn_*)."
                    )
                }
            )
    if not is_production_matrix_edition_code(normalized):
        raise ValidationError(
            {
                "code": (
                    "Код редакции должен начинаться с «dn_» и содержать только латиница, цифры и «_» "
                    "(например dn_before_20260401). Произвольные коды в админке и API запрещены — "
                    "импортируйте матрицу из JSON-bundle."
                )
            }
        )
