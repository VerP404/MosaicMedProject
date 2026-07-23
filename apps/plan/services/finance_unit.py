"""
Единица отображения/ввода финансов плана и факта.

В БД amount всегда в рублях (до копейки). «Тыс. руб.» — только UI:
при вводе ×1000, при показе ÷1000. План и факт масштабируются одинаково,
% считается до масштабирования (или после — математически то же).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

FINANCE_UNIT_RUBLES = "rubles"
FINANCE_UNIT_THOUSANDS = "thousands"
FINANCE_UNIT_CHOICES = (
    (FINANCE_UNIT_RUBLES, "Рубли"),
    (FINANCE_UNIT_THOUSANDS, "Тысячи рублей"),
)
FINANCE_UNIT_DROPDOWN_OPTIONS = [
    {"label": "Руб.", "value": FINANCE_UNIT_RUBLES},
    {"label": "Тыс. руб.", "value": FINANCE_UNIT_THOUSANDS},
]

_FACTOR = Decimal("1000")
_Q2 = Decimal("0.01")

# Денежные поля SVPOD / похожих таблиц (не трогать «%», подписи)
SVPOD_MONEY_KEYS = (
    "План",
    "Факт",
    "Остаток",
    "План 1/12",
    "Входящий остаток",
    "новые",
    "в_тфомс",
    "оплачено",
    "исправлено",
    "отказано",
    "отменено",
    "План (сумма)",
    "Факт (сумма)",
)


def normalize_finance_unit(unit: str | None) -> str:
    raw = (unit or FINANCE_UNIT_RUBLES).strip().lower()
    if raw in (
        FINANCE_UNIT_THOUSANDS,
        "thousand",
        "thousands",
        "тыс",
        "тыс.",
        "тыс.руб",
        "тыс. руб.",
        "k",
    ):
        return FINANCE_UNIT_THOUSANDS
    return FINANCE_UNIT_RUBLES


def finance_unit_label(unit: str | None) -> str:
    u = normalize_finance_unit(unit)
    return "тыс. руб." if u == FINANCE_UNIT_THOUSANDS else "руб."


def get_default_finance_unit() -> str:
    """Предпочтительная единица из MainSettings (по умолчанию рубли)."""
    try:
        from apps.home.models import MainSettings

        settings = MainSettings.objects.first()
        if settings is not None:
            return normalize_finance_unit(getattr(settings, "finance_plan_unit", None))
    except Exception:
        pass
    return FINANCE_UNIT_RUBLES


def _to_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def rubles_to_display(value: Any, unit: str | None) -> float:
    """Рубли из БД → число для UI."""
    amount = _to_decimal(value)
    if normalize_finance_unit(unit) == FINANCE_UNIT_THOUSANDS:
        amount = (amount / _FACTOR).quantize(_Q2, rounding=ROUND_HALF_UP)
    else:
        amount = amount.quantize(_Q2, rounding=ROUND_HALF_UP)
    return float(amount)


def display_to_rubles(value: Any, unit: str | None) -> float:
    """Число из UI → рубли для БД."""
    amount = _to_decimal(value)
    if normalize_finance_unit(unit) == FINANCE_UNIT_THOUSANDS:
        amount = (amount * _FACTOR).quantize(_Q2, rounding=ROUND_HALF_UP)
    else:
        amount = amount.quantize(_Q2, rounding=ROUND_HALF_UP)
    return float(amount)


def scale_month_map(
    month_map: Mapping[str, Any] | None,
    unit: str | None,
    *,
    to_display: bool,
) -> dict[str, float]:
    """Помесячная карта amount: to_display=True → UI, False → рубли."""
    src = month_map or {}
    out: dict[str, float] = {}
    convert = rubles_to_display if to_display else display_to_rubles
    for m in range(1, 13):
        key = str(m)
        out[key] = convert(src.get(key, 0), unit)
    return out


def convert_month_map_units(
    month_map: Mapping[str, Any] | None,
    from_unit: str | None,
    to_unit: str | None,
) -> dict[str, float]:
    """Перевод карты между единицами UI через канонические рубли."""
    fu = normalize_finance_unit(from_unit)
    tu = normalize_finance_unit(to_unit)
    if fu == tu:
        return scale_month_map(month_map, fu, to_display=True)
    rubles = scale_month_map(month_map, fu, to_display=False)
    return scale_month_map(rubles, tu, to_display=True)


def scale_kind_payload_amounts(payload: dict | None, unit: str | None, *, to_display: bool) -> dict:
    """Масштабировать org_amount / buildings[].amount в одной версии плана."""
    out = dict(payload or {})
    out["org_amount"] = scale_month_map(out.get("org_amount"), unit, to_display=to_display)
    out["org_amt_total"] = round(sum(out["org_amount"].values()), 2)
    buildings = []
    for b in out.get("buildings") or []:
        row = dict(b)
        row["amount"] = scale_month_map(row.get("amount"), unit, to_display=to_display)
        row["amt_total"] = round(sum(row["amount"].values()), 2)
        buildings.append(row)
    out["buildings"] = buildings
    return out


def scale_dual_payload_amounts(payload: dict | None, unit: str | None, *, to_display: bool) -> dict:
    """Масштабировать tfoms/internal в dual-payload формы ввода."""
    out = dict(payload or {})
    for kind in ("tfoms", "internal"):
        if kind in out and isinstance(out[kind], dict):
            out[kind] = scale_kind_payload_amounts(out[kind], unit, to_display=to_display)
    return out


def convert_dual_payload_units(
    payload: dict | None,
    from_unit: str | None,
    to_unit: str | None,
) -> dict:
    fu = normalize_finance_unit(from_unit)
    tu = normalize_finance_unit(to_unit)
    if fu == tu:
        return dict(payload or {})
    rubles = scale_dual_payload_amounts(payload, fu, to_display=False)
    return scale_dual_payload_amounts(rubles, tu, to_display=True)


def scale_money_value_in_row(
    row: MutableMapping[str, Any],
    keys: Iterable[str],
    unit: str | None,
) -> None:
    """In-place: рубли → display для перечисленных ключей."""
    if normalize_finance_unit(unit) == FINANCE_UNIT_RUBLES:
        return
    for key in keys:
        if key in row and row[key] is not None:
            try:
                row[key] = rubles_to_display(row[key], unit)
            except Exception:
                pass


def scale_rows_money(
    rows: Sequence[Mapping[str, Any]] | None,
    unit: str | None,
    keys: Sequence[str] = SVPOD_MONEY_KEYS,
) -> list[dict]:
    """Копия строк с масштабированием денежных полей (для отчётов)."""
    if not rows:
        return []
    if normalize_finance_unit(unit) == FINANCE_UNIT_RUBLES:
        return [dict(r) for r in rows]
    out = []
    for r in rows:
        row = dict(r)
        scale_money_value_in_row(row, keys, unit)
        out.append(row)
    return out


def scale_pivoted_finance_records(
    records: Sequence[Mapping[str, Any]] | None,
    unit: str | None,
    *,
    layout: str | None = None,
) -> list[dict]:
    """
    Масштабировать свод «Индикаторы по корпусам».
    % не трогаем. Для layout с месяцами — строки Показатель ∈ {План, Факт, Остаток}.
    """
    if not records:
        return []
    if normalize_finance_unit(unit) == FINANCE_UNIT_RUBLES:
        return [dict(r) for r in records]

    money_labels = {"План", "Факт", "Остаток"}
    skip_cols = {"Индикатор", "Корпус", "Показатель", "%"}
    out: list[dict] = []
    for r in records:
        row = dict(r)
        if layout == "indicator_building_months" or "Показатель" in row:
            if row.get("Показатель") in money_labels:
                for col, val in list(row.items()):
                    if col in skip_cols:
                        continue
                    try:
                        row[col] = rubles_to_display(val, unit)
                    except Exception:
                        pass
        else:
            for col in ("План", "Факт", "Остаток"):
                if col in row and row[col] is not None:
                    try:
                        row[col] = rubles_to_display(row[col], unit)
                    except Exception:
                        pass
        out.append(row)
    return out
