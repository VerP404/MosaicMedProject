from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.data_loader.models.iszl import ISZLPeople
from apps.people.models import ISZLPeopleReport, People, ISZLReportSummary


class Command(BaseCommand):
    help = "Создает отчет по населению из ИСЗЛ"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(self.style.NOTICE(f"Начало создания отчета по населению на {today}"))
        # Удаляем данные за сегодняшнюю дату, если они уже существуют
        ISZLPeopleReport.objects.filter(date_report=today).delete()

        for person in ISZLPeople.objects.all():
            # Проверяем, есть ли пациент с данным ENP в People
            patient, created = People.objects.get_or_create(
                enp=person.enp,
                defaults={'fio': person.fio, 'dr': person.dr}
            )

            # Создаем снимок состояния
            ISZLPeopleReport.objects.create(
                date_report=today,
                people=patient,
                smo=person.smo,
                ss_doctor=person.ss_doctor,
                lpuuch=person.lpuuch,
            )

        # Подсчитываем общее количество пациентов
        patient_count = ISZLPeopleReport.objects.filter(date_report=today).count()

        # Определяем изменение по сравнению с предыдущим отчетом
        previous_report = ISZLReportSummary.objects.order_by('-date_report').first()
        previous_count = previous_report.patient_count if previous_report else 0
        change = patient_count - previous_count

        # Создаем или обновляем запись в ISZLReportSummary
        ISZLReportSummary.objects.update_or_create(
            date_report=today,
            defaults={'patient_count': patient_count, 'change': change}
        )
        self.stdout.write(self.style.SUCCESS(f"Отчет по населению на {today} сохранен с {patient_count} пациентами"))
