from django.core.management.base import BaseCommand

from apps.data_loader.management.commands.query_kauz import query_kauz_talon, query_kauz_doctors
from apps.data_loader.models.oms_data import DataType, DataLoaderConfig
from apps.data_loader.data_loader import DataLoader, engine
import fdb
import pandas as pd

from datetime import datetime, timedelta

from apps.home.models import MainSettings


class Command(BaseCommand):
    help = 'Загрузка данных из базы данных Firebird (КАУЗ) в PostgreSQL'

    def handle(self, *args, **kwargs):
        # Получаем настройки подключения к Firebird из MainSettings
        settings = MainSettings.objects.first()
        if not settings:
            self.stdout.write(self.style.ERROR("Настройки для подключения к КАУЗ не найдены"))
            return

        # Устанавливаем параметры подключения и даты
        dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"
        # date_start = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        # date_end = datetime.now().strftime('%Y-%m-%d')

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

            # Выполнение запроса
            cursor = con.cursor()
            cursor.execute(query_kauz_doctors)
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
                sep=config.delimiter
            )
            data_loader.load_data_from_db(df)  # Используем метод для загрузки из DataFrame
            self.stdout.write(self.style.SUCCESS('Загрузка данных из Firebird успешно завершена'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при подключении к Firebird или загрузке данных: {e}'))
