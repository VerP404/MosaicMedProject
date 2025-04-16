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
    source = models.CharField(max_length=255, default='-')  # "Источник"
    source_id = models.CharField(max_length=255, default='-')  # "ID источника"
    account_number = models.CharField(max_length=255, default='-')  # "Номер счёта"
    upload_date = models.CharField(max_length=255, default='-')  # "Дата выгрузки"
    cancellation_reason = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Причина аннулирования"
    status = models.CharField(max_length=255, default='-')  # "Статус"
    talon_type = models.CharField(max_length=255, default='-')  # "Тип талона"
    goal = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Цель"
    federal_goal = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Фед. цель"
    patient = models.CharField(max_length=255, default='-')  # "Пациент"
    birth_date = models.CharField(max_length=255, default='-')  # "Дата рождения"
    age = models.CharField(max_length=255, default='-')  # "Возраст"
    gender = models.CharField(max_length=50, default='-')  # "Пол"
    policy = models.CharField(max_length=255, default='-')  # "Полис"
    smo_code = models.CharField(max_length=255, default='-')  # "Код СМО"
    insurance = models.CharField(max_length=255, default='-')  # "Страховая"
    enp = models.CharField(max_length=255, default='-')  # "ЕНП"
    treatment_start = models.CharField(max_length=255, default='-')  # "Начало лечения"
    treatment_end = models.CharField(max_length=255, default='-')  # "Окончание лечения"
    doctor = models.CharField(max_length=255, default='-')  # "Врач"
    doctor_profile = models.CharField(max_length=255, default='-')  # "Врач (Профиль МП)"
    staff_position = models.CharField(max_length=255, default='-')  # "Должность мед.персонала (V021)"
    department = models.CharField(max_length=255, default='-')  # "Подразделение"
    care_conditions = models.CharField(max_length=255, default='-')  # "Условия оказания помощи"
    medical_assistance_type = models.CharField(max_length=255, default='-')  # "Вид мед. помощи"
    disease_type = models.CharField(max_length=255, default='-')  # "Тип заболевания"
    main_disease_character = models.CharField(max_length=255, default='-')  # "Характер основного заболевания"
    visits = models.CharField(max_length=255, default='-')  # "Посещения"
    mo_visits = models.CharField(max_length=255, default='-')  # "Посещения в МО"
    home_visits = models.CharField(max_length=255, default='-')  # "Посещения на Дому"
    case_code = models.CharField(max_length=255, default='-')  # "Случай"
    main_diagnosis = models.CharField(max_length=255, default='-')  # "Диагноз основной (DS1)"
    additional_diagnosis = models.CharField(max_length=1000, null=True, blank=True, default='-')  # "Сопутствующий диагноз (DS2)"
    mp_profile = models.CharField(max_length=255, default='-')  # "Профиль МП"
    bed_profile = models.CharField(max_length=255, default='-')  # "Профиль койки"
    dispensary_monitoring = models.CharField(max_length=255, default='-')  # "Диспансерное наблюдение"
    specialty = models.CharField(max_length=255, default='-')  # "Специальность"
    outcome = models.CharField(max_length=255, default='-')  # "Исход"
    result = models.CharField(max_length=255, default='-')  # "Результат"
    operator = models.CharField(max_length=255, default='-')  # "Оператор"
    initial_input_date = models.CharField(max_length=255, default='-')  # "Первоначальная дата ввода"
    last_change_date = models.CharField(max_length=255, default='-')  # "Дата последнего изменения"
    tariff = models.CharField(max_length=255, default='-')  # "Тариф"
    amount = models.CharField(max_length=255, default='-')  # "Сумма"
    paid = models.CharField(max_length=255, default='-')  # "Оплачено"
    payment_type = models.CharField(max_length=255, default='-')  # "Тип оплаты"
    sanctions = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Санкции"
    ksg = models.CharField(max_length=255, null=True, blank=True, default='-')  # "КСГ"
    kz = models.CharField(max_length=255, null=True, blank=True, default='-')  # "КЗ"
    therapy_schema_code = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Код схемы лекарственной терапии"
    uet = models.CharField(max_length=255, null=True, blank=True, default='-')  # "УЕТ"
    classification_criterion = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Классификационный критерий"
    shrm = models.CharField(max_length=255, null=True, blank=True, default='-')  # "ШРМ"
    directing_mo = models.CharField(max_length=255, null=True, blank=True, default='-')  # "МО, направившая"
    payment_method_code = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Код способа оплаты"
    newborn = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Новорожденный"
    representative = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Представитель"
    additional_status_info = models.CharField(max_length=1500, null=True, blank=True, default='-')  # "Доп. инф. о статусе талона"
    kslp = models.CharField(max_length=255, null=True, blank=True, default='-')  # "КСЛП"
    payment_source = models.CharField(max_length=255, null=True, blank=True, default='-')  # "Источник оплаты"
    report_period = models.CharField(max_length=255, default='-')  # "Отчетный период выгрузки"

    def __str__(self):
        return f"{self.talon} - {self.patient}"

    class Meta:
        verbose_name = "ОМС: Талон"
        verbose_name_plural = "ОМС: Талоны"
        constraints = [
            models.UniqueConstraint(fields=['talon', 'source'], name='unique_talon_source')
        ]


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
        constraints = [
            models.UniqueConstraint(fields=['snils', 'doctor_code'], name='unique_snils_doctor_code')
        ]


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
        constraints = [
            models.UniqueConstraint(fields=['talon_number', 'service_code'], name='unique_talon_code')
        ]

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Категория")
    description = models.CharField(max_length=255, verbose_name="Описание категории", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Справочник: Категория данных"
        verbose_name_plural = "Справочник: Категории данных"


# Модель для типов данных, связанных с категорией
class DataType(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="types", verbose_name="Категория")
    name = models.CharField(max_length=255, verbose_name="Тип данных")
    description = models.CharField(max_length=255, verbose_name="Описание типа данных", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        verbose_name = "Справочник: Тип данных"
        verbose_name_plural = "Справочник: Типы данных"


# Модель для хранения соответствий столбцов CSV и полей модели
class DataTypeFieldMapping(models.Model):
    data_type = models.ForeignKey(DataType, on_delete=models.CASCADE, related_name="field_mappings",
                                  verbose_name="Тип данных")
    csv_column_name = models.CharField(max_length=255, verbose_name="Название столбца в CSV")
    model_field_name = models.CharField(max_length=255, verbose_name="Название поля в модели")

    def __str__(self):
        return f"Mapping for {self.data_type.name}: {self.csv_column_name} -> {self.model_field_name}"

    class Meta:
        verbose_name = "Справочник: Соответствие полей"
        verbose_name_plural = "Справочник: Соответствия полей"


class DataImport(models.Model):
    csv_file = models.FileField(upload_to='oms_data_imports/', verbose_name="CSV файл", blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    added_count = models.IntegerField(default=0, verbose_name="Количество добавленных записей")
    updated_count = models.IntegerField(default=0, verbose_name="Количество обновленных записей")
    error_count = models.IntegerField(default=0, verbose_name="Количество ошибок")
    data_type = models.ForeignKey(DataType, on_delete=models.CASCADE, verbose_name="Тип данных")
    message = models.TextField(verbose_name="Итоговое сообщение", blank=True, null=True)
    def __str__(self):
        return f"Импорт {self.data_type.description} от {self.date_added}"

    class Meta:
        verbose_name = "Импорт данных"
        verbose_name_plural = "Импорт данных"


class DataLoaderConfig(models.Model):
    data_type = models.OneToOneField(DataType, on_delete=models.CASCADE, verbose_name="Тип данных")
    table_name = models.CharField(max_length=255, verbose_name="Имя таблицы")
    column_check = models.CharField(max_length=255, verbose_name="Столбец для проверки (после переименования)")
    columns_for_update = models.TextField(verbose_name="Столбцы для обновления", help_text="Перечислите через запятую")
    encoding = models.CharField(max_length=50, default='utf-8', verbose_name="Кодировка файла")
    delimiter = models.CharField(max_length=10, default=';', verbose_name="Разделитель")
    clear_all_rows = models.BooleanField(default=False, verbose_name="Очистить всю таблицу при загрузке")

    def __str__(self):
        return f"Настройки для {self.data_type.name}"

    def get_columns_for_update(self):
        return [col.strip() for col in self.columns_for_update.split(',')]

    class Meta:
        verbose_name = "Конфигуратор импорта таблиц"
        verbose_name_plural = "Конфигуратор импорта"
