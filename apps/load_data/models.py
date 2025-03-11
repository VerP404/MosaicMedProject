from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # время создания
    updated_at = models.DateTimeField(auto_now_add=True)  # время последнего обновления

    class Meta:
        abstract = True


class Talon(TimeStampedModel):
    # Модель для обычных талонов (не комплексных)
    talon = models.CharField(max_length=255)
    report_period = models.CharField(max_length=255, default='-')
    source = models.CharField(max_length=255, default='-')
    account_number = models.CharField(max_length=255, default='-')
    upload_date = models.CharField(max_length=255, default='-')
    status = models.CharField(max_length=255, default='-')
    talon_type = models.CharField(max_length=255, default='-')
    goal = models.CharField(max_length=255, null=True, blank=True, default='-')
    patient = models.CharField(max_length=255, default='-')
    birth_date = models.CharField(max_length=255, default='-')
    gender = models.CharField(max_length=50, default='-')
    policy = models.CharField(max_length=255, default='-')
    smo_code = models.CharField(max_length=255, default='-')
    enp = models.CharField(max_length=255, default='-')
    treatment_start = models.CharField(max_length=255, default='-')
    treatment_end = models.CharField(max_length=255, default='-')
    doctor = models.CharField(max_length=255, default='-')
    doctor_profile = models.CharField(max_length=255, default='-')
    staff_position = models.CharField(max_length=255, default='-')
    department = models.CharField(max_length=255, default='-')
    care_conditions = models.CharField(max_length=255, default='-')
    medical_assistance_type = models.CharField(max_length=255, default='-')
    disease_type = models.CharField(max_length=255, default='-')
    main_disease_character = models.CharField(max_length=255, default='-')
    visits = models.CharField(max_length=255, default='-')
    mo_visits = models.CharField(max_length=255, default='-')
    home_visits = models.CharField(max_length=255, default='-')
    case_code = models.CharField(max_length=255, default='-')
    main_diagnosis = models.CharField(max_length=255, default='-')
    additional_diagnosis = models.CharField(max_length=500, null=True, blank=True, default='-')
    mp_profile = models.CharField(max_length=255, default='-')
    bed_profile = models.CharField(max_length=255, default='-')
    dispensary_monitoring = models.CharField(max_length=255, default='-')
    specialty = models.CharField(max_length=255, default='-')
    outcome = models.CharField(max_length=255, default='-')
    result = models.CharField(max_length=255, default='-')
    operator = models.CharField(max_length=255, default='-')
    initial_input_date = models.CharField(max_length=255, default='-')
    last_change_date = models.CharField(max_length=255, default='-')
    amount = models.CharField(max_length=255, default='-')
    sanctions = models.CharField(max_length=255, null=True, blank=True, default='-')
    ksg = models.CharField(max_length=255, null=True, blank=True, default='-')
    uet = models.CharField(max_length=255, null=True, blank=True, default='-')
    additional_status_info = models.CharField(max_length=1500, null=True, blank=True, default='-')

    # Поле is_complex всегда False для этой модели
    is_complex = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.talon} - {self.patient}"

    class Meta:
        db_table = "load_data_talons"
        verbose_name = "ОМС: Талон"
        verbose_name_plural = "ОМС: Талоны"
        unique_together = (("talon", "source"),)


class ComplexTalon(TimeStampedModel):
    # Модель для комплексных талонов
    talon = models.CharField(max_length=255)
    report_period = models.CharField(max_length=255, default='-')
    source = models.CharField(max_length=255, default='-')
    account_number = models.CharField(max_length=255, default='-')
    upload_date = models.CharField(max_length=255, default='-')
    status = models.CharField(max_length=255, default='-')
    talon_type = models.CharField(max_length=255, default='-')
    goal = models.CharField(max_length=255, null=True, blank=True, default='-')
    patient = models.CharField(max_length=255, default='-')
    birth_date = models.CharField(max_length=255, default='-')
    gender = models.CharField(max_length=50, default='-')
    policy = models.CharField(max_length=255, default='-')
    smo_code = models.CharField(max_length=255, default='-')
    enp = models.CharField(max_length=255, default='-')
    treatment_start = models.CharField(max_length=255, default='-')
    treatment_end = models.CharField(max_length=255, default='-')
    doctor = models.CharField(max_length=255, default='-')
    doctor_profile = models.CharField(max_length=255, default='-')
    staff_position = models.CharField(max_length=255, default='-')
    department = models.CharField(max_length=255, default='-')
    care_conditions = models.CharField(max_length=255, default='-')
    medical_assistance_type = models.CharField(max_length=255, default='-')
    disease_type = models.CharField(max_length=255, default='-')
    main_disease_character = models.CharField(max_length=255, default='-')
    visits = models.CharField(max_length=255, default='-')
    mo_visits = models.CharField(max_length=255, default='-')
    home_visits = models.CharField(max_length=255, default='-')
    case_code = models.CharField(max_length=255, default='-')
    main_diagnosis = models.CharField(max_length=255, default='-')
    additional_diagnosis = models.CharField(max_length=500, null=True, blank=True, default='-')
    mp_profile = models.CharField(max_length=255, default='-')
    bed_profile = models.CharField(max_length=255, default='-')
    dispensary_monitoring = models.CharField(max_length=255, default='-')
    specialty = models.CharField(max_length=255, default='-')
    outcome = models.CharField(max_length=255, default='-')
    result = models.CharField(max_length=255, default='-')
    operator = models.CharField(max_length=255, default='-')
    initial_input_date = models.CharField(max_length=255, default='-')
    last_change_date = models.CharField(max_length=255, default='-')
    amount = models.CharField(max_length=255, default='-')
    sanctions = models.CharField(max_length=255, null=True, blank=True, default='-')
    ksg = models.CharField(max_length=255, null=True, blank=True, default='-')
    uet = models.CharField(max_length=255, null=True, blank=True, default='-')
    additional_status_info = models.CharField(max_length=1500, null=True, blank=True, default='-')

    # Поле is_complex всегда True для этой модели
    is_complex = models.BooleanField(default=True)

    def __str__(self):
        return f"Complex: {self.talon} - {self.patient}"

    class Meta:
        db_table = "load_data_complex_talons"
        verbose_name = "ОМС: Комплексный талон"
        verbose_name_plural = "ОМС: Комплексные талоны"
        unique_together = (("talon", "source", "doctor"),)


class SickLeaveSheet(TimeStampedModel):
    number = models.CharField("Номер", max_length=255, unique=True)
    eln = models.CharField("ЭЛН", max_length=255)
    duplicate = models.CharField("Дубликат", max_length=255)
    status = models.CharField("Статус", max_length=255)
    fss_status = models.CharField("Статус ФСС", max_length=255)
    issue_date = models.CharField("Дата выдачи", max_length=255)
    first = models.CharField("Первичный", max_length=255)
    previous_ln = models.CharField("Предыдущий ЛН", max_length=255)
    next_ln = models.CharField("Следущий ЛН", max_length=255)
    patient_last_name = models.CharField("Фамилия пациента", max_length=255)
    patient_first_name = models.CharField("Имя пациента", max_length=255)
    patient_middle_name = models.CharField("Отчество пациента", max_length=255)
    birth_date = models.CharField("Дата рождения", max_length=255)
    gender = models.CharField("Пол", max_length=255)
    snils = models.CharField("СНИЛС", max_length=255)
    age = models.CharField("Возраст", max_length=255)
    workplace = models.CharField("Место работы", max_length=255)
    incapacity_reason_code = models.CharField("Код причины нетрудоспособности", max_length=255)
    mkb = models.CharField("МКБ", max_length=255)
    incapacity_start_date = models.CharField("Период нетрудоспособности: дата начала", max_length=255)
    incapacity_end_date = models.CharField("Период нетрудоспособности: дата окончания", max_length=255)
    days_count = models.CharField("Количество дней", max_length=255)
    tvsp = models.CharField("ТВСП", max_length=255)
    issuing_doctor = models.CharField("Выдавший врач", max_length=255)
    closing_doctor = models.CharField("Закрывший врач", max_length=255)
    closing_date = models.CharField("Дата закрытия", max_length=255)
    history_number = models.CharField("№ истории болезни", max_length=255)
    patient_care = models.CharField("Уход за больными", max_length=255)

    class Meta:
        db_table = "load_data_sick_leave_sheets"
        verbose_name = "Лист нетрудоспособности"
        verbose_name_plural = "Листы нетрудоспособности"

    def __str__(self):
        return f"{self.number} - {self.patient_last_name} {self.patient_first_name}"
