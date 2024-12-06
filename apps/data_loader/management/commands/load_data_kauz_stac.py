from django.core.management.base import BaseCommand

from apps.data_loader.management.commands.query_kauz import query_kauz_talon, query_kauz_stac
from apps.data_loader.models.oms_data import DataType, DataLoaderConfig
from apps.data_loader.data_loader import DataLoader, engine
import fdb
import pandas as pd

from datetime import datetime, timedelta

from apps.home.models import MainSettings


class Command(BaseCommand):
    help = 'Загрузка данных из базы данных Firebird (КАУЗ) в PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('--date_start', type=str, help='Начальная дата в формате ДД.ММ.ГГГГ')
        parser.add_argument('--date_end', type=str, help='Конечная дата в формате ДД.ММ.ГГГГ')
        parser.add_argument('--last-week', action='store_true', help='Загрузить данные за последнюю неделю')
        parser.add_argument('--last-month', action='store_true', help='Загрузить данные за последний месяц')
        parser.add_argument('--since-jan1', action='store_true',
                            help='Загрузить данные с 1 января текущего года по текущую дату')

    def handle(self, *args, **options):
        # Получаем настройки подключения к Firebird из MainSettings
        settings = MainSettings.objects.first()
        if not settings:
            self.stdout.write(self.style.ERROR("Настройки для подключения к КАУЗ не найдены"))
            return

        # Устанавливаем параметры подключения и даты
        dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"

        # Определяем диапазон дат
        date_start = None
        date_end = None
        if options['date_start'] and options['date_end']:
            try:
                date_start = datetime.strptime(options['date_start'], '%d.%m.%Y')
                date_end = datetime.strptime(options['date_end'], '%d.%m.%Y')
            except ValueError:
                self.stdout.write(self.style.ERROR("Неверный формат даты. Используйте ДД.ММ.ГГГГ"))
                return
        elif options['last_week']:
            date_end = datetime.now()
            date_start = date_end - timedelta(days=7)
        elif options['last_month']:
            date_end = datetime.now()
            date_start = date_end - timedelta(days=30)
        elif options['since_jan1']:
            date_start = datetime(datetime.now().year, 1, 1)
            date_end = datetime.now()
        else:
            # Если параметры не заданы, используем последние 24 часа
            date_end = datetime.now()
            date_start = date_end - timedelta(days=1)

        # Форматируем даты для SQL-запроса в формате 'ДД.ММ.ГГГГ'
        date_start_str = date_start.strftime('%d.%m.%Y')
        date_end_str = date_end.strftime('%d.%m.%Y')

        # Выполняем подключение к Firebird и загрузку данных
        try:
            try:
                con = fdb.connect(
                    dsn=dsn,
                    user=settings.kauz_user,
                    password=settings.kauz_password,
                    charset='WIN1251',  # Указание кодировки
                    port=settings.kauz_port
                )
            except Exception as e:
                return f"Ошибка подключения: {e}"

            # Выполнение запроса с подстановкой дат
            cursor = con.cursor()

            formatted_query = query_kauz_stac(date_start=date_start_str, date_end=date_end_str)
            cursor.execute(formatted_query)
            data = cursor.fetchall()

            # Преобразуем данные в DataFrame
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            con.close()

            # Получаем конфигурацию DataLoaderConfig для типа данных КАУЗ
            try:
                data_type = DataType.objects.get(name="KAUZ")
                config = DataLoaderConfig.objects.get(data_type=data_type)
            except DataType.DoesNotExist:
                self.stdout.write(self.style.ERROR('Тип данных КАУЗ не найден'))
                return
            except DataLoaderConfig.DoesNotExist:
                self.stdout.write(self.style.ERROR('Конфигурация для типа данных КАУЗ не найдена'))
                return

            # Инициализируем DataLoader и загружаем данные
            data_loader = DataLoader(
                engine=engine,
                table_name=config.table_name,
                data_type_name=data_type.name,
                column_check=config.column_check,
                columns_for_update=config.get_columns_for_update(),
                encoding=config.encoding,
                sep=config.delimiter,
                filter_column='treatment_end'
            )
            data_loader.load_data_from_db(df)  # Используем метод для загрузки из DataFrame
            self.stdout.write(self.style.SUCCESS('Загрузка данных из Firebird успешно завершена'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при подключении к Firebird или загрузке данных: {e}'))
