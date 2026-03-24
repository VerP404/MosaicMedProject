# -*- coding: utf-8 -*-
"""
Отчёт по выгрузке detail_services_*.csv (свод по диагнозам, талоны 1/2+ услуг,
проверка кодов по справочнику услуг).

По умолчанию допустимые коды берутся из SQLite (таблица dn_service, каталог global).
Опционально — из Excel «свод услуг.xlsx» (как раньше).

Используется CLI `scripts/дн услуги/report_detail_services.py` и вкладка «Анализ» в dash_dn.
"""
from __future__ import annotations

import csv
import io
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

try:
    from openpyxl import Workbook
    from openpyxl import load_workbook
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "Нужен пакет openpyxl: pip install openpyxl"
    ) from e

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE = _PROJECT_ROOT / "scripts" / "дн услуги" / "свод услуг.xlsx"

CODE_RE = re.compile(r"^[AB]\d{2}\.\d{2,3}\.\d{3}$", re.IGNORECASE)


def resolve_reference_path() -> Path:
    env = os.environ.get("DASH_DN_DETAIL_SERVICES_REF")
    if env:
        return Path(env.strip()).resolve()
    return DEFAULT_REFERENCE.resolve()


def _norm_code(s: str | None) -> str:
    if s is None:
        return ""
    t = str(s).strip().replace("\u00a0", " ")
    return t


def _is_missing_code(code: str) -> bool:
    if not code:
        return True
    if code in ("-", "—", ".", "–"):
        return True
    return False


def _parse_money(s: str | None) -> float:
    if s is None or str(s).strip() in ("", "-", "—"):
        return 0.0
    t = str(s).strip().replace("\u00a0", " ").replace(" ", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def load_allowed_service_codes(xlsx_path: Path) -> set[str]:
    """Читает коды услуг из 3-й колонки первого листа свода (колонка «Код»)."""
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    allowed: set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        if len(row) < 3:
            continue
        raw = row[2]
        if raw is None:
            continue
        c = _norm_code(str(raw))
        if not c or _is_missing_code(c):
            continue
        allowed.add(c.upper())
    wb.close()
    return allowed


def load_allowed_service_codes_from_db(
    catalog: str = "global",
    *,
    engine: Engine | None = None,
) -> set[str]:
    """Коды активных услуг из локальной SQLite (dn_service), как во вкладке «Подбор услуг ДН»."""
    from apps.dash_dn.sqlite_catalog.db import get_engine

    eng = engine or get_engine()
    q = text(
        """
        SELECT UPPER(TRIM(code)) AS c
        FROM dn_service
        WHERE catalog = :cat AND is_active = 1
          AND code IS NOT NULL AND TRIM(code) != ''
        """
    )
    with eng.connect() as conn:
        rows = conn.execute(q, {"cat": catalog}).fetchall()
    return {r[0] for r in rows if r[0]}


def pick_csv_path(script_dir: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    d = script_dir / "выгрузки"
    candidates = sorted(
        d.glob("detail_services_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"Не найден CSV в {d}. Укажите --csv путь к файлу."
        )
    return candidates[0]


def read_detail_csv_from_text(text: str) -> tuple[list[str], list[dict[str, str]]]:
    f = io.StringIO(text)
    r = csv.DictReader(f, delimiter=";")
    if not r.fieldnames:
        raise ValueError("Пустой CSV или нет заголовка")
    fieldnames = list(r.fieldnames)
    rows = [dict(row) for row in r]
    return fieldnames, rows


def read_detail_csv_from_bytes(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = raw.decode("utf-8-sig")
    return read_detail_csv_from_text(text)


def read_detail_csv(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    return read_detail_csv_from_bytes(csv_path.read_bytes())


def _status_from_row(row: dict[str, str]) -> str:
    v = row.get("Статус")
    if v is None:
        return ""
    return _norm_code(str(v))


def _format_services_for_ticket(trows: list[dict[str, str]]) -> str:
    """Строка для отчёта: «код — сумма» по каждой строке талона, через «; ».

    Код берётся только из колонки «Код услуги». Если там «-» или пусто (часто у Квазар
    для части строк одного талона), показываем «без кода в выгрузке», а не второй прочерк.
    """
    parts: list[str] = []
    for r in trows:
        code = _norm_code(r.get("Код услуги"))
        if _is_missing_code(code):
            label = "без кода в выгрузке"
        else:
            label = code
        sm = _parse_money(r.get("Сумма услуги"))
        qty_raw = r.get("Кол-во услуг")
        try:
            if qty_raw in (None, "", "-", "—"):
                qty = 1.0
            else:
                qty = float(str(qty_raw).strip().replace(",", ".").replace(" ", ""))
        except ValueError:
            qty = 1.0
        if qty != 1.0:
            parts.append(f"{label} — {sm} (×{qty:g})")
        else:
            parts.append(f"{label} — {sm}")
    return "; ".join(parts)


def build_report(
    rows: list[dict[str, str]],
    allowed_codes: set[str],
) -> dict[str, Any]:
    col_ticket = "Талон"
    col_ds1 = "Диагноз основной (DS1)"
    col_code = "Код услуги"
    col_ticket_sum = "Сумма талона"

    if not rows:
        raise ValueError("В CSV нет строк данных.")

    for c in (col_ticket, col_ds1, col_code, col_ticket_sum):
        if c not in rows[0]:
            raise KeyError(
                f"В CSV нет колонки «{c}». Проверьте формат выгрузки."
            )

    ticket_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        tid = _norm_code(row.get(col_ticket))
        if not tid:
            continue
        ticket_rows[tid].append(row)

    per_ticket: list[dict[str, Any]] = []
    for tid, trows in ticket_rows.items():
        first = trows[0]
        diagnosis = _norm_code(first.get(col_ds1)) or "(без диагноза)"
        n_services = len(trows)
        ticket_sum = _parse_money(first.get(col_ticket_sum))
        per_ticket.append(
            {
                "талон": tid,
                "статус": _status_from_row(first),
                "диагноз": diagnosis,
                "число_строк_услуг": n_services,
                "сумма_талона": ticket_sum,
                "услуги": _format_services_for_ticket(trows),
            }
        )

    by_diagnosis: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"талонов": 0, "сумма_талонов": 0.0}
    )
    for t in per_ticket:
        d = str(t["диагноз"])
        by_diagnosis[d]["талонов"] += 1
        by_diagnosis[d]["сумма_талонов"] += float(t["сумма_талона"])

    single_service = [t for t in per_ticket if t["число_строк_услуг"] == 1]
    multi_service = [t for t in per_ticket if t["число_строк_услуг"] > 1]

    invalid_lines: list[dict[str, Any]] = []
    invalid_by_code: dict[str, int] = defaultdict(int)
    no_code_lines: list[dict[str, Any]] = []

    for row in rows:
        tid = _norm_code(row.get(col_ticket))
        code = _norm_code(row.get(col_code))
        ds1 = _norm_code(row.get(col_ds1)) or "(без диагноза)"
        if _is_missing_code(code):
            no_code_lines.append(
                {
                    "талон": tid,
                    "статус": _status_from_row(row),
                    "диагноз": ds1,
                    "код_услуги": code or "",
                    "сумма_услуги": _parse_money(row.get("Сумма услуги")),
                }
            )
            continue
        if not CODE_RE.match(code):
            invalid_lines.append(
                {
                    "талон": tid,
                    "статус": _status_from_row(row),
                    "диагноз": ds1,
                    "код_услуги": code,
                    "причина": "неверный формат кода",
                    "сумма_услуги": _parse_money(row.get("Сумма услуги")),
                }
            )
            invalid_by_code[code.upper()] += 1
            continue
        if code.upper() not in allowed_codes:
            invalid_lines.append(
                {
                    "талон": tid,
                    "статус": _status_from_row(row),
                    "диагноз": ds1,
                    "код_услуги": code,
                    "причина": "нет в справочнике услуг",
                    "сумма_услуги": _parse_money(row.get("Сумма услуги")),
                }
            )
            invalid_by_code[code.upper()] += 1

    return {
        "per_ticket": per_ticket,
        "by_diagnosis": by_diagnosis,
        "single_service": single_service,
        "multi_service": multi_service,
        "invalid_lines": invalid_lines,
        "invalid_by_code": dict(sorted(invalid_by_code.items(), key=lambda x: -x[1])),
        "no_code_lines": no_code_lines,
        "unique_tickets": len(ticket_rows),
        "total_rows": len(rows),
    }


def write_xlsx(
    out_path: Path,
    report: dict[str, Any],
    *,
    source_csv: Path,
    reference_note: str,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    ws0 = wb.active
    ws0.title = "Параметры"
    ws0.append(["Источник CSV", str(source_csv)])
    ws0.append(["Справочник услуг", reference_note])
    ws0.append(["Уникальных талонов", report["unique_tickets"]])
    ws0.append(["Строк в выгрузке", report["total_rows"]])

    ws1 = wb.create_sheet("Свод по диагнозам")
    ws1.append(["Диагноз основной (DS1)", "Талонов", "Сумма талонов"])
    for diag, agg in sorted(
        report["by_diagnosis"].items(),
        key=lambda x: (-x[1]["талонов"], x[0]),
    ):
        ws1.append([diag, agg["талонов"], round(float(agg["сумма_талонов"]), 2)])

    ws2 = wb.create_sheet("Талоны 1 услуга")
    ws2.append(["Талон", "Статус", "Диагноз (DS1)", "Услуги (код — сумма)", "Сумма талона"])
    for t in sorted(report["single_service"], key=lambda x: x["талон"]):
        ws2.append(
            [
                t["талон"],
                t.get("статус", ""),
                t["диагноз"],
                t.get("услуги", ""),
                round(float(t["сумма_талона"]), 2),
            ]
        )

    ws3 = wb.create_sheet("Талоны 2+ услуг")
    ws3.append(
        [
            "Талон",
            "Статус",
            "Диагноз (DS1)",
            "Услуги (код — сумма)",
            "Сумма талона",
            "Число строк услуг",
        ]
    )
    for t in sorted(report["multi_service"], key=lambda x: (-x["число_строк_услуг"], x["талон"])):
        ws3.append(
            [
                t["талон"],
                t.get("статус", ""),
                t["диагноз"],
                t.get("услуги", ""),
                round(float(t["сумма_талона"]), 2),
                t["число_строк_услуг"],
            ]
        )

    ws4 = wb.create_sheet("Коды не из справочника")
    ws4.append(
        ["Талон", "Статус", "Диагноз (DS1)", "Код услуги", "Причина", "Сумма услуги"]
    )
    for line in report["invalid_lines"]:
        ws4.append(
            [
                line["талон"],
                line.get("статус", ""),
                line["диагноз"],
                line["код_услуги"],
                line["причина"],
                round(float(line["сумма_услуги"]), 2),
            ]
        )

    ws5 = wb.create_sheet("Свод по «левым» кодам")
    ws5.append(["Код услуги", "Строк в выгрузке"])
    for code, n in report["invalid_by_code"].items():
        ws5.append([code, n])

    ws6 = wb.create_sheet("Строки без кода услуги")
    ws6.append(["Талон", "Статус", "Диагноз (DS1)", "Поле «Код услуги»", "Сумма услуги"])
    for line in report["no_code_lines"]:
        ws6.append(
            [
                line["талон"],
                line.get("статус", ""),
                line["диагноз"],
                line["код_услуги"],
                round(float(line["сумма_услуги"]), 2),
            ]
        )

    wb.save(out_path)
