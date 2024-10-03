from django.db import models


class OMSSettings(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "ОМС: Настройка"
        verbose_name_plural = "ОМС: Настройки"


class OMSData(models.Model):
    talon = models.CharField(max_length=255, unique=True)  # "Талон"
    source = models.CharField(max_length=255)  # "Источник"
    source_id = models.CharField(max_length=255)  # "ID источника"
    account_number = models.CharField(max_length=255)  # "Номер счёта"
    upload_date = models.CharField(max_length=255)  # "Дата выгрузки"
    cancellation_reason = models.CharField(max_length=255, null=True, blank=True)  # "Причина аннулирования"
    status = models.CharField(max_length=255)  # "Статус"
    talon_type = models.CharField(max_length=255)  # "Тип талона"
    goal = models.CharField(max_length=255, null=True, blank=True)  # "Цель"
    federal_goal = models.CharField(max_length=255, null=True, blank=True)  # "Фед. цель"
    patient = models.CharField(max_length=255)  # "Пациент"
    birth_date = models.CharField(max_length=255)  # "Дата рождения"
    age = models.CharField(max_length=255)  # "Возраст"
    gender = models.CharField(max_length=50)  # "Пол"
    policy = models.CharField(max_length=255)  # "Полис"
    smo_code = models.CharField(max_length=255)  # "Код СМО"
    insurance = models.CharField(max_length=255)  # "Страховая"
    enp = models.CharField(max_length=255)  # "ЕНП"
    treatment_start = models.CharField(max_length=255)  # "Начало лечения"
    treatment_end = models.CharField(max_length=255)  # "Окончание лечения"
    doctor = models.CharField(max_length=255)  # "Врач"
    doctor_profile = models.CharField(max_length=255)  # "Врач (Профиль МП)"
    staff_position = models.CharField(max_length=255)  # "Должность мед.персонала (V021)"
    department = models.CharField(max_length=255)  # "Подразделение"
    care_conditions = models.CharField(max_length=255)  # "Условия оказания помощи"
    medical_assistance_type = models.CharField(max_length=255)  # "Вид мед. помощи"
    disease_type = models.CharField(max_length=255)  # "Тип заболевания"
    main_disease_character = models.CharField(max_length=255)  # "Характер основного заболевания"
    visits = models.CharField(max_length=255)  # "Посещения"
    mo_visits = models.CharField(max_length=255)  # "Посещения в МО"
    home_visits = models.CharField(max_length=255)  # "Посещения на Дому"
    case = models.CharField(max_length=255)  # "Случай"
    main_diagnosis = models.CharField(max_length=255)  # "Диагноз основной (DS1)"
    additional_diagnosis = models.CharField(max_length=500, null=True, blank=True)  # "Сопутствующий диагноз (DS2)"
    mp_profile = models.CharField(max_length=255)  # "Профиль МП"
    bed_profile = models.CharField(max_length=255)  # "Профиль койки"
    dispensary_monitoring = models.CharField(max_length=255)  # "Диспансерное наблюдение"
    specialty = models.CharField(max_length=255)  # "Специальность"
    outcome = models.CharField(max_length=255)  # "Исход"
    result = models.CharField(max_length=255)  # "Результат"
    operator = models.CharField(max_length=255)  # "Оператор"
    initial_input_date = models.CharField(max_length=255)  # "Первоначальная дата ввода"
    last_change_date = models.CharField(max_length=255)  # "Дата последнего изменения"
    tariff = models.CharField(max_length=255)  # "Тариф"
    amount = models.CharField(max_length=255)  # "Сумма"
    paid = models.CharField(max_length=255)  # "Оплачено"
    payment_type = models.CharField(max_length=255)  # "Тип оплаты"
    sanctions = models.CharField(max_length=255, null=True, blank=True)  # "Санкции"
    ksg = models.CharField(max_length=255, null=True, blank=True)  # "КСГ"
    kz = models.CharField(max_length=255, null=True, blank=True)  # "КЗ"
    therapy_schema_code = models.CharField(max_length=255, null=True, blank=True)  # "Код схемы лекарственной терапии"
    uet = models.CharField(max_length=255, null=True, blank=True)  # "УЕТ"
    classification_criterion = models.CharField(max_length=255, null=True, blank=True)  # "Классификационный критерий"
    shrm = models.CharField(max_length=255, null=True, blank=True)  # "ШРМ"
    directing_mo = models.CharField(max_length=255, null=True, blank=True)  # "МО, направившая"
    payment_method_code = models.CharField(max_length=255, null=True, blank=True)  # "Код способа оплаты"
    newborn = models.CharField(max_length=255, null=True, blank=True)  # "Новорожденный"
    representative = models.CharField(max_length=255, null=True, blank=True)  # "Представитель"
    additional_status_info = models.CharField(max_length=255, null=True, blank=True)  # "Доп. инф. о статусе талона"
    kslp = models.CharField(max_length=255, null=True, blank=True)  # "КСЛП"
    payment_source = models.CharField(max_length=255, null=True, blank=True)  # "Источник оплаты"
    report_period = models.CharField(max_length=255)  # "Отчетный период выгрузки"

    def __str__(self):
        return f"{self.talon} - {self.patient}"

    class Meta:
        verbose_name = "ОМС: Талон"
        verbose_name_plural = "ОМС: Талоны"


class DoctorData(models.Model):
    snils = models.CharField(max_length=255, verbose_name="СНИЛС")
    doctor_code = models.CharField(max_length=255, verbose_name="Код врача")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    middle_name = models.CharField(max_length=255, verbose_name="Отчество")
    birth_date = models.CharField(max_length=255, verbose_name="Дата рождения")
    gender = models.CharField(max_length=255, verbose_name="Пол")
    start_date = models.CharField(max_length=255, verbose_name="Дата начала работы")
    end_date = models.CharField(max_length=255, verbose_name="Дата окончания работы")
    department = models.CharField(max_length=255, verbose_name="Структурное подразделение")
    medical_profile_code = models.CharField(max_length=255, verbose_name="Код профиля медпомощи")
    specialty_code = models.CharField(max_length=255, verbose_name="Код специальности")
    department_code = models.CharField(max_length=255, verbose_name="Код отделения")
    comment = models.CharField(max_length=255, verbose_name="Комментарий")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.doctor_code})"

    class Meta:
        verbose_name = "ОМС: Врач"
        verbose_name_plural = "ОМС: Врачи"


class DetailedData(models.Model):
    talon_number = models.CharField(max_length=255, verbose_name="Номер талона")
    account_number = models.CharField(max_length=255, verbose_name="Счет")
    upload_date = models.CharField(max_length=255, verbose_name="Дата выгрузки")
    status = models.CharField(max_length=255, verbose_name="Статус")
    mo = models.CharField(max_length=255, verbose_name="МО")
    start_date = models.CharField(max_length=255, verbose_name="Дата начала")
    end_date = models.CharField(max_length=255, verbose_name="Дата окончания")
    policy_series = models.CharField(max_length=255, verbose_name="Серия полиса")
    policy_number = models.CharField(max_length=255, verbose_name="Номер полиса")
    enp = models.CharField(max_length=255, verbose_name="ЕНП")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    middle_name = models.CharField(max_length=255, verbose_name="Отчество")
    insurance_org = models.CharField(max_length=255, verbose_name="Страховая организация")
    gender = models.CharField(max_length=255, verbose_name="Пол")
    birth_date = models.CharField(max_length=255, verbose_name="Дата рождения")
    talon_type = models.CharField(max_length=255, verbose_name="Тип талона")
    main_diagnosis = models.CharField(max_length=255, verbose_name="Основной диагноз")
    additional_diagnosis = models.CharField(max_length=255, verbose_name="Сопутствующий диагноз")
    health_group = models.CharField(max_length=255, verbose_name="Группа здоровья")
    doctor_code = models.CharField(max_length=255, verbose_name="Доктор (Код)")
    doctor_name = models.CharField(max_length=255, verbose_name="Доктор (ФИО)")
    cost = models.CharField(max_length=255, verbose_name="Стоимость")
    service_name = models.CharField(max_length=255, verbose_name="Название услуги")
    service_code = models.CharField(max_length=255, verbose_name="Номенклатурный код услуги")
    service_doctor_code = models.CharField(max_length=255, verbose_name="Доктор-Услуги (Код)")
    service_doctor_name = models.CharField(max_length=255, verbose_name="Доктор-Услуги (ФИО)")
    service_date = models.CharField(max_length=255, verbose_name="Дата-Услуги")
    service_status = models.CharField(max_length=255, verbose_name="Статус-Услуги")
    route = models.CharField(max_length=255, verbose_name="Маршрут")
    service_department = models.CharField(max_length=255, verbose_name="Подразделение врача-Услуги")
    external_mo_code = models.CharField(max_length=255, verbose_name="Код МО (при оказ.услуги в другой МО)")

    def __str__(self):
        return f"{self.talon_number} - {self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "ОМС: Детализация"
        verbose_name_plural = "ОМС: Детализация"


class DataImport(models.Model):
    csv_file = models.FileField(upload_to='oms_data_imports/', verbose_name="CSV файл", blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    added_count = models.IntegerField(default=0, verbose_name="Количество добавленных записей")
    updated_count = models.IntegerField(default=0, verbose_name="Количество обновленных записей")
    error_count = models.IntegerField(default=0, verbose_name="Количество ошибок")
    type = models.CharField(max_length=20, verbose_name="Тип данных")
    category = models.CharField(max_length=255, verbose_name="Категория")

    def __str__(self):
        return f"Импорт {self.type} от {self.date_added}"

    class Meta:
        verbose_name = "Импорт данных"
        verbose_name_plural = "Импорт данных"
