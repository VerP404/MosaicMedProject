from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class MatrixEdition(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ACTIVE = "active", "Активна"
        ARCHIVED = "archived", "Архив"

    code = models.SlugField("Код издания", max_length=64, unique=True, db_index=True)
    title = models.CharField("Название", max_length=256)
    effective_from = models.DateField("Действует с")
    effective_to = models.DateField("Действует по", null=True, blank=True)
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    notes = models.TextField("Примечания", blank=True, default="")
    max_doctor_visits = models.PositiveSmallIntegerField(
        "Макс. явок к врачу (диспансерный приём)",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text=(
            "Сколько раз учитывается услуга «Диспансерный приём …» на талон: "
            "1 — одна позиция в матрице до 01.04, 3 — по числу явок с 01.04."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Издание матрицы ДН"
        verbose_name_plural = "ДН: издания матрицы"
        ordering = ["-effective_from", "code"]

    def __str__(self) -> str:
        return f"{self.code} ({self.title})"

    def clean(self) -> None:
        from apps.dn_matrix.services.matrix_edition_guard import validate_matrix_edition_code

        validate_matrix_edition_code(self.code)

    def save(self, *args, **kwargs):
        skip_guard = kwargs.pop("_skip_matrix_code_guard", False)
        if not skip_guard:
            from apps.dn_matrix.services.matrix_edition_guard import matrix_edition_guard_enabled

            if matrix_edition_guard_enabled():
                self.full_clean()
        super().save(*args, **kwargs)


class DnSpecialty(models.Model):
    edition = models.ForeignKey(
        MatrixEdition, on_delete=models.CASCADE, related_name="specialties", verbose_name="Издание"
    )
    code = models.SlugField("Код", max_length=64)
    title = models.CharField("Название", max_length=256)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Специальность (матрица ДН)"
        verbose_name_plural = "ДН: специальности"
        ordering = ["sort_order", "code"]
        unique_together = [("edition", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"


class DnDiagnosisCategory(models.Model):
    edition = models.ForeignKey(
        MatrixEdition, on_delete=models.CASCADE, related_name="diagnosis_categories", verbose_name="Издание"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Родитель",
    )
    code = models.SlugField("Код", max_length=64)
    title = models.CharField("Название", max_length=256)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Категория диагнозов"
        verbose_name_plural = "ДН: категории диагнозов"
        ordering = ["sort_order", "code"]
        unique_together = [("edition", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"


class DnDiagnosis(models.Model):
    edition = models.ForeignKey(MatrixEdition, on_delete=models.CASCADE, related_name="diagnoses", verbose_name="Издание")
    category = models.ForeignKey(
        DnDiagnosisCategory, on_delete=models.PROTECT, related_name="diagnoses", verbose_name="Категория"
    )
    mkb_code = models.CharField("Код МКБ", max_length=16, db_index=True)
    title = models.CharField("Название", max_length=512)

    class Meta:
        verbose_name = "Диагноз (матрица ДН)"
        verbose_name_plural = "ДН: диагнозы"
        ordering = ["mkb_code"]
        unique_together = [("edition", "mkb_code")]

    def __str__(self) -> str:
        return f"{self.mkb_code} — {self.title}"


class DnDiagnosisSpecialty(models.Model):
    class Kind(models.TextChoices):
        PRIMARY = "primary", "Основная"
        JOINT = "joint", "Совместная"
        ACCOMPANYING = "accompanying", "Сопутствующая"

    diagnosis = models.ForeignKey(
        DnDiagnosis, on_delete=models.CASCADE, related_name="specialty_links", verbose_name="Диагноз"
    )
    specialty = models.ForeignKey(
        DnSpecialty, on_delete=models.CASCADE, related_name="diagnosis_links", verbose_name="Специальность"
    )
    kind = models.CharField("Тип связи", max_length=16, choices=Kind.choices, default=Kind.PRIMARY)

    class Meta:
        verbose_name = "Диагноз — специальность"
        verbose_name_plural = "ДН: связи диагноз—специальность"
        unique_together = [("diagnosis", "specialty", "kind")]

    def __str__(self) -> str:
        return f"{self.diagnosis_id}:{self.specialty_id}:{self.kind}"


class DnDiagnosisGroup(models.Model):
    edition = models.ForeignKey(
        MatrixEdition, on_delete=models.CASCADE, related_name="diagnosis_groups", verbose_name="Издание"
    )
    code = models.SlugField("Код группы", max_length=64)
    title = models.CharField("Название", max_length=256)
    rule = models.JSONField("Правило (расширение)", default=dict, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Группа диагнозов"
        verbose_name_plural = "ДН: группы диагнозов"
        ordering = ["sort_order", "code"]
        unique_together = [("edition", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"


class DnDiagnosisGroupMembership(models.Model):
    group = models.ForeignKey(
        DnDiagnosisGroup, on_delete=models.CASCADE, related_name="memberships", verbose_name="Группа"
    )
    diagnosis = models.ForeignKey(
        DnDiagnosis, on_delete=models.CASCADE, related_name="group_memberships", verbose_name="Диагноз"
    )

    class Meta:
        verbose_name = "Вхождение диагноза в группу"
        verbose_name_plural = "ДН: вхождения в группы"
        unique_together = [("group", "diagnosis")]

    def __str__(self) -> str:
        return f"group={self.group_id} diag={self.diagnosis_id}"


class DnService(models.Model):
    class SexRestriction(models.TextChoices):
        ANY = "", "Любой"
        MALE = "M", "Мужской"
        FEMALE = "F", "Женский"

    edition = models.ForeignKey(MatrixEdition, on_delete=models.CASCADE, related_name="services", verbose_name="Издание")
    code = models.CharField("Код услуги", max_length=32)
    title = models.CharField("Название", max_length=512)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    sex_restriction = models.CharField(
        "Ограничение по полу",
        max_length=1,
        choices=SexRestriction.choices,
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = "Услуга (матрица ДН)"
        verbose_name_plural = "ДН: услуги"
        ordering = ["sort_order", "code"]
        unique_together = [("edition", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"


class DnServicePricePeriod(models.Model):
    edition = models.ForeignKey(
        MatrixEdition, on_delete=models.CASCADE, related_name="price_periods", verbose_name="Издание"
    )
    code = models.SlugField("Код периода", max_length=64)
    title = models.CharField("Подпись", max_length=256, blank=True, default="")
    valid_from = models.DateField("Действует с")
    valid_to = models.DateField("Действует по", null=True, blank=True)

    class Meta:
        verbose_name = "Период цен"
        verbose_name_plural = "ДН: периоды цен"
        ordering = ["-valid_from", "code"]
        unique_together = [("edition", "code")]

    def __str__(self) -> str:
        return f"{self.code} ({self.valid_from}…{self.valid_to or '∞'})"


class DnServicePrice(models.Model):
    period = models.ForeignKey(
        DnServicePricePeriod, on_delete=models.CASCADE, related_name="prices", verbose_name="Период"
    )
    service = models.ForeignKey(DnService, on_delete=models.CASCADE, related_name="prices", verbose_name="Услуга")
    amount = models.DecimalField("Цена", max_digits=14, decimal_places=2)
    currency = models.CharField("Валюта", max_length=8, default="RUB")

    class Meta:
        verbose_name = "Цена услуги"
        verbose_name_plural = "ДН: цены услуг"
        unique_together = [("period", "service")]

    def __str__(self) -> str:
        return f"{self.service_id} @ {self.period_id}: {self.amount}"


class DnServiceRequirement(models.Model):
    """Строка требования: услуга применима, если выполняется эта строка (конъюнкция полей внутри строки)."""

    service = models.ForeignKey(
        DnService, on_delete=models.CASCADE, related_name="requirements", verbose_name="Услуга"
    )
    specialty = models.ForeignKey(
        DnSpecialty,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="service_requirements",
        verbose_name="Специальность",
    )
    diagnosis = models.ForeignKey(
        DnDiagnosis,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="service_requirements",
        verbose_name="Диагноз",
    )
    diagnosis_group = models.ForeignKey(
        DnDiagnosisGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="service_requirements",
        verbose_name="Группа диагнозов",
    )

    class Meta:
        verbose_name = "Условие применимости услуги"
        verbose_name_plural = "ДН: условия применимости услуг"
        constraints = [
            models.CheckConstraint(
                check=models.Q(specialty__isnull=False)
                | models.Q(diagnosis__isnull=False)
                | models.Q(diagnosis_group__isnull=False),
                name="dn_matrix_svc_req_non_empty_scope",
            )
        ]

    def clean(self):
        super().clean()
        if not self.specialty_id and not self.diagnosis_id and not self.diagnosis_group_id:
            raise ValidationError("Заполните хотя бы одно из полей: специальность, диагноз или группа.")

    def __str__(self) -> str:
        return f"req svc={self.service_id}"
