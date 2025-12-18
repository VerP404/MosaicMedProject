"""
Management команда для загрузки адресов из CSV файла.
"""
import csv
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.zones.models import Address


class Command(BaseCommand):
    help = 'Загружает адреса из CSV файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='apps/zones/data/address.csv',
            help='Путь к CSV файлу с адресами (по умолчанию: apps/zones/data/address.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие адреса перед загрузкой'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            help='Пропускать дубликаты (по умолчанию обновлять существующие)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        skip_duplicates = options['skip_duplicates']

        # Определяем абсолютный путь к файлу
        if not os.path.isabs(file_path):
            base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            file_path = base_dir / file_path
        else:
            file_path = Path(file_path)

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Файл не найден: {file_path}')
            )
            return

        self.stdout.write(f'Загрузка адресов из файла: {file_path}')

        # Очистка существующих адресов
        if clear_existing:
            count = Address.objects.count()
            Address.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Удалено {count} существующих адресов')
            )

        # Чтение и загрузка CSV
        loaded = 0
        updated = 0
        skipped = 0
        errors = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Проверяем наличие необходимых колонок
                required_columns = ['osm_id', 'osm_type', 'latitude', 'longitude']
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                if missing_columns:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}'
                        )
                    )
                    return

                batch = []
                batch_size = 1000

                for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, т.к. первая строка - заголовок
                    try:
                        # Парсим osm_id (формат: "type/id")
                        osm_id_full = row.get('osm_id', '').strip()
                        if not osm_id_full:
                            skipped += 1
                            continue

                        # Извлекаем тип и ID из osm_id
                        if '/' in osm_id_full:
                            parts = osm_id_full.split('/', 1)
                            osm_type_from_id = parts[0]
                            osm_id = parts[1]
                        else:
                            osm_type_from_id = row.get('osm_type', '').strip()
                            osm_id = osm_id_full

                        # Используем osm_type из колонки, если есть, иначе из osm_id
                        osm_type = row.get('osm_type', '').strip() or osm_type_from_id

                        # Парсим координаты
                        try:
                            latitude = float(row.get('latitude', 0))
                            longitude = float(row.get('longitude', 0))
                        except (ValueError, TypeError):
                            skipped += 1
                            continue

                        # Получаем остальные поля
                        housenumber = row.get('housenumber', '').strip()
                        street = row.get('street', '').strip()
                        city = row.get('city', '').strip()
                        postcode = row.get('postcode', '').strip()

                        # Создаем или обновляем адрес
                        address_data = {
                            'osm_id': osm_id,
                            'osm_type': osm_type,
                            'latitude': latitude,
                            'longitude': longitude,
                            'housenumber': housenumber,
                            'street': street,
                            'city': city,
                            'postcode': postcode,
                            'source': 'csv_import',
                        }

                        if skip_duplicates:
                            # Пропускаем если уже существует
                            if Address.objects.filter(
                                osm_type=osm_type,
                                osm_id=osm_id
                            ).exists():
                                skipped += 1
                                continue
                            # Создаем новый
                            Address.objects.create(**address_data)
                            loaded += 1
                        else:
                            # Обновляем или создаем
                            address, created = Address.objects.update_or_create(
                                osm_type=osm_type,
                                osm_id=osm_id,
                                defaults=address_data
                            )
                            if created:
                                loaded += 1
                            else:
                                updated += 1

                        # Пакетная обработка для производительности
                        if (loaded + updated) % batch_size == 0:
                            self.stdout.write(
                                f'Обработано: {loaded + updated} адресов...'
                            )

                    except Exception as e:
                        errors += 1
                        if errors <= 10:  # Показываем только первые 10 ошибок
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Ошибка в строке {row_num}: {str(e)}'
                                )
                            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nЗагрузка завершена:\n'
                    f'  Загружено новых: {loaded}\n'
                    f'  Обновлено: {updated}\n'
                    f'  Пропущено: {skipped}\n'
                    f'  Ошибок: {errors}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Критическая ошибка при загрузке: {str(e)}')
            )
            raise
