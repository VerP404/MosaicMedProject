from django.core.management.base import BaseCommand

from apps.data_loader.models.iszl import ISZLSettings
from apps.data_loader.models.oms_data import OMSSettings, DataType, DataLoaderConfig
from apps.data_loader.selenium.iszl_people import selenium_iszl_people
from apps.data_loader.selenium.iszl_people_chrome import selenium_iszl_people_chrome
from apps.data_loader.selenium.oms import selenium_oms
from apps.data_loader.data_loader import DataLoader, engine
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Загрузка данных населения из ИСЗЛ в базу данных через Selenium'

    def handle(self, *args, **kwargs):
        # Получаем настройки для авторизации
        try:
            settings = ISZLSettings.objects.first()
            username = settings.user_people
            password = settings.password_people
        except OMSSettings.DoesNotExist:
            self.stdout.write(self.style.ERROR('Настройки ISZLSettings не найдены'))
            return
        try:
            data_type = DataType.objects.get(name="people")
            config = DataLoaderConfig.objects.get(data_type=data_type)
        except DataType.DoesNotExist:
            self.stdout.write(self.style.ERROR('Тип данных people не найден'))
            return
        except DataLoaderConfig.DoesNotExist:
            self.stdout.write(self.style.ERROR('Конфигурация для типа данных people не найдена'))
            return

        # Запускаем Selenium для скачивания CSV файла
        success, file_path = selenium_iszl_people(username, password)

        if not success:
            self.stdout.write(self.style.ERROR('Ошибка при загрузке файла через Selenium'))
            return

        # Инициализируем DataLoader и загружаем данные в базу
        data_loader = DataLoader(
            engine=engine,
            table_name=config.table_name,
            data_type_name=data_type.name,
            column_check=config.column_check,
            columns_for_update=config.get_columns_for_update(),
            encoding=config.encoding,
            sep=config.delimiter
        )

        try:
            data_loader.load_data(file_path)
            self.stdout.write(self.style.SUCCESS('Загрузка данных успешно завершена'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке данных: {e}'))
