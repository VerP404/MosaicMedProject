from django.apps import AppConfig


class DataLoaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.data_loader'
    verbose_name = 'Загрузка данных'
