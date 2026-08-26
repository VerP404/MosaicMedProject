"""
Загрузка ВСЕХ годовых Report*.csv ИСЗЛ ДН в load_data_dispansery_iszl.

Dagster iszl_job_dn при load_all_matching_files тоже читает все файлы из iszl/dn,
но удобнее один раз прогнать архив из scripts/дн исзл/выгрузки этой командой.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from psycopg2.extras import execute_values

DEFAULT_SOURCE = os.path.join("scripts", "дн исзл", "выгрузки")
MAPPING_PATH = os.path.join("mosaic_conductor", "etl", "config", "mapping.json")
TABLE = "load_data_dispansery_iszl"


class Command(BaseCommand):
    help = "Load all ISZL DN Report*.csv (all PlanYears) into load_data_dispansery_iszl"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default=DEFAULT_SOURCE,
            help="Папка с Report*.csv (по умолчанию scripts/дн исзл/выгрузки)",
        )
        parser.add_argument(
            "--sync",
            action="store_true",
            help="После загрузки вызвать sync_dn_from_iszl по всем годам",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить load_data_dispansery_iszl перед загрузкой",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_absolute():
            source = Path(os.getcwd()) / source
        if not source.exists():
            raise CommandError(f"Папка не найдена: {source}")

        mapping_file = Path(os.getcwd()) / MAPPING_PATH
        with open(mapping_file, encoding="utf-8") as f:
            mappings = json.load(f)
        table_cfg = mappings["tables"][TABLE]
        field_map = table_cfg["mapping_fields"]  # CSV header -> db column
        encoding = table_cfg.get("encoding", "cp1251")
        delimiter = table_cfg.get("delimiter", ";")

        files = sorted(source.glob("Report*.csv"))
        if not files:
            raise CommandError(f"Нет Report*.csv в {source}")

        frames = []
        for f in files:
            df = None
            for enc in (encoding, "cp1251", "utf-8-sig", "utf-8"):
                try:
                    df = pd.read_csv(f, sep=delimiter, encoding=enc, dtype=str, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                self.stdout.write(self.style.WARNING(f"Пропуск (encoding): {f.name}"))
                continue
            df.columns = [str(c).strip() for c in df.columns]
            rename = {src: dst for src, dst in field_map.items() if src in df.columns}
            df = df.rename(columns=rename)
            needed = list(field_map.values())
            for col in needed:
                if col not in df.columns:
                    df[col] = "-"
            df = df[needed].copy()
            df = df.fillna("-")
            # нормализация plan_year / enp
            df["plan_year"] = (
                df["plan_year"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
            )
            df["enp"] = df["enp"].astype(str).str.replace("`", "", regex=False).str.strip()
            df["pdwid"] = df["pdwid"].astype(str).str.strip()
            df = df[df["pdwid"].ne("") & df["pdwid"].ne("-")]
            # дедуп внутри файла по pdwid
            df = df.drop_duplicates(subset=["pdwid"], keep="last")
            self.stdout.write(f"{f.name}: {len(df)} rows, years={sorted(df['plan_year'].unique())[:5]}")
            frames.append(df)

        if not frames:
            raise CommandError("Не удалось прочитать ни одного файла")

        all_df = pd.concat(frames, ignore_index=True)
        all_df = all_df.drop_duplicates(subset=["pdwid"], keep="last")
        self.stdout.write(f"Итого уникальных pdwid: {len(all_df)}")
        self.stdout.write(str(all_df["plan_year"].value_counts().sort_index().to_dict()))

        cols = list(field_map.values())
        now = timezone.now()

        with connection.cursor() as cursor:
            if options["clear"]:
                cursor.execute(f"TRUNCATE TABLE {TABLE} RESTART IDENTITY")
                self.stdout.write("Таблица очищена")

            # batch upsert
            insert_cols = cols + ["created_at", "updated_at"]
            update_cols = [c for c in cols if c != "pdwid"]
            update_sql = ", ".join(f"{c}=EXCLUDED.{c}" for c in update_cols)
            update_sql += ", updated_at=EXCLUDED.updated_at"
            sql = f"""
                INSERT INTO {TABLE} ({", ".join(insert_cols)})
                VALUES %s
                ON CONFLICT (pdwid) DO UPDATE SET {update_sql}
            """
            rows = []
            for row in all_df[cols].itertuples(index=False, name=None):
                rows.append(tuple(row) + (now, now))

            batch = 2000
            for i in range(0, len(rows), batch):
                chunk = rows[i : i + batch]
                execute_values(cursor, sql, chunk, page_size=batch)
                self.stdout.write(f"  upsert {min(i + batch, len(rows))}/{len(rows)}")

            cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
            total = cursor.fetchone()[0]
            cursor.execute(
                f"""
                SELECT plan_year, COUNT(*) FROM {TABLE}
                GROUP BY plan_year ORDER BY plan_year
                """
            )
            by_year = cursor.fetchall()

        self.stdout.write(self.style.SUCCESS(f"В таблице {total} строк: {by_year}"))

        if options["sync"]:
            from django.core.management import call_command

            call_command("sync_dn_from_iszl", all_years=True)
