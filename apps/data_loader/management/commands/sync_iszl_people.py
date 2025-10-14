from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import csv
from typing import Dict, Any, List, Set
import re

from apps.data_loader.models.iszl import ISZLPeople


CSV_POSSIBLE_MAP = {
    "pid": ["pid", "PID"],
    "fio": ["fio", "FIO"],
    "dr": ["dr", "DR", "birth_date", "BIRTH_DATE", "Дата рождения", "ДР"],
    "smo": ["smo", "SMO"],
    "enp": ["enp", "ENP"],
    "lpu": ["lpu", "LPU"],
    "ss_doctor": ["ss_doctor", "SS_DOCTOR", "SS_D"],
    "lpuuch": ["lpuuch", "LPUUCH", "Участок", "UCH"],
    "upd": ["upd", "UPD", "updated", "UPDATED"],
    "closed": ["closed", "CLOSED"],
    "column1": ["column1", "Column1", "COLUMN1"],
}


def get_by_keys(row: Dict[str, Any], keys: List[str], default: str = "-") -> str:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    # try case-insensitive
    lowered = {k.lower(): v for k, v in row.items()}
    for key in keys:
        lk = key.lower()
        if lk in lowered and lowered[lk] not in (None, ""):
            return lowered[lk]
    return default


class Command(BaseCommand):
    help = (
        "Синхронизация таблицы ISZLPeople из CSV снапшота: добавляет отсутствующие, обновляет существующие и "
        "удаляет записи, отсутствующие в файле (по ключу ENP)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", dest="file_path", required=True, help="Путь к CSV файлу населения")
        parser.add_argument("--encoding", dest="encoding", default="utf-8-sig")
        parser.add_argument("--delimiter", dest="delimiter", default=";")
        parser.add_argument("--chunk", dest="chunk", type=int, default=1000, help="Размер чанка для bulk операций")

    def handle(self, *args, **options):
        file_path = options["file_path"]
        encoding = options["encoding"]
        delimiter = options["delimiter"]
        chunk_size = options["chunk"]

        try:
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                file_rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"CSV файл не найден: {file_path}")

        if not file_rows:
            self.stdout.write(self.style.WARNING("CSV пустой — изменений не требуется"))
            return

        desired_records: Dict[str, Dict[str, Any]] = {}
        for row in file_rows:
            raw_enp = get_by_keys(row, CSV_POSSIBLE_MAP["enp"], default="-")
            # Очистка ENP: убрать обратные кавычки и любые нецифровые символы
            enp = re.sub(r"[^0-9]", "", str(raw_enp))
            if not enp or enp == "-":
                continue
            desired_records[enp] = {
                "pid": get_by_keys(row, CSV_POSSIBLE_MAP["pid"]),
                "fio": get_by_keys(row, CSV_POSSIBLE_MAP["fio"]),
                "dr": get_by_keys(row, CSV_POSSIBLE_MAP["dr"]),
                "smo": get_by_keys(row, CSV_POSSIBLE_MAP["smo"]),
                "enp": enp,
                "lpu": get_by_keys(row, CSV_POSSIBLE_MAP["lpu"]),
                "ss_doctor": get_by_keys(row, CSV_POSSIBLE_MAP["ss_doctor"]),
                "lpuuch": get_by_keys(row, CSV_POSSIBLE_MAP["lpuuch"]),
                "upd": get_by_keys(row, CSV_POSSIBLE_MAP["upd"]),
                "closed": get_by_keys(row, CSV_POSSIBLE_MAP["closed"], default="0"),
                "column1": get_by_keys(row, CSV_POSSIBLE_MAP["column1"], default="-"),
            }

        if not desired_records:
            self.stdout.write(self.style.WARNING("В CSV нет валидных ENP — изменений не требуется"))
            return

        desired_enps: Set[str] = set(desired_records.keys())

        with transaction.atomic():
            # Текущее состояние
            existing_qs = ISZLPeople.objects.all().only(
                "pid", "fio", "dr", "smo", "enp", "lpu", "ss_doctor", "lpuuch", "upd", "closed", "column1"
            )
            existing_by_enp: Dict[str, ISZLPeople] = {obj.enp: obj for obj in existing_qs}

            to_create: List[ISZLPeople] = []
            to_update: List[ISZLPeople] = []

            for enp, values in desired_records.items():
                existing = existing_by_enp.get(enp)
                if existing is None:
                    to_create.append(ISZLPeople(**values))
                else:
                    changed = False
                    for field, new_val in values.items():
                        if getattr(existing, field) != new_val:
                            setattr(existing, field, new_val)
                            changed = True
                    if changed:
                        to_update.append(existing)

            # Удаления — всё, чего нет в файле
            to_delete_qs = ISZLPeople.objects.exclude(enp__in=desired_enps)
            deleted_count, _ = to_delete_qs.delete()

            # Вставки
            created_total = 0
            if to_create:
                for i in range(0, len(to_create), chunk_size):
                    ISZLPeople.objects.bulk_create(to_create[i : i + chunk_size], ignore_conflicts=True)
                created_total = len(to_create)

            # Обновления
            updated_total = 0
            if to_update:
                for i in range(0, len(to_update), chunk_size):
                    ISZLPeople.objects.bulk_update(
                        to_update[i : i + chunk_size],
                        [
                            "pid",
                            "fio",
                            "dr",
                            "smo",
                            "lpu",
                            "ss_doctor",
                            "lpuuch",
                            "upd",
                            "closed",
                            "column1",
                        ],
                    )
                updated_total = len(to_update)

        self.stdout.write(
            self.style.SUCCESS(
                f"ISZLPeople sync завершён: добавлено {created_total}, обновлено {updated_total}, удалено {deleted_count}."
            )
        )


