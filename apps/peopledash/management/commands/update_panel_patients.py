# update_panel_patients.py
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from apps.home.models import MainSettings
from apps.peopledash.models import RegisteredPatients


class Command(BaseCommand):
    help = 'Обновляет данные в RegisteredPatients из API'

    def handle(self, *args, **kwargs):
        try:
            # Получаем URL API из MainSettings
            settings = MainSettings.objects.first()
            if not settings or not settings.api_panel_patients_url:
                self.stdout.write(self.style.ERROR("URL API не настроен в MainSettings"))
                return

            api_url = settings.api_panel_patients_url

            # 1. Проверка доступности API
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при обращении к API: {e}"))
                return

            # 2. Проверка наличия данных и соответствия полей
            data = response.json()
            if not data:
                self.stdout.write(self.style.ERROR("API не вернул данных"))
                return

            required_fields = {'organization', 'subdivision', 'speciality', 'slots_today',
                               'free_slots_today', 'slots_14_days', 'free_slots_14_days', 'report_datetime'}
            for item in data:
                if not required_fields.issubset(item.keys()):
                    self.stdout.write(self.style.ERROR("API не содержит всех необходимых полей"))
                    return

            # 3. Проверка актуальности report_datetime
            api_report_datetime = max(item['report_datetime'] for item in data)
            latest_local_record = RegisteredPatients.objects.order_by('-report_datetime').first()
            local_report_datetime = latest_local_record.report_datetime if latest_local_record else None

            if local_report_datetime and datetime.strptime(api_report_datetime, '%H:%M %d.%m.%Y') <= datetime.strptime(
                    local_report_datetime, '%H:%M %d.%m.%Y'):
                self.stdout.write(self.style.WARNING("Данные в API не новее локальных"))
                return

            # Удаляем старые данные
            RegisteredPatients.objects.all().delete()

            # Сохраняем новые данные с текущим временем вместо времени из API
            current_datetime = datetime.now().strftime('%H:%M %d.%m.%Y')
            for item in data:
                RegisteredPatients.objects.create(
                    organization=item['organization'],
                    subdivision=item['subdivision'],
                    speciality=item['speciality'],
                    slots_today=item['slots_today'],
                    free_slots_today=item['free_slots_today'],
                    slots_14_days=item['slots_14_days'],
                    free_slots_14_days=item['free_slots_14_days'],
                    report_datetime=current_datetime
                )

            self.stdout.write(self.style.SUCCESS("Данные успешно обновлены из API"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
