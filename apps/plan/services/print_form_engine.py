"""Сборка данных и HTML печатного бланка «Выполнение объёмных показателей»."""
from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any, Sequence

import pandas as pd
from sqlalchemy import text

from apps.analytical_app.components.navbar import get_organization_name
from apps.analytical_app.query_executor import engine
from apps.plan.services.building_report_engine import (
    BuildReportParams,
    accumulate_pair,
    build_long_report,
    fetch_fact_by_building,
    resolve_payment_type,
)

MONTH_NAMES_RU = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


def payment_mode_label(payment_type: str, period_closed: bool) -> str:
    if period_closed or payment_type == "paid":
        return "оплаченным (статус 3)"
    if payment_type == "presented_2_3":
        return "предъявленным (2, 3); прошлые месяцы — оплаченные"
    return "предъявленным и оплаченным (1,2,3,4,6,8,19); прошлые месяцы — оплаченные"


def _fmt_num(value: float, metric: str = "volumes") -> str:
    if value is None:
        return "0"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "0"
    if metric == "finance":
        return f"{v:,.2f}".replace(",", " ").replace(".", ",")
    if abs(v - round(v)) < 0.001:
        return str(int(round(v)))
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "—"


def fetch_annual_building_plans(
    year: int,
    group_ids: Sequence[int],
    metric: str = "volumes",
    plan_kind: str = "internal",
) -> dict[tuple[int, int], float]:
    """План на год по корпусу: (group_id, building_id) -> sum months 1..12."""
    if not group_ids:
        return {}
    plan_field = "quantity" if metric != "finance" else "amount"
    kind = (plan_kind or "internal").strip().lower()
    if kind not in ("internal", "tfoms"):
        kind = "internal"
    group_sql = ",".join(str(int(i)) for i in group_ids)
    query = text(
        f"""
        SELECT
            ap.group_id,
            bp.building_id,
            COALESCE(SUM(mbp.{plan_field}), 0) AS year_plan
        FROM plan_monthlybuildingplan mbp
        INNER JOIN plan_buildingplan bp ON bp.id = mbp.building_plan_id
        INNER JOIN plan_annualplan ap ON ap.id = bp.annual_plan_id
        WHERE ap.year = :year
          AND ap.plan_kind = :plan_kind
          AND ap.group_id IN ({group_sql})
          AND mbp.month BETWEEN 1 AND 12
        GROUP BY ap.group_id, bp.building_id
        """
    )
    df = pd.read_sql(query, engine, params={"year": int(year), "plan_kind": kind})
    out: dict[tuple[int, int], float] = {}
    for _, row in df.iterrows():
        out[(int(row["group_id"]), int(row["building_id"]))] = float(row["year_plan"] or 0)
    return out


def collect_indicator_ids(config: dict) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for sec in config.get("sections") or []:
        for it in sec.get("items") or []:
            try:
                iid = int(it["indicator_id"])
            except (KeyError, TypeError, ValueError):
                continue
            if iid not in seen:
                seen.add(iid)
                ids.append(iid)
    return ids


def _append_unassigned_building_rows(
    by_group: dict[int, list[dict]],
    *,
    year: int,
    reporting_month: int,
    indicator_ids: list[int],
    payment_type: str,
    period_closed: bool,
    metric: str,
    unique_flag: bool,
) -> None:
    """
    Факт без привязки к корпусу (или корпус не из плана) → строка «без корпуса», план 0.
    """
    from apps.analytical_app.pages.economist.svpod.query import get_filter_conditions

    effective = resolve_payment_type(payment_type, period_closed)
    for gid in indicator_ids:
        filter_conditions = get_filter_conditions([gid], year)
        try:
            fact_all = fetch_fact_by_building(
                engine,
                year,
                gid,
                None,  # все корпуса, включая NULL / «Без корпуса»
                metric,
                unique_flag,
                filter_conditions,
            )
        except Exception:
            continue
        if not fact_all:
            continue

        known_bids = {
            int(r["building_id"])
            for r in by_group.get(gid, [])
            if r.get("building_id") is not None
        }
        unassigned_by_month: dict[int, dict] = {}
        for row in fact_all:
            bid = row.get("building_id")
            try:
                bid_int = int(bid) if bid is not None and str(bid).strip() != "" else None
            except (TypeError, ValueError):
                bid_int = None
            # NULL / 0 / корпус не из плана
            if bid_int is not None and bid_int in known_bids:
                continue
            month = int(row.get("month") or 0)
            if month < 1:
                continue
            bucket = unassigned_by_month.setdefault(
                month,
                {"новые": 0, "в_тфомс": 0, "оплачено": 0, "исправлено": 0, "month": month},
            )
            for key in ("новые", "в_тфомс", "оплачено", "исправлено"):
                bucket[key] = float(bucket.get(key) or 0) + float(row.get(key) or 0)

        if not unassigned_by_month:
            continue
        _month_rows, _plan, cum_fact, _bal = accumulate_pair(
            {},
            list(unassigned_by_month.values()),
            reporting_month,
            effective,
            period_closed=period_closed,
        )
        if cum_fact <= 0:
            continue
        by_group.setdefault(gid, []).append(
            {
                "building_id": None,
                "building_name": "без корпуса",
                "plan": 0.0,
                "fact": cum_fact,
                "pct": 0.0,
                "year_plan": 0.0,
                "of_year": None,
            }
        )
        by_group[gid].sort(
            key=lambda r: (r.get("building_name") == "без корпуса", str(r.get("building_name") or ""))
        )


def build_print_form_data(
    *,
    year: int,
    reporting_month: int,
    config: dict,
    payment_type: str = "presented",
    period_closed: bool = False,
    metric: str = "volumes",
    unique_flag: bool = False,
    plan_kind: str = "internal",
) -> dict[str, Any]:
    """
    Возвращает структуру для рендера бланка:
    {
      header: {...},
      sections: [{title, tables: [{short_title, show_of_year, rows, total}]}]
    }
    row: building_name, plan, fact, pct, of_year?
    """
    indicator_ids = collect_indicator_ids(config)
    year = int(year)
    reporting_month = max(1, min(12, int(reporting_month)))
    metric = "finance" if metric == "finance" else "volumes"
    kind = (plan_kind or "internal").strip().lower()
    if kind not in ("internal", "tfoms"):
        kind = "internal"

    header = {
        "organization": get_organization_name(),
        "title": "Выполнение объёмных показателей",
        "year": year,
        "reporting_month": reporting_month,
        "period_label": (
            f"{MONTH_NAMES_RU[1]}–{MONTH_NAMES_RU[reporting_month]} {year}"
            if reporting_month > 1
            else f"{MONTH_NAMES_RU[1]} {year}"
        ),
        "payment_label": payment_mode_label(payment_type, period_closed),
        "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "columns": int(config.get("columns") or 2),
        "page_columns": int(config.get("page_columns") or 2),
        "page_orientation": config.get("page_orientation") or "landscape",
        "metric": metric,
        "plan_kind": kind,
    }

    if not indicator_ids:
        return {"header": header, "sections": [], "missing": []}

    params = BuildReportParams(
        year=year,
        reporting_month=reporting_month,
        indicator_ids=indicator_ids,
        building_ids=None,
        metric=metric,
        payment_type=payment_type,
        period_closed=period_closed,
        unique_flag=unique_flag,
        require_building_plan=True,
        plan_kind=kind,
    )
    long_df = build_long_report(engine, params)

    by_group: dict[int, list[dict]] = {}
    if long_df is not None and not long_df.empty:
        totals = long_df[long_df["is_total"] == True].copy()  # noqa: E712
        year_plans = fetch_annual_building_plans(year, indicator_ids, metric, plan_kind=kind)
        for _, row in totals.iterrows():
            gid = int(row["group_id"])
            bid = int(row["building_id"])
            plan = float(row["plan"] or 0)
            fact = float(row["fact"] or 0)
            pct = float(row["pct"] or 0) if plan else 0.0
            year_plan = float(year_plans.get((gid, bid), 0) or 0)
            of_year = round(fact / year_plan * 100, 1) if year_plan > 0 else None
            by_group.setdefault(gid, []).append(
                {
                    "building_id": bid,
                    "building_name": row["building_name"],
                    "plan": plan,
                    "fact": fact,
                    "pct": pct,
                    "year_plan": year_plan,
                    "of_year": of_year,
                }
            )

    # Факт вне корпусов плана → «без корпуса», план 0
    _append_unassigned_building_rows(
        by_group,
        year=year,
        reporting_month=reporting_month,
        indicator_ids=indicator_ids,
        payment_type=payment_type,
        period_closed=period_closed,
        metric=metric,
        unique_flag=unique_flag,
    )

    for gid in by_group:
        by_group[gid].sort(
            key=lambda r: (r.get("building_name") == "без корпуса", str(r.get("building_name") or ""))
        )

    sections_out = []
    missing: list[dict] = []
    for sec in config.get("sections") or []:
        tables = []
        for it in sec.get("items") or []:
            try:
                gid = int(it["indicator_id"])
            except (KeyError, TypeError, ValueError):
                continue
            rows = by_group.get(gid) or []
            short_title = (it.get("short_title") or "").strip() or str(gid)
            if not rows:
                missing.append(
                    {
                        "indicator_id": gid,
                        "short_title": short_title,
                        "reason": "нет плана по корпусам и нет факта «без корпуса» на период",
                    }
                )
                continue
            show_of_year = bool(it.get("show_of_year"))
            sum_plan = sum(r["plan"] for r in rows)
            sum_fact = sum(r["fact"] for r in rows)
            sum_year = sum(r["year_plan"] for r in rows)
            total = {
                "building_name": "итого",
                "plan": sum_plan,
                "fact": sum_fact,
                "pct": round(sum_fact / sum_plan * 100, 1) if sum_plan > 0 else 0.0,
                "of_year": (
                    round(sum_fact / sum_year * 100, 1) if show_of_year and sum_year > 0 else None
                ),
            }
            tables.append(
                {
                    "indicator_id": gid,
                    "short_title": short_title,
                    "show_of_year": show_of_year,
                    "rows": rows,
                    "total": total,
                }
            )
        try:
            item_columns = max(1, min(4, int(sec.get("item_columns") or header.get("columns") or 2)))
        except (TypeError, ValueError):
            item_columns = max(1, min(4, int(header.get("columns") or 2)))
        # Пустой раздел тоже сохраняем — иначе число колонок листа «прыгает»
        sections_out.append(
            {
                "title": (sec.get("title") or "").strip() or "Раздел",
                "item_columns": item_columns,
                "tables": tables,
            }
        )

    return {"header": header, "sections": sections_out, "missing": missing}


def render_print_form_html(data: dict[str, Any]) -> str:
    """HTML бланка: разделы в сетке page_columns; внутри — сетка индикаторов."""
    header = data.get("header") or {}
    sections = list(data.get("sections") or [])
    metric = header.get("metric") or "volumes"
    default_columns = max(1, min(4, int(header.get("columns") or 2)))
    try:
        page_columns = max(1, min(4, int(header.get("page_columns") or 2)))
    except (TypeError, ValueError):
        page_columns = 2
    orientation = header.get("page_orientation") or "landscape"
    if orientation not in ("landscape", "portrait"):
        orientation = "landscape"
    page_size = "A4 landscape" if orientation == "landscape" else "A4 portrait"
    if not sections:
        sections = [{"title": "Раздел", "item_columns": default_columns, "tables": []}]

    parts: list[str] = []
    parts.append(
        "<style id=\"pvf-dynamic-page\">"
        f"@media print {{ @page {{ size: {page_size}; margin: 8mm; }} }}"
        "</style>"
    )
    parts.append(
        f'<div id="print-volume-form-sheet" class="print-volume-form pvf-orient-{escape(orientation)}" '
        f'data-orientation="{escape(orientation)}" '
        f'style="--pvf-section-count:{page_columns}; --pvf-columns:{default_columns}">'
    )
    parts.append('<div class="pvf-header">')
    parts.append(f'<div class="pvf-org">{escape(str(header.get("organization") or ""))}</div>')
    parts.append(f'<div class="pvf-title">{escape(str(header.get("title") or ""))}</div>')
    parts.append(
        f'<div class="pvf-meta">'
        f'Период: <strong>{escape(str(header.get("period_label") or ""))}</strong>'
        f' &nbsp;|&nbsp; По данным: <strong>{escape(str(header.get("payment_label") or ""))}</strong>'
        f"</div>"
    )
    if header.get("generated_at"):
        parts.append(
            f'<div class="pvf-generated">'
            f'Сформировано: <strong>{escape(str(header["generated_at"]))}</strong>'
            f' &nbsp;|&nbsp; Лист: <strong>{"альбомный" if orientation == "landscape" else "книжный"}</strong>'
            f' &nbsp;|&nbsp; Столбцов: <strong>{page_columns}</strong>'
            f"</div>"
        )
    parts.append("</div>")

    has_tables = any(sec.get("tables") for sec in sections)
    if not has_tables:
        parts.append('<div class="pvf-empty">')
        parts.append(
            "Нет данных для бланка. Добавьте индикаторы в разделы макета "
            "и задайте план по корпусам (вкладка «Ввод планов»). "
        )
        missing = data.get("missing") or []
        if missing:
            parts.append("<ul class='pvf-missing-list'>")
            for m in missing:
                parts.append(
                    "<li>"
                    f"{escape(str(m.get('short_title')))} (id={escape(str(m.get('indicator_id')))})"
                    f" — {escape(str(m.get('reason') or 'нет данных'))}"
                    "</li>"
                )
            parts.append("</ul>")
        parts.append("</div>")
        parts.append("</div>")
        return "".join(parts)

    parts.append(
        f'<div class="pvf-sections" style="--pvf-section-count:{page_columns}">'
    )
    for sec in sections:
        try:
            item_cols = max(1, min(4, int(sec.get("item_columns") or default_columns)))
        except (TypeError, ValueError):
            item_cols = default_columns
        parts.append('<section class="pvf-section">')
        parts.append(f'<h3 class="pvf-section-title">{escape(sec.get("title") or "")}</h3>')
        parts.append(f'<div class="pvf-grid" style="--pvf-columns:{item_cols}">')
        for table in sec.get("tables") or []:
            show_of_year = bool(table.get("show_of_year"))
            parts.append('<div class="pvf-mini">')
            parts.append(
                f'<div class="pvf-mini-title">{escape(table.get("short_title") or "")}</div>'
            )
            parts.append("<table>")
            parts.append("<thead><tr>")
            parts.append("<th></th><th>план</th><th>факт</th><th>%</th>")
            if show_of_year:
                parts.append("<th>от года</th>")
            parts.append("</tr></thead><tbody>")
            for row in table.get("rows") or []:
                parts.append("<tr>")
                parts.append(f'<td class="pvf-name">{escape(str(row.get("building_name") or ""))}</td>')
                parts.append(f"<td>{_fmt_num(row.get('plan'), metric)}</td>")
                parts.append(f"<td>{_fmt_num(row.get('fact'), metric)}</td>")
                parts.append(f"<td>{_fmt_pct(row.get('pct'))}</td>")
                if show_of_year:
                    parts.append(f"<td>{_fmt_pct(row.get('of_year'))}</td>")
                parts.append("</tr>")
            total = table.get("total") or {}
            parts.append('<tr class="pvf-total">')
            parts.append(f'<td class="pvf-name">{escape(str(total.get("building_name") or "итого"))}</td>')
            parts.append(f"<td>{_fmt_num(total.get('plan'), metric)}</td>")
            parts.append(f"<td>{_fmt_num(total.get('fact'), metric)}</td>")
            parts.append(f"<td>{_fmt_pct(total.get('pct'))}</td>")
            if show_of_year:
                parts.append(f"<td>{_fmt_pct(total.get('of_year'))}</td>")
            parts.append("</tr>")
            parts.append("</tbody></table>")
            parts.append("</div>")
        if not (sec.get("tables") or []):
            parts.append('<div class="pvf-empty-col">Нет индикаторов в разделе</div>')
        parts.append("</div></section>")
    parts.append("</div>")

    parts.append("</div>")
    return "".join(parts)
