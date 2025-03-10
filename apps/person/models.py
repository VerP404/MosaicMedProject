from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

from organization.models import Station


class Insurance(models.Model):
    """
    Страховые компании
    """
    code = models.IntegerField(unique=True, verbose_name="Код")
    name = models.CharField("Название", max_length=255)

    class Meta:
        verbose_name = "Страховую компанию"
        verbose_name_plural = "Страховые компании"

    def __str__(self):
        return f"{self.name} - {self.code}"


class InsurancePolicy(models.Model):
    """
    Страховые полисы
    """
    enp = models.CharField("ЕНП", max_length=16, validators=[
        RegexValidator(
            regex=r'^[0-9]{16}$',
            message="ЕНП должен состоять из 16 цифр"
        )
    ])
    start_date = models.DateField("Дата начала страхования")
    end_date = models.DateField("Дата окончания страхования", null=True, blank=True)
    insurance = models.ForeignKey(
        Insurance,
        on_delete=models.PROTECT,
        verbose_name="Страховая организация"
    )
    # Каждый полис привязан к одному физическому лицу.
    physical_person = models.ForeignKey(
        "PhysicalPerson",
        on_delete=models.CASCADE,
        verbose_name="Физическое лицо",
        related_name="policies"
    )

    class Meta:
        verbose_name = "Полис"
        verbose_name_plural = "Полисы"
        indexes = [
            models.Index(fields=['enp']),
        ]

    def __str__(self):
        return f'{self.enp}: {self.start_date} - {self.end_date}'

    def clean(self):
        """
        Проверяем, что если полис с таким же ENP уже существует,
        то он принадлежит тому же физическому лицу.
        """
        super().clean()
        # Найдем все полисы с таким же enp, исключая текущую запись (если обновляем)
        qs = InsurancePolicy.objects.filter(enp=self.enp)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        # Если найдены записи с таким же ENP, проверяем, что у всех physical_person совпадает
        for policy in qs:
            if policy.physical_person != self.physical_person:
                raise ValidationError(
                    {"enp": "Полис с таким ЕНП уже существует для другого физического лица."}
                )


class PhysicalPerson(models.Model):
    """
    Физические лица
    """
    last_name = models.CharField("Фамилия", max_length=255)
    first_name = models.CharField("Имя", max_length=255)
    middle_name = models.CharField("Отчество", max_length=255, default='-')
    birth_date = models.DateField("Дата рождения")
    gender = models.CharField("Пол", max_length=1, choices=(('М', 'М'), ('Ж', 'Ж')))
    snils = models.CharField(
        "СНИЛС",
        max_length=11,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{11}$',
                message="СНИЛС должен состоять из 11 цифр"
            )
        ]
    )
    phone = models.CharField(
        "Телефон",
        max_length=11,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^8[0-9]{10}$',
                message="Телефон должен начинаться с 8 и содержать 11 цифр"
            )
        ]
    )
    telegram = models.BigIntegerField("Телеграм", null=True, blank=True)

    class Meta:
        verbose_name = "Физическое лицо"
        verbose_name_plural = "Физические лица"
        constraints = [
            models.UniqueConstraint(
                fields=['snils'],
                condition=Q(snils__isnull=False),
                name='unique_snils'
            )
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class AttachmentPeriod(models.Model):
    physical_person = models.ForeignKey(
        PhysicalPerson,
        on_delete=models.CASCADE,
        verbose_name="Физическое лицо"
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Участок"
    )
    enp = models.CharField("ЕНП", max_length=16, blank=True, null=True)
    smo = models.CharField("СМО", max_length=50, blank=True, null=True)
    start_date = models.DateField("Дата начала прикрепления")
    end_date = models.DateField("Дата окончания прикрепления", null=True, blank=True)
    report_date = models.DateField("Дата отчёта")

    class Meta:
        verbose_name = "Прикрепление (интервал)"
        verbose_name_plural = "Прикрепления (интервалы)"
        indexes = [
            models.Index(fields=["report_date"]),
            models.Index(fields=["enp"]),
        ]

    def __str__(self):
        return f"{self.physical_person} прикреплён с {self.start_date} по {self.end_date or 'настоящее время'}"