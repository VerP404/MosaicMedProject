from django.db import models


class People(models.Model):
    fio = models.CharField(max_length=255, verbose_name="ФИО")
    dr = models.CharField(max_length=255, verbose_name="Дата рождения")
    enp = models.CharField(max_length=255, unique=True, verbose_name="ЕНП")
    phone = models.CharField(max_length=255, default="-", verbose_name="Телефон")
    address = models.CharField(max_length=255, default="-", verbose_name="Адрес")

    def __str__(self):
        return f"{self.fio} - {self.enp}"

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"


class ISZLPeopleReport(models.Model):
    date_report = models.DateField(verbose_name="Дата отчета")
    people = models.ForeignKey(People, on_delete=models.CASCADE, verbose_name="Пациент")
    smo = models.CharField(max_length=255, verbose_name="СМО")
    ss_doctor = models.CharField(max_length=255, verbose_name="Врач")
    lpuuch = models.CharField(max_length=255, verbose_name="Участок")

    def __str__(self):
        return f"Отчет на {self.date_report} для {self.people}"

    class Meta:
        verbose_name = "Отчет по населению в ИСЗЛ"
        verbose_name_plural = "Отчеты по населению в ИСЗЛ"


class ISZLReportSummary(models.Model):
    date_report = models.DateField(unique=True, verbose_name="Дата отчета")
    patient_count = models.IntegerField(verbose_name="Количество пациентов")
    change = models.IntegerField(verbose_name="Изменение")

    def __str__(self):
        return f"Отчет на {self.date_report}: {self.patient_count} пациентов"
