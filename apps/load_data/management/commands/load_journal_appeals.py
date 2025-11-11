from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

import os
import csv
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from apps.load_data.models import JournalAppeals
from psycopg2.extras import execute_values


APPEALS_DIR = os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "kvazar", "appeals")


def find_latest_csv(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Папка не найдена: {path}")
    files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.csv')]
    if not files:
        raise FileNotFoundError(f"В {path} нет CSV файлов")
    return max(files, key=os.path.getmtime)


RUS_MAP_SINGLE = {
    # patient fields
    "Дата рождения": "birth_date",
    "Пол": "gender",
    "Телефон": "phone",
    "ЕНП": "enp",
    "Прикрепление": "attachment",
    "Серия": "series",
    "Номер": "number",
    # employee fields
    "Должность": "position",
    "Дата приема": "acceptance_date",
    "Дата записи": "record_date",
    "Тип расписания": "schedule_type",
    "Источник записи": "record_source",
    "Подразделение": "department",
    "Создавший": "creator",
    "Не явился": "no_show",
    "ЭПМЗ": "epmz",
}


def build_header_index(header_row: List[str]) -> Dict[str, List[int]]:
    idx: Dict[str, List[int]] = {}
    for i, h in enumerate(header_row):
        key = (h or '').strip()
        idx.setdefault(key, []).append(i)
    return idx


def resolve_duplicated_names(header_row: List[str]) -> Dict[int, str]:
    """Разруливает дубли 'Фамилия;Имя;Отчество': первые встречные — пациент, вторые — сотрудник."""
    name_keys = ["Фамилия", "Имя", "Отчество"]
    result: Dict[int, str] = {}
    counts = {k: 0 for k in name_keys}
    for i, h in enumerate(header_row):
        h_norm = (h or '').strip()
        if h_norm in name_keys:
            counts[h_norm] += 1
            if counts[h_norm] == 1:
                # первая тройка — пациент
                if h_norm == "Фамилия":
                    result[i] = "patient_last_name"
                elif h_norm == "Имя":
                    result[i] = "patient_first_name"
                elif h_norm == "Отчество":
                    result[i] = "patient_middle_name"
            else:
                # вторая тройка — сотрудник (врач/сотрудник расписания)
                if h_norm == "Фамилия":
                    result[i] = "employee_last_name"
                elif h_norm == "Имя":
                    result[i] = "employee_first_name"
                elif h_norm == "Отчество":
                    result[i] = "employee_middle_name"
    return result


def normalize_enp(value: str) -> str:
    return ''.join(ch for ch in str(value) if ch.isdigit()) or '-'


class Command(BaseCommand):
    help = "Загрузка CSV обращений в таблицу load_data_journal_appeals с разруливанием дублирующихся ФИО"

    def add_arguments(self, parser):
        parser.add_argument("--file", dest="file_path", help="Путь к CSV; если не указан — берём последний из папки appeals")
        parser.add_argument("--encoding", dest="encoding", default="utf-8-sig")
        parser.add_argument("--delimiter", dest="delimiter", default=";")
        parser.add_argument("--chunk", dest="chunk", type=int, default=2000)

    def handle(self, *args, **options):
        file_path = options.get("file_path") or find_latest_csv(APPEALS_DIR)
        encoding = options.get("encoding")
        delimiter = options.get("delimiter")
        chunk = int(options.get("chunk") or 2000)

        def log(msg: str):
            self.stdout.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

        log(f"Старт загрузки appeals | file={file_path}")
        t0 = time.time()
        try:
            enc_candidates = []
            for enc in [encoding, "utf-8-sig", "utf-8", "cp1251", "windows-1251", "koi8-r", "utf-16", "utf-16le", "utf-16be"]:
                if enc and enc not in enc_candidates:
                    enc_candidates.append(enc)

            header = None
            rows_raw: List[List[str]] = []
            used_encoding = None
            for enc_try in enc_candidates:
                try:
                    with open(file_path, "r", encoding=enc_try, newline="") as f:
                        reader = csv.reader(f, delimiter=delimiter)
                        header_try = next(reader)
                        rows_try = list(reader)
                        header = [h.strip() for h in header_try]
                        rows_raw = rows_try
                        used_encoding = enc_try
                        break
                except UnicodeDecodeError:
                    continue
            if header is None:
                raise CommandError("Не удалось декодировать CSV ни в одной из кодировок: " + ", ".join(enc_candidates))

            log(f"Кодировка распознана: {used_encoding}")

            dup_map = resolve_duplicated_names(header)
            single_idx = build_header_index(header)

            table = JournalAppeals._meta.db_table
            columns = [
                "patient_last_name", "patient_first_name", "patient_middle_name",
                "birth_date", "gender", "phone", "enp", "attachment", "series", "number",
                "employee_last_name", "employee_first_name", "employee_middle_name",
                "position", "acceptance_date", "record_date", "schedule_type", "record_source",
                "department", "creator", "no_show", "epmz"
            ]

            def row_to_values(row: List[str]) -> List[str]:
                values: Dict[str, Optional[str]] = {c: '-' for c in columns}
                # дубли ФИО
                for i, val in enumerate(row):
                    if i in dup_map:
                        values[dup_map[i]] = (val or '-').strip()
                # одиночные поля
                for rus, field in RUS_MAP_SINGLE.items():
                    idx_list = single_idx.get(rus, [])
                    if idx_list:
                        values[field] = (row[idx_list[0]] or '-').strip()
                # нормализация ENP
                values["enp"] = normalize_enp(values["enp"])
                return [values[c] for c in columns]

            rows: List[List[str]] = [row_to_values(r) for r in rows_raw]
            log(f"CSV прочитан, строк: {len(rows_raw)} | {time.time() - t0:.2f}s")

            # Дедупликация по ключу конфликта (enp, employee_last_name, acceptance_date)
            # Оставляем последнюю запись для каждого уникального ключа
            enp_idx = columns.index("enp")
            employee_last_name_idx = columns.index("employee_last_name")
            acceptance_date_idx = columns.index("acceptance_date")
            
            seen_keys = {}
            deduplicated_rows = []
            for row in rows:
                key = (
                    row[enp_idx] or '-',
                    row[employee_last_name_idx] or '-',
                    row[acceptance_date_idx] or '-'
                )
                seen_keys[key] = row
            
            deduplicated_rows = list(seen_keys.values())
            if len(deduplicated_rows) < len(rows):
                log(f"Дедупликация: {len(rows)} -> {len(deduplicated_rows)} строк (удалено {len(rows) - len(deduplicated_rows)} дубликатов)")
            rows = deduplicated_rows

        except FileNotFoundError as e:
            raise CommandError(str(e))

        # DB upsert через временную таблицу
        with transaction.atomic():
            with connection.cursor() as cursor:
                table = JournalAppeals._meta.db_table
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]
                log(f"Строк в {table} до загрузки: {count_before}")
                cursor.execute(
                    """
                    CREATE TEMP TABLE tmp_journal_appeals (
                        patient_last_name varchar(255),
                        patient_first_name varchar(255),
                        patient_middle_name varchar(255),
                        birth_date varchar(50),
                        gender varchar(50),
                        phone varchar(50),
                        enp varchar(255),
                        attachment varchar(255),
                        series varchar(50),
                        number varchar(50),
                        employee_last_name varchar(255),
                        employee_first_name varchar(255),
                        employee_middle_name varchar(255),
                        position varchar(255),
                        acceptance_date varchar(50),
                        record_date varchar(50),
                        schedule_type varchar(255),
                        record_source varchar(255),
                        department varchar(255),
                        creator varchar(255),
                        no_show varchar(50),
                        epmz varchar(255)
                    ) ON COMMIT DROP;
                    """
                )

                log("Загрузка во временную таблицу...")
                t_load = time.time()
                execute_values(
                    cursor,
                    """
                    INSERT INTO tmp_journal_appeals (
                        patient_last_name, patient_first_name, patient_middle_name,
                        birth_date, gender, phone, enp, attachment, series, number,
                        employee_last_name, employee_first_name, employee_middle_name,
                        position, acceptance_date, record_date, schedule_type, record_source,
                        department, creator, no_show, epmz
                    ) VALUES %s
                    """,
                    rows,
                    page_size=chunk,
                )
                log(f"Во временную загружено | {time.time() - t_load:.2f}s")

                log("Upsert в основную таблицу...")
                t_upsert = time.time()
                cursor.execute(
                    f"""
                    INSERT INTO {table} (
                        patient_last_name, patient_first_name, patient_middle_name,
                        birth_date, gender, phone, enp, attachment, series, number,
                        employee_last_name, employee_first_name, employee_middle_name,
                        position, acceptance_date, record_date, schedule_type, record_source,
                        department, creator, no_show, epmz
                    )
                    SELECT 
                        patient_last_name, patient_first_name, patient_middle_name,
                        birth_date, gender, phone, enp, attachment, series, number,
                        employee_last_name, employee_first_name, employee_middle_name,
                        position, acceptance_date, record_date, schedule_type, record_source,
                        department, creator, no_show, epmz
                    FROM tmp_journal_appeals
                    ON CONFLICT (enp, employee_last_name, acceptance_date) DO UPDATE SET
                        patient_last_name = EXCLUDED.patient_last_name,
                        patient_first_name = EXCLUDED.patient_first_name,
                        patient_middle_name = EXCLUDED.patient_middle_name,
                        birth_date = EXCLUDED.birth_date,
                        gender = EXCLUDED.gender,
                        phone = EXCLUDED.phone,
                        attachment = EXCLUDED.attachment,
                        series = EXCLUDED.series,
                        number = EXCLUDED.number,
                        employee_first_name = EXCLUDED.employee_first_name,
                        employee_middle_name = EXCLUDED.employee_middle_name,
                        position = EXCLUDED.position,
                        record_date = EXCLUDED.record_date,
                        schedule_type = EXCLUDED.schedule_type,
                        record_source = EXCLUDED.record_source,
                        department = EXCLUDED.department,
                        creator = EXCLUDED.creator,
                        no_show = EXCLUDED.no_show,
                        epmz = EXCLUDED.epmz
                    ;
                    """
                )
                log(f"Upsert завершён | {time.time() - t_upsert:.2f}s")

                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_after = cursor.fetchone()[0]
                log(f"Строк в {table} после загрузки: {count_after} (изменение={count_after - count_before})")

        self.stdout.write(self.style.SUCCESS("Загрузка обращений завершена успешно"))

