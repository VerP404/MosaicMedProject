"""
Management команда для загрузки данных ГАР (Государственный адресный реестр)
Использует утилиту ru_address для конвертации XML в SQL/CSV
Фильтрует данные по региону 36 (Воронежская область) для уменьшения объема
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from apps.gar.models import GarLoadHistory, GarAddress


class Command(BaseCommand):
    help = 'Загружает данные ГАР для указанного региона (по умолчанию 36 - Воронежская область)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            default='36',
            help='Код региона для загрузки (по умолчанию 36 - Воронежская область)'
        )
        parser.add_argument(
            '--source-path',
            type=str,
            required=True,
            help='Путь к распакованным файлам ГАР (XML и XSD схемы)'
        )
        parser.add_argument(
            '--schema-path',
            type=str,
            help='Путь к XSD схеме (если отличается от source-path)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['psql', 'mysql', 'csv', 'tsv'],
            default='psql',
            help='Формат выходных данных (по умолчанию psql для PostgreSQL)'
        )
        parser.add_argument(
            '--mode',
            type=str,
            choices=['direct', 'per_region', 'per_table', 'region_tree'],
            default='per_region',
            help='Режим вывода данных (по умолчанию per_region - один файл на регион)'
        )
        parser.add_argument(
            '--skip-conversion',
            action='store_true',
            help='Пропустить конвертацию, использовать уже существующие файлы'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Директория для сохранения конвертированных файлов (по умолчанию временная)'
        )

    def handle(self, *args, **options):
        region_code = options['region']
        source_path = options['source_path']
        schema_path = options.get('schema_path') or source_path
        output_format = options['format']
        mode = options['mode']
        skip_conversion = options['skip_conversion']
        output_dir = options.get('output_dir')

        self.stdout.write(self.style.SUCCESS(f'Начало загрузки данных ГАР для региона {region_code}'))

        # Создаем запись в истории загрузок
        load_history = GarLoadHistory.objects.create(
            region_code=region_code,
            status='processing',
            source_file=source_path
        )

        try:
            # Проверяем наличие ru_address
            if not self.check_ru_address():
                raise Exception('Утилита ru_address не найдена. Установите её: pip install ru-address')

            # Создаем временную директорию для выходных файлов
            if not output_dir:
                temp_dir = tempfile.mkdtemp(prefix='gar_')
                output_dir = temp_dir
                cleanup_temp = True
            else:
                os.makedirs(output_dir, exist_ok=True)
                cleanup_temp = False

            try:
                # Шаг 1: Конвертация схемы
                if not skip_conversion:
                    self.stdout.write('Конвертация XSD схемы...')
                    schema_output = os.path.join(output_dir, 'schema.sql')
                    self.convert_schema(source_path, schema_output, output_format)
                    self.stdout.write(self.style.SUCCESS(f'Схема сохранена в {schema_output}'))

                # Шаг 2: Конвертация данных
                if not skip_conversion:
                    self.stdout.write(f'Конвертация XML данных для региона {region_code}...')
                    self.convert_data(
                        source_path,
                        output_dir,
                        schema_path,
                        region_code,
                        output_format,
                        mode
                    )
                    self.stdout.write(self.style.SUCCESS('Конвертация данных завершена'))

                # Шаг 3: Импорт данных в БД
                self.stdout.write('Импорт данных в базу данных...')
                records_loaded = self.import_data(output_dir, region_code, output_format)

                load_history.status = 'completed'
                load_history.records_loaded = records_loaded
                load_history.completed_at = self.get_current_time()
                load_history.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Загрузка завершена успешно. Загружено записей: {records_loaded}'
                    )
                )

            finally:
                # Очистка временных файлов
                if cleanup_temp and os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
                    self.stdout.write('Временные файлы удалены')

        except Exception as e:
            load_history.status = 'failed'
            load_history.error_message = str(e)
            load_history.completed_at = self.get_current_time()
            load_history.save()

            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке: {e}'))
            raise

    def check_ru_address(self):
        """Проверяет наличие утилиты ru_address"""
        try:
            result = subprocess.run(
                ['ru_address', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Пробуем через python -m
            try:
                result = subprocess.run(
                    ['python', '-m', 'ru_address.command', '--help'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

    def convert_schema(self, source_path, output_path, target_format):
        """Конвертирует XSD схему в SQL"""
        cmd = [
            'python', '-m', 'ru_address.command', 'schema',
            '--target', target_format,
            source_path,
            output_path
        ]

        self.stdout.write(f'Выполняется команда: {" ".join(cmd)}')
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 час на конвертацию схемы
        )

        if result.returncode != 0:
            raise Exception(f'Ошибка конвертации схемы: {result.stderr}')

    def convert_data(self, source_path, output_dir, schema_path, region_code, target_format, mode):
        """Конвертирует XML данные в указанный формат"""
        cmd = [
            'python', '-m', 'ru_address.command', 'dump',
            '--target', target_format,
            '--region', region_code,
            '--mode', mode,
            source_path,
            output_dir,
            schema_path
        ]

        self.stdout.write(f'Выполняется команда: {" ".join(cmd)}')
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 часа на конвертацию данных
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            raise Exception(f'Ошибка конвертации данных: {error_msg}')

        # Выводим информацию о процессе
        if result.stdout:
            self.stdout.write(result.stdout)

    def import_data(self, output_dir, region_code, output_format):
        """Импортирует данные в базу данных"""
        records_loaded = 0

        if output_format in ['psql', 'mysql']:
            # Импорт SQL файлов
            sql_files = list(Path(output_dir).glob('*.sql'))
            for sql_file in sql_files:
                self.stdout.write(f'Импорт файла: {sql_file.name}')
                records = self.import_sql_file(sql_file)
                records_loaded += records

        elif output_format in ['csv', 'tsv']:
            # Импорт CSV/TSV файлов
            pattern = '*.csv' if output_format == 'csv' else '*.tsv'
            data_files = list(Path(output_dir).glob(pattern))
            for data_file in data_files:
                self.stdout.write(f'Импорт файла: {data_file.name}')
                records = self.import_csv_file(data_file, output_format)
                records_loaded += records

        return records_loaded

    def import_sql_file(self, sql_file):
        """Импортирует SQL файл в базу данных"""
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Разделяем на отдельные команды
        # Простая обработка - в реальности может потребоваться более сложная логика
        with connection.cursor() as cursor:
            try:
                # Выполняем SQL команды
                cursor.execute(sql_content)
                return cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Ошибка при импорте SQL: {e}'))
                # Пробуем выполнить построчно
                return self.import_sql_line_by_line(sql_content)

    def import_sql_line_by_line(self, sql_content):
        """Импортирует SQL построчно"""
        records = 0
        statements = sql_content.split(';')
        
        with connection.cursor() as cursor:
            for statement in statements:
                statement = statement.strip()
                if not statement or statement.startswith('--'):
                    continue
                try:
                    cursor.execute(statement)
                    if hasattr(cursor, 'rowcount'):
                        records += cursor.rowcount
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Пропущена команда: {e}'))
                    continue

        return records

    def import_csv_file(self, csv_file, file_format):
        """Импортирует CSV/TSV файл в базу данных"""
        import pandas as pd
        from apps.gar.utils import parse_gar_address
        from django.db import transaction

        delimiter = ',' if file_format == 'csv' else '\t'
        
        try:
            # Читаем файл порциями для экономии памяти
            chunk_size = 10000
            records = 0
            errors = 0
            
            self.stdout.write(f'Чтение файла {csv_file.name}...')
            
            for chunk_num, df_chunk in enumerate(pd.read_csv(
                csv_file,
                delimiter=delimiter,
                encoding='utf-8',
                low_memory=False,
                chunksize=chunk_size
            )):
                self.stdout.write(f'Обработка блока {chunk_num + 1} ({len(df_chunk)} записей)...')
                
                addresses_to_create = []
                
                for _, row in df_chunk.iterrows():
                    try:
                        # Преобразуем строку в словарь
                        row_dict = row.to_dict()
                        
                        # Парсим адрес
                        address_data = parse_gar_address(row_dict, csv_file.stem)
                        
                        if address_data and address_data.get('gar_object_id'):
                            # Проверяем, не существует ли уже такой адрес
                            if not GarAddress.objects.filter(
                                gar_object_id=address_data['gar_object_id']
                            ).exists():
                                addresses_to_create.append(
                                    GarAddress(**address_data)
                                )
                    except Exception as e:
                        errors += 1
                        if errors <= 10:  # Показываем только первые 10 ошибок
                            self.stdout.write(
                                self.style.WARNING(f'Ошибка при парсинге строки: {e}')
                            )
                        continue
                
                # Массовая вставка
                if addresses_to_create:
                    with transaction.atomic():
                        GarAddress.objects.bulk_create(
                            addresses_to_create,
                            ignore_conflicts=True,
                            batch_size=1000
                        )
                    records += len(addresses_to_create)
                    self.stdout.write(f'Загружено {len(addresses_to_create)} записей из блока {chunk_num + 1}')
            
            if errors > 10:
                self.stdout.write(
                    self.style.WARNING(f'Всего ошибок при обработке: {errors}')
                )
            
            return records
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при чтении файла {csv_file}: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            return 0

    def get_current_time(self):
        """Возвращает текущее время для Django"""
        from django.utils import timezone
        return timezone.now()

