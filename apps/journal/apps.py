from django.apps import AppConfig


class JournalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.journal'
    verbose_name = 'Обращения граждан'
