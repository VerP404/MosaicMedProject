from django.db import models


class MedicalOrganization(models.Model):
    name = models.CharField("Название организации", max_length=255)
    name_kvazar = models.CharField("Название организации в Квазар", max_length=255)
    name_miskauz = models.CharField("Название организации в КАУЗ", max_length=255)
    address = models.TextField("Адрес")
    phone_number = models.CharField("Номер телефона", max_length=20)
    email = models.EmailField("Электронная почта")
    code_mo = models.CharField("Код МО в СМО", max_length=20, blank=True, null=True)  # Новое поле

    class Meta:
        verbose_name = "Медицинскую организацию"
        verbose_name_plural = "Медицинская организация"

    def __str__(self):
        return f"{self.name} ({self.code_mo or 'без кода МО'})"


class Building(models.Model):
    organization = models.ForeignKey(
        MedicalOrganization,
        on_delete=models.CASCADE,
        related_name='buildings',
        verbose_name="Организация"
    )
    name = models.CharField("Название корпуса", max_length=255)
    additional_name = models.CharField("Дополнительное название корпуса", max_length=255, blank=True, null=True)
    address = models.TextField("Адрес", blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпусы"

    def __str__(self):
        return f"{self.name} - {self.additional_name}"


class Department(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name="Корпус"
    )
    name = models.CharField("Название отделения", max_length=255)
    additional_name = models.CharField("Дополнительное название отделения", max_length=255, blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)

    class Meta:
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"

    def __str__(self):
        return f"{self.name} ({self.building.name})"
