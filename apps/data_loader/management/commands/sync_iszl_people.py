from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import csv
import time
from datetime import datetime
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

        def log_info(message: str):
            ts = datetime.now().strftime("%H:%M:%S")
            self.stdout.write(f"[{ts}] {message}")

        log_info(
            f"Старт sync ISZLPeople | file={file_path} encoding={encoding} delimiter='{delimiter}' chunk={chunk_size}"
        )
        t0 = time.time()
        try:
            t_read0 = time.time()
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                file_rows = list(reader)
            log_info(f"CSV прочитан, строк: {len(file_rows)} | {time.time() - t_read0:.2f}s")
        except FileNotFoundError:
            raise CommandError(f"CSV файл не найден: {file_path}")

        if not file_rows:
            log_info("CSV пустой — изменений не требуется")
            return

        t_map0 = time.time()
        desired_records: Dict[str, Dict[str, Any]] = {}
        for idx, row in enumerate(file_rows, start=1):
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
            if idx % 50000 == 0:
                log_info(f"Парсинг CSV прогресс: {idx} строк обработано")
        log_info(f"Парсинг CSV завершён, валидных ENP: {len(desired_records)} | {time.time() - t_map0:.2f}s")

        if not desired_records:
            log_info("В CSV нет валидных ENP — изменений не требуется")
            return

        desired_enps: Set[str] = set(desired_records.keys())

        t_tx0 = time.time()
        log_info("Начало транзакции")
        with transaction.atomic():
            # Текущее состояние
            t_exist0 = time.time()
            existing_qs = ISZLPeople.objects.all().only(
                "pid", "fio", "dr", "smo", "enp", "lpu", "ss_doctor", "lpuuch", "upd", "closed", "column1"
            )
            existing_by_enp: Dict[str, ISZLPeople] = {obj.enp: obj for obj in existing_qs}
            log_info(f"Загружено из БД: {len(existing_by_enp)} строк | {time.time() - t_exist0:.2f}s")

            to_create: List[ISZLPeople] = []
            to_update: List[ISZLPeople] = []

            t_diff0 = time.time()
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
            log_info(
                f"Дифф рассчитан | create={len(to_create)} update={len(to_update)} delete={ISZLPeople.objects.exclude(enp__in=desired_enps).count()} | {time.time() - t_diff0:.2f}s"
            )

            # Удаления — всё, чего нет в файле
            t_del0 = time.time()
            to_delete_qs = ISZLPeople.objects.exclude(enp__in=desired_enps)
            deleted_before = to_delete_qs.count()
            log_info(f"Удаление отсутствующих записей start | count={deleted_before}")
            deleted_count, _ = to_delete_qs.delete()
            log_info(f"Удаление завершено | deleted={deleted_count} | {time.time() - t_del0:.2f}s")

            # Вставки
            created_total = 0
            if to_create:
                t_cre0 = time.time()
                total = len(to_create)
                for i in range(0, total, chunk_size):
                    ISZLPeople.objects.bulk_create(to_create[i : i + chunk_size], ignore_conflicts=True)
                    log_info(f"bulk_create прогресс: {min(i + chunk_size, total)}/{total}")
                created_total = total
                log_info(f"bulk_create завершён | total={created_total} | {time.time() - t_cre0:.2f}s")

            # Обновления
            updated_total = 0
            if to_update:
                t_upd0 = time.time()
                total = len(to_update)
                for i in range(0, total, chunk_size):
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
                    log_info(f"bulk_update прогресс: {min(i + chunk_size, total)}/{total}")
                updated_total = total
                log_info(f"bulk_update завершён | total={updated_total} | {time.time() - t_upd0:.2f}s")

        log_info(
            f"ISZLPeople sync завершён: добавлено {created_total}, обновлено {updated_total}, удалено {deleted_count}."
        )
        log_info(f"Итого время: {time.time() - t0:.2f}s")


