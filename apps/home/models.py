from django.db import models


class MainSettings(models.Model):
    dash_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_port = models.PositiveIntegerField(default=5000)
    main_app_ip = models.GenericIPAddressField(default='127.0.0.1')
    main_app_port = models.PositiveIntegerField(default=8000)
    dash_chief_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_chief_port = models.PositiveIntegerField(default=5010)
    kauz_server_ip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="КАУЗ: IP сервера")
    kauz_database_path = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Путь к базе данных")
    kauz_port = models.PositiveIntegerField(default=3050, verbose_name="КАУЗ: Порт")
    kauz_user = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Пользователь")
    kauz_password = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Пароль")
    api_panel_patients_url = models.URLField(
        max_length=500,
        default='http://10.37.170.101:8000/peopledash/api/registered_patients/',
        verbose_name="URL для обновления панели пациентов"
    )
    api_update_registry_not_hospitalize_url = models.URLField(
        max_length=500,
        default='http://10.37.170.101:8000/api/patient_registry/',
        verbose_name="URL для обновления реестра не госпитализированных пациентов"
    )
    # Поля для Dagster
    dagster_ip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="Dagster IP")
    dagster_port = models.PositiveIntegerField(default=3000, verbose_name="Dagster Port")

    def get_dash_url(self):
        return f"http://{self.dash_ip}:{self.dash_port}"

    def get_dash_chief_url(self):
        return f"http://{self.dash_chief_ip}:{self.dash_chief_port}"

    def get_dagster_url(self):
        return f"http://{self.dagster_ip}:{self.dagster_port}"

    def __str__(self):
        return (f"Аналитическая система - {self.dash_ip}:{self.dash_port}, "
                f"Основное приложение - {self.main_app_ip}:{self.main_app_port}, "
                f"Панель главного врача - {self.dash_chief_ip}:{self.dash_chief_port}, "
                f"Dagster - {self.dagster_ip}:{self.dagster_port}")

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"
