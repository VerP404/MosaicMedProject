from django.db import models


class OMS(models.Model):
    # Талон
    talon = models.CharField(max_length=255, verbose_name="Талон", null=True, blank=True)
    is_update = models.BooleanField(default=True,
                                    verbose_name="Обновление")  # Нужно для блокировки талона для обновления

    # Тип источника
    source_id = models.CharField(max_length=255, verbose_name="ID источника", null=True, blank=True)
    source = models.CharField(max_length=255, verbose_name="Источник", null=True, blank=True)

    # Информация о статусе талона в базе
    report_month = models.CharField(max_length=255, verbose_name="Месяц отчета", null=True, blank=True)
    report_month_number = models.IntegerField(verbose_name="Номер месяца отчета", null=True, blank=True)
    report_year = models.IntegerField(verbose_name="Год отчета", null=True, blank=True)
    status = models.CharField(max_length=255, verbose_name="Статус", null=True, blank=True)

    # Информация о цели в талоне
    id_goal = models.CharField(max_length=255, verbose_name="ID цели", null=True, blank=True)
    goal = models.CharField(max_length=255, verbose_name="Цель", null=True, blank=True)
    target_categories = models.TextField(verbose_name="Категории целей", null=True, blank=True)

    # Пациент
    patient_id = models.CharField(max_length=255, verbose_name="ID пациента", null=True, blank=True)
    patient = models.CharField(max_length=255, verbose_name="Пациент", null=True, blank=True)
    birth_date = models.DateField(verbose_name="Дата рождения", null=True, blank=True)
    age = models.IntegerField(verbose_name="Возраст", null=True, blank=True)
    gender = models.CharField(max_length=10, verbose_name="Пол", null=True, blank=True)
    enp = models.CharField(max_length=255, verbose_name="ЕНП", null=True, blank=True)
    smo_code = models.CharField(max_length=255, verbose_name="Код СМО", null=True, blank=True)
    inogorodniy = models.BooleanField(verbose_name="Иногородний", default=False)

    # Даты лечения
    treatment_start = models.DateField(verbose_name="Дата начала лечения", null=True, blank=True)
    treatment_end = models.DateField(verbose_name="Дата окончания лечения", null=True, blank=True)

    # Посещения
    visits = models.IntegerField(verbose_name="Посещения", null=True, blank=True)
    mo_visits = models.IntegerField(verbose_name="Посещения в МО", null=True, blank=True)
    home_visits = models.IntegerField(verbose_name="Посещения на дому", null=True, blank=True)

    # Диагнозы
    diagnosis = models.CharField(max_length=255, verbose_name="Диагнозы", null=True, blank=True)
    main_diagnosis_code = models.CharField(max_length=255, verbose_name="Основной диагноз (код)", null=True, blank=True)
    additional_diagnosis_codes = models.TextField(verbose_name="Дополнительные диагнозы (коды)", null=True, blank=True)

    # Даты ввода и изменения во внешних системах
    initial_input_date = models.DateField(verbose_name="Дата ввода", null=True, blank=True)
    last_change_date = models.DateField(verbose_name="Дата последнего изменения", null=True, blank=True)

    # Информация об оплате
    amount_numeric = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма", null=True, blank=True)
    sanctions = models.CharField(max_length=255, verbose_name="Санкции", null=True, blank=True)

    # КСГ для стационаров
    ksg = models.CharField(max_length=255, verbose_name="КСГ", null=True, blank=True)

    # Информация об отделении и корпусе
    department_id = models.IntegerField(verbose_name="ID отделения", null=True, blank=True)
    department = models.CharField(max_length=255, verbose_name="Отделение", null=True, blank=True)
    building_id = models.IntegerField(verbose_name="ID корпуса", null=True, blank=True)
    building = models.CharField(max_length=255, verbose_name="Корпус", null=True, blank=True)

    # Информация о враче: специальность, профиль, код
    doctor_code = models.CharField(max_length=255, verbose_name="Код врача", null=True, blank=True)
    doctor_id = models.IntegerField(verbose_name="ID врача", null=True, blank=True)
    doctor = models.CharField(max_length=255, verbose_name="Врач", null=True, blank=True)
    specialty = models.CharField(max_length=255, verbose_name="Специальность", null=True, blank=True)
    profile = models.CharField(max_length=255, verbose_name="Профиль", null=True, blank=True)
    profile_id = models.IntegerField(verbose_name="ID профиля", null=True, blank=True)

    # Информация для диспансеризации
    id_health_group = models.IntegerField(verbose_name="ID группы здоровья", null=True, blank=True)
    health_group = models.CharField(max_length=255, verbose_name="Группа здоровья", null=True, blank=True)

    class Meta:
        verbose_name = "Запись ОМС"
        verbose_name_plural = "Записи ОМС"

    def __str__(self):
        return f"OMS Record: {self.talon or 'Без талона'}"
