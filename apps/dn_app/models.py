from django.db import models
from django.utils import timezone


class Person(models.Model):
    enp = models.CharField("Единый номер полиса", max_length=255, unique=True)
    fio = models.CharField("ФИО", max_length=255)
    dr = models.DateField("Дата рождения", null=True, blank=True)
    lpuuch = models.CharField("Участок", max_length=255, blank=True, default="")
    is_detached = models.BooleanField(
        "Откреплен",
        default=False,
        help_text="Пациент откреплен (отсутствует в последней загрузке текущего года)",
    )
    detached_date = models.DateTimeField("Дата открепления", blank=True, null=True)
    last_import_date = models.DateTimeField("Дата последней загрузки", blank=True, null=True)

    class Meta:
        verbose_name = "Пациент ДН"
        verbose_name_plural = "Пациенты ДН"
        indexes = [
            models.Index(fields=["fio"]),
        ]

    def __str__(self):
        return f"{self.fio} ({self.enp})"


class DnLine(models.Model):
    """Линия диспансерного наблюдения (аналог строки грида ИСЗЛ)."""

    STATUS_CHOICES = [
        ("planned", "Запланирован"),
        ("completed", "Выполнен"),
        ("not_completed", "Не выполнен"),
        ("detached", "Откреплен / снят"),
    ]

    person = models.ForeignKey(Person, related_name="dn_lines", on_delete=models.CASCADE)
    pdwid = models.CharField("pdwID", max_length=50, unique=True, db_index=True)
    pid = models.CharField("pID", max_length=50, blank=True, default="")
    ldwid = models.CharField("ldwID", max_length=50, blank=True, default="")
    ds = models.CharField("Диагноз (сырой)", max_length=255, blank=True, default="")
    ds_code = models.CharField("Код МКБ", max_length=32, db_index=True, blank=True, default="")
    date_begin = models.DateField("Поставлен на ДН", blank=True, null=True)
    date_end = models.DateField("Снят с ДН", blank=True, null=True)
    reason = models.CharField("Причина снятия", max_length=255, blank=True, default="")
    plan_year = models.IntegerField("Плановый год", db_index=True)
    plan_month = models.CharField("Плановый месяц", max_length=10, blank=True, default="")
    doctor = models.CharField("Врач ДН", max_length=255, blank=True, default="")
    specialty_raw = models.CharField("Специальность (сырая)", max_length=255, blank=True, default="")
    category_168n = models.CharField(
        "Категория 168н",
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="БСК / ОНКО / СД / Прочие",
    )
    profile_cluster = models.CharField(
        "Профиль (кластер)",
        max_length=128,
        blank=True,
        default="",
        db_index=True,
        help_text="Терапия (ВОП/терапия/леч.дело) и др.",
    )
    out_of_168n = models.BooleanField(
        "Вне 168н",
        default=False,
        db_index=True,
        help_text="МКБ нет в справочнике → кандидат на цель 305",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned", db_index=True)
    is_current = models.BooleanField("Актуально в снимке года", default=True, db_index=True)
    talon_number = models.CharField("Талон ОМС", max_length=64, blank=True, default="")
    actual_date = models.DateField("Дата факта", blank=True, null=True)
    import_batch = models.ForeignKey(
        "DataImport",
        related_name="dn_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Линия ДН"
        verbose_name_plural = "Линии ДН"
        indexes = [
            models.Index(fields=["plan_year", "is_current"]),
            models.Index(fields=["plan_year", "status"]),
            models.Index(fields=["person", "ds_code"]),
            models.Index(fields=["plan_year", "category_168n"]),
            models.Index(fields=["plan_year", "out_of_168n"]),
        ]

    def __str__(self):
        return f"{self.pdwid} {self.ds_code} Y{self.plan_year}"


class DnFact(models.Model):
    """Факт прохождения / внешний источник (ОМС, Квазар)."""

    SOURCE_OMS = "oms"
    SOURCE_KVAZAR = "kvazar"
    SOURCE_CHOICES = [
        (SOURCE_OMS, "ОМС талон"),
        (SOURCE_KVAZAR, "Квазар журнал ДН"),
    ]

    person = models.ForeignKey(Person, related_name="dn_facts", on_delete=models.CASCADE)
    enp = models.CharField("ЕНП", max_length=255, db_index=True)
    ds_code = models.CharField("Код МКБ", max_length=32, db_index=True, blank=True, default="")
    report_year = models.IntegerField("Год", db_index=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, db_index=True)
    talon = models.CharField("Номер талона", max_length=64, blank=True, default="")
    goal = models.CharField("Цель", max_length=32, blank=True, default="", db_index=True)
    treatment_end = models.CharField("Дата окончания", max_length=32, blank=True, default="")
    status = models.CharField("Статус талона", max_length=64, blank=True, default="")
    doctor = models.CharField("Врач", max_length=255, blank=True, default="")
    raw_diagnosis = models.CharField("Диагноз сырой", max_length=512, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Факт ДН"
        verbose_name_plural = "Факты ДН"
        indexes = [
            models.Index(fields=["enp", "ds_code", "report_year"]),
            models.Index(fields=["report_year", "source", "goal"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "enp", "ds_code", "report_year", "talon"],
                name="dn_fact_uniq_source_enp_ds_year_talon",
            )
        ]

    def __str__(self):
        return f"{self.source} {self.enp} {self.ds_code} {self.report_year}"


# --- legacy (сохраняем для старых загрузок / совместимости) ---

class Encounter(models.Model):
    person = models.ForeignKey(Person, related_name="encounters", on_delete=models.CASCADE)
    pid = models.CharField("PID", max_length=50)
    ldwid = models.CharField("LDWID", max_length=50)
    ds = models.CharField("Диагноз", max_length=255)

    class Meta:
        unique_together = (("person", "ldwid", "ds"),)

    def __str__(self):
        return f"{self.person.fio} - {self.ds} (LDWID: {self.ldwid})"


class Observation(models.Model):
    STATUS_CHOICES = [
        ("planned", "Запланирован"),
        ("completed", "Выполнен"),
        ("not_completed", "Не выполнен"),
        ("detached", "Откреплен"),
    ]

    encounter = models.ForeignKey(Encounter, related_name="observations", on_delete=models.CASCADE)
    pdwid = models.CharField("PDWID", max_length=50)
    plan_month = models.CharField("Плановый месяц", max_length=10, blank=True, null=True)
    plan_year = models.IntegerField("Плановый год", blank=True, null=True)
    date_begin = models.DateField("Дата начала наблюдения", blank=True, null=True)
    date_end = models.DateField("Дата окончания наблюдения", blank=True, null=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="planned")
    actual_date = models.DateField("Дата фактического посещения", blank=True, null=True)
    talon_number = models.CharField("Номер талона ОМС", max_length=50, blank=True, null=True)
    effective_from = models.DateTimeField("Начало действия", auto_now_add=True)
    effective_to = models.DateTimeField("Окончание действия", blank=True, null=True)
    is_current = models.BooleanField("Актуально", default=True)
    import_batch = models.ForeignKey(
        "DataImport", related_name="observations", on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        unique_together = (("encounter", "pdwid", "effective_from"),)
        indexes = [
            models.Index(fields=["plan_year", "status"]),
            models.Index(fields=["plan_year", "is_current"]),
        ]

    def __str__(self):
        return f"Observation {self.pdwid}"


class DataImport(models.Model):
    import_date = models.DateTimeField("Дата загрузки", auto_now_add=True)
    year = models.IntegerField("Год данных")
    file_name = models.CharField("Имя файла", max_length=255)
    file_path = models.CharField("Путь к файлу", max_length=500, blank=True, null=True)
    total_rows = models.IntegerField("Всего строк в файле", default=0)
    processed_rows = models.IntegerField("Обработано строк", default=0)
    created_persons = models.IntegerField("Создано пациентов", default=0)
    updated_persons = models.IntegerField("Обновлено пациентов", default=0)
    created_encounters = models.IntegerField("Создано встреч", default=0)
    created_observations = models.IntegerField("Создано наблюдений", default=0)
    detached_patients = models.IntegerField("Откреплено пациентов", default=0)
    status = models.CharField(
        "Статус",
        max_length=20,
        default="processing",
        choices=[("processing", "Обработка"), ("completed", "Завершено"), ("error", "Ошибка")],
    )
    error_message = models.TextField("Сообщение об ошибке", blank=True, null=True)

    class Meta:
        ordering = ["-import_date"]
        verbose_name = "Загрузка данных"
        verbose_name_plural = "Загрузки данных"

    def __str__(self):
        return f"Загрузка {self.year} года от {self.import_date.strftime('%d.%m.%Y %H:%M')}"
