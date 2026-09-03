# -*- coding: utf-8 -*-
"""Сопоставление МКБ пациента со школой здоровья цели 307."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SchoolSpec:
    number: int
    name: str
    group_name: str
    mkb_rule: str
    visits: int
    duration: str
    tariff: str
    service_code: str
    service_title: str
    period_years: int = 3
    criterion: str = "mkb"
    min_age: int | None = None
    max_age: int | None = None


_SKIP_TOKENS = ("МКБ", "ИМТ", "ФАКТОР", "НАПРАВЛЕН", "НЕ ")


def normalize_mkb(code: str | None) -> str:
    s = str(code or "").strip().upper().replace("О", "O").replace(",", ".")
    s = s.replace(" ", "")
    if not s or s in {"-", "NAN", "NONE"}:
        return ""
    return s.split()[0]


def parse_diagnosis_codes(*parts: object) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = str(part or "")
        for token in re.split(r"[;|,]", text):
            code = normalize_mkb(token)
            if code and code not in seen:
                seen.add(code)
                codes.append(code)
    return codes


def _split_letter_num(code: str) -> tuple[str, str]:
    m = re.match(r"^([A-Z])(.+)$", code)
    if not m:
        return "", code
    return m.group(1), m.group(2)


def _mkb_key(code: str, *, as_end: bool = False) -> tuple:
    letter, rest = _split_letter_num(code)
    if "." in rest:
        a, b = rest.split(".", 1)
        try:
            return (letter, int(a), int(re.sub(r"\D", "", b) or "0"))
        except ValueError:
            return (letter, 0, 0)
    try:
        num = int(re.sub(r"\D", "", rest) or "0")
    except ValueError:
        return (letter, 0, 0)
    return (letter, num, 999 if as_end else -1)


def _in_range(code: str, start: str, end: str) -> bool:
    return _mkb_key(start) <= _mkb_key(code) <= _mkb_key(end, as_end=True)


def _prefix_match(code: str, prefix: str) -> bool:
    return code == prefix or code.startswith(prefix + ".")


def code_matches_rule(code: str, rule: str) -> bool:
    code = normalize_mkb(code)
    if not code:
        return False
    for raw in str(rule or "").split(","):
        token = raw.strip().upper().replace("О", "O")
        if not token or any(skip in token for skip in _SKIP_TOKENS):
            continue
        if "-" in token:
            a, b = [x.strip() for x in token.split("-", 1)]
            if a and b and a[0].isalpha() and b[0].isalpha():
                if _in_range(code, a, b):
                    return True
                parent = a.split(".", 1)[0]
                if parent == b.split(".", 1)[0] and code == parent:
                    return True
                continue
        if _prefix_match(code, token):
            return True
    return False


def age_years(birth: date | None, on: date | None) -> int | None:
    if not birth or not on:
        return None
    years = on.year - birth.year
    if (on.month, on.day) < (birth.month, birth.day):
        years -= 1
    return years


def _age_ok(spec: SchoolSpec, age: int | None) -> bool:
    if age is None:
        # Детская школа требует возраст; взрослые без даты рождения допускаются.
        return spec.max_age is None
    if spec.min_age is not None and age < spec.min_age:
        return False
    if spec.max_age is not None and age > spec.max_age:
        return False
    return True


def match_schools(
    codes: Sequence[str],
    catalog: Iterable[SchoolSpec],
    *,
    age: int | None = None,
) -> list[SchoolSpec]:
    """Школы, подходящие по МКБ и возрасту. СД дети — только при age < 18."""
    hits: list[SchoolSpec] = []
    seen: set[int] = set()
    norm_codes = [normalize_mkb(c) for c in codes if normalize_mkb(c)]

    for spec in catalog:
        if spec.number in seen:
            continue
        if not _age_ok(spec, age):
            continue
        if spec.criterion == "age":
            if age is not None and spec.min_age is not None and age >= spec.min_age:
                hits.append(spec)
                seen.add(spec.number)
            continue
        if spec.criterion == "risk":
            if any(c.startswith("Z72") for c in norm_codes):
                hits.append(spec)
                seen.add(spec.number)
            continue
        if spec.criterion == "bmi":
            if any(c.startswith("E66") for c in norm_codes):
                hits.append(spec)
                seen.add(spec.number)
            continue
        if any(code_matches_rule(c, spec.mkb_rule) for c in norm_codes):
            hits.append(spec)
            seen.add(spec.number)
    return hits


def primary_school(
    main_code: str,
    extra_codes: Sequence[str],
    catalog: Iterable[SchoolSpec],
    *,
    age: int | None = None,
) -> tuple[SchoolSpec | None, list[SchoolSpec]]:
    catalog_list = list(catalog)
    all_codes = parse_diagnosis_codes(main_code, *extra_codes)
    hits = match_schools(all_codes, catalog_list, age=age)
    main_hits = match_schools(parse_diagnosis_codes(main_code), catalog_list, age=age)
    primary = main_hits[0] if main_hits else (hits[0] if hits else None)
    return primary, hits
