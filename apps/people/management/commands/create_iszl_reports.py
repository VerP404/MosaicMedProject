from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection

from apps.data_loader.models.iszl import ISZLPeople
from apps.people.models import ISZLPeopleReport, People, ISZLReportSummary


class Command(BaseCommand):
    help = "Создает отчет по населению из ИСЗЛ с использованием временной таблицы"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(self.style.NOTICE(f"Начало создания отчета по населению на {today}"))

        with connection.cursor() as cursor:
            # 1. Создание временной таблицы
            cursor.execute("""
                CREATE TEMP TABLE temp_iszl_people AS
                SELECT * FROM data_loader_iszlpeople;
            """)

            # 2. Удаление старых отчетов за сегодня
            cursor.execute("DELETE FROM people_iszlpeoplereport WHERE date_report = %s;", [today])

            # 3. Вставка данных в основную таблицу отчетов
            cursor.execute("""
                INSERT INTO people_iszlpeoplereport (date_report, people_id, smo, ss_doctor, lpuuch)
                SELECT %s, p.id, t.smo, t.ss_doctor, t.lpuuch
                FROM temp_iszl_people t
                JOIN people_people p ON p.enp = t.enp;
            """, [today])

            # 4. Подсчет общего количества пациентов
            cursor.execute("""
                SELECT COUNT(*) 
                FROM people_iszlpeoplereport 
                WHERE date_report = %s;
            """, [today])
            patient_count = cursor.fetchone()[0]

            # 5. Определение изменений по сравнению с предыдущим отчетом
            cursor.execute("""
                SELECT patient_count 
                FROM people_iszlreportsummary 
                ORDER BY date_report DESC 
                LIMIT 1;
            """)
            previous_count = cursor.fetchone()[0] if cursor.rowcount > 0 else 0
            change = patient_count - previous_count

            # 6. Сохранение итогового отчета
            cursor.execute("""
                INSERT INTO people_iszlreportsummary (date_report, patient_count, change)
                VALUES (%s, %s, %s)
                ON CONFLICT (date_report)
                DO UPDATE SET patient_count = EXCLUDED.patient_count, change = EXCLUDED.change;
            """, [today, patient_count, change])

        self.stdout.write(self.style.SUCCESS(f"Отчет по населению на {today} создан с {patient_count} пациентами."))
