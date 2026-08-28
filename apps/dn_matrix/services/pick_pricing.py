"""Расчёт суммы подобранных услуг ДН (цена × количество, явки для per-visit)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def _clean_title(title: str) -> str:
    return (title or "").strip()


def is_per_visit_service(title: str) -> bool:
    """Услуги «Диспансерный прием …» умножаются на число явок."""
    return "диспансерный прием" in _clean_title(title).lower()


def parse_price_amount(raw: str | Decimal | float | int | None) -> Decimal | None:
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return raw
    text = str(raw).strip().replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def service_line_qty(title: str, visits: int, *, max_visits: int = 3) -> int:
    cap = min(max(int(max_visits), 1), 3)
    visits = max(1, min(cap, int(visits)))
    return visits if is_per_visit_service(title) else 1


def sum_services_amount(
    services: list[dict[str, Any]],
    visits: int,
    *,
    max_visits: int = 3,
) -> tuple[Decimal, bool]:
    """
    Сумма по списку услуг pick. Возвращает (amount, missing_prices).
    missing_prices=True, если хотя бы у одной услуги нет цены.
    """
    total = Decimal("0")
    missing_prices = False
    for row in services:
        title = str(row.get("title") or "")
        amt = parse_price_amount(row.get("price"))
        if amt is None:
            missing_prices = True
            continue
        qty = service_line_qty(title, visits, max_visits=max_visits)
        total += amt * qty
    return total, missing_prices


def format_amount(amount: Decimal) -> str:
    return f"{amount.quantize(Decimal('0.01'))}"
