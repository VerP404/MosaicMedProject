"""
Загрузка журнала ДН Квазар → load_data_dn_kvazar.

По умолчанию: scripts/дн исзл/квазар/Журнал диспансерного наблюдения.csv
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from psycopg2.extras import execute_values

DEFAULT_FILE = os.path.join(
    "scripts", "дн исзл", "квазар", "Журнал диспансерного наблюдения.csv"
)
TABLE = "load_data_dn_kvazar"


def _extract_mkb(raw) -> str:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return ""
    s = str(raw).strip().upper()
    m = re.match(r"([A-Z]\d{2}(?:\.\d{1,2})?)", s)
    return m.group(1) if m else ""


def _clean_enp(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace("`", "", regex=False).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.replace({"nan": "", "None": "", "-": ""})
    return s


def _find_col(columns, *needles: str):
    lower = {c: str(c).lower() for c in columns}
    for needle in needles:
        n = needle.lower()
        for c, lc in lower.items():
            if n in lc:
                return c
    return None


def _norm_header(c) -> str:
    return " ".join(str(c).replace("\n", " ").split()).strip()


class Command(BaseCommand):
    help = "Load Kvazar DN journal CSV into load_data_dn_kvazar"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=DEFAULT_FILE,
            help="Путь к CSV журнала Квазар",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить таблицу перед загрузкой",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_absolute():
            path = Path(os.getcwd()) / path
        if not path.exists():
            raise CommandError(f"Файл не найден: {path}")

        df = None
        for enc in ("cp1251", "utf-8-sig", "utf-8", "windows-1251"):
            try:
                df = pd.read_csv(path, sep=";", encoding=enc, dtype=str, low_memory=False)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise CommandError(f"Не удалось прочитать {path}")

        df.columns = [_norm_header(c) for c in df.columns]
        enp_col = _find_col(df.columns, "енп", "enp")
        diag_col = _find_col(df.columns, "диагноз")
        if enp_col is None or diag_col is None:
            raise CommandError(f"Нет колонок ЕНП/Диагноз. Колонки: {list(df.columns)}")

        fam = _find_col(df.columns, "фамилия")
        im = _find_col(df.columns, "имя")
        ot = _find_col(df.columns, "отчество")
        dr_col = _find_col(df.columns, "дата рождения", "д.р")
        sex_col = _find_col(df.columns, "пол")
        phone_col = _find_col(df.columns, "телефон", "контакт")
        begin_col = _find_col(df.columns, "дата постанов")
        end_cols = [c for c in df.columns if "снят" in str(c).lower() or "дата снятия" in str(c).lower()]
        end_col = end_cols[0] if end_cols else None
        doctor_col = _find_col(df.columns, "врач, наблюдающий", "врач наблюдающ")
        if doctor_col is None:
            doctor_col = _find_col(df.columns, "врач")
        spec_col = _find_col(df.columns, "специальность")
        uch_col = _find_col(df.columns, "участок")
        mo_col = _find_col(df.columns, "мо прикрепления", "организация")

        def col(name):
            if name is None:
                return pd.Series(["-"] * len(df))
            return df[name].fillna("-").astype(str)

        fio_parts = []
        for part_col in (fam, im, ot):
            if part_col:
                fio_parts.append(col(part_col).str.strip())
        if fio_parts:
            fio = fio_parts[0]
            for p in fio_parts[1:]:
                fio = (fio + " " + p).str.replace(r"\s+", " ", regex=True).str.strip()
        else:
            fio = pd.Series(["-"] * len(df))

        out = pd.DataFrame(
            {
                "enp": _clean_enp(col(enp_col)),
                "fio": fio,
                "dr": col(dr_col),
                "sex": col(sex_col),
                "phone": col(phone_col),
                "ds": col(diag_col),
                "date_begin": col(begin_col),
                "date_end": col(end_col),
                "doctor": col(doctor_col),
                "specialty": col(spec_col),
                "lpuuch": col(uch_col),
                "mo": col(mo_col),
            }
        )
        out["ds_code"] = out["ds"].map(_extract_mkb)
        out["source_file"] = path.name
        out = out[out["enp"].ne("") & out["ds_code"].ne("")].copy()

        def row_hash(r) -> str:
            key = "|".join(
                [
                    r.enp,
                    r.ds_code,
                    str(r.date_begin),
                    str(r.doctor),
                    str(r.ds)[:80],
                ]
            )
            return hashlib.sha1(key.encode("utf-8")).hexdigest()

        out["row_hash"] = [row_hash(r) for r in out.itertuples(index=False)]
        out = out.drop_duplicates(subset=["row_hash"], keep="last")
        self.stdout.write(f"Строк к загрузке: {len(out)} (ЕНП={out['enp'].nunique()})")

        cols = [
            "enp",
            "fio",
            "dr",
            "sex",
            "phone",
            "ds",
            "ds_code",
            "date_begin",
            "date_end",
            "doctor",
            "specialty",
            "lpuuch",
            "mo",
            "row_hash",
            "source_file",
        ]
        now = timezone.now()

        with connection.cursor() as cursor:
            if options["clear"]:
                cursor.execute(f"TRUNCATE TABLE {TABLE} RESTART IDENTITY")
                self.stdout.write("Таблица очищена")

            insert_cols = cols + ["created_at", "updated_at"]
            update_cols = [c for c in cols if c != "row_hash"]
            update_sql = ", ".join(f"{c}=EXCLUDED.{c}" for c in update_cols)
            update_sql += ", updated_at=EXCLUDED.updated_at"
            sql = f"""
                INSERT INTO {TABLE} ({", ".join(insert_cols)})
                VALUES %s
                ON CONFLICT (row_hash) DO UPDATE SET {update_sql}
            """
            rows = []
            for row in out[cols].itertuples(index=False, name=None):
                rows.append(tuple(row) + (now, now))

            batch = 2000
            for i in range(0, len(rows), batch):
                chunk = rows[i : i + batch]
                execute_values(cursor, sql, chunk, page_size=batch)
                self.stdout.write(f"  upsert {min(i + batch, len(rows))}/{len(rows)}")

            cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
            total = cursor.fetchone()[0]

        self.stdout.write(self.style.SUCCESS(f"В {TABLE}: {total} строк"))
