from django.core.management.base import BaseCommand
from django.db import transaction, connection
import logging

from apps.data.models import OMS
from apps.data.query import base_query_oms

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Загрузка данных из OMSData в OMS с проверкой уникальности по talon и source'

    def handle(self, *args, **kwargs):
        self.stdout.write("Начинается загрузка данных из OMSData в OMS...")

        query = base_query_oms()

        with transaction.atomic():
            try:
                with connection.cursor() as cursor:
                    # Выполняем запрос
                    cursor.execute(query)
                    rows = cursor.fetchall()

                logger.info(f"Количество строк, возвращённых запросом: {len(rows)}")

                if len(rows) == 0:
                    self.stdout.write(self.style.WARNING("Запрос не вернул данных."))
                    return

                # Лог структуры данных первой строки
                logger.info(f"Пример строки данных: {rows[0]}")

                # Проверяем количество полей в строке
                expected_columns = 36  # Убедитесь, что это соответствует вашему запросу
                if len(rows[0]) != expected_columns:
                    raise ValueError(
                        f"Ожидалось {expected_columns} полей, но получено {len(rows[0])}. Проверьте запрос."
                    )

                # Словарь для существующих записей
                unique_keys = [(row[0], row[1]) for row in rows]  # (talon, source)
                existing_records = {
                    (record.talon, record.source): record
                    for record in OMS.objects.filter(
                        talon__in=[key[0] for key in unique_keys],
                        source__in=[key[1] for key in unique_keys]
                    )
                }

                new_records = []
                updated_records = []
                skipped_count = 0

                for row in rows:
                    try:
                        # Лог строки для диагностики
                        # logger.debug(f"Обрабатывается строка: {row}")

                        if len(row) < expected_columns:
                            # logger.error(f"Некорректное количество полей в строке: {len(row)}. Пропуск.")
                            continue

                        oms_data = {
                            "talon": row[0],
                            "source": row[1],
                            "report_month": row[2],
                            "report_month_number": row[3],
                            "report_year": row[4],
                            "status": row[5],
                            "goal": row[6],
                            "target_categories": row[7],
                            "patient": row[8],
                            "birth_date": row[9],
                            "age": row[10],
                            "gender": row[11],
                            "enp": row[12],
                            "smo_code": row[13],
                            "inogorodniy": row[14],
                            "treatment_start": row[15],
                            "treatment_end": row[16],
                            "visits": row[17],
                            "mo_visits": row[18],
                            "home_visits": row[19],
                            "main_diagnosis_code": row[20],
                            "additional_diagnosis_codes": row[21],
                            "initial_input_date": row[22],
                            "last_change_date": row[23],
                            "amount_numeric": row[24],
                            "sanctions": row[25],
                            "ksg": row[26],
                            "department_id": row[27],
                            "department": row[28],
                            "building_id": row[29],
                            "building": row[30],
                            "doctor_code": row[31],
                            "doctor_id": row[32],
                            "doctor": row[33],
                            "specialty": row[34],
                            "profile": row[35],
                            "profile_id": row[36],
                        }

                        key = (oms_data['talon'], oms_data['source'])

                        # Проверка существующей записи
                        if key in existing_records:
                            existing_record = existing_records[key]
                            if not existing_record.is_update:
                                skipped_count += 1
                                continue

                            # Проверка на изменения
                            changes_detected = False
                            for field, value in oms_data.items():
                                if getattr(existing_record, field) != value:
                                    changes_detected = True
                                    break

                            if changes_detected:
                                for field, value in oms_data.items():
                                    setattr(existing_record, field, value)
                                updated_records.append(existing_record)
                            else:
                                skipped_count += 1
                        else:
                            # Добавление новых записей
                            new_records.append(OMS(**oms_data))

                    except Exception as e:
                        continue

                # Массовое обновление и вставка
                if new_records:
                    OMS.objects.bulk_create(new_records, batch_size=1000)
                if updated_records:
                    OMS.objects.bulk_update(updated_records, fields=oms_data.keys(), batch_size=1000)

                self.stdout.write(self.style.SUCCESS(
                    f"Загрузка завершена: добавлено {len(new_records)}, обновлено {len(updated_records)}, пропущено {skipped_count}."
                ))
            except Exception as e:
                logger.error(f"Ошибка при выполнении команды: {e}")
                self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
