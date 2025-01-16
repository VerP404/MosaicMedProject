from django.core.management.base import BaseCommand

from apps.data_loader.models.oms_data import OMSSettings, DataType, DataLoaderConfig
from apps.data_loader.data_loader import SeleniumDataLoader, engine
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

        column_mapping = {
            "Талон": "talon",
            "Источник": "source",
            "Статус": "status",
            "Цель": "goal",
            "Пациент": "patient",
            "Дата рождения": "birth_date",
            "Пол": "gender",
            "Код СМО": "smo_code",
            "ЕНП": "enp",
            "Начало лечения": "treatment_start",
            "Окончание лечения": "treatment_end",
            "Врач": "doctor",
            "Посещения": "visits",
            "Посещения в МО": "mo_visits",
            "Посещения на Дому": "home_visits",
            "Диагноз основной (DS1)": "main_diagnosis",
            "Сопутствующий диагноз (DS2)": "additional_diagnosis",
            "Первоначальная дата ввода": "initial_input_date",
            "Дата последнего изменения": "last_change_date",
            "Сумма": "amount",
            "Санкции": "sanctions",
            "КСГ": "ksg",
            "Отчетный период выгрузки": "report_period",
        }
        # Инициализируем DataLoader и загружаем данные в базу
        selenium_loader = SeleniumDataLoader(
            engine=engine,
            table_name="data_loader_omsdata",
            table_name_temp=f"temp_data_loader_omsdata",
            data_type_name="OMS",
            column_mapping=column_mapping,
            column_check='patient',
            columns_for_update=["talon", "source"],
            username=username,
            password=password,
            start_date=start_date,
            end_date=end_date,
            start_date_treatment=start_date_treatment,
            file_format='csv',
            dtype=str,
            encoding='utf-8',
            sep=';',
        )

        try:
            selenium_loader.run_etl("ignored_source_name")
            self.stdout.write(self.style.SUCCESS('Загрузка данных успешно завершена'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке данных: {e}'))
