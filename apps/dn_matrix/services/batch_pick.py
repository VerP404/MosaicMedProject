"""Пакетный подбор услуг матрицы ДН для списков (не прошедшие и т.п.)."""
from __future__ import annotations

import re
from typing import Any

from apps.dn_matrix.models import DnSpecialty, MatrixEdition
from apps.dn_matrix.services.matrix import (
    MatrixPickCache,
    build_matrix_pick_cache,
    normalize_mkb,
    select_services_from_cache,
)
from apps.dn_matrix.services.pick_pricing import format_amount, sum_services_amount
from apps.dn_reference.specialty_clusters import THERAPY_CLUSTER, is_therapy_specialty, specialty_to_cluster

COL_SERVICES = "Услуги матрицы"
COL_UNAVAILABLE = "Не проводится (матрица)"
COL_SUM_1 = "Сумма 1 явка"
COL_SUM_2 = "Сумма 2 явки"
COL_SUM_3 = "Сумма 3 явки"
COL_NOTE = "Матрица: примечание"

_SPLIT_MKB = re.compile(r"[,;/|]+")


def parse_mkb_list(raw: str | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for part in _SPLIT_MKB.split(str(raw or "")):
        code = normalize_mkb(part)
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(code)
    return out


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        val = row.get(key)
        if val is None:
            continue
        text = str(val).strip()
        if text:
            return text
    return ""


def _therapy_rank(title: str) -> int:
    low = (title or "").lower().replace("ё", "е")
    if "участков" in low:
        return 0
    if "общ" in low and "практик" in low:
        return 1
    if "воп" in low:
        return 1
    if "терап" in low:
        return 2
    return 9


def resolve_specialty_id(
    cache: MatrixPickCache,
    specialties: list[DnSpecialty],
    *,
    profile: str,
    mkb_code: str,
) -> int | None:
    diagnosis_id = cache.mkb_to_diagnosis_id.get(normalize_mkb(mkb_code))
    linked = [s for s in specialties if diagnosis_id is not None and (diagnosis_id, s.id) in cache.diagnosis_specialty]
    pool = linked or list(specialties)
    if not pool:
        return None

    profile_n = (profile or "").strip()
    cluster = specialty_to_cluster(profile_n) or profile_n

    def by_title(items: list[DnSpecialty], needle: str) -> DnSpecialty | None:
        n = needle.lower().replace("ё", "е")
        for s in items:
            if (s.title or "").lower().replace("ё", "е") == n:
                return s
        return None

    exact = by_title(pool, profile_n)
    if exact:
        return exact.id

    if cluster == THERAPY_CLUSTER:
        therapy = [s for s in pool if is_therapy_specialty(s.title)]
        if therapy:
            therapy.sort(key=lambda s: (_therapy_rank(s.title), s.sort_order, s.id))
            return therapy[0].id

    clustered = [s for s in pool if specialty_to_cluster(s.title) == cluster]
    if len(clustered) == 1:
        return clustered[0].id
    if clustered:
        clustered.sort(key=lambda s: (s.sort_order, s.id))
        return clustered[0].id

    if len(linked) == 1:
        return linked[0].id
    return None


def _format_codes(services: list[dict]) -> tuple[str, str]:
    included: list[str] = []
    skipped: list[str] = []
    for row in services:
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        if row.get("unavailable"):
            skipped.append(code)
        else:
            included.append(code)
    return ", ".join(included), ", ".join(skipped)


def _visit_sums(services: list[dict], max_visits: int) -> tuple[str, str, str]:
    amounts: list[str] = []
    for n in (1, 2, 3):
        if n > max_visits:
            amounts.append("")
            continue
        total, _ = sum_services_amount(services, n, max_visits=max_visits)
        amounts.append(format_amount(total))
    return amounts[0], amounts[1], amounts[2]


def _set_matrix_cols(
    row: dict[str, Any],
    *,
    services: str = "",
    unavailable: str = "",
    sum1: str = "",
    sum2: str = "",
    sum3: str = "",
    note: str = "",
) -> dict[str, Any]:
    row[COL_SERVICES] = services
    row[COL_UNAVAILABLE] = unavailable
    row[COL_SUM_1] = sum1
    row[COL_SUM_2] = sum2
    row[COL_SUM_3] = sum3
    row[COL_NOTE] = note
    return row


def enrich_not_passed_rows(
    rows: list[dict[str, Any]],
    edition: MatrixEdition,
    *,
    grouped: bool,
) -> tuple[list[dict[str, Any]], str]:
    """Добавляет колонки набора услуг. Не меняет исходные dict in-place копии."""
    if not rows:
        return [], "Нет строк для подбора."

    cache = build_matrix_pick_cache(edition)
    specialties = list(edition.specialties.all().order_by("sort_order", "id"))
    max_visits = min(max(int(edition.max_doctor_visits or 3), 1), 3)
    memo: dict[tuple, tuple[str, str, str, str, str, str]] = {}
    spec_memo: dict[tuple[str, str], int | None] = {}

    out: list[dict[str, Any]] = []
    empty_diag = 0
    no_spec = 0
    no_link = 0

    for raw in rows:
        row = dict(raw)
        if grouped:
            mkb = _first_present(row, ("Основной МКБ", "main_mkb"))
            secondary = parse_mkb_list(_first_present(row, ("Сопутствующие МКБ", "accompanying")))
            profile = _first_present(row, ("Профиль", "main_profile"))
        else:
            mkb = _first_present(row, ("МКБ", "ds_code", "Основной МКБ"))
            secondary = []
            profile = _first_present(row, ("Профиль", "profile_cluster"))

        if not mkb:
            _set_matrix_cols(row, note="нет МКБ")
            empty_diag += 1
            out.append(row)
            continue

        spec_key = (profile, mkb)
        if spec_key not in spec_memo:
            spec_memo[spec_key] = resolve_specialty_id(cache, specialties, profile=profile, mkb_code=mkb)
        specialty_id = spec_memo[spec_key]
        if specialty_id is None:
            _set_matrix_cols(row, note="нет специальности матрицы для профиля")
            no_spec += 1
            out.append(row)
            continue

        pick_key = (specialty_id, mkb, tuple(secondary))
        if pick_key not in memo:
            services, _, diagnosis_id = select_services_from_cache(
                cache,
                specialty_id=specialty_id,
                mkb_code=mkb,
                secondary_mkb_list=secondary or None,
            )
            codes, skipped = _format_codes(services)
            sum1, sum2, sum3 = _visit_sums(services, max_visits)
            if diagnosis_id is None:
                note = "диагноз не найден в матрице"
            elif not services:
                note = "нет услуг по правилам матрицы"
            else:
                note = ""
            memo[pick_key] = (codes, skipped, note, sum1, sum2, sum3)

        codes, skipped, note, sum1, sum2, sum3 = memo[pick_key]
        if note == "диагноз не найден в матрице" or note == "нет услуг по правилам матрицы":
            no_link += 1
        _set_matrix_cols(
            row,
            services=codes,
            unavailable=skipped,
            sum1=sum1,
            sum2=sum2,
            sum3=sum3,
            note=note,
        )
        out.append(row)

    status = (
        f"{edition.title}: услуг по матрице для {len(out)} строк "
        f"(уникальных комбинаций {len(memo)}). "
        f"Без МКБ: {empty_diag}, без специальности: {no_spec}, пустой подбор: {no_link}."
    )
    return out, status
