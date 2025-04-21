from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # время создания
    updated_at = models.DateTimeField(auto_now_add=True)  # время последнего обновления

    class Meta:
        abstract = True


class LoadLog(models.Model):
    table_name = models.CharField(max_length=255, verbose_name="Таблица")
    start_time = models.DateTimeField(verbose_name="Время старта")
    end_time = models.DateTimeField(verbose_name="Время окончания")
    count_before = models.IntegerField(verbose_name="Количество до обновления")
    count_after = models.IntegerField(verbose_name="Количество после обновления")
    duration = models.FloatField(help_text="Длительность в секундах", verbose_name="Длительность")
    error_occurred = models.BooleanField(default=False, verbose_name="Ошибка")
    error_code = models.CharField(max_length=255, null=True, blank=True, verbose_name="Код ошибки")
    run_url = models.URLField(null=True, blank=True, verbose_name="Ссылка на запуск")

    def __str__(self):
        return f"{self.table_name} ({self.start_time.strftime('%Y-%m-%d %H:%M:%S')})"

    class Meta:
        verbose_name = "Лог загрузки"
        verbose_name_plural = "Логи загрузок"


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
    additional_diagnosis = models.CharField(max_length=1000, null=True, blank=True, default='-')
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
    # Отчетный период
    report_year = models.CharField(max_length=4, default='-')
    report_month = models.IntegerField(null=True, blank=True)

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
    additional_diagnosis = models.CharField(max_length=1000, null=True, blank=True, default='-')
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
    # Отчетный период
    report_year = models.CharField(max_length=4, default='-')
    report_month = models.IntegerField(null=True, blank=True)

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


class PopulationISZL(TimeStampedModel):
    pid = models.CharField("PID", max_length=50, unique=True)
    fio = models.CharField("FIO", max_length=255)
    dr = models.CharField("DR", max_length=50)
    smo = models.CharField("SMO", max_length=255, default='-')
    enp = models.CharField("ENP", max_length=255, unique=True)
    lpu = models.CharField("LPU", max_length=255, default='-')
    ss_doctor = models.CharField("SS_DOCTOR", max_length=255, default='-')
    lpuuch = models.CharField("LPUUCH", max_length=255, default='-')
    upd = models.CharField("Upd", max_length=255, default='-')
    closed = models.CharField("CLOSED", max_length=50, default='-')

    def __str__(self):
        return f"{self.pid} - {self.fio}"

    class Meta:
        db_table = "load_data_iszl_population"
        verbose_name = "Население ИСЗЛ"
        verbose_name_plural = "Население ИСЗЛ"


class DispanseryISZL(TimeStampedModel):
    pid = models.CharField("pID", max_length=50)
    ldwid = models.CharField("ldwID", max_length=50)
    pdwid = models.CharField("pdwID", max_length=50, unique=True)
    fio = models.CharField("FIO", max_length=255)
    dr = models.CharField("DR", max_length=50)
    ds = models.CharField("DS", max_length=50)
    date_begin = models.CharField("DateBegin", max_length=50, default='-')
    date_end = models.CharField("DateEnd", max_length=50, default='-')
    id_reason = models.CharField("idReason", max_length=50, default='-')
    name_reason = models.CharField("nameReason", max_length=255, default='-')
    plan_month = models.CharField("PlanMonth", max_length=10, default='-')
    plan_year = models.CharField("PlanYear", max_length=10, default='-')
    fam_d = models.CharField("FAM_D", max_length=100, default='-')
    im_d = models.CharField("IM_D", max_length=100, default='-')
    ot_d = models.CharField("OT_D", max_length=100, default='-')
    ss_d = models.CharField("SS_D", max_length=50, default='-')
    spec_d = models.CharField("SPEC_D", max_length=255, default='-')
    spec_v015 = models.CharField("SpecV015", max_length=50, default='-')
    date_info = models.CharField("DateInfo", max_length=50, default='-')
    way_info = models.CharField("WayInfo", max_length=255, default='-')
    res_info = models.CharField("ResInfo", max_length=255, default='-')
    fact_dn = models.CharField("FactDN", max_length=255, default='-')
    rezult_dn = models.CharField("RezultDN", max_length=255, default='-')
    adr = models.CharField("ADR", max_length=255, default='-')
    enp = models.CharField("ENP", max_length=255, default='-')
    lpu = models.CharField("LPU", max_length=255, default='-')
    fio_doctor = models.CharField("FIO_DOCTOR", max_length=255, default='-')
    ss_doctor = models.CharField("SS_DOCTOR", max_length=50, default='-')
    lpuuch = models.CharField("LPUUCH", max_length=255, default='-')
    smo = models.CharField("SMO", max_length=50, default='-')
    lpuauto = models.CharField("LPUAUTO", max_length=50, default='-')
    lpudt = models.CharField("LPUDT", max_length=50, default='-')
    user_update_list = models.CharField("UserUpdateList", max_length=50, default='-')
    date_update_list = models.CharField("DateUpdateList", max_length=50, default='-')
    user_update_plan = models.CharField("UserUpdatePlan", max_length=50, default='-')
    date_update_plan = models.CharField("DateUpdatePlan", max_length=50, default='-')
    period_w = models.CharField("PeriodW", max_length=50, default='-')
    date_prev = models.CharField("DatePrev", max_length=50, default='-')
    place_w = models.CharField("PlaceW", max_length=50, default='-')
    w = models.CharField("w", max_length=50, default='-')
    unemp = models.CharField("UNEMP", max_length=50, default='-')

    def __str__(self):
        return f"{self.pid} - {self.fio}"

    class Meta:
        db_table = "load_data_dispansery_iszl"
        verbose_name = "Диспансерное ИСЗЛ"
        verbose_name_plural = "Диспансерное ИСЗЛ"


class ElectronicMedicalDocument(TimeStampedModel):
    epmd_id = models.CharField('ИД', max_length=255, unique=True)
    original_epmz_id = models.CharField('ИД исходного ЭПМЗ', max_length=255, default='-')
    document_date = models.CharField('Дата документа', max_length=255, default='-')
    document_type = models.CharField('Тип документа', max_length=255, default='-')
    doctor = models.CharField('Врач', max_length=255, default='-')
    branch = models.CharField('Обособленное подразделение', max_length=255, default='-')
    subdivision = models.CharField('Подразделение', max_length=255, default='-')
    patient = models.CharField('Пациент', max_length=255, default='-')
    formation_date = models.CharField('Дата формирования электронного документа', max_length=255, default='-')
    doctor_signature = models.CharField('Наличие подписи врача', max_length=50, default='-')
    organization_signature = models.CharField('Наличие подписи МО', max_length=50, default='-')
    sending_date = models.CharField('Дата отправки в РИР.РЭМД', max_length=255, default='-')
    sending_status = models.CharField('Статус отправки в РИР.РЭМД', max_length=255, default='-')
    registration_number = models.CharField('Регистрационный номер', max_length=255, default='-')
    status_details = models.TextField('Детали статуса отправки', default='-')

    def __str__(self):
        return f"{self.epmd_id} - {self.patient}"

    class Meta:
        db_table = 'load_data_emd'
        verbose_name = 'Электронный медицинский документ'
        verbose_name_plural = 'Электронные медицинские документы'


class Recipe(TimeStampedModel):
    number = models.CharField("Номер", max_length=255, unique=True)
    series = models.CharField("Серия", max_length=255, default="-")
    recipe_type = models.CharField("Тип рецепта", max_length=255, default="-")
    date = models.CharField("Дата", max_length=255, default="-")  # можно заменить на DateField при необходимости
    digital_signature = models.CharField("ЭЦП", max_length=255, default="-")
    signature_owner = models.CharField("Владелец подписи", max_length=255, default="-")
    organization = models.CharField("Организация", max_length=255, default="-")
    subdivision = models.CharField("Подразделение", max_length=255, default="-")
    sending_status_rir_farm = models.CharField("Статус отправки РИР/ФАРМ", max_length=255, default="-")
    additional_status_info_rir = models.TextField("Дополнительная информация по статусу отправки в РИР", default="-")
    status = models.CharField("Статус", max_length=255, default="-")
    status_change_date = models.CharField("Дата изменения статуса", max_length=255, default="-")
    status_author = models.CharField("Автор статуса", max_length=255, default="-")
    first_er_status = models.CharField("1ЭР (статус отправки)", max_length=255, default="-")
    emd_verification = models.CharField("Верификация ЭМД", max_length=255, default="-")
    sending_status_remd = models.CharField("Статус отправки в РЭМД", max_length=255, default="-")
    additional_status_info_remd = models.TextField("Дополнительная информация по статусу отправки в РЭМД", default="-")
    validity_period = models.CharField("Срок действия", max_length=255, default="-")
    patient_full_name = models.CharField("Ф.И.О. пациента", max_length=255, default="-")
    patient_birth_date = models.CharField("Дата рождения пациента", max_length=255, default="-")
    patient_snils = models.CharField("СНИЛС пациента", max_length=255, default="-")
    diagnosis_code = models.CharField("Код диагноза", max_length=255, default="-")
    diagnosis_name = models.CharField("Название диагноза", max_length=255, default="-")
    benefit_category_name = models.CharField("Название льготной категории", max_length=255, default="-")
    benefit_category_type = models.CharField("Тип льготной категории", max_length=255, default="-")
    financing_source = models.CharField("Источник финансирования", max_length=255, default="-")
    doctor_full_name = models.CharField("Ф.И.О. врача", max_length=255, default="-")
    doctor_position = models.CharField("Должность врача", max_length=255, default="-")
    medicinal_product = models.TextField("Лекарственный препарат", default="-")
    trn = models.TextField("ТРН", default="-")
    inn = models.TextField("МНН", default="-")
    quantity_total_prescribed = models.CharField("Кол-во/Всего назначено", max_length=255, default="-")
    payment_percentage = models.CharField("Процент оплаты", max_length=255, default="-")

    def __str__(self):
        return f"{self.number} - {self.patient_full_name}"

    class Meta:
        db_table = "load_data_recipes"
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class MortalityRecord(TimeStampedModel):
    series = models.CharField("Серия", max_length=255, default="-")
    number = models.CharField("Номер", max_length=255, default="-")
    damaged = models.CharField("ИСПОРЧЕНО", max_length=255, default="-")
    duplicate = models.CharField("Дубликат", max_length=255, default="-")
    perinatal = models.CharField("Перинатальная", max_length=255, default="-")
    issue_date = models.CharField("Дата выдачи", max_length=255, default="-")
    mortality_type = models.CharField("Тип", max_length=255, default="-")
    emd_sending_date = models.CharField("Дата отправки ЭМД", max_length=255, default="-")
    emd_sending_status = models.CharField("Статус отправки ЭМД", max_length=255, default="-")
    emd_error = models.TextField("ЭМД ошибка", default="-")
    creator = models.CharField("Создавший", max_length=255, default="-")
    doctor = models.CharField("Врач", max_length=255, default="-")
    deceased_full_name = models.CharField("ФИО умершего(ей)", max_length=255, default="-")
    birth_date = models.CharField("Дата рождения", max_length=255, default="-")
    death_date = models.CharField("Дата смерти", max_length=255, default="-")
    gender = models.CharField("Пол", max_length=255, default="-")
    age = models.CharField("Возраст, лет", max_length=255, default="-")
    initial_statistic = models.CharField("Первоначальная (статистика)", max_length=255, default="-")
    reason_a = models.CharField("Причина (а)", max_length=255, default="-")
    reason_b = models.CharField("Причина (б)", max_length=255, default="-")
    reason_c = models.CharField("Причина (в)", max_length=255, default="-")
    reason_d = models.CharField("Причина (г)", max_length=255, default="-")
    region = models.CharField("Регион", max_length=255, default="-")
    district = models.CharField("Район", max_length=255, default="-")
    city_or_locality = models.CharField("Город / Населенный пункт", max_length=255, default="-")
    street = models.CharField("Улица", max_length=255, default="-")
    house = models.CharField("Дом", max_length=255, default="-")
    apartment = models.CharField("Квартира", max_length=255, default="-")
    attachment = models.CharField("Прикрепление", max_length=255, default="-")

    def __str__(self):
        return f"{self.number} - {self.deceased_full_name}"

    class Meta:
        db_table = "load_data_death"
        verbose_name = "Смертность"
        verbose_name_plural = "Смертность"
        unique_together = (("series", "number"),)


class Reference(TimeStampedModel):
    series_number = models.CharField("Серия и номер справки", max_length=255, unique=True)
    issue_date = models.CharField("Дата выдачи", max_length=255, default="-")
    full_name = models.CharField("ФИО", max_length=255, default="-")
    birth_date = models.CharField("Дата рождения", max_length=255, default="-")
    doctor = models.CharField("Врач", max_length=255, default="-")
    organization = models.CharField("Организация выдавшая документ", max_length=255, default="-")
    reference_type = models.CharField("Вид справки", max_length=255, default="-")
    conclusion = models.CharField("Заключение", max_length=255, default="-")
    status = models.CharField("Статус", max_length=255, default="-")
    errors = models.TextField("Ошибки по справке", default="-")

    def __str__(self):
        return f"{self.series_number} - {self.full_name}"

    class Meta:
        db_table = 'load_data_reference'
        verbose_name = 'Справка'
        verbose_name_plural = 'Справки'


class Doctor(TimeStampedModel):
    snils = models.CharField("СНИЛС", max_length=255)
    doctor_code = models.CharField("Код врача", max_length=255, default="-")
    last_name = models.CharField("Фамилия", max_length=255, default="-")
    first_name = models.CharField("Имя", max_length=255, default="-")
    middle_name = models.CharField("Отчество", max_length=255, default="-")
    birth_date = models.CharField("Дата рождения", max_length=255, default="-")
    gender = models.CharField("Пол", max_length=255, default="-")
    start_date = models.CharField("Дата начала работы", max_length=255, default="-")
    end_date = models.CharField("Дата окончания работы", max_length=255, default="-")
    department = models.CharField("Структурное подразделение", max_length=255, default="-")
    medical_profile_code = models.CharField("Код профиля медпомощи", max_length=255, default="-")
    specialty_code = models.CharField("Код специальности", max_length=255, default="-")
    department_code = models.CharField("Код отделения", max_length=255, default="-")
    comment = models.CharField("Комментарий", max_length=255, default="-")

    def __str__(self):
        return f"{self.doctor_code} - {self.last_name}"

    class Meta:
        db_table = 'load_data_doctor'
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'
        constraints = [
            models.UniqueConstraint(fields=['snils', 'doctor_code'], name='unique_snils_code_doctor')
        ]


class TalonRefusal(TimeStampedModel):
    """
    Модель для хранения отказов в талонах.
    is_fixed - показывает, был ли талон исправлен (True/False)
    """
    source = models.CharField(max_length=255, default='-', verbose_name="Источник")
    error = models.CharField(max_length=255, default='-', unique=True, verbose_name="Ошибка")
    error_status = models.CharField(max_length=255, default='-', verbose_name="Статус ошибки")
    talon_status = models.CharField(max_length=255, default='-', verbose_name="Статус талона")
    talon = models.CharField(max_length=255, default='-', verbose_name="Талон")
    talon_type = models.CharField(max_length=255, default='-', verbose_name="Тип талона")
    goal = models.CharField(max_length=255, default='-', verbose_name="Цель")
    error_type = models.CharField(max_length=255, default='-', verbose_name="Тип ошибки")
    patient = models.CharField(max_length=255, default='-', verbose_name="Пациент")
    birth_date = models.CharField(max_length=255, default='-', verbose_name="Дата рождения")
    treatment_start = models.CharField(max_length=255, default='-', verbose_name="Начало лечения")
    treatment_end = models.CharField(max_length=255, default='-', verbose_name="Окончание лечения")
    insurance = models.CharField(max_length=255, default='-', verbose_name="Страховая")
    enp = models.CharField(max_length=255, default='-', verbose_name="ЕНП")
    operator = models.CharField(max_length=255, default='-', verbose_name="Оператор")
    doctor = models.CharField(max_length=255, default='-', verbose_name="Врач")
    department = models.CharField(max_length=255, default='-', verbose_name="Подразделение")
    tfoms_error_code = models.CharField(max_length=255, default='-', verbose_name="Код ошибки ТФОМС")
    tfoms_error_text = models.TextField(default='-', verbose_name="Текст ошибки ТФОМС")
    tfoms_error_extra = models.CharField(max_length=500, default='-', verbose_name="Доп.инф. к ошибке ТФОМС")
    field_with_error = models.CharField(max_length=255, default='-', verbose_name="Поле с ошибкой")
    base_element = models.CharField(max_length=255, default='-', verbose_name="Базовый элемент")
    sanctions_amount = models.CharField(max_length=255, default='-', verbose_name="Сумма санкций")
    source_file = models.CharField(max_length=255, default='-', verbose_name="Исходный файл с загрузкой")
    account_number = models.CharField(max_length=255, default='-', verbose_name="Номер счета")
    account_date = models.CharField(max_length=255, default='-', verbose_name="Дата счета")
    edit_date = models.CharField(max_length=255, default='-', verbose_name="Дата редактирования")

    # Поле для отметки исправления
    is_fixed = models.BooleanField(default=False, verbose_name="Исправлено")

    def __str__(self):
        return f"{self.talon} - {self.error}"

    class Meta:
        db_table = "load_data_error_log_talon"
        verbose_name = "Отказ в талоне"
        verbose_name_plural = "Отказы в талонах"


class DetailedMedicalExamination(TimeStampedModel):
    """
    Модель для хранения детализации диспансеризации.
    """
    talon_number = models.CharField(max_length=255, default='-', verbose_name="Номер талона")
    account = models.CharField(max_length=255, default='-', verbose_name="Счет")
    upload_date = models.CharField(max_length=255, default='-', verbose_name="Дата выгрузки")
    status = models.CharField(max_length=255, default='-', verbose_name="Статус")
    mo = models.CharField(max_length=255, default='-', verbose_name="МО")
    start_date = models.CharField(max_length=255, default='-', verbose_name="Дата начала")
    end_date = models.CharField(max_length=255, default='-', verbose_name="Дата окончания")
    policy_series = models.CharField(max_length=255, default='-', verbose_name="Серия полиса")
    policy_number = models.CharField(max_length=255, default='-', verbose_name="Номер полиса")
    enp = models.CharField(max_length=255, default='-', verbose_name="ЕНП")
    last_name = models.CharField(max_length=255, default='-', verbose_name="Фамилия")
    first_name = models.CharField(max_length=255, default='-', verbose_name="Имя")
    middle_name = models.CharField(max_length=255, default='-', verbose_name="Отчество")
    insurance_org = models.CharField(max_length=255, default='-', verbose_name="Страховая организация")
    gender = models.CharField(max_length=255, default='-', verbose_name="Пол")
    birth_date = models.CharField(max_length=255, default='-', verbose_name="Дата рождения")
    talon_type = models.CharField(max_length=255, default='-', verbose_name="Тип талона")
    main_diagnosis = models.CharField(max_length=255, default='-', verbose_name="Основной диагноз")
    additional_diagnosis = models.CharField(max_length=1000, default='-', verbose_name="Сопутствующий диагноз")
    health_group = models.CharField(max_length=255, default='-', verbose_name="Группа здоровья")
    doctor_code = models.CharField(max_length=255, default='-', verbose_name="Доктор (Код)")
    doctor_fio = models.CharField(max_length=255, default='-', verbose_name="Доктор (ФИО)")
    cost = models.CharField(max_length=255, default='-', verbose_name="Стоимость")
    service_name = models.CharField(max_length=255, default='-', verbose_name="Название услуги")
    service_nomenclature = models.CharField(max_length=255, default='-', verbose_name="Номенклатурный код услуги")
    doctor_services_code = models.CharField(max_length=255, default='-', verbose_name="Доктор-Услуги (Код)")
    doctor_services_fio = models.CharField(max_length=255, default='-', verbose_name="Доктор-Услуги (ФИО)")
    service_date = models.CharField(max_length=255, default='-', verbose_name="Дата-Услуги")
    service_status = models.CharField(max_length=255, default='-', verbose_name="Статус-Услуги")
    route = models.CharField(max_length=255, default='-', verbose_name="Маршрут")
    service_department = models.CharField(max_length=255, default='-', verbose_name="Подразделение врача-Услуги")
    mo_code_other = models.CharField(max_length=255, default='-', verbose_name="Код МО (при оказ.услуги в другой МО)")

    def __str__(self):
        return f"{self.talon_number} - {self.account}"

    class Meta:
        db_table = "load_data_detailed_medical_examination"
        verbose_name = "Детализация диспансеризации"
        verbose_name_plural = "Детализации диспансеризации"
        unique_together = (("talon_number", "service_nomenclature"),)


class JournalAppeals(models.Model):
    # Поля для данных пациента
    patient_last_name = models.CharField("Фамилия пациента", max_length=255, default='-')
    patient_first_name = models.CharField("Имя пациента", max_length=255, default='-')
    patient_middle_name = models.CharField("Отчество пациента", max_length=255, default='-')
    birth_date = models.CharField("Дата рождения", max_length=50, default='-')
    gender = models.CharField("Пол", max_length=50, default='-')
    phone = models.CharField("Телефон", max_length=50, default='-')
    enp = models.CharField("ЕНП", max_length=255, default='-')
    attachment = models.CharField("Прикрепление", max_length=255, default='-')
    series = models.CharField("Серия", max_length=50, default='-')
    number = models.CharField("Номер", max_length=50, default='-')

    # Поля для данных о сотруднике (расписании)
    employee_last_name = models.CharField("Фамилия сотрудника", max_length=255, default='-')
    employee_first_name = models.CharField("Имя сотрудника", max_length=255, default='-')
    employee_middle_name = models.CharField("Отчество сотрудника", max_length=255, default='-')
    position = models.CharField("Должность", max_length=255, default='-')
    acceptance_date = models.CharField("Дата приема", max_length=50, default='-')
    record_date = models.CharField("Дата записи", max_length=50, default='-')
    schedule_type = models.CharField("Тип расписания", max_length=255, default='-')
    record_source = models.CharField("Источник записи", max_length=255, default='-')
    department = models.CharField("Подразделение", max_length=255, default='-')
    creator = models.CharField("Создавший", max_length=255, default='-')
    no_show = models.CharField("Не явился", max_length=50, default='-')
    epmz = models.CharField("ЭПМЗ", max_length=255, default='-')

    def __str__(self):
        return f"{self.patient_last_name} {self.patient_first_name} - {self.enp}"

    class Meta:
        db_table = "load_data_journal_appeals"
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        unique_together = (("enp", "employee_last_name", "acceptance_date"),)
