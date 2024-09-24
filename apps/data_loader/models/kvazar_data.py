from django.db import models


class KvazarSettings(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Квазар: Настройка"
        verbose_name_plural = "Квазар: Настройки"
