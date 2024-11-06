from django.db import models


class MainSettings(models.Model):
    dash_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_port = models.PositiveIntegerField(default='5000')
    main_app_ip = models.GenericIPAddressField(default='127.0.0.1')
    main_app_port = models.PositiveIntegerField(default='8000')
    dash_chief_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_chief_port = models.PositiveIntegerField(default='5010')
    kauz_server_ip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="КАУЗ: IP сервера")
    kauz_database_path = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Путь к базе данных")
    kauz_port = models.PositiveIntegerField(default='3050', verbose_name="КАУЗ: Порт")
    kauz_user = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Пользователь")
    kauz_password = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Пароль")

    def get_dash_url(self):
        return f"http://{self.dash_ip}:{self.dash_port}"

    def get_dash_chief_url(self):
        return f"http://{self.dash_chief_ip}:{self.dash_chief_port}"

    def __str__(self):
        return (f"Аналитическая система - {self.dash_ip}:{self.dash_port}, "
                f"Основное приложение - {self.main_app_ip}:{self.main_app_port}, "
                f"Панель главного врача - {self.dash_chief_ip}:{self.dash_chief_port}")

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"
