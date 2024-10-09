from django.db import models


class OMSTargetCategory(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория целей"
        verbose_name_plural = "Категории целей"


class GeneralOMSTarget(models.Model):
    code = models.CharField("Код цели", max_length=255)
    name = models.CharField("Наименование цели", max_length=255)
    start_date = models.DateField("Дата начала действия", blank=True, null=True)
    end_date = models.DateField("Дата окончания действия", blank=True, null=True)

    class Meta:
        verbose_name = "Общая цель ОМС"
        verbose_name_plural = "Общие цели ОМС"

    def __str__(self):
        return self.code


class MedicalOrganizationOMSTarget(models.Model):
    general_target = models.ForeignKey(
        GeneralOMSTarget,
        on_delete=models.CASCADE,
        verbose_name="Базовая цель"
    )
    organization = models.ForeignKey(
        "organization.MedicalOrganization",
        on_delete=models.CASCADE,
        verbose_name="Медицинская организация"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активная цель")
    start_date = models.DateField(null=True, blank=True, verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")

    # Новое поле для связи с категориями
    categories = models.ManyToManyField(
        OMSTargetCategory,
        related_name="medical_targets",
        blank=True,
        verbose_name="Категории"
    )

    def __str__(self):
        return f"{self.organization} - {self.general_target}"

    class Meta:
        verbose_name = "Цель ОМС Медицинской организации"
        verbose_name_plural = "Цели ОМС Медицинских организаций"
        unique_together = ('organization', 'general_target')


class SQLQueryParameters(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название параметра")
    query = models.TextField(verbose_name="SQL-запрос")
    parameters = models.JSONField(verbose_name="Параметры запроса", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "SQL Параметр"
        verbose_name_plural = "SQL Параметры"

    def __str__(self):
        return self.name


class StatusWebOMS(models.Model):
    status = models.CharField("Статус", max_length=255)
    name = models.CharField("Название", max_length=255)

    class Meta:
        verbose_name = "Статус Web-ОМС"
        verbose_name_plural = "Статусы Web-ОМС"

    def __str__(self):
        return f"{self.status} - {self.name}"
