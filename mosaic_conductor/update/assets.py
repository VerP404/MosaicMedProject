import os
# Указываем модуль настроек вашего Django проекта. Замените 'mosaic_med_project.settings' на актуальное имя.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

import datetime
import dagster as dg
from dagster import op, job, schedule

@op
def update_appeal_statuses_op(context):
    # Импорт модели после инициализации Django
    from apps.journal.models import Appeal
    updated_count = 0
    appeals = Appeal.objects.all()
    for appeal in appeals:
        old_status = appeal.status
        new_status = appeal.compute_status()
        if new_status != old_status:
            appeal.status = new_status
            appeal.save(update_fields=['status'])
            updated_count += 1
    context.log.info(f"Обновлено статусов: {updated_count}")
    return updated_count

@job
def update_status_job():
    update_appeal_statuses_op()

@schedule(cron_schedule="0 3 * * *", job=update_status_job, execution_timezone="Europe/Moscow")
def daily_status_update_schedule(_context):
    return {}

# Определения для Dagster, включающие job и schedule
defs = dg.Definitions(
    jobs=[update_status_job],
    schedules=[daily_status_update_schedule],
)
