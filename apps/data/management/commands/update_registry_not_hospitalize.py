import requests
from django.core.management.base import BaseCommand
from apps.home.models import MainSettings
from apps.data.models.registry.nothospitalized import PatientRegistry


class Command(BaseCommand):
    help = 'Обновляет данные в PatientRegistry из API'

    def handle(self, *args, **kwargs):
        try:
            # Получаем URL API из MainSettings
            settings = MainSettings.objects.first()
            if not settings or not settings.api_update_registry_not_hospitalize_url:
                self.stdout.write(self.style.ERROR("URL API не настроен в MainSettings"))
                return

            api_url = settings.api_update_registry_not_hospitalize_url

            # Проверка доступности API
            try:
                response = requests.get(api_url, timeout=10, proxies={"http": None, "https": None})
                response.raise_for_status()
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при обращении к API: {e}"))
                return

            # Проверка наличия данных
            data = response.json()
            if not data:
                self.stdout.write(self.style.ERROR("API не вернул данных"))
                return

            # Удаляем существующие записи, которые совпадают по ключам, и добавляем новые
            updated_count = 0
            added_count = 0
            for item in data:
                obj, created = PatientRegistry.objects.update_or_create(
                    number=item['number'],  # Основной ключ для сверки
                    defaults={
                        'full_name': item['full_name'],
                        'date_of_birth': item['date_of_birth'],
                        'address': item['address'],
                        'phone': item['phone'],
                        'medical_organization': item['medical_organization'],
                        'hospital_name': item['hospital_name'],
                        'admission_date': item['admission_date'],
                        'referral_method': item['referral_method'],
                        'admission_diagnosis': item['admission_diagnosis'],
                        'refusal_date': item['refusal_date'],
                        'refusal_reason': item['refusal_reason']
                    }
                )
                if created:
                    added_count += 1
                else:
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Данные успешно обновлены: добавлено {added_count}, обновлено {updated_count} записей."
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
