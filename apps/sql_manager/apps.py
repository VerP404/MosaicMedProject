from django.apps import AppConfig


class SqlManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sql_manager'
    verbose_name = 'Менеджер запросов'
