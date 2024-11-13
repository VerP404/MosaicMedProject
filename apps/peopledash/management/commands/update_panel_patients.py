# update_registered_patients.py
from datetime import datetime

import requests
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

            # Запрос к API для получения данных
            response = requests.get(api_url)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR("Ошибка при получении данных с API"))
                return

            data = response.json()

            # Получаем текущее время запуска команды
            current_datetime = datetime.now().strftime('%H:%M %d.%m.%Y')

            # Удаляем старые данные
            RegisteredPatients.objects.all().delete()

            # Сохраняем новые данные
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
