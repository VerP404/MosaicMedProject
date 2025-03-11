from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    name = models.CharField("Название организации", max_length=255)
    address = models.TextField("Адрес")
    phone_number = models.CharField("Номер телефона", max_length=20)
    email = models.EmailField("Электронная почта")
    code_mo = models.CharField("Код МО в СМО", max_length=20, blank=True, null=True)
    oid_mo = models.CharField("OID МО", max_length=50)
    region = models.CharField("Регион", max_length=50)

    class Meta:
        verbose_name = "Организацию"
        verbose_name_plural = "Организации"

    def __str__(self):
        return f"{self.name} ({self.code_mo or 'без кода МО'})"


class ActiveOrganization(models.Model):
    """
    Модель для задания главной (активной) организации.
    Только подразделения, отделения и участки этой организации будут отображаться
    в развернутой версии приложения.
    """
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Главная организация"
    )
    is_active = models.BooleanField("Активна", default=False)

    class Meta:
        verbose_name = "Активную организацию"
        verbose_name_plural = "Активная организация"

    def __str__(self):
        return f"Активная организация: {self.organization}"


class Building(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='buildings',
        verbose_name="Организация"
    )
    name = models.CharField("Название корпуса", max_length=255)
    additional_name = models.CharField("Дополнительное название корпуса", max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпусы"

    def __str__(self):
        additional = f" - {self.additional_name}" if self.additional_name else ""
        return f"{self.name}{additional}"


class Department(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name="Корпус"
    )
    name = models.CharField("Название отделения", max_length=255)
    additional_name = models.CharField("Дополнительное название отделения", max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"

    def __str__(self):
        return f"{self.name} ({self.building.name})"


class Station(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='stations',
        verbose_name="Отделение"
    )
    code = models.CharField("Код участка", max_length=255)
    name = models.CharField("Название участка", max_length=255, blank=True, null=True)
    open_date = models.DateField("Дата введения участка", blank=True, null=True)
    close_date = models.DateField("Дата закрытия участка", blank=True, null=True)

    class Meta:
        verbose_name = "Участок"
        verbose_name_plural = "Участки"

    def __str__(self):
        return f"{self.name or self.code} ({self.department})"


class StationDoctorAssignment(models.Model):
    station = models.ForeignKey(
        'organizations.Station',
        on_delete=models.CASCADE,
        related_name='doctor_assignments',
        verbose_name='Участок'
    )
    doctor = models.ForeignKey(
        'kadry.Employee',
        on_delete=models.CASCADE,
        verbose_name='Врач'
    )
    appointment_date = models.DateField('Дата начала')
    removal_date = models.DateField('Дата окончания', blank=True, null=True)

    class Meta:
        verbose_name = 'Назначение врача на участок'
        verbose_name_plural = 'Назначения врачей на участок'

    def __str__(self):
        return f"{self.doctor} на {self.station} с {self.appointment_date}"

    def clean(self):
        super().clean()
        # Проверяем, что дата окончания не раньше даты начала, если она указана
        if self.removal_date and self.removal_date < self.appointment_date:
            raise ValidationError("Дата окончания не может быть раньше даты начала")

        # Если назначение активно (removal_date не указана)
        if self.removal_date is None:
            # Получаем все активные назначения для данного участка
            active_assignments = StationDoctorAssignment.objects.filter(
                station=self.station, removal_date__isnull=True
            )
            # Если запись обновляется, исключаем текущую запись из выборки
            if self.pk:
                active_assignments = active_assignments.exclude(pk=self.pk)

            if active_assignments.count() >= 2:
                raise ValidationError("На участке может быть не более 2 активных назначений (без даты окончания)")

            if active_assignments.filter(doctor=self.doctor).exists():
                raise ValidationError("Данный врач уже назначен на участок на активный период")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SourceSystem(models.Model):
    """
    Модель для хранения сведений о внешних системах.
    Здесь централизовано задаются название внешней системы и регион.
    """
    name = models.CharField("Название внешней системы", max_length=255)
    region = models.CharField("Регион", max_length=255)

    class Meta:
        verbose_name = "Внешняя система"
        verbose_name_plural = "Внешние системы"

    def __str__(self):
        return f"{self.name} ({self.region})"


class RelatedDepartment(models.Model):
    """
    Модель для связи отделения (из нашей базы) с данными из внешней системы.
    Например, если во внешней системе отделение называется иначе, здесь можно указать
    соответствующее имя и связать с внешней системой.
    """
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='related_departments',
        verbose_name="Отделение"
    )
    external_department_name = models.CharField("Название отделения во внешней системе", max_length=255)
    source_system = models.ForeignKey(
        SourceSystem,
        on_delete=models.CASCADE,
        verbose_name="Внешняя система"
    )

    class Meta:
        verbose_name = "Связь с внешним отделением"
        verbose_name_plural = "Связи с внешними отделениями"

    def __str__(self):
        return f"{self.department.name} — {self.external_department_name} ({self.source_system.name})"
