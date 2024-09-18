import os
from celery import Celery

# Устанавливаем правильный модуль настроек Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('MosaicMedProject')

# Используем настройки из Django
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.result_backend = 'redis://localhost:6379/0'
# Автоматически обнаруживаем задачи в приложениях
app.autodiscover_tasks()
