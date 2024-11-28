from django.apps import AppConfig


class OmsReferenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.oms_reference'
    verbose_name = 'Справочники ТФОМС'

    def ready(self):
        import apps.oms_reference.signals  # Подключение сигналов
