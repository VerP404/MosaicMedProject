"""ORM API для ввода планов индикатора по корпусам (объёмы+финансы, ТФОМС + внутренний)."""
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
    year = int(year)
    group_id = int(group_id)
    defaults = {
        "show_in_cumulative_report": False,
        "show_in_indicators_report": False,
    }
    # Новый ТФОМС/внутренний наследует флаги отображения от «соседа», если есть
    sibling = (
        AnnualPlan.objects.filter(group_id=group_id, year=year)
        .exclude(plan_kind=kind)
        .first()
    )
    if sibling:
        defaults["show_in_cumulative_report"] = sibling.show_in_cumulative_report
        defaults["show_in_indicators_report"] = sibling.show_in_indicators_report
        defaults["sort_order"] = sibling.sort_order

    ap, _ = AnnualPlan.objects.get_or_create(
        group_id=group_id,
        year=year,
        plan_kind=kind,
        defaults=defaults,
    )
    return ap


def _group_path(group_id: int) -> str:
    group = GroupIndicators.objects.filter(pk=group_id).first()
    if not group:
        return str(group_id)
    return group.get_hierarchy_display().replace(" - ", " \\ ")


def _plan_totals(ap: AnnualPlan | None) -> dict:
    qty = _empty_month_map(finance=False)
    amt = _empty_month_map(finance=True)
    if ap is None:
        return {
            "annual_plan_id": None,
            "has_buildings": False,
            "quantity": qty,
            "amount": amt,
            "qty_total": 0,
            "amt_total": 0.0,
        }
    for mp in ap.monthly_plans.all():
        qty[str(mp.month)] = int(mp.quantity or 0)
        amt[str(mp.month)] = float(mp.amount or 0)
    return {
        "annual_plan_id": ap.id,
        "has_buildings": ap.building_plans.exists(),
        "quantity": qty,
        "amount": amt,
        "qty_total": sum(qty.values()),
        "amt_total": round(sum(amt.values()), 2),
    }


def list_plan_catalog(year: int, plan_kind: str | None = None) -> list[dict]:
    """
    Каталог для ввода планов: группы с show_in_indicators_report=True (любая версия).
    В каждой строке — итоги ТФОМС и внутреннего плана.
    plan_kind оставлен для совместимости вызовов и игнорируется.
    """
    del plan_kind  # dual catalog
    year = int(year)
    flagged_group_ids = list(
        AnnualPlan.objects.filter(year=year, show_in_indicators_report=True)
        .values_list("group_id", flat=True)
        .distinct()
    )
    if not flagged_group_ids:
        return []

    plans = (
        AnnualPlan.objects.filter(year=year, group_id__in=flagged_group_ids)
        .select_related("group")
        .prefetch_related("monthly_plans", "building_plans")
    )
    by_group: dict[int, dict[str, AnnualPlan]] = {}
    sort_key: dict[int, tuple] = {}
    for ap in plans:
        by_group.setdefault(ap.group_id, {})[ap.plan_kind] = ap
        so = ap.sort_order if ap.sort_order is not None else 10**9
        prev = sort_key.get(ap.group_id)
        if prev is None or (so, ap.group.name or "") < prev:
            sort_key[ap.group_id] = (so, ap.group.name or "")

    catalog: list[dict] = []
    for gid in flagged_group_ids:
        kinds = by_group.get(gid) or {}
        tfoms = _plan_totals(kinds.get(AnnualPlan.PlanKind.TFOMS))
        internal = _plan_totals(kinds.get(AnnualPlan.PlanKind.INTERNAL))
        catalog.append(
            {
                "group_id": gid,
                "group_path": _group_path(gid),
                "tfoms_qty_total": tfoms["qty_total"],
                "tfoms_amt_total": tfoms["amt_total"],
                "tfoms_has_buildings": tfoms["has_buildings"],
                "internal_qty_total": internal["qty_total"],
                "internal_amt_total": internal["amt_total"],
                "internal_has_buildings": internal["has_buildings"],
                # совместимость со старым UI
                "qty_total": internal["qty_total"],
                "amt_total": internal["amt_total"],
                "has_buildings": internal["has_buildings"] or tfoms["has_buildings"],
            }
        )

    catalog.sort(key=lambda x: (sort_key.get(x["group_id"], (10**9, "")), x["group_path"]))
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


def load_dual_indicator_plan_form(year: int, group_id: int) -> dict:
    """Загрузка обеих версий плана для формы ввода."""
    year = int(year)
    group_id = int(group_id)
    tfoms = load_indicator_plan_form(year, group_id, AnnualPlan.PlanKind.TFOMS)
    internal = load_indicator_plan_form(year, group_id, AnnualPlan.PlanKind.INTERNAL)
    available = [
        {"label": b.name, "value": b.id} for b in Building.objects.order_by("name")
    ]
    return {
        "group_id": group_id,
        "group_path": _group_path(group_id),
        "year": year,
        "tfoms": tfoms,
        "internal": internal,
        "available_buildings": available,
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


def add_building_to_dual_plan(
    year: int,
    group_id: int,
    building_id: int,
    plan_kind: str,
) -> dict:
    """Добавить корпус в одну версию плана и вернуть dual-payload."""
    add_building_to_plan(int(year), int(group_id), int(building_id), plan_kind)
    return load_dual_indicator_plan_form(int(year), int(group_id))


def remove_building_from_plan(
    year: int,
    group_id: int,
    building_id: int,
    plan_kind: str = "internal",
) -> dict:
    ap = _ensure_annual_plan(int(group_id), int(year), plan_kind)
    BuildingPlan.objects.filter(annual_plan=ap, building_id=int(building_id)).delete()
    return load_indicator_plan_form(int(year), int(group_id), plan_kind)


def remove_building_from_dual_plan(
    year: int,
    group_id: int,
    building_id: int,
    plan_kind: str,
) -> dict:
    """Удалить корпус из одной версии плана и вернуть dual-payload."""
    remove_building_from_plan(int(year), int(group_id), int(building_id), plan_kind)
    return load_dual_indicator_plan_form(int(year), int(group_id))


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


def save_dual_indicator_plan_form(
    *,
    year: int,
    group_id: int,
    tfoms: dict,
    internal: dict,
    raise_org_from_buildings: bool = False,
) -> dict:
    """Сохранить обе версии; при ошибке валидации ни одна не пишется (сначала обе проверки)."""
    year = int(year)
    group_id = int(group_id)

    # Сначала dry-run валидации обеих версий без raise, если raise выключен —
    # вызываем save последовательно; при ошибке первой вторая не пишется.
    # При raise — обе сохраняются с подъёмом.
    r_tfoms = save_indicator_plan_form(
        year=year,
        group_id=group_id,
        plan_kind=AnnualPlan.PlanKind.TFOMS,
        org_quantity=(tfoms or {}).get("org_quantity") or {},
        org_amount=(tfoms or {}).get("org_amount") or {},
        buildings=(tfoms or {}).get("buildings") or [],
        raise_org_from_buildings=raise_org_from_buildings,
    )
    if not r_tfoms.get("ok"):
        return {
            "ok": False,
            "updated_org": 0,
            "updated_buildings": 0,
            "raised_org_months": 0,
            "errors": [f"ТФОМС: {e}" for e in (r_tfoms.get("errors") or [])],
        }

    r_int = save_indicator_plan_form(
        year=year,
        group_id=group_id,
        plan_kind=AnnualPlan.PlanKind.INTERNAL,
        org_quantity=(internal or {}).get("org_quantity") or {},
        org_amount=(internal or {}).get("org_amount") or {},
        buildings=(internal or {}).get("buildings") or [],
        raise_org_from_buildings=raise_org_from_buildings,
    )
    if not r_int.get("ok"):
        return {
            "ok": False,
            "updated_org": r_tfoms.get("updated_org", 0),
            "updated_buildings": r_tfoms.get("updated_buildings", 0),
            "raised_org_months": r_tfoms.get("raised_org_months", 0),
            "errors": [f"Внутренний: {e}" for e in (r_int.get("errors") or [])],
            "partial_tfoms_saved": True,
        }

    return {
        "ok": True,
        "updated_org": (r_tfoms.get("updated_org", 0) or 0) + (r_int.get("updated_org", 0) or 0),
        "updated_buildings": (r_tfoms.get("updated_buildings", 0) or 0)
        + (r_int.get("updated_buildings", 0) or 0),
        "raised_org_months": (r_tfoms.get("raised_org_months", 0) or 0)
        + (r_int.get("raised_org_months", 0) or 0),
        "errors": [],
    }
