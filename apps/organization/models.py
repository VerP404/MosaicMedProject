from django.db import models

from apps.personnel.models import Person, DoctorRecord


class MedicalOrganization(models.Model):
    name = models.CharField("Название организации", max_length=255)
    name_kvazar = models.CharField("Название организации в Квазар", max_length=255)
    name_miskauz = models.CharField("Название организации в КАУЗ", max_length=255)
    address = models.TextField("Адрес")
    phone_number = models.CharField("Номер телефона", max_length=20)
    email = models.EmailField("Электронная почта")
    code_mo = models.CharField("Код МО в СМО", max_length=20, blank=True, null=True)
    oid_mo = models.CharField("OID МО", max_length=50)

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
    name_kvazar = models.CharField("Название корпуса в Квазар", max_length=255)
    name_miskauz = models.CharField("Название корпуса в КАУЗ", max_length=255)
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


class OMSDepartment(models.Model):
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='oms_departments',
        verbose_name="Отделение"
    )
    name = models.CharField("Название отделения в Web-ОМС", max_length=255)

    class Meta:
        verbose_name = "Отделение Web-ОМС"
        verbose_name_plural = "Отделения Web-ОМС"

    def __str__(self):
        return f"{self.name} (Web-ОМС)"


# Модель для связи с отделениями Квазар
class KvazarDepartment(models.Model):
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='kvazar_departments',
        verbose_name="Отделение"
    )
    name = models.CharField("Название отделения в Квазар", max_length=255)

    class Meta:
        verbose_name = "Отделение Квазар"
        verbose_name_plural = "Отделения Квазар"

    def __str__(self):
        return f"{self.name} (Квазар)"


# Модель для связи с отделениями МИСКАУЗ
class MiskauzDepartment(models.Model):
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='miskauz_departments',
        verbose_name="Отделение"
    )
    name = models.CharField("Название отделения в МИСКАУЗ", max_length=255)

    class Meta:
        verbose_name = "Отделение МИСКАУЗ"
        verbose_name_plural = "Отделения МИСКАУЗ"

    def __str__(self):
        return f"{self.name} (МИСКАУЗ)"


class Station(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name="Отделение"
    )
    code = models.CharField("Код участка", max_length=255)
    name = models.CharField("Название участка", max_length=255, blank=True, null=True)
    open_date = models.DateField("Дата введения участка", blank=True, null=True)
    close_date = models.DateField("Дата закрытия участка", blank=True, null=True)
    doctor = models.ForeignKey(
        DoctorRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections',
        verbose_name="Врач"
    )

    class Meta:
        verbose_name = "Участок"
        verbose_name_plural = "Участки"

    def __str__(self):
        return f"{self.name} ({self.department})"


class DoctorAssignment(models.Model):
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='doctor_assignments',
        verbose_name="Участок"
    )
    doctor = models.ForeignKey(
        DoctorRecord,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="Врач"
    )
    start_date = models.DateField("Дата назначения")
    end_date = models.DateField("Дата завершения работы", blank=True, null=True)
    reason_for_transfer = models.TextField("Причина перевода", blank=True, null=True)

    class Meta:
        verbose_name = "Назначение врача на участок"
        verbose_name_plural = "Назначения врачей на участки"
        ordering = ['-start_date']

    def __str__(self):
        return f"Назначение врача {self.doctor} на участок {self.station}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_station_doctor()

    def update_station_doctor(self):
        """Обновление текущего врача в Station при изменении назначения"""
        if self.end_date is None:  # Если назначение активно
            # Назначаем врача на Station
            self.station.doctor = self.doctor
        else:
            # Если назначение завершено, проверяем, есть ли другие активные назначения
            active_assignment = DoctorAssignment.objects.filter(
                station=self.station,
                end_date__isnull=True
            ).exclude(id=self.id).first()

            # Если другое активное назначение есть, обновляем врача на него, иначе убираем врача
            self.station.doctor = active_assignment.doctor if active_assignment else None

        # Сохраняем изменения в Station
        self.station.save()
