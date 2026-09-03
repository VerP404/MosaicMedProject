"""Рабочие дни РФ по производственному календарю (статический JSON)."""

from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Iterator

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=8)
def _load_calendar(year: int) -> tuple[frozenset[date], frozenset[date]] | None:
    path = _DATA_DIR / f"rf_calendar_{year}.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    non_working = {date.fromisoformat(s) for s in payload.get("non_working") or []}
    extra_working = {date.fromisoformat(s) for s in payload.get("extra_working") or []}
    return frozenset(non_working), frozenset(extra_working)


def is_rf_workday(day: date, *, year: int | None = None) -> bool:
    cal_year = year or day.year
    loaded = _load_calendar(cal_year)
    if loaded is None:
        return day.weekday() < 5
    non_working, extra_working = loaded
    if day in extra_working:
        return True
    if day in non_working:
        return False
    return day.weekday() < 5


def iter_rf_workdays(date_from: date, date_to: date) -> Iterator[date]:
    if date_to < date_from:
        return
    current = date_from
    while current <= date_to:
        if is_rf_workday(current):
            yield current
        current += timedelta(days=1)


def _advance_workdays(start: date, step: int) -> date:
    if step < 1:
        raise ValueError("step_workdays must be >= 1")
    current = start
    moved = 0
    guard = 0
    while moved < step:
        current += timedelta(days=1)
        guard += 1
        if guard > 730:
            raise ValueError("Не удалось найти следующий рабочий день.")
        if is_rf_workday(current):
            moved += 1
    return current


def add_rf_workdays(start: date, n: int) -> date:
    """Сдвинуть на n рабочих дней вперёд (выходные и праздники не считаются)."""
    if n < 1:
        if is_rf_workday(start):
            return start
        return _advance_workdays(start, 1)
    return _advance_workdays(start, n)


def next_unblocked_workday(day: date, blocked: set[date] | None = None) -> date:
    """Ближайший рабочий день, которого нет среди дат журнала."""
    blocked = blocked or set()
    current = day
    guard = 0
    while True:
        if is_rf_workday(current) and current not in blocked:
            return current
        current += timedelta(days=1)
        guard += 1
        if guard > 730:
            raise ValueError("Не удалось найти рабочий день без записи в журнале обращений.")


def pick_visit_dates_from_anchor(
    anchor: date,
    *,
    visits: int = 3,
    step_workdays: int = 1,
    offset_workdays: int = 5,
    blocked: set[date] | None = None,
) -> list[str]:
    """
    Явки от даты приёма в журнале: первая = якорь + offset рабочих дней,
    далее шаг step_workdays, даты из журнала (blocked) пропускаются.
    """
    if visits < 1:
        raise ValueError("visits must be >= 1")
    if step_workdays < 1:
        raise ValueError("step_workdays must be >= 1")
    blocked = set(blocked or [])
    first = next_unblocked_workday(add_rf_workdays(anchor, offset_workdays), blocked)
    dates = [first]
    cursor = first
    for _ in range(visits - 1):
        cursor = next_unblocked_workday(_advance_workdays(cursor, step_workdays), blocked)
        dates.append(cursor)
    return [format_visit_ui_date(d) for d in dates]


def format_visit_ui_date(day: date) -> str:
    """dd-mm-yy для web.ОМС."""
    return day.strftime("%d-%m-%y")


def pick_visit_dates(
    date_from: date,
    date_to: date,
    *,
    visits: int = 3,
    step_workdays: int = 1,
    rng,
) -> list[str]:
    """
    Даты явок в формате dd-mm-yy.
    step_workdays=1 — подряд идущие рабочие дни; 2 — через один рабочий день.
    """
    if visits < 1:
        raise ValueError("visits must be >= 1")
    if step_workdays not in (1, 2):
        raise ValueError("step_workdays must be 1 or 2")

    workdays = list(iter_rf_workdays(date_from, date_to))
    if not workdays:
        raise ValueError("В указанном интервале нет рабочих дней.")

    eligible: list[date] = []
    for start in workdays:
        cursor = start
        ok = True
        for _ in range(visits - 1):
            try:
                nxt = _advance_workdays(cursor, step_workdays)
            except ValueError:
                ok = False
                break
            if nxt > date_to:
                ok = False
                break
            cursor = nxt
        if ok:
            eligible.append(start)

    if not eligible:
        raise ValueError(
            f"Недостаточно рабочих дней для {visits} явок (шаг {step_workdays}) в интервале "
            f"{date_from.isoformat()} — {date_to.isoformat()}."
        )

    start = eligible[int(rng.randint(0, len(eligible) - 1))]
    dates = [start]
    cursor = start
    for _ in range(visits - 1):
        cursor = _advance_workdays(cursor, step_workdays)
        dates.append(cursor)
    return [format_visit_ui_date(d) for d in dates]
