"""Обёртки данных для страницы конструктора «индикаторы × корпуса»."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from sqlalchemy import text

from apps.analytical_app.query_executor import engine
from apps.plan.services.building_report_engine import (
    BuildReportParams,
    build_report,
    LAYOUT_INDICATOR_BUILDING,
    LAYOUT_BUILDING_INDICATOR,
    LAYOUT_INDICATOR_BUILDING_MONTHS,
    VALID_LAYOUTS,
)


def list_indicator_options(
    year: int,
    *,
    for_editor: bool = False,
    only_with_building_plan: bool = False,
) -> list[dict]:
    """
    Индикаторы с AnnualPlan на год (полная иерархия).
    for_editor=True — в подписи план МО (сумма помесячных объёмов).
    only_with_building_plan=True — только те, у кого есть BuildingPlan.
    """
    query = text(
        """
        WITH RECURSIVE group_paths AS (
            SELECT
                g.id,
                g.name,
                g.parent_id,
                g.name::text AS full_path,
                0 AS level
            FROM plan_groupindicators g
            INNER JOIN plan_annualplan ap ON ap.group_id = g.id AND ap.year = :year
            WHERE 1=1

            UNION ALL

            SELECT
                gp.id,
                p.name,
                p.parent_id,
                p.name || ' \\ ' || gp.full_path,
                gp.level + 1
            FROM plan_groupindicators p
            INNER JOIN group_paths gp ON gp.parent_id = p.id
        ),
        paths AS (
            SELECT DISTINCT ON (id) id, full_path AS name
            FROM group_paths
            ORDER BY id, level DESC
        )
        SELECT
            p.id,
            p.name,
            COALESCE(SUM(mp.quantity), 0) AS org_qty,
            COALESCE(SUM(mp.amount), 0) AS org_amt,
            EXISTS (
                SELECT 1
                FROM plan_buildingplan bp
                WHERE bp.annual_plan_id = ap.id
            ) AS has_building_plan
        FROM paths p
        INNER JOIN plan_annualplan ap ON ap.group_id = p.id AND ap.year = :year
        LEFT JOIN plan_monthlyplan mp ON mp.annual_plan_id = ap.id
        GROUP BY p.id, p.name, ap.id
        ORDER BY p.name
        """
    )
    df = pd.read_sql(query, engine, params={"year": int(year)})
    if df.empty:
        return []
    if only_with_building_plan:
        df = df[df["has_building_plan"] == True]  # noqa: E712
    options = []
    for _, row in df.iterrows():
        label = row["name"]
        if for_editor:
            qty = int(float(row["org_qty"] or 0))
            mark = "есть корпуса" if row["has_building_plan"] else "нет корпусов"
            label = f"{label}  [МО: {qty}; {mark}]"
        options.append({"label": label, "value": int(row["id"])})
    return options


def list_building_options() -> list[dict]:
    query = text(
        """
        SELECT id, name
        FROM organization_building
        ORDER BY name
        """
    )
    df = pd.read_sql(query, engine)
    return [{"label": row["name"], "value": int(row["id"])} for _, row in df.iterrows()]


def list_existing_building_plans_catalog(year: int) -> list[dict]:
    """
    Уже введённые планы по корпусам на год — для списка «открыть и править».
    [{group_id, group_path, building_ids, buildings_label, plan_qty, org_qty}]
    """
    query = text(
        """
        WITH RECURSIVE group_paths AS (
            SELECT
                g.id,
                g.name,
                g.parent_id,
                g.name::text AS full_path,
                0 AS level
            FROM plan_groupindicators g
            INNER JOIN plan_annualplan ap ON ap.group_id = g.id AND ap.year = :year
            INNER JOIN plan_buildingplan bp ON bp.annual_plan_id = ap.id
            GROUP BY g.id, g.name, g.parent_id

            UNION ALL

            SELECT
                gp.id,
                p.name,
                p.parent_id,
                p.name || ' \\ ' || gp.full_path,
                gp.level + 1
            FROM plan_groupindicators p
            INNER JOIN group_paths gp ON gp.parent_id = p.id
        ),
        paths AS (
            SELECT DISTINCT ON (id) id, full_path
            FROM group_paths
            ORDER BY id, level DESC
        )
        SELECT
            p.id AS group_id,
            p.full_path AS group_path,
            b.id AS building_id,
            b.name AS building_name,
            COALESCE(SUM(mbp.quantity), 0) AS plan_qty,
            (
                SELECT COALESCE(SUM(mp.quantity), 0)
                FROM plan_monthlyplan mp
                WHERE mp.annual_plan_id = ap.id
            ) AS org_qty
        FROM paths p
        INNER JOIN plan_annualplan ap ON ap.group_id = p.id AND ap.year = :year
        INNER JOIN plan_buildingplan bp ON bp.annual_plan_id = ap.id
        INNER JOIN organization_building b ON b.id = bp.building_id
        LEFT JOIN plan_monthlybuildingplan mbp ON mbp.building_plan_id = bp.id
        GROUP BY p.id, p.full_path, b.id, b.name, ap.id
        ORDER BY p.full_path, b.name
        """
    )
    df = pd.read_sql(query, engine, params={"year": int(year)})
    if df.empty:
        return []

    catalog: list[dict] = []
    for group_id, grp in df.groupby("group_id", sort=False):
        building_ids = [int(x) for x in grp["building_id"].tolist()]
        names = grp["building_name"].tolist()
        plan_qty = int(float(grp["plan_qty"].sum() or 0))
        org_qty = int(float(grp["org_qty"].iloc[0] or 0))
        catalog.append(
            {
                "group_id": int(group_id),
                "group_path": grp["group_path"].iloc[0],
                "building_ids": building_ids,
                "buildings_label": ", ".join(names),
                "plan_qty": plan_qty,
                "org_qty": org_qty,
            }
        )
    catalog.sort(key=lambda x: x["group_path"])
    return catalog


def list_presets() -> list[dict]:
    query = text(
        """
        SELECT id, name, config, notes, is_active, created_at, updated_at
        FROM plan_buildingindicatorreportpreset
        WHERE is_active = true
        ORDER BY name
        """
    )
    df = pd.read_sql(query, engine)
    options = []
    for _, row in df.iterrows():
        options.append(
            {
                "label": row["name"],
                "value": int(row["id"]),
            }
        )
    return options


def get_preset(preset_id: int) -> dict | None:
    query = text(
        """
        SELECT id, name, config, notes
        FROM plan_buildingindicatorreportpreset
        WHERE id = :id
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"id": preset_id}).mappings().first()
    if not row:
        return None
    config = row["config"]
    if isinstance(config, str):
        config = json.loads(config)
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "config": config or {},
        "notes": row["notes"] or "",
    }


def save_preset(name: str, config: dict, preset_id: int | None = None, notes: str = "") -> int:
    """Создать или обновить пресет. Возвращает id."""
    config_json = json.dumps(config, ensure_ascii=False)
    with engine.begin() as conn:
        if preset_id:
            conn.execute(
                text(
                    """
                    UPDATE plan_buildingindicatorreportpreset
                    SET name = :name,
                        config = CAST(:config AS jsonb),
                        notes = :notes,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {"name": name, "config": config_json, "notes": notes, "id": preset_id},
            )
            return int(preset_id)
        result = conn.execute(
            text(
                """
                INSERT INTO plan_buildingindicatorreportpreset (name, config, notes, is_active, created_at, updated_at)
                VALUES (:name, CAST(:config AS jsonb), :notes, true, NOW(), NOW())
                RETURNING id
                """
            ),
            {"name": name, "config": config_json, "notes": notes},
        )
        return int(result.scalar())


def delete_preset(preset_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM plan_buildingindicatorreportpreset WHERE id = :id"),
            {"id": preset_id},
        )


DEFAULT_PRINT_CONFIG = {
    "columns": 3,
    "page_orientation": "landscape",
    "sections": [
        {"title": "Лечебно-диагностическая работа", "items": []},
        {"title": "Профилактическая работа", "items": []},
    ],
}


def normalize_print_config(config: dict | None) -> dict:
    cfg = dict(config or {})
    columns = int(cfg.get("columns") or 3)
    columns = max(1, min(4, columns))
    orientation = cfg.get("page_orientation") or "landscape"
    if orientation not in ("landscape", "portrait"):
        orientation = "landscape"
    sections = []
    for sec in cfg.get("sections") or []:
        items = []
        for it in sec.get("items") or []:
            try:
                iid = int(it.get("indicator_id"))
            except (TypeError, ValueError):
                continue
            items.append(
                {
                    "indicator_id": iid,
                    "short_title": (it.get("short_title") or "").strip() or str(iid),
                    "show_of_year": bool(it.get("show_of_year")),
                }
            )
        sections.append(
            {
                "title": (sec.get("title") or "").strip() or "Раздел",
                "items": items,
            }
        )
    if not sections:
        sections = list(DEFAULT_PRINT_CONFIG["sections"])
    return {
        "columns": columns,
        "page_orientation": orientation,
        "sections": sections,
    }


def list_print_templates() -> list[dict]:
    query = text(
        """
        SELECT id, name
        FROM plan_buildingvolumeprinttemplate
        WHERE is_active = true
        ORDER BY name
        """
    )
    try:
        df = pd.read_sql(query, engine)
    except Exception:
        return []
    if df.empty:
        return []
    return [{"label": row["name"], "value": int(row["id"])} for _, row in df.iterrows()]


def get_print_template(template_id: int) -> dict | None:
    query = text(
        """
        SELECT id, name, config, notes
        FROM plan_buildingvolumeprinttemplate
        WHERE id = :id
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"id": template_id}).mappings().first()
    if not row:
        return None
    config = row["config"]
    if isinstance(config, str):
        config = json.loads(config)
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "config": normalize_print_config(config),
        "notes": row["notes"] or "",
    }


def save_print_template(
    name: str,
    config: dict,
    template_id: int | None = None,
    notes: str = "",
) -> int:
    config_json = json.dumps(normalize_print_config(config), ensure_ascii=False)
    with engine.begin() as conn:
        if template_id:
            conn.execute(
                text(
                    """
                    UPDATE plan_buildingvolumeprinttemplate
                    SET name = :name,
                        config = CAST(:config AS jsonb),
                        notes = :notes,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {"name": name, "config": config_json, "notes": notes, "id": template_id},
            )
            return int(template_id)
        result = conn.execute(
            text(
                """
                INSERT INTO plan_buildingvolumeprinttemplate
                    (name, config, notes, is_active, created_at, updated_at)
                VALUES (:name, CAST(:config AS jsonb), :notes, true, NOW(), NOW())
                RETURNING id
                """
            ),
            {"name": name, "config": config_json, "notes": notes},
        )
        return int(result.scalar())


def delete_print_template(template_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM plan_buildingvolumeprinttemplate WHERE id = :id"),
            {"id": template_id},
        )


def run_building_report(
    year: int,
    reporting_month: int,
    indicator_ids: list[int] | None,
    building_ids: list[int] | None,
    layout: str,
    metric: str,
    payment_type: str,
    unique_flag: bool,
    require_building_plan: bool = True,
    period_closed: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if layout not in VALID_LAYOUTS:
        layout = LAYOUT_INDICATOR_BUILDING
    params = BuildReportParams(
        year=year,
        reporting_month=reporting_month,
        indicator_ids=indicator_ids or None,
        building_ids=building_ids or None,
        metric=metric,
        payment_type=payment_type,
        period_closed=period_closed,
        unique_flag=unique_flag,
        require_building_plan=require_building_plan,
    )
    return build_report(engine, params, layout=layout)


LAYOUT_OPTIONS = [
    {"label": "Индикатор -> корпус", "value": LAYOUT_INDICATOR_BUILDING},
    {"label": "Корпус -> индикатор", "value": LAYOUT_BUILDING_INDICATOR},
    {"label": "Индикатор x корпус по месяцам", "value": LAYOUT_INDICATOR_BUILDING_MONTHS},
]


def load_building_plan_editor_data(
    year: int,
    building_ids: list[int],
    indicator_ids: list[int] | None,
    metric: str = "volumes",
) -> list[dict]:
    """
    Данные для редактора: по одному блоку на индикатор.
    [{group_id, group_path, org_plan: {'1'..'12'}, org_total, rows: [...]}]
    """
    if not building_ids:
        return []

    year = int(year)
    buildings_sql = ",".join(str(int(b)) for b in building_ids)
    plan_field = "quantity" if metric != "finance" else "amount"

    if indicator_ids:
        groups_sql = ",".join(str(int(i)) for i in indicator_ids)
        group_filter = f"AND g.id IN ({groups_sql})"
    else:
        group_filter = ""

    query = text(
        f"""
        WITH RECURSIVE group_paths AS (
            SELECT
                g.id,
                g.name,
                g.parent_id,
                g.name::text AS full_path,
                0 AS level
            FROM plan_groupindicators g
            INNER JOIN plan_annualplan ap ON ap.group_id = g.id AND ap.year = :year
            WHERE 1=1 {group_filter}

            UNION ALL

            SELECT
                gp.id,
                p.name,
                p.parent_id,
                p.name || ' \\ ' || gp.full_path,
                gp.level + 1
            FROM plan_groupindicators p
            INNER JOIN group_paths gp ON gp.parent_id = p.id
        ),
        paths AS (
            SELECT DISTINCT ON (id) id, full_path
            FROM group_paths
            ORDER BY id, level DESC
        ),
        buildings AS (
            SELECT id, name
            FROM organization_building
            WHERE id IN ({buildings_sql})
        )
        SELECT
            p.id AS group_id,
            p.full_path AS group_path,
            b.id AS building_id,
            b.name AS building_name,
            mbp.month,
            COALESCE(mbp.{plan_field}, 0) AS plan_value
        FROM paths p
        CROSS JOIN buildings b
        LEFT JOIN plan_annualplan ap
            ON ap.group_id = p.id AND ap.year = :year
        LEFT JOIN plan_buildingplan bp
            ON bp.annual_plan_id = ap.id AND bp.building_id = b.id
        LEFT JOIN plan_monthlybuildingplan mbp
            ON mbp.building_plan_id = bp.id
        ORDER BY p.full_path, b.name, mbp.month
        """
    )
    org_query = text(
        f"""
        WITH RECURSIVE group_paths AS (
            SELECT
                g.id,
                g.name,
                g.parent_id,
                g.name::text AS full_path,
                0 AS level
            FROM plan_groupindicators g
            INNER JOIN plan_annualplan ap ON ap.group_id = g.id AND ap.year = :year
            WHERE 1=1 {group_filter}

            UNION ALL

            SELECT
                gp.id,
                p.name,
                p.parent_id,
                p.name || ' \\ ' || gp.full_path,
                gp.level + 1
            FROM plan_groupindicators p
            INNER JOIN group_paths gp ON gp.parent_id = p.id
        ),
        paths AS (
            SELECT DISTINCT ON (id) id, full_path
            FROM group_paths
            ORDER BY id, level DESC
        )
        SELECT
            p.id AS group_id,
            p.full_path AS group_path,
            mp.month,
            COALESCE(mp.{plan_field}, 0) AS org_value
        FROM paths p
        INNER JOIN plan_annualplan ap ON ap.group_id = p.id AND ap.year = :year
        LEFT JOIN plan_monthlyplan mp ON mp.annual_plan_id = ap.id
        ORDER BY p.full_path, mp.month
        """
    )
    df = pd.read_sql(query, engine, params={"year": year})
    org_df = pd.read_sql(org_query, engine, params={"year": year})
    if df.empty and org_df.empty:
        return []

    org_by_group: dict[int, dict] = {}
    for gid, grp in org_df.groupby("group_id", sort=False):
        gid_i = int(gid)
        org_plan = {str(m): (0.0 if metric == "finance" else 0) for m in range(1, 13)}
        path = grp["group_path"].iloc[0]
        for _, r in grp.iterrows():
            if pd.notna(r.get("month")):
                m = int(r["month"])
                val = r["org_value"]
                org_plan[str(m)] = float(val or 0) if metric == "finance" else int(float(val or 0))
        total = (
            round(sum(float(org_plan[str(m)]) for m in range(1, 13)), 2)
            if metric == "finance"
            else sum(int(org_plan[str(m)]) for m in range(1, 13))
        )
        org_by_group[gid_i] = {"group_path": path, "org_plan": org_plan, "org_total": total}

    blocks: dict[int, dict] = {}
    # если есть только org без корпусов в df — всё равно покажем блоки
    for gid_i, org_info in org_by_group.items():
        blocks[gid_i] = {
            "group_id": gid_i,
            "group_path": org_info["group_path"],
            "org_plan": org_info["org_plan"],
            "org_total": org_info["org_total"],
            "rows": [],
        }

    if not df.empty:
        for (group_id, building_id), grp in df.groupby(["group_id", "building_id"], sort=False):
            gid = int(group_id)
            bid = int(building_id)
            path = grp["group_path"].iloc[0]
            bname = grp["building_name"].iloc[0]
            if gid not in blocks:
                org_info = org_by_group.get(gid) or {
                    "org_plan": {str(m): 0 for m in range(1, 13)},
                    "org_total": 0,
                }
                blocks[gid] = {
                    "group_id": gid,
                    "group_path": path,
                    "org_plan": org_info["org_plan"],
                    "org_total": org_info["org_total"],
                    "rows": [],
                }
            row = {
                "building_id": bid,
                "building_name": bname,
                "total": 0,
            }
            for m in range(1, 13):
                row[str(m)] = 0
            for _, r in grp.iterrows():
                if pd.notna(r.get("month")):
                    m = int(r["month"])
                    val = r["plan_value"]
                    if metric == "finance":
                        row[str(m)] = float(val or 0)
                    else:
                        row[str(m)] = int(float(val or 0))
            if metric == "finance":
                row["total"] = round(sum(float(row[str(m)]) for m in range(1, 13)), 2)
            else:
                row["total"] = sum(int(row[str(m)]) for m in range(1, 13))
            blocks[gid]["rows"].append(row)

    # если buildings выбраны, но df пуст — всё равно строки корпусов с нулями
    if not df.empty or building_ids:
        building_names = {
            int(r["id"]): r["name"]
            for _, r in pd.read_sql(
                text(
                    f"SELECT id, name FROM organization_building WHERE id IN ({buildings_sql})"
                ),
                engine,
            ).iterrows()
        }
        for block in blocks.values():
            existing = {int(r["building_id"]) for r in block["rows"]}
            for bid in building_ids:
                bid = int(bid)
                if bid in existing:
                    continue
                row = {
                    "building_id": bid,
                    "building_name": building_names.get(bid, str(bid)),
                    "total": 0,
                    **{str(m): (0.0 if metric == "finance" else 0) for m in range(1, 13)},
                }
                block["rows"].append(row)
            block["rows"].sort(key=lambda r: r["building_name"])

    return sorted(blocks.values(), key=lambda x: x["group_path"])


def _parse_cell_value(value, metric: str):
    if value is None or value == "":
        return 0.0 if metric == "finance" else 0
    try:
        if metric == "finance":
            return float(value)
        return int(float(value))
    except (TypeError, ValueError):
        return 0.0 if metric == "finance" else 0


def save_building_plan_diffs(
    year: int,
    metric: str,
    baseline: dict,
    current_blocks: list[dict],
    raise_org_from_buildings: bool = False,
) -> dict:
    """
    Сохраняет только изменённые месячные ячейки через SQL.
    baseline: {str(group_id): {str(building_id): {str(month): value}}}

    Правило: сумма планов корпусов по месяцу ≤ план МО.
    Если raise_org_from_buildings=True и сумма > план МО — поднимаем план МО до суммы.
    """
    year = int(year)
    is_finance = metric == "finance"
    field = "amount" if is_finance else "quantity"
    baseline = baseline or {}
    updated = 0
    created_bp = 0
    raised_org = 0
    skipped = 0
    errors: list[str] = []

    with engine.begin() as conn:
        for block in current_blocks or []:
            group_id = int(block["group_id"])
            group_path = block.get("group_path") or str(group_id)
            group_base = baseline.get(str(group_id)) or {}
            rows = block.get("rows") or []

            ap_row = conn.execute(
                text(
                    """
                    SELECT id FROM plan_annualplan
                    WHERE group_id = :gid AND year = :year
                    """
                ),
                {"gid": group_id, "year": year},
            ).fetchone()
            if not ap_row:
                ap_id = conn.execute(
                    text(
                        """
                        INSERT INTO plan_annualplan
                            (group_id, year, show_in_cumulative_report, show_in_indicators_report)
                        VALUES (:gid, :year, false, false)
                        RETURNING id
                        """
                    ),
                    {"gid": group_id, "year": year},
                ).scalar()
                for month in range(1, 13):
                    conn.execute(
                        text(
                            """
                            INSERT INTO plan_monthlyplan (annual_plan_id, month, quantity, amount)
                            VALUES (:ap, :m, 0, 0)
                            """
                        ),
                        {"ap": ap_id, "m": month},
                    )
            else:
                ap_id = int(ap_row[0])
                for month in range(1, 13):
                    exists = conn.execute(
                        text(
                            """
                            SELECT 1 FROM plan_monthlyplan
                            WHERE annual_plan_id = :ap AND month = :m
                            """
                        ),
                        {"ap": ap_id, "m": month},
                    ).fetchone()
                    if not exists:
                        conn.execute(
                            text(
                                """
                                INSERT INTO plan_monthlyplan (annual_plan_id, month, quantity, amount)
                                VALUES (:ap, :m, 0, 0)
                                """
                            ),
                            {"ap": ap_id, "m": month},
                        )

            # все корпуса в БД (не только открытые в редакторе)
            db_building_vals: dict[int, dict[int, float]] = {}
            for r in conn.execute(
                text(
                    f"""
                    SELECT bp.building_id, mbp.month, COALESCE(mbp.{field}, 0)
                    FROM plan_buildingplan bp
                    JOIN plan_monthlybuildingplan mbp ON mbp.building_plan_id = bp.id
                    WHERE bp.annual_plan_id = :ap
                    """
                ),
                {"ap": ap_id},
            ).fetchall():
                bid, month, val = int(r[0]), int(r[1]), float(r[2] or 0)
                db_building_vals.setdefault(bid, {})[month] = val

            # наложение значений из редактора
            for row in rows:
                bid = int(row["building_id"])
                db_building_vals.setdefault(bid, {})
                for month in range(1, 13):
                    db_building_vals[bid][month] = float(
                        _parse_cell_value(row.get(str(month)), metric)
                    )

            org_plans = {
                int(r[0]): (int(r[1] or 0), float(r[2] or 0))
                for r in conn.execute(
                    text(
                        """
                        SELECT month, quantity, amount
                        FROM plan_monthlyplan
                        WHERE annual_plan_id = :ap
                        """
                    ),
                    {"ap": ap_id},
                ).fetchall()
            }

            # месяцы с dirty-ячейками среди редактируемых корпусов
            dirty_months: set[int] = set()
            pending_updates: list[tuple[int, int, float, str]] = []  # bid, month, value, bname
            for row in rows:
                building_id = int(row["building_id"])
                b_base = group_base.get(str(building_id)) or {}
                bname = row.get("building_name") or str(building_id)
                for month in range(1, 13):
                    new_val = _parse_cell_value(row.get(str(month)), metric)
                    old_val = _parse_cell_value(b_base.get(str(month), 0), metric)
                    if is_finance:
                        changed = abs(float(new_val) - float(old_val)) > 0.001
                    else:
                        changed = int(new_val) != int(old_val)
                    if not changed:
                        continue
                    dirty_months.add(month)
                    pending_updates.append((building_id, month, float(new_val), bname))

            if not pending_updates:
                continue

            blocked_months: set[int] = set()
            for month in dirty_months:
                month_sum = sum(
                    float(db_building_vals.get(bid, {}).get(month, 0) or 0)
                    for bid in db_building_vals
                )
                org_qty, org_amt = org_plans.get(month, (0, 0.0))
                org_limit = float(org_amt) if is_finance else float(org_qty)

                if month_sum <= org_limit + (0.001 if is_finance else 0):
                    continue

                if raise_org_from_buildings:
                    if is_finance:
                        new_org = round(month_sum, 2)
                        conn.execute(
                            text(
                                """
                                UPDATE plan_monthlyplan
                                SET amount = :val
                                WHERE annual_plan_id = :ap AND month = :m
                                """
                            ),
                            {"val": new_org, "ap": ap_id, "m": month},
                        )
                        org_plans[month] = (org_qty, new_org)
                    else:
                        new_org = int(round(month_sum))
                        conn.execute(
                            text(
                                """
                                UPDATE plan_monthlyplan
                                SET quantity = :val
                                WHERE annual_plan_id = :ap AND month = :m
                                """
                            ),
                            {"val": new_org, "ap": ap_id, "m": month},
                        )
                        org_plans[month] = (new_org, org_amt)
                    raised_org += 1
                    continue

                blocked_months.add(month)
                if org_limit <= 0:
                    errors.append(
                        f"{group_path} мес.{month}: план МО = 0, сумма по корпусам = "
                        f"{int(month_sum) if not is_finance else month_sum}. "
                        f"Сначала заполните план МО или включите «Поднять план МО из суммы корпусов»."
                    )
                else:
                    errors.append(
                        f"{group_path} мес.{month}: сумма корпусов "
                        f"{int(month_sum) if not is_finance else month_sum} > план МО {int(org_limit) if not is_finance else org_limit}."
                    )

            # сохранить dirty-ячейки (кроме заблокированных месяцев)
            bp_cache: dict[int, int] = {}
            for building_id, month, value, bname in pending_updates:
                if month in blocked_months:
                    skipped += 1
                    continue

                if building_id not in bp_cache:
                    bp_row = conn.execute(
                        text(
                            """
                            SELECT id FROM plan_buildingplan
                            WHERE annual_plan_id = :ap AND building_id = :bid
                            """
                        ),
                        {"ap": ap_id, "bid": building_id},
                    ).fetchone()
                    if not bp_row:
                        bp_id = conn.execute(
                            text(
                                """
                                INSERT INTO plan_buildingplan (annual_plan_id, building_id)
                                VALUES (:ap, :bid)
                                RETURNING id
                                """
                            ),
                            {"ap": ap_id, "bid": building_id},
                        ).scalar()
                        created_bp += 1
                        for m in range(1, 13):
                            conn.execute(
                                text(
                                    """
                                    INSERT INTO plan_monthlybuildingplan
                                        (building_plan_id, month, quantity, amount)
                                    VALUES (:bp, :m, 0, 0)
                                    """
                                ),
                                {"bp": bp_id, "m": m},
                            )
                    else:
                        bp_id = int(bp_row[0])
                    bp_cache[building_id] = bp_id
                else:
                    bp_id = bp_cache[building_id]

                save_val = float(value) if is_finance else int(value)
                exists = conn.execute(
                    text(
                        """
                        SELECT id FROM plan_monthlybuildingplan
                        WHERE building_plan_id = :bp AND month = :m
                        """
                    ),
                    {"bp": bp_id, "m": month},
                ).fetchone()
                if not exists:
                    conn.execute(
                        text(
                            """
                            INSERT INTO plan_monthlybuildingplan
                                (building_plan_id, month, quantity, amount)
                            VALUES (:bp, :m, 0, 0)
                            """
                        ),
                        {"bp": bp_id, "m": month},
                    )
                conn.execute(
                    text(
                        f"""
                        UPDATE plan_monthlybuildingplan
                        SET {field} = :val
                        WHERE building_plan_id = :bp AND month = :m
                        """
                    ),
                    {"val": save_val, "bp": bp_id, "m": month},
                )
                updated += 1

    return {
        "updated": updated,
        "created_building_plans": created_bp,
        "raised_org_months": raised_org,
        "skipped": skipped,
        "errors": errors[:20],
    }


def baseline_from_blocks(blocks: list[dict]) -> dict:
    """{group_id: {building_id: {month: value}}}"""
    out: dict = {}
    for block in blocks or []:
        gid = str(block["group_id"])
        out[gid] = {}
        for row in block.get("rows") or []:
            bid = str(row["building_id"])
            out[gid][bid] = {str(m): row.get(str(m), 0) for m in range(1, 13)}
    return out
