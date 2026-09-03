# -*- coding: utf-8 -*-
"""Импорт справочника школ 307 из Excel."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.health_schools.models import HealthSchool

_APP_DIR = Path(__file__).resolve().parents[2]
_PROJECT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_XLSX = _PROJECT_DIR / "scripts" / "307 цель" / "Справочник 307 цели.xlsx"
APP_XLSX = _APP_DIR / "data" / "catalog.xlsx"


def _cell(row: dict, *names: str) -> str:
    lower = {str(k).strip().lower(): k for k in row}
    for name in names:
        key = lower.get(name.lower())
        if key is not None:
            val = row[key]
            if val is None:
                return ""
            s = str(val).strip()
            if s.lower() in {"nan", "none"}:
                return ""
            return s
    return ""


def _int(val: str, default: int) -> int:
    try:
        return int(float(str(val).replace(",", ".").strip() or default))
    except (TypeError, ValueError):
        return default


def _money(val: str) -> Decimal:
    try:
        return Decimal(str(val).replace(",", ".").replace(" ", "") or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def infer_criterion(name: str, mkb: str, group: str) -> tuple[str, int | None, int | None]:
    blob = f"{name} {mkb} {group}".lower()
    if "65" in blob or "долголет" in blob:
        return HealthSchool.Criterion.AGE, 65, None
    if "дети" in blob or "подрост" in blob:
        return HealthSchool.Criterion.MKB, None, 17
    if "взрослые" in blob:
        return HealthSchool.Criterion.MKB, 18, None
    if "имт" in blob or "ожирен" in blob or "массы тела" in blob:
        return HealthSchool.Criterion.BMI, None, None
    if "фактор риска" in blob or "образ жизни" in blob:
        return HealthSchool.Criterion.RISK, None, None
    return HealthSchool.Criterion.MKB, None, None


class Command(BaseCommand):
    help = "Импорт справочника школ цели 307 из Excel (колонки как в «Справочник 307 цели.xlsx»)."

    def add_arguments(self, parser):
        parser.add_argument("xlsx_path", nargs="?", default="", help="Путь к xlsx")
        parser.add_argument("--period", type=int, default=3, help="Периодичность по умолчанию, лет")

    def handle(self, *args, **options):
        raw = options["xlsx_path"]
        path = Path(raw) if raw else (DEFAULT_XLSX if DEFAULT_XLSX.is_file() else APP_XLSX)
        if not path.is_file():
            raise CommandError(f"Файл не найден: {path}")
        try:
            import pandas as pd
        except ImportError as e:
            raise CommandError("Нужен pandas") from e

        df = pd.read_excel(path, dtype=str).fillna("")
        if df.empty:
            raise CommandError("Пустой справочник")

        period = int(options["period"] or 3)
        created = updated = 0
        with transaction.atomic():
            for rec in df.to_dict("records"):
                number = _int(_cell(rec, "№", "n", "номер"), 0)
                name = _cell(rec, "школа", "name")
                if not number or not name:
                    continue
                mkb = _cell(rec, "МКБ / критерий", "мкб", "mkb")
                group = _cell(rec, "группа", "group")
                criterion, min_age, max_age = infer_criterion(name, mkb, group)
                defaults = {
                    "name": name,
                    "group_name": group,
                    "mkb_rule": mkb,
                    "visits": _int(_cell(rec, "явки", "visits"), 4),
                    "duration": _cell(rec, "длительность", "duration"),
                    "tariff": _money(_cell(rec, "тариф_руб", "тариф")),
                    "service_code": _cell(rec, "код_услуги", "код"),
                    "service_title": _cell(rec, "наименование_услуги", "услуга"),
                    "criterion": criterion,
                    "min_age": min_age,
                    "max_age": max_age,
                    "is_active": True,
                }
                obj, was_created = HealthSchool.objects.update_or_create(number=number, defaults=defaults)
                if was_created:
                    obj.period_years = period
                    obj.save(update_fields=["period_years"])
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Импорт {path.name}: создано {created}, обновлено {updated}"))
