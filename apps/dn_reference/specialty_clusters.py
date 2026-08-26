"""
Терапевтический кластер специальностей 168н:
ВОП / терапия / леч.дело → «Терапия».
"""
from __future__ import annotations

import re

THERAPY_CLUSTER = "Терапия"

_THERAPY_PATTERNS = (
    r"терап",
    r"воп",
    r"общ\w*\s+практик",
    r"семейн",
    r"леч\.?\s*дело",
    r"лечебн",
)


def specialty_to_cluster(name: str | None) -> str:
    """Возвращает кластер профиля для специальности (или исходное имя)."""
    if not name:
        return ""
    s = str(name).strip()
    if not s:
        return ""
    low = s.lower().replace("ё", "е")
    for pat in _THERAPY_PATTERNS:
        if re.search(pat, low):
            return THERAPY_CLUSTER
    return s


def is_therapy_specialty(name: str | None) -> bool:
    return specialty_to_cluster(name) == THERAPY_CLUSTER
