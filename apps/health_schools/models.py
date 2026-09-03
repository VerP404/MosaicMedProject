from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class HealthSchool(models.Model):
    """Строка справочника школ цели 307 (тариф + услуга + периодичность)."""

    class Criterion(models.TextChoices):
        MKB = "mkb", "МКБ"
        AGE = "age", "Возраст"
        RISK = "risk", "Фактор риска"
        BMI = "bmi", "ИМТ / ожирение"

    number = models.PositiveSmallIntegerField("№", unique=True)
    name = models.CharField("Школа", max_length=256)
    group_name = models.CharField("Группа", max_length=128, blank=True, default="")
    mkb_rule = models.CharField("МКБ / критерий", max_length=512)
    visits = models.PositiveSmallIntegerField("Явки", default=4, validators=[MinValueValidator(1)])
    duration = models.CharField("Длительность", max_length=64, blank=True, default="")
    tariff = models.DecimalField("Тариф, руб.", max_digits=10, decimal_places=2, default=0)
    service_code = models.CharField("Код услуги", max_length=64, blank=True, default="")
    service_title = models.CharField("Наименование услуги", max_length=512, blank=True, default="")
    period_years = models.PositiveSmallIntegerField(
        "Периодичность, лет",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Повторное комплексное посещение этой школы не раньше чем через N лет. По умолчанию 3.",
    )
    criterion = models.CharField(
        "Тип отбора",
        max_length=16,
        choices=Criterion.choices,
        default=Criterion.MKB,
        db_index=True,
    )
    min_age = models.PositiveSmallIntegerField("Мин. возраст", null=True, blank=True)
    max_age = models.PositiveSmallIntegerField("Макс. возраст", null=True, blank=True)
    notes = models.TextField("Примечание", blank=True, default="")
    is_active = models.BooleanField("Активна", default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Школа здоровья (307)"
        verbose_name_plural = "Школы здоровья (307)"
        ordering = ["number"]

    def __str__(self) -> str:
        return f"{self.number}. {self.name}"
