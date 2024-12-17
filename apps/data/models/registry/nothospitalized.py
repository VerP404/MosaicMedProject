from django.db import models


class PatientRegistry(models.Model):
    number = models.IntegerField(verbose_name="№ п/п")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    address = models.CharField(max_length=500, verbose_name="Адрес")
    phone = models.CharField(max_length=15, verbose_name="Телефон")
    medical_organization = models.CharField(max_length=255, verbose_name="Прикрепление к МО")
    hospital_name = models.CharField(max_length=255, verbose_name="Наименование стационара")
    admission_date = models.DateField(verbose_name="Дата обращения в приемное отделение")
    REFERRAL_CHOICES = [
        ('ССМП', 'ССМП'),
        ('Самообращение', 'Самообращение'),
    ]
    referral_method = models.CharField(
        max_length=20, choices=REFERRAL_CHOICES, verbose_name="Способ обращения"
    )
    admission_diagnosis = models.CharField(max_length=255, verbose_name="Диагноз при поступлении")
    refusal_date = models.DateField(verbose_name="Дата отказа")
    REFUSAL_REASON_CHOICES = [
        ('Нет показаний для госпитализации', 'Нет показаний для госпитализации'),
        ('Отказ пациента (законного представителя)', 'Отказ пациента (законного представителя)'),
    ]
    refusal_reason = models.CharField(
        max_length=50, choices=REFUSAL_REASON_CHOICES, verbose_name="Причина отказа в госпитализации"
    )

    class Meta:
        verbose_name = "Реестр не госпитализированных пациентов"
        verbose_name_plural = "Реестр не госпитализированных пациентов"
        ordering = ['number']

    def __str__(self):
        return f"{self.number}: {self.full_name}"
