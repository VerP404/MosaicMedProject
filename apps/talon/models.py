from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.kadry.models import DoctorCode
from apps.person.models import PhysicalPerson


class Source(models.Model):
    name = models.CharField("Название", max_length=255)

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"

    def __str__(self):
        return self.name


class TicketStatus(models.Model):
    code = models.CharField("Код", max_length=255)
    name = models.CharField("Название", max_length=255)

    class Meta:
        verbose_name = "Статус талона"
        verbose_name_plural = "Статусы талонов"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Goal(models.Model):
    code = models.CharField("Код", max_length=255)
    name = models.CharField("Название", max_length=500)

    class Meta:
        verbose_name = "Цель"
        verbose_name_plural = "Цели"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    number = models.CharField("Номер", max_length=255)
    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        verbose_name="Источник"
    )
    status = models.ForeignKey(
        TicketStatus,
        on_delete=models.CASCADE,
        verbose_name="Статус талона"
    )
    report_month = models.PositiveIntegerField(
        "Отчетный месяц",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    report_year = models.PositiveIntegerField(
        "Отчетный год",
        validators=[MinValueValidator(2020), MaxValueValidator(2030)]
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        verbose_name="Цель"
    )
    patient = models.ForeignKey(
        PhysicalPerson,
        on_delete=models.CASCADE,
        verbose_name="Пациент"
    )
    treatment_start = models.DateField("Начало лечения")
    treatment_end = models.DateField("Окончание лечения")
    visits = models.PositiveIntegerField("Посещения")
    visits_in_mo = models.PositiveIntegerField("Посещения в МО")
    visits_at_home = models.PositiveIntegerField("Посещения на дому")
    diagnosis = models.CharField("Диагноз", max_length=255)
    diagnosis_2 = models.CharField("Диагноз 2", max_length=255, blank=True, null=True)
    diagnosis_3 = models.CharField("Диагноз 3", max_length=255, blank=True, null=True)
    diagnosis_4 = models.CharField("Диагноз 4", max_length=255, blank=True, null=True)
    health_group = models.CharField("Группа здоровья", max_length=255, blank=True, null=True)
    ksg = models.CharField("КСГ", max_length=255, blank=True, null=True)
    amount = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    sanctions = models.DecimalField("Санкции", max_digits=10, decimal_places=2)
    doctor_code = models.ForeignKey(
        DoctorCode,
        on_delete=models.CASCADE,
        verbose_name="Код врача"
    )
    formation_date = models.DateField("Дата формирования")
    change_date = models.DateField("Дата изменения")
    updated = models.DateTimeField("Обновлено", default=timezone.now)
    blocked = models.BooleanField("Заблокировано", default=False)

    class Meta:
        verbose_name = "Талон"
        verbose_name_plural = "Талоны"
        indexes = [
            models.Index(fields=['number']),
        ]

    def __str__(self):
        return f"Талон {self.number} для пациента {self.patient}"
