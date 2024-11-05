from django.core.management.base import BaseCommand

from apps.data_loader.models.oms_data import OMSSettings, DataType, DataLoaderConfig
from apps.data_loader.selenium.oms import selenium_oms
from apps.data_loader.data_loader import DataLoader, engine
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Загрузка данных в базу данных через Selenium'

    def handle(self, *args, **kwargs):
        # Получаем настройки для авторизации
        try:
            settings = OMSSettings.objects.first()
            username = settings.username
            password = settings.password
        except OMSSettings.DoesNotExist:
            self.stdout.write(self.style.ERROR('Настройки OMSSettings не найдены'))
            return
        # Получаем конфигурацию для типа данных OMS
        try:
            data_type = DataType.objects.get(name="OMS")
            config = DataLoaderConfig.objects.get(data_type=data_type)
        except DataType.DoesNotExist:
            self.stdout.write(self.style.ERROR('Тип данных OMS не найден'))
            return
        except DataLoaderConfig.DoesNotExist:
            self.stdout.write(self.style.ERROR('Конфигурация для типа данных OMS не найдена'))
            return
        # Устанавливаем даты
        today = datetime.now()
        start_date = (today - timedelta(days=1)).strftime('%d-%m-%y')  # Вчерашняя дата в формате дд-мм-гг
        end_date = (today - timedelta(days=1)).strftime('%d-%m-%y')  # Вчерашняя дата в формате дд-мм-гг
        start_date_treatment = f'01-01-{today.strftime("%y")}'  # 1 января текущего года в формате дд-мм-гг

        # Запускаем Selenium для скачивания CSV файла
        success, file_path = selenium_oms(username, password, start_date, end_date, start_date_treatment)

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
