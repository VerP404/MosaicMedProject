"""
Движок отчёта «индикатор × корпус»: план из MonthlyBuildingPlan, факт как в своде.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Sequence

import pandas as pd
from sqlalchemy import text

LAYOUT_INDICATOR_BUILDING = "indicator_building"
LAYOUT_BUILDING_INDICATOR = "building_indicator"
LAYOUT_INDICATOR_BUILDING_MONTHS = "indicator_building_months"
VALID_LAYOUTS = (
    LAYOUT_INDICATOR_BUILDING,
    LAYOUT_BUILDING_INDICATOR,
    LAYOUT_INDICATOR_BUILDING_MONTHS,
)


@dataclass
class BuildReportParams:
    year: int
    reporting_month: int
    indicator_ids: Sequence[int] | None = None
    building_ids: Sequence[int] | None = None
    metric: str = "volumes"  # volumes | finance
    # presented = 1,2,3,4,6,8,19; presented_2_3 = 2,3; paid = 3
    # режимы presented* применяются только к reporting_month; остальные месяцы — всегда paid (3)
    payment_type: str = "presented"
    period_closed: bool = False
    unique_flag: bool = False
    require_building_plan: bool = True
    plan_kind: str = "internal"
    columns: Sequence[str] = field(
        default_factory=lambda: ["plan", "fact", "pct", "balance"]
    )


def resolve_payment_type(payment_type: str | None, period_closed: bool) -> str:
    """Если период закрыт — только оплаченные; иначе presented | presented_2_3."""
    if period_closed:
        return "paid"
    if payment_type == "presented_2_3":
        return "presented_2_3"
    return "presented"


def _month_fact(month_data: dict, m: int, current_month: int, payment_type: str) -> float:
    """
    Факт месяца из агрегатов sql_query_rep_by_building:
      новые(1), в_тфомс(2), оплачено(3), исправлено(4,6,8,19).

    - paid / месяцы != reporting_month: только оплачено (3)
    - presented + reporting_month: 1+2+3+4/6/8/19
    - presented_2_3 + reporting_month: 2+3
    """
    paid = float(month_data.get("оплачено", 0) or 0)
    if payment_type == "paid" or m != current_month:
        return paid
    if payment_type == "presented_2_3":
        return float(month_data.get("в_тфомс", 0) or 0) + paid
    # presented: 1,2,3,4,6,8,19
    return (
        float(month_data.get("новые", 0) or 0)
        + float(month_data.get("в_тфомс", 0) or 0)
        + paid
        + float(month_data.get("исправлено", 0) or 0)
    )

def _default_reporting_month() -> int:
    today = datetime.today()
    return today.month - 1 if today.day <= 5 else today.month


def resolve_indicator_ids(
    engine, year: int, indicator_ids: Sequence[int] | None, plan_kind: str = "internal"
) -> list[int]:
    if indicator_ids:
        return [int(x) for x in indicator_ids]
    kind = (plan_kind or "internal").strip().lower()
    if kind not in ("internal", "tfoms"):
        kind = "internal"
    query = text(
        """
        SELECT DISTINCT ap.group_id AS id
        FROM plan_annualplan ap
        INNER JOIN plan_buildingplan bp ON bp.annual_plan_id = ap.id
        WHERE ap.year = :year AND ap.plan_kind = :plan_kind
        ORDER BY ap.group_id
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"year": year, "plan_kind": kind}).fetchall()
    return [int(r[0]) for r in rows]


def fetch_group_paths(engine, group_ids: Sequence[int]) -> dict[int, str]:
    if not group_ids:
        return {}
    ids = ",".join(str(int(i)) for i in group_ids)
    query = text(
        f"""
        WITH RECURSIVE group_paths AS (
            SELECT g.id, g.name, g.parent_id, g.name::text AS full_path, 0 AS level
            FROM plan_groupindicators g
            WHERE g.id IN ({ids})
            UNION ALL
            SELECT gp.id, p.name, p.parent_id, p.name || ' \\ ' || gp.full_path, gp.level + 1
            FROM plan_groupindicators p
            INNER JOIN group_paths gp ON gp.parent_id = p.id
        )
        SELECT DISTINCT ON (id) id, full_path
        FROM group_paths
        ORDER BY id, level DESC
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return {int(r["id"]): r["full_path"] for r in rows}


def fetch_building_plans(
    engine,
    year: int,
    reporting_month: int,
    group_ids: Sequence[int],
    building_ids: Sequence[int] | None,
    metric: str,
    plan_kind: str = "internal",
) -> pd.DataFrame:
    """План по месяцам: group_id, building_id, building_name, month, plan."""
    if not group_ids:
        return pd.DataFrame(columns=["group_id", "building_id", "building_name", "month", "plan"])

    plan_field = "quantity" if metric == "volumes" else "amount"
    group_sql = ",".join(str(int(i)) for i in group_ids)
    building_filter = ""
    kind = (plan_kind or "internal").strip().lower()
    if kind not in ("internal", "tfoms"):
        kind = "internal"
    params: dict[str, Any] = {"year": year, "m": reporting_month, "plan_kind": kind}
    if building_ids:
        building_filter = "AND bp.building_id IN (" + ",".join(str(int(i)) for i in building_ids) + ")"

    query = text(
        f"""
        SELECT
            ap.group_id,
            bp.building_id,
            b.name AS building_name,
            mbp.month,
            COALESCE(mbp.{plan_field}, 0) AS plan
        FROM plan_monthlybuildingplan mbp
        INNER JOIN plan_buildingplan bp ON bp.id = mbp.building_plan_id
        INNER JOIN plan_annualplan ap ON ap.id = bp.annual_plan_id
        INNER JOIN organization_building b ON b.id = bp.building_id
        WHERE ap.year = :year
          AND ap.plan_kind = :plan_kind
          AND ap.group_id IN ({group_sql})
          AND mbp.month BETWEEN 1 AND :m
          {building_filter}
        ORDER BY ap.group_id, bp.building_id, mbp.month
        """
    )
    return pd.read_sql(query, engine, params=params)


def fetch_fact_by_building(
    engine,
    year: int,
    group_id: int,
    building_ids: Sequence[int] | None,
    metric: str,
    unique_flag: bool,
    filter_conditions: str | None,
) -> list[dict]:
    """Факт по корпусам/месяцам для одного индикатора."""
    from apps.analytical_app.callback import TableUpdater
    from apps.analytical_app.pages.economist.svpod.query import sql_query_rep_by_building

    mode = "finance" if metric == "finance" else "volumes"
    months = ",".join(str(m) for m in range(1, 13))
    building_list = list(building_ids) if building_ids else None
    sql = sql_query_rep_by_building(
        year,
        months_placeholder=months,
        filter_conditions=filter_conditions,
        mode=mode,
        unique_flag=unique_flag,
        building=building_list,
    )
    _cols, rows = TableUpdater.query_to_df(engine, sql)
    return rows or []


def accumulate_pair(
    plan_by_month: dict[int, float],
    fact_rows: list[dict],
    reporting_month: int,
    payment_type: str,
    period_closed: bool = False,
) -> tuple[list[dict], float, float, float]:
    """
    Возвращает (month_rows, cumulative_plan, cumulative_fact, balance).
    month_rows: month, plan, fact, balance, pct
    """
    effective_payment = resolve_payment_type(payment_type, period_closed)
    fact_by_month: dict[int, dict] = {}
    for row in fact_rows:
        fact_by_month[int(row["month"])] = row

    incoming_balance = 0.0
    cumulative_plan = 0.0
    cumulative_fact = 0.0
    month_rows = []

    for m in range(1, reporting_month + 1):
        month_data = fact_by_month.get(m, {})
        month_plan_12 = float(plan_by_month.get(m, 0) or 0)
        month_fact = _month_fact(month_data, m, reporting_month, effective_payment)
        month_plan = month_plan_12 + incoming_balance
        remainder = month_plan - month_fact
        incoming_balance = remainder
        cumulative_plan += month_plan_12
        cumulative_fact += month_fact
        pct = round(month_fact / month_plan_12 * 100, 1) if month_plan_12 > 0 else 0.0
        month_rows.append(
            {
                "month": m,
                "plan": month_plan_12,
                "fact": month_fact,
                "balance": remainder,
                "pct": pct,
            }
        )

    return month_rows, cumulative_plan, cumulative_fact, incoming_balance


def build_long_report(engine, params: BuildReportParams) -> pd.DataFrame:
    """
    Длинный DataFrame ячеек:
    group_id, group_path, building_id, building_name, month (nullable for totals),
    plan, fact, balance, pct, is_total
    """
    from apps.analytical_app.pages.economist.svpod.query import get_filter_conditions

    year = int(params.year)
    reporting_month = int(params.reporting_month or _default_reporting_month())
    reporting_month = max(1, min(12, reporting_month))
    metric = "finance" if params.metric == "finance" else "volumes"

    group_ids = resolve_indicator_ids(engine, year, params.indicator_ids, params.plan_kind)
    if not group_ids:
        return pd.DataFrame()

    paths = fetch_group_paths(engine, group_ids)
    plans_df = fetch_building_plans(
        engine,
        year,
        reporting_month,
        group_ids,
        params.building_ids,
        metric,
        plan_kind=params.plan_kind,
    )
    if plans_df.empty:
        return pd.DataFrame()

    # пары с ненулевым планом за период (если require_building_plan)
    period_totals = (
        plans_df.groupby(["group_id", "building_id", "building_name"], as_index=False)["plan"]
        .sum()
    )
    if params.require_building_plan:
        period_totals = period_totals[period_totals["plan"] > 0]
    if period_totals.empty:
        return pd.DataFrame()

    long_rows: list[dict] = []

    for group_id in group_ids:
        pair_rows = period_totals[period_totals["group_id"] == group_id]
        if pair_rows.empty:
            continue

        filter_conditions = get_filter_conditions([group_id], year)
        building_ids_for_group = [int(x) for x in pair_rows["building_id"].tolist()]
        if params.building_ids:
            allowed = {int(x) for x in params.building_ids}
            building_ids_for_group = [b for b in building_ids_for_group if b in allowed]
        if not building_ids_for_group:
            continue

        fact_all = fetch_fact_by_building(
            engine,
            year,
            group_id,
            building_ids_for_group,
            metric,
            params.unique_flag,
            filter_conditions,
        )

        # group fact rows by building
        fact_by_building: dict[Any, list[dict]] = {}
        for row in fact_all:
            bid = row.get("building_id")
            fact_by_building.setdefault(bid, []).append(row)

        group_plans = plans_df[plans_df["group_id"] == group_id]
        group_path = paths.get(int(group_id), str(group_id))

        for _, pair in pair_rows.iterrows():
            bid = int(pair["building_id"])
            bname = pair["building_name"]
            plan_months = {
                int(r["month"]): float(r["plan"] or 0)
                for _, r in group_plans[group_plans["building_id"] == bid].iterrows()
            }
            month_rows, cum_plan, cum_fact, balance = accumulate_pair(
                plan_months,
                fact_by_building.get(bid, []),
                reporting_month,
                params.payment_type,
                period_closed=params.period_closed,
            )
            if params.require_building_plan and cum_plan <= 0:
                continue

            pct = round(cum_fact / cum_plan * 100, 1) if cum_plan > 0 else 0.0
            for mr in month_rows:
                long_rows.append(
                    {
                        "group_id": int(group_id),
                        "group_path": group_path,
                        "building_id": bid,
                        "building_name": bname,
                        "month": mr["month"],
                        "plan": mr["plan"],
                        "fact": mr["fact"],
                        "balance": mr["balance"],
                        "pct": mr["pct"],
                        "is_total": False,
                    }
                )
            long_rows.append(
                {
                    "group_id": int(group_id),
                    "group_path": group_path,
                    "building_id": bid,
                    "building_name": bname,
                    "month": None,
                    "plan": cum_plan,
                    "fact": cum_fact,
                    "balance": balance,
                    "pct": pct,
                    "is_total": True,
                }
            )

    return pd.DataFrame(long_rows)


def _metric_cols(columns: Iterable[str], prefix: str = "") -> list[str]:
    mapping = {
        "plan": "План",
        "fact": "Факт",
        "pct": "%",
        "balance": "Остаток",
    }
    out = []
    for key in columns:
        if key in mapping:
            label = mapping[key]
            out.append(f"{prefix}{label}" if prefix else label)
    return out if out else ["План", "Факт", "%", "Остаток"]


def pivot_report(
    long_df: pd.DataFrame,
    layout: str,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Сводная таблица для UI из длинного df."""
    columns = list(columns or ["plan", "fact", "pct", "balance"])
    if long_df is None or long_df.empty:
        return pd.DataFrame()

    totals = long_df[long_df["is_total"] == True].copy()  # noqa: E712
    months = long_df[long_df["is_total"] == False].copy()  # noqa: E712

    col_map = {"plan": "План", "fact": "Факт", "pct": "%", "balance": "Остаток"}
    value_cols = [c for c in columns if c in col_map]

    if layout == LAYOUT_INDICATOR_BUILDING_MONTHS:
        rows = []
        for (gid, bid), grp in months.groupby(["group_id", "building_id"], sort=False):
            path = grp["group_path"].iloc[0]
            bname = grp["building_name"].iloc[0]
            total = totals[(totals["group_id"] == gid) & (totals["building_id"] == bid)]
            for metric_key in value_cols:
                label = col_map[metric_key]
                row = {
                    "Индикатор": path,
                    "Корпус": bname,
                    "Показатель": label,
                }
                for _, mr in grp.sort_values("month").iterrows():
                    row[str(int(mr["month"]))] = mr[metric_key]
                if not total.empty:
                    row["Итого"] = total.iloc[0][metric_key]
                else:
                    row["Итого"] = grp[metric_key].sum() if metric_key != "pct" else None
                rows.append(row)
        return pd.DataFrame(rows)

    # summary layouts use totals only
    if totals.empty:
        return pd.DataFrame()

    rows = []
    if layout == LAYOUT_BUILDING_INDICATOR:
        order_cols = ["building_name", "group_path"]
        for _, r in totals.sort_values(order_cols).iterrows():
            row = {"Корпус": r["building_name"], "Индикатор": r["group_path"]}
            for key in value_cols:
                row[col_map[key]] = r[key]
            rows.append(row)
    else:
        # indicator_building (default)
        order_cols = ["group_path", "building_name"]
        for _, r in totals.sort_values(order_cols).iterrows():
            row = {"Индикатор": r["group_path"], "Корпус": r["building_name"]}
            for key in value_cols:
                row[col_map[key]] = r[key]
            rows.append(row)

    return pd.DataFrame(rows)


def build_report(
    engine,
    params: BuildReportParams,
    layout: str = LAYOUT_INDICATOR_BUILDING,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Возвращает (long_df, pivoted_df)."""
    if layout not in VALID_LAYOUTS:
        layout = LAYOUT_INDICATOR_BUILDING
    long_df = build_long_report(engine, params)
    pivoted = pivot_report(long_df, layout, params.columns)
    return long_df, pivoted
