from __future__ import annotations

from django.db import models


class DnDiagnosisCategory(models.Model):
    """
    Категория/группа из файла 168н (колонка `group` на вашем скрине: например 'СД', 'Прочие').
    Это НЕ "группы диагнозов" из матрицы услуг (I10–I15, E11 и т.п.), а более широкая классификация.
    """

    name = models.CharField("Категория", max_length=128, unique=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Категория диагнозов (168н)"
        verbose_name_plural = "Категории диагнозов (168н)"
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class DnSpecialty(models.Model):
    """Специальность (терапия, ВОП и т.п.)."""

    name = models.CharField("Специальность", max_length=255, unique=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Специальность (ДН)"
        verbose_name_plural = "Специальности (ДН)"
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class DnDiagnosis(models.Model):
    """Диагноз (код МКБ), может встречаться в нескольких специальностях."""

    code = models.CharField("Код МКБ", max_length=32, unique=True, db_index=True)
    category = models.ForeignKey(
        DnDiagnosisCategory,
        on_delete=models.PROTECT,
        related_name="diagnoses",
        verbose_name="Категория (168н)",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Диагноз (168н)"
        verbose_name_plural = "Диагнозы (168н)"
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class DnDiagnosisSpecialty(models.Model):
    """
    Связь диагноза и специальности.
    В файле 168н есть `speciality` (основная) и `joint_speciality` (доп. через '/').
    """

    SOURCE_PRIMARY = "primary"
    SOURCE_JOINT = "joint"
    SOURCE_CHOICES = [
        (SOURCE_PRIMARY, "Основная"),
        (SOURCE_JOINT, "Совместная"),
    ]

    diagnosis = models.ForeignKey(
        DnDiagnosis, on_delete=models.CASCADE, related_name="specialties", verbose_name="Диагноз"
    )
    specialty = models.ForeignKey(
        DnSpecialty, on_delete=models.CASCADE, related_name="diagnoses", verbose_name="Специальность"
    )
    source = models.CharField("Источник", max_length=16, choices=SOURCE_CHOICES)

    class Meta:
        verbose_name = "Диагноз ↔ Специальность (168н)"
        verbose_name_plural = "Диагноз ↔ Специальности (168н)"
        unique_together = ("diagnosis", "specialty", "source")
        indexes = [
            models.Index(fields=["specialty", "source"]),
            models.Index(fields=["diagnosis", "source"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.diagnosis.code} — {self.specialty.name} ({self.source})"


class DnDiagnosisGroup(models.Model):
    """
    Группа диагнозов для матрицы услуг (колонки вида I10–I15, E11, J44, 'K63.9', списки и т.п.).
    Это "аналитическая" группа, которая объединяет набор диагнозов по правилам.
    """

    code = models.CharField("Код группы", max_length=256, unique=True)
    title = models.CharField("Название", max_length=255, blank=True, default="")
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    # Храним исходное правило как текст (например: "I10-I15" или "J41.0,J41.1,J41.8" или "K63.9")
    rule = models.TextField("Правило (исходный заголовок)", blank=True, default="")

    class Meta:
        verbose_name = "Группа диагнозов (матрица услуг)"
        verbose_name_plural = "Группы диагнозов (матрица услуг)"
        ordering = ["order", "code"]

    def __str__(self) -> str:  # pragma: no cover
        return self.title or self.code


class DnDiagnosisGroupMembership(models.Model):
    """Ручное/импортируемое включение диагноза в группу (если нужно фиксировать состав)."""

    group = models.ForeignKey(
        DnDiagnosisGroup, on_delete=models.CASCADE, related_name="memberships", verbose_name="Группа"
    )
    diagnosis = models.ForeignKey(
        DnDiagnosis, on_delete=models.CASCADE, related_name="group_memberships", verbose_name="Диагноз"
    )
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        verbose_name = "Диагноз в группе"
        verbose_name_plural = "Диагнозы в группах"
        unique_together = ("group", "diagnosis")
        indexes = [
            models.Index(fields=["group", "is_active"]),
            models.Index(fields=["diagnosis", "is_active"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.group.code} <- {self.diagnosis.code}"


class DnService(models.Model):
    """Услуга (строка матрицы)."""

    code = models.CharField("Код услуги", max_length=128, unique=True, db_index=True)
    name = models.CharField("Наименование услуги", max_length=512)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Услуга ДН"
        verbose_name_plural = "Услуги ДН"
        ordering = ["order", "code"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code} — {self.name}"


class DnServicePricePeriod(models.Model):
    """Единый период действия тарифов для всех услуг."""

    date_start = models.DateField("Дата начала действия", db_index=True)
    date_end = models.DateField("Дата окончания действия", null=True, blank=True, db_index=True)
    title = models.CharField("Название периода", max_length=128, blank=True, default="")
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Период стоимости услуги"
        verbose_name_plural = "Периоды стоимости услуг"
        ordering = ["-date_start", "date_end"]
        unique_together = ("date_start", "date_end")

    def __str__(self) -> str:  # pragma: no cover
        if self.date_end:
            return f"{self.date_start:%d.%m.%Y} - {self.date_end:%d.%m.%Y}"
        return f"с {self.date_start:%d.%m.%Y}"


class DnServicePrice(models.Model):
    """Стоимость услуги в конкретный период."""

    service = models.ForeignKey(
        DnService, on_delete=models.CASCADE, related_name="prices", verbose_name="Услуга"
    )
    period = models.ForeignKey(
        DnServicePricePeriod, on_delete=models.CASCADE, related_name="service_prices", verbose_name="Период"
    )
    price = models.DecimalField("Стоимость", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Стоимость услуги"
        verbose_name_plural = "Стоимость услуг"
        unique_together = ("service", "period")
        ordering = ["service__code", "-period__date_start"]
        indexes = [
            models.Index(fields=["service", "period"]),
            models.Index(fields=["period"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.service.code}: {self.price} ({self.period})"


class DnServiceRequirement(models.Model):
    """Требование: услуга обязательна для группы диагнозов (ячейка '+') в рамках специальности."""

    service = models.ForeignKey(
        DnService, on_delete=models.CASCADE, related_name="requirements", verbose_name="Услуга"
    )
    group = models.ForeignKey(
        DnDiagnosisGroup, on_delete=models.CASCADE, related_name="requirements", verbose_name="Группа диагнозов"
    )
    specialty = models.ForeignKey(
        DnSpecialty,
        on_delete=models.CASCADE,
        related_name="requirements",
        verbose_name="Специальность",
        null=True,
        blank=True,
    )
    is_required = models.BooleanField("Требуется", default=True)

    class Meta:
        verbose_name = "Требование услуги по группе и специальности"
        verbose_name_plural = "Требования услуг по группам и специальностям"
        unique_together = ("service", "group", "specialty")
        indexes = [
            models.Index(fields=["group", "is_required"]),
            models.Index(fields=["service", "is_required"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.service.code} -> {self.group.code} ({'+' if self.is_required else '-'})"

