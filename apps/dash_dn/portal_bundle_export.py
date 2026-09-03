"""
Конвертация dash_dn_catalog (JSON из build_catalog_from_excel) → пакет MosaicPortal
dispensary schema_version=1 (с checksum) для manage.py import_dispensary_bundle.

Граница периодов (как в catalog_periods / CATALOG_VERSIONS_QA.md):
  • «До»  — slug каталога matrix_before_20260401, effective_to = 2026-03-31
  • «После» — matrix_after_20260401, effective_from = 2026-04-01

Пример (из корня MosaicMedProject, PYTHONPATH=корень репозитория):

  py -m apps.dash_dn.build_catalog_from_excel \\
    --out apps/dash_dn/data/tmp_before.json \\
    --usl-spec apps/dn_reference/data/usl_spec \\
    --target-catalog matrix_before_20260401

  py -m apps.dash_dn.portal_bundle_export convert \\
    --dash-json apps/dash_dn/data/tmp_before.json \\
    --edition-code dn_before_20260401 \\
    --edition-title "Матрица ДН до 01.04.2026" \\
    --effective-from 2019-01-01 --effective-to 2026-03-31 \\
    --out apps/dash_dn/data/portal_dn_before.json

  py -m apps.dash_dn.build_catalog_from_excel \\
    --out apps/dash_dn/data/tmp_after.json \\
    --usl-spec apps/dash_dn/usl_spec_after \\
    --services "apps/dash_dn/Прил.8(Прил 35(Тарифы_диспансерное наблюдение_01 04 2026)).xlsx" \\
    --target-catalog matrix_after_20260401

  py -m apps.dash_dn.portal_bundle_export convert ... --out portal_dn_after.json

Затем в MosaicPortal:

  python manage.py import_dispensary_bundle apps/dash_dn/data/portal_dn_before.json
  python manage.py import_dispensary_bundle apps/dash_dn/data/portal_dn_after.json --activate
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def compute_bundle_checksum(payload: dict) -> str:
    body = {k: v for k, v in payload.items() if k != "checksum"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _slug_token(s: str, max_len: int = 64) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s.]+", "-", s)
    s = re.sub(r"[^a-z0-9_-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "x"
    return s[:max_len]


def _unique_slug(base: str, used: set[str]) -> str:
    b = base[:64]
    if b not in used:
        used.add(b)
        return b
    n = 2
    while True:
        suf = f"-{n}"
        cand = (base[: 64 - len(suf)] + suf)[:64]
        if cand not in used:
            used.add(cand)
            return cand
        n += 1


def dash_tables_to_portal_bundle(
    tables: dict[str, list[dict[str, Any]]],
    *,
    edition_code: str,
    edition_title: str,
    effective_from: str,
    effective_to: str | None,
    edition_status: str = "draft",
    notes: str = "",
) -> dict[str, Any]:
    used_slugs: set[str] = set()

    def slug(base: str, prefix: str, eid: int) -> str:
        raw = _slug_token(base)
        if len(raw) < 2:
            raw = f"{prefix}{eid}"
        return _unique_slug(raw[:64], used_slugs)

    cats = {int(r["id"]): r for r in tables.get("dn_diagnosis_category") or []}
    specs = {int(r["id"]): r for r in tables.get("dn_specialty") or []}
    diags = {int(r["id"]): r for r in tables.get("dn_diagnosis") or []}
    groups = {int(r["id"]): r for r in tables.get("dn_diagnosis_group") or []}
    services = {int(r["id"]): r for r in tables.get("dn_service") or []}
    periods = {int(r["id"]): r for r in tables.get("dn_service_price_period") or []}

    cat_id_to_code: dict[int, str] = {}
    for cid, r in sorted(cats.items()):
        name = str(r.get("name") or f"cat_{cid}")
        cat_id_to_code[cid] = slug(name, "ct_", cid)

    spec_id_to_code: dict[int, str] = {}
    for sid, r in sorted(specs.items()):
        name = str(r.get("name") or f"spec_{sid}")
        spec_id_to_code[sid] = slug(name, "sp_", sid)

    group_id_to_code: dict[int, str] = {}
    for gid, r in sorted(groups.items()):
        raw = str(r.get("code") or r.get("title") or f"g{gid}")
        group_id_to_code[gid] = slug(raw, "g_", gid)

    svc_id_to_code: dict[int, str] = {}
    for sid, r in sorted(services.items()):
        raw = str(r.get("code") or r.get("name") or f"svc{sid}")
        svc_id_to_code[sid] = slug(raw, "u_", sid)

    period_id_to_code: dict[int, str] = {}
    for pid, r in sorted(periods.items()):
        # Уникальный slug периода (даты/подписи могут совпасть между строками)
        period_id_to_code[pid] = _unique_slug(f"p{pid}", used_slugs)

    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "edition": {
            "code": edition_code.strip()[:64],
            "title": edition_title[:256],
            "effective_from": effective_from[:10],
            "effective_to": effective_to[:10] if effective_to else None,
            "status": edition_status,
            "notes": notes[:10000],
        },
        "specialties": [],
        "diagnosis_categories": [],
        "diagnoses": [],
        "diagnosis_specialties": [],
        "diagnosis_groups": [],
        "diagnosis_group_memberships": [],
        "services": [],
        "service_price_periods": [],
        "service_prices": [],
        "service_requirements": [],
        "organization_exclusions": [],
    }

    for sid, r in sorted(specs.items()):
        out["specialties"].append(
            {
                "code": spec_id_to_code[sid],
                "title": str(r.get("name") or spec_id_to_code[sid])[:256],
                "sort_order": int(sid),
            }
        )

    for cid, r in sorted(cats.items()):
        out["diagnosis_categories"].append(
            {
                "code": cat_id_to_code[cid],
                "title": str(r.get("name") or cat_id_to_code[cid])[:256],
                "parent_code": None,
                "sort_order": cid,
            }
        )

    for did, r in sorted(diags.items()):
        mkb = str(r.get("code") or "").strip().upper().replace(",", ".")[:16]
        if not mkb:
            continue
        cat_id = r.get("category_id")
        ccode = cat_id_to_code.get(int(cat_id)) if cat_id is not None else None
        if not ccode:
            ccode = next(iter(cat_id_to_code.values()), "misc")
        out["diagnoses"].append(
            {
                "mkb_code": mkb,
                "title": mkb[:512],
                "category_code": ccode,
            }
        )

    mkb_by_diag_id: dict[int, str] = {}
    for did, r in diags.items():
        mkb_by_diag_id[did] = str(r.get("code") or "").strip().upper().replace(",", ".")[:16]

    seen_ds: set[tuple[str, str, str]] = set()
    for row in tables.get("dn_diagnosis_specialty") or []:
        did = int(row["diagnosis_id"])
        sid = int(row["specialty_id"])
        src = str(row.get("source") or "primary").lower()
        if src not in ("primary", "joint", "accompanying"):
            src = "primary"
        mkb = mkb_by_diag_id.get(did, "")
        spc = spec_id_to_code.get(sid, "")
        if not mkb or not spc:
            continue
        key = (mkb, spc, src)
        if key in seen_ds:
            continue
        seen_ds.add(key)
        out["diagnosis_specialties"].append(
            {
                "mkb_code": mkb,
                "specialty_code": spc,
                "kind": src,
            }
        )

    for gid, r in sorted(groups.items()):
        out["diagnosis_groups"].append(
            {
                "code": group_id_to_code[gid],
                "title": str(r.get("title") or r.get("code") or group_id_to_code[gid])[:256],
                "rule": {},
                "sort_order": int(r.get("sort_order") or 0),
            }
        )

    seen_m: set[tuple[str, str]] = set()
    for row in tables.get("dn_diagnosis_group_membership") or []:
        gid = int(row["group_id"])
        did = int(row["diagnosis_id"])
        mkb = mkb_by_diag_id.get(did, "")
        gc = group_id_to_code.get(gid)
        if mkb and gc:
            k = (gc, mkb)
            if k in seen_m:
                continue
            seen_m.add(k)
            out["diagnosis_group_memberships"].append({"group_code": gc, "mkb_code": mkb})

    for sid, r in sorted(services.items()):
        code = svc_id_to_code[sid]
        name = str(r.get("name") or code)[:512]
        raw_code = str(r.get("code") or "")
        if raw_code and raw_code not in name:
            name = f"{raw_code} — {name}"[:512]
        out["services"].append(
            {
                "code": code,
                "title": name,
                "sort_order": int(r.get("sort_order") or sid),
            }
        )

    for pid, r in sorted(periods.items()):
        ds = str(r.get("date_start") or "")[:10]
        de = (str(r.get("date_end"))[:10] if r.get("date_end") else None) or None
        if len(ds) < 10:
            ds = effective_from[:10]
        out["service_price_periods"].append(
            {
                "code": period_id_to_code[pid],
                "title": str(r.get("title") or "")[:256],
                "valid_from": ds,
                "valid_to": de,
            }
        )

    seen_pr: set[tuple[str, str]] = set()
    for row in tables.get("dn_service_price") or []:
        sc = svc_id_to_code.get(int(row["service_id"]))
        pc = period_id_to_code.get(int(row["period_id"]))
        if not sc or not pc:
            continue
        price = row.get("price")
        try:
            amt = str(Decimal(str(price)).quantize(Decimal("0.01")))
        except Exception:
            continue
        pk = (pc, sc)
        if pk in seen_pr:
            continue
        seen_pr.add(pk)
        out["service_prices"].append(
            {
                "period_code": pc,
                "service_code": sc,
                "amount": amt,
                "currency": "RUB",
            }
        )

    seen_rq: set[tuple[str, str, str]] = set()
    for row in tables.get("dn_service_requirement") or []:
        sc = svc_id_to_code.get(int(row["service_id"]))
        gc = group_id_to_code.get(int(row["group_id"]))
        spc = spec_id_to_code.get(int(row["specialty_id"]))
        if not sc or not gc or not spc:
            continue
        rk = (sc, gc, spc)
        if rk in seen_rq:
            continue
        seen_rq.add(rk)
        out["service_requirements"].append(
            {
                "service_code": sc,
                "specialty_code": spc,
                "mkb_code": None,
                "diagnosis_group_code": gc,
            }
        )

    out["checksum"] = compute_bundle_checksum(out)
    return out


def _load_dash_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != "dash_dn_catalog":
        raise SystemExit(f"Ожидается format=dash_dn_catalog, получено: {data.get('format')}")
    tables = data.get("tables")
    if not isinstance(tables, dict):
        raise SystemExit("Нет ключа tables")
    return tables


def filter_tables_for_catalog(tables: dict[str, list], catalog_slug: str) -> dict[str, list]:
    """Оставить строки, у которых поле catalog совпадает со slug (как в bundle_global.json)."""
    slug = (catalog_slug or "").strip()
    out: dict[str, list] = {}
    for name, rows in tables.items():
        if not isinstance(rows, list):
            continue
        out[name] = [r for r in rows if str(r.get("catalog") or "") == slug]
    return out


def cmd_convert(args: argparse.Namespace) -> None:
    tables = _load_dash_json(Path(args.dash_json))
    bundle = dash_tables_to_portal_bundle(
        tables,
        edition_code=args.edition_code,
        edition_title=args.edition_title,
        effective_from=args.effective_from,
        effective_to=args.effective_to or None,
        edition_status=args.edition_status,
        notes=args.notes or "",
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Записано: {out} (checksum {bundle.get('checksum', '')[:32]}…)")


def cmd_convert_global(args: argparse.Namespace) -> None:
    """Вырезать один catalog из apps/dash_dn/data/bundle_global.json и конвертировать."""
    raw = json.loads(Path(args.global_json).read_text(encoding="utf-8"))
    if raw.get("format") != "dash_dn_catalog":
        raise SystemExit("Ожидается format=dash_dn_catalog")
    tables_all = raw.get("tables") or {}
    if not isinstance(tables_all, dict):
        raise SystemExit("Нет tables")
    tables = filter_tables_for_catalog(tables_all, args.catalog_slug)
    bundle = dash_tables_to_portal_bundle(
        tables,
        edition_code=args.edition_code,
        edition_title=args.edition_title,
        effective_from=args.effective_from,
        effective_to=args.effective_to or None,
        edition_status=args.edition_status,
        notes=args.notes or f"Источник: {args.global_json} catalog={args.catalog_slug}",
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Записано: {out} (catalog_slug={args.catalog_slug!r})")


def main() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    p = argparse.ArgumentParser(description="dash_dn_catalog → MosaicPortal dispensary bundle JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="Конвертировать один JSON dash_dn_catalog")
    c.add_argument("--dash-json", type=Path, required=True)
    c.add_argument("--edition-code", type=str, required=True)
    c.add_argument("--edition-title", type=str, required=True)
    c.add_argument("--effective-from", type=str, required=True)
    c.add_argument("--effective-to", type=str, default=None)
    c.add_argument("--edition-status", type=str, default="draft")
    c.add_argument("--notes", type=str, default="")
    c.add_argument("--out", type=Path, required=True)
    c.set_defaults(func=cmd_convert)

    g = sub.add_parser(
        "convert-global",
        help="Вырезать catalog_slug из одного bundle_global.json (несколько каталогов в одном файле)",
    )
    g.add_argument("--global-json", type=Path, required=True)
    g.add_argument("--catalog-slug", type=str, required=True, help="Напр. matrix_after_20260401")
    g.add_argument("--edition-code", type=str, required=True)
    g.add_argument("--edition-title", type=str, required=True)
    g.add_argument("--effective-from", type=str, required=True)
    g.add_argument("--effective-to", type=str, default=None)
    g.add_argument("--edition-status", type=str, default="draft")
    g.add_argument("--notes", type=str, default="")
    g.add_argument("--out", type=Path, required=True)
    g.set_defaults(func=cmd_convert_global)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
