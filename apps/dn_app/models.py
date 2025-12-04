from django.db import models
from django.utils import timezone


class Person(models.Model):
    enp = models.CharField("Единый номер полиса", max_length=255, unique=True)
    fio = models.CharField("ФИО", max_length=255)
    dr = models.DateField("Дата рождения")
    is_detached = models.BooleanField("Откреплен", default=False, help_text="Пациент откреплен (отсутствует в последней загрузке)")
    detached_date = models.DateTimeField("Дата открепления", blank=True, null=True)
    last_import_date = models.DateTimeField("Дата последней загрузки", blank=True, null=True)

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
    STATUS_CHOICES = [
        ('planned', 'Запланирован'),
        ('completed', 'Выполнен'),
        ('not_completed', 'Не выполнен'),
        ('detached', 'Откреплен'),
    ]
    
    encounter = models.ForeignKey(Encounter, related_name="observations", on_delete=models.CASCADE)
    pdwid = models.CharField("PDWID", max_length=50)
    plan_month = models.CharField("Плановый месяц", max_length=10, blank=True, null=True)
    plan_year = models.IntegerField("Плановый год", blank=True, null=True)
    date_begin = models.DateField("Дата начала наблюдения", blank=True, null=True)
    date_end = models.DateField("Дата окончания наблюдения", blank=True, null=True)
    
    # Статус наблюдения
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='planned')
    actual_date = models.DateField("Дата фактического посещения", blank=True, null=True)
    talon_number = models.CharField("Номер талона ОМС", max_length=50, blank=True, null=True)
    
    # Поля для отслеживания истории
    effective_from = models.DateTimeField("Начало действия", auto_now_add=True)
    effective_to = models.DateTimeField("Окончание действия", blank=True, null=True)
    is_current = models.BooleanField("Актуально", default=True)
    
    # Связь с загрузкой
    import_batch = models.ForeignKey('DataImport', related_name='observations', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = (("encounter", "pdwid", "effective_from"),)
        indexes = [
            models.Index(fields=['plan_year', 'status']),
            models.Index(fields=['plan_year', 'is_current']),
        ]

    def __str__(self):
        status = "активна" if self.is_current else f"закрыта {self.effective_to}"
        return f"Observation {self.pdwid} ({self.get_status_display()}) for {self.encounter}"


class DataImport(models.Model):
    """Модель для отслеживания загрузок CSV файлов"""
    import_date = models.DateTimeField("Дата загрузки", auto_now_add=True)
    year = models.IntegerField("Год данных")
    file_name = models.CharField("Имя файла", max_length=255)
    file_path = models.CharField("Путь к файлу", max_length=500, blank=True, null=True)
    
    # Статистика загрузки
    total_rows = models.IntegerField("Всего строк в файле", default=0)
    processed_rows = models.IntegerField("Обработано строк", default=0)
    created_persons = models.IntegerField("Создано пациентов", default=0)
    updated_persons = models.IntegerField("Обновлено пациентов", default=0)
    created_encounters = models.IntegerField("Создано встреч", default=0)
    created_observations = models.IntegerField("Создано наблюдений", default=0)
    detached_patients = models.IntegerField("Откреплено пациентов", default=0)
    
    # Статус обработки
    status = models.CharField("Статус", max_length=20, default='processing', 
                              choices=[('processing', 'Обработка'), ('completed', 'Завершено'), ('error', 'Ошибка')])
    error_message = models.TextField("Сообщение об ошибке", blank=True, null=True)
    
    class Meta:
        ordering = ['-import_date']
        verbose_name = "Загрузка данных"
        verbose_name_plural = "Загрузки данных"
    
    def __str__(self):
        return f"Загрузка {self.year} года от {self.import_date.strftime('%d.%m.%Y %H:%M')}"

