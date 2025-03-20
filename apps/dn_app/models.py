from django.db import models


class Person(models.Model):
    enp = models.CharField("Единый номер полиса", max_length=255, unique=True)
    fio = models.CharField("ФИО", max_length=255)
    dr = models.DateField("Дата рождения")

    def __str__(self):
        return f"{self.fio} ({self.enp})"


class Encounter(models.Model):
    """
    Отражает конкретную встречу или контакт пациента с системой (на основе ldwid и ds).
    """
    person = models.ForeignKey(Person, related_name="encounters", on_delete=models.CASCADE)
    pid = models.CharField("PID", max_length=50)  # можно сохранить для справки
    ldwid = models.CharField("LDWID", max_length=50)
    ds = models.CharField("Диагноз", max_length=255)

    class Meta:
        unique_together = (("person", "ldwid", "ds"),)

    def __str__(self):
        return f"{self.person.fio} - {self.ds} (LDWID: {self.ldwid})"


class Observation(models.Model):
    encounter = models.ForeignKey(Encounter, related_name="observations", on_delete=models.CASCADE)
    pdwid = models.CharField("PDWID", max_length=50)
    plan_month = models.CharField("Плановый месяц", max_length=10, blank=True, null=True)
    plan_year = models.CharField("Плановый год", max_length=10, blank=True, null=True)
    date_begin = models.DateField("Дата начала наблюдения", blank=True, null=True)
    date_end = models.DateField("Дата окончания наблюдения", blank=True, null=True)

    # Поля для отслеживания истории
    effective_from = models.DateTimeField("Начало действия", auto_now_add=True)
    effective_to = models.DateTimeField("Окончание действия", blank=True, null=True)
    is_current = models.BooleanField("Актуально", default=True)

    class Meta:
        unique_together = (("encounter", "pdwid", "effective_from"),)

    def __str__(self):
        status = "активна" if self.is_current else f"закрыта {self.effective_to}"
        return f"Observation {self.pdwid} ({status}) for {self.encounter}"

