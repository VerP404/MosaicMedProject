"""ORM API для ввода планов индикатора по корпусам (объёмы+финансы, plan_kind)."""
from __future__ import annotations

from apps.organization.models import Building
from apps.plan.models import (
    AnnualPlan,
    BuildingPlan,
    GroupIndicators,
    MonthlyBuildingPlan,
    MonthlyPlan,
)


def _normalize_plan_kind(plan_kind: str | None) -> str:
    raw = (plan_kind or "internal").strip().lower()
    if raw in ("tfoms", "тфомс"):
        return AnnualPlan.PlanKind.TFOMS
    return AnnualPlan.PlanKind.INTERNAL


def _empty_month_map(*, finance: bool = False) -> dict:
    if finance:
        return {str(m): 0.0 for m in range(1, 13)}
    return {str(m): 0 for m in range(1, 13)}


def _ensure_annual_plan(group_id: int, year: int, plan_kind: str) -> AnnualPlan:
    kind = _normalize_plan_kind(plan_kind)
    ap, _ = AnnualPlan.objects.get_or_create(
        group_id=group_id,
        year=int(year),
        plan_kind=kind,
        defaults={
            "show_in_cumulative_report": False,
            "show_in_indicators_report": False,
        },
    )
    return ap


def _group_path(group_id: int) -> str:
    group = GroupIndicators.objects.filter(pk=group_id).first()
    if not group:
        return str(group_id)
    return group.get_hierarchy_display().replace(" - ", " \\ ")


def list_plan_catalog(year: int, plan_kind: str = "internal") -> list[dict]:
    """
    Каталог для ввода планов: только AnnualPlan с show_in_indicators_report=True.
    """
    kind = _normalize_plan_kind(plan_kind)
    year = int(year)
    plans = (
        AnnualPlan.objects.filter(
            year=year,
            plan_kind=kind,
            show_in_indicators_report=True,
        )
        .select_related("group")
        .prefetch_related("monthly_plans", "building_plans")
        .order_by("sort_order", "group__name")
    )
    catalog: list[dict] = []
    for ap in plans:
        qty = _empty_month_map(finance=False)
        amt = _empty_month_map(finance=True)
        for mp in ap.monthly_plans.all():
            qty[str(mp.month)] = int(mp.quantity or 0)
            amt[str(mp.month)] = float(mp.amount or 0)
        catalog.append(
            {
                "group_id": ap.group_id,
                "group_path": _group_path(ap.group_id),
                "annual_plan_id": ap.id,
                "has_buildings": ap.building_plans.exists(),
                "quantity": qty,
                "amount": amt,
                "qty_total": sum(qty.values()),
                "amt_total": round(sum(amt.values()), 2),
            }
        )
    catalog.sort(key=lambda x: x["group_path"])
    return catalog


def load_indicator_plan_form(
    year: int,
    group_id: int,
    plan_kind: str = "internal",
) -> dict:
    year = int(year)
    group_id = int(group_id)
    kind = _normalize_plan_kind(plan_kind)
    ap = _ensure_annual_plan(group_id, year, kind)

    org_qty = _empty_month_map(finance=False)
    org_amt = _empty_month_map(finance=True)
    for mp in ap.monthly_plans.all():
        org_qty[str(mp.month)] = int(mp.quantity or 0)
        org_amt[str(mp.month)] = float(mp.amount or 0)

    buildings: list[dict] = []
    for bp in ap.building_plans.select_related("building").prefetch_related(
        "monthly_building_plans"
    ):
        qty = _empty_month_map(finance=False)
        amt = _empty_month_map(finance=True)
        for mbp in bp.monthly_building_plans.all():
            qty[str(mbp.month)] = int(mbp.quantity or 0)
            amt[str(mbp.month)] = float(mbp.amount or 0)
        buildings.append(
            {
                "building_id": bp.building_id,
                "building_name": bp.building.name,
                "quantity": qty,
                "amount": amt,
                "qty_total": sum(qty.values()),
                "amt_total": round(sum(amt.values()), 2),
            }
        )
    buildings.sort(key=lambda x: x["building_name"])

    used_ids = {b["building_id"] for b in buildings}
    available_buildings = [
        {"label": b.name, "value": b.id}
        for b in Building.objects.exclude(id__in=used_ids).order_by("name")
    ]

    return {
        "group_id": group_id,
        "group_path": _group_path(group_id),
        "year": year,
        "plan_kind": kind,
        "annual_plan_id": ap.id,
        "org_quantity": org_qty,
        "org_amount": org_amt,
        "org_qty_total": sum(org_qty.values()),
        "org_amt_total": round(sum(org_amt.values()), 2),
        "buildings": buildings,
        "available_buildings": available_buildings,
    }


def add_building_to_plan(
    year: int,
    group_id: int,
    building_id: int,
    plan_kind: str = "internal",
) -> dict:
    ap = _ensure_annual_plan(int(group_id), int(year), plan_kind)
    bp, created = BuildingPlan.objects.get_or_create(annual_plan=ap, building_id=int(building_id))
    if created:
        for month in range(1, 13):
            MonthlyBuildingPlan.objects.get_or_create(
                building_plan=bp,
                month=month,
                defaults={"quantity": 0, "amount": 0},
            )
    return load_indicator_plan_form(int(year), int(group_id), plan_kind)


def _parse_qty(value) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _parse_amt(value) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def save_indicator_plan_form(
    *,
    year: int,
    group_id: int,
    plan_kind: str,
    org_quantity: dict,
    org_amount: dict,
    buildings: list[dict],
    raise_org_from_buildings: bool = False,
) -> dict:
    year = int(year)
    group_id = int(group_id)
    kind = _normalize_plan_kind(plan_kind)
    errors: list[str] = []
    updated_org = 0
    updated_bld = 0
    raised = 0

    ap = _ensure_annual_plan(group_id, year, kind)

    org_qty = {m: _parse_qty((org_quantity or {}).get(str(m))) for m in range(1, 13)}
    org_amt = {m: _parse_amt((org_amount or {}).get(str(m))) for m in range(1, 13)}

    bld_qty: dict[int, dict[int, int]] = {}
    bld_amt: dict[int, dict[int, float]] = {}
    for row in buildings or []:
        bid = int(row["building_id"])
        qmap = row.get("quantity") or {}
        amap = row.get("amount") or {}
        bld_qty[bid] = {m: _parse_qty(qmap.get(str(m))) for m in range(1, 13)}
        bld_amt[bid] = {m: _parse_amt(amap.get(str(m))) for m in range(1, 13)}

    for month in range(1, 13):
        sum_q = sum(bld_qty.get(bid, {}).get(month, 0) for bid in bld_qty)
        sum_a = sum(bld_amt.get(bid, {}).get(month, 0.0) for bid in bld_amt)
        if sum_q > org_qty[month]:
            if raise_org_from_buildings:
                org_qty[month] = sum_q
                raised += 1
            else:
                errors.append(
                    f"мес.{month} объёмы: сумма корпусов {sum_q} > план МО {org_qty[month]}"
                )
        if sum_a > org_amt[month] + 0.001:
            if raise_org_from_buildings:
                org_amt[month] = round(sum_a, 2)
                raised += 1
            else:
                errors.append(
                    f"мес.{month} финансы: сумма корпусов {sum_a} > план МО {org_amt[month]}"
                )

    if errors and not raise_org_from_buildings:
        return {
            "ok": False,
            "updated_org": 0,
            "updated_buildings": 0,
            "raised_org_months": 0,
            "errors": errors[:30],
        }

    for month in range(1, 13):
        MonthlyPlan.objects.filter(annual_plan=ap, month=month).update(
            quantity=org_qty[month],
            amount=org_amt[month],
        )
        updated_org += 1

    for bid in sorted(set(bld_qty) | set(bld_amt)):
        bp, created = BuildingPlan.objects.get_or_create(annual_plan=ap, building_id=bid)
        if created:
            for month in range(1, 13):
                MonthlyBuildingPlan.objects.get_or_create(
                    building_plan=bp,
                    month=month,
                    defaults={"quantity": 0, "amount": 0},
                )
        for month in range(1, 13):
            MonthlyBuildingPlan.objects.filter(building_plan=bp, month=month).update(
                quantity=bld_qty.get(bid, {}).get(month, 0),
                amount=bld_amt.get(bid, {}).get(month, 0.0),
            )
            updated_bld += 1

    return {
        "ok": True,
        "updated_org": updated_org,
        "updated_buildings": updated_bld,
        "raised_org_months": raised,
        "errors": [],
    }
