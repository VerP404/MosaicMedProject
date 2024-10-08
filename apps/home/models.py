from django.db import models


class MainSettings(models.Model):
    dash_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_port = models.PositiveIntegerField(default='5000')
    main_app_ip = models.GenericIPAddressField(default='127.0.0.1')
    main_app_port = models.PositiveIntegerField(default='8000')

    def get_dash_url(self):
        return f"http://{self.dash_ip}:{self.dash_port}"

    def __str__(self):
        return f"Аналитическая система - {self.dash_ip}:{self.dash_port}, Основное приложение - {self.main_app_ip}:{self.main_app_port}"

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"
