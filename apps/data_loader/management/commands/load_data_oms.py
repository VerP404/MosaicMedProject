from django.core.management.base import BaseCommand
from apps.data_loader.models.oms_data import OMSSettings, DataType, DataLoaderConfig
from apps.data_loader.data_loader import SeleniumDataLoader, engine
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Загрузка данных в базу данных через Selenium'

    def add_arguments(self, parser):
        parser.add_argument('--start_date', type=str, help='Начальная дата в формате дд-мм-гг')
        parser.add_argument('--end_date', type=str, help='Конечная дата в формате дд-мм-гг')
        parser.add_argument('--start_date_treatment', type=str, help='Дата начала лечения в формате дд-мм-гг')
        parser.add_argument('--browser', type=str, choices=['firefox', 'chrome'], default='firefox',
                            help='Браузер для запуска Selenium')

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
        start_date = kwargs.get('start_date') or (today - timedelta(days=1)).strftime('%d-%m-%y')
        end_date = kwargs.get('end_date') or (today - timedelta(days=1)).strftime('%d-%m-%y')
        start_date_treatment = kwargs.get('start_date_treatment') or f'01-01-{today.strftime("%y")}'

        # Проверяем формат дат
        try:
            datetime.strptime(start_date, '%d-%m-%y')
            datetime.strptime(end_date, '%d-%m-%y')
            datetime.strptime(start_date_treatment, '%d-%m-%y')
        except ValueError:
            self.stdout.write(self.style.ERROR("Неверный формат даты. Используйте дд-мм-гг"))
            return

        browser = kwargs.get('browser', 'firefox')

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
            "Врач (Профиль МП)": "doctor_profile",
            "Специальность": "specialty",
            "Подразделение": "department",
            "Посещения": "visits",
            "Посещения в МО": "mo_visits",
            "Посещения на Дому": "home_visits",
            "Случай": "case_code",
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
            browser=browser,
        )

        try:
            selenium_loader.run_etl("ignored_source_name")
            self.stdout.write(self.style.SUCCESS('Загрузка данных успешно завершена'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке данных: {e}'))
