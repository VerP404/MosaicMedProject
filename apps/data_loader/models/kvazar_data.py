from django.db import models


class KvazarSettings(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Квазар: Настройка"
        verbose_name_plural = "Квазар: Настройки"


class KvazarEMD(models.Model):
    id_emd = models.CharField(max_length=255, verbose_name="ИД ЭМД")
    source_epmz_id = models.CharField(max_length=255, verbose_name="ИД исходного ЭПМЗ")
    document_date = models.CharField(max_length=255, verbose_name="Дата документа")
    document_type = models.CharField(max_length=255, verbose_name="Тип документа")
    doctor = models.CharField(max_length=255, verbose_name="Врач")
    independent_division = models.CharField(max_length=255, verbose_name="Обособленное подразделение")
    department = models.CharField(max_length=255, verbose_name="Подразделение")
    patient = models.CharField(max_length=255, verbose_name="Пациент")
    document_creation_date = models.CharField(max_length=255, verbose_name="Дата формирования электронного документа")
    doctor_signature = models.CharField(max_length=255, verbose_name="Наличие подписи врача")
    mo_signature = models.CharField(max_length=255, verbose_name="Наличие подписи МО")
    rir_remd_sent_date = models.CharField(max_length=255, verbose_name="Дата отправки в РИР.РЭМД")
    rir_remd_status = models.CharField(max_length=255, verbose_name="Статус отправки в РИР.РЭМД")
    registration_number = models.CharField(max_length=255, verbose_name="Регистрационный номер")
    rir_remd_status_details = models.CharField(max_length=255, verbose_name="Детали статуса отправки")

    def __str__(self):
        return f"KvazarEMD: {self.id} - {self.patient}"

    class Meta:
        verbose_name = "Квазар: ЭМД"
        verbose_name_plural = "Квазар: ЭМД"


class KvazarRecipe(models.Model):
    number = models.CharField(max_length=255, verbose_name="Номер")
    series = models.CharField(max_length=255, verbose_name="Серия")
    recept_type = models.CharField(max_length=255, verbose_name="Тип рецепта")
    date = models.CharField(max_length=255, verbose_name="Дата")
    ecp = models.CharField(max_length=255, verbose_name="ЭЦП")
    ecp_owner = models.CharField(max_length=255, verbose_name="Владелец подписи")
    organization = models.CharField(max_length=255, verbose_name="Организация")
    department = models.CharField(max_length=255, verbose_name="Подразделение")
    status = models.CharField(max_length=255, verbose_name="Статус")
    status_change_date = models.CharField(max_length=255, verbose_name="Дата изменения статуса")
    status_author = models.CharField(max_length=255, verbose_name="Автор статуса")
    farm_status = models.CharField(max_length=255, verbose_name="Статус отправки в ФАРМ")
    er_status = models.CharField(max_length=255, verbose_name="Статус отправки в 1ЭР")
    er_status_details = models.TextField(null=True, blank=True,
                                         verbose_name="Дополнительная информация по статусу отправки в 1ЭР")
    emd_verification = models.CharField(max_length=255, verbose_name="Верификация ЭМД")
    remd_status = models.CharField(max_length=255, verbose_name="Статус отправки в РЭМД")
    remd_status_details = models.TextField(null=True, blank=True,
                                           verbose_name="Дополнительная информация по статусу отправки в РЭМД")
    expiration_date = models.CharField(max_length=255, verbose_name="Срок действия")
    patient_name = models.CharField(max_length=255, verbose_name="Ф.И.О. пациента")
    patient_birth_date = models.CharField(max_length=255, verbose_name="Дата рождения пациента")
    patient_snils = models.CharField(max_length=255, verbose_name="СНИЛС пациента")
    diagnosis_code = models.CharField(max_length=255, verbose_name="Код диагноза")
    diagnosis_name = models.CharField(max_length=255, verbose_name="Название диагноза")
    benefit_category_name = models.CharField(max_length=255, verbose_name="Название льготной категории")
    benefit_category_type = models.CharField(max_length=255, verbose_name="Тип льготной категории")
    funding_source = models.CharField(max_length=255, verbose_name="Источник финансирования")
    doctor_name = models.CharField(max_length=255, verbose_name="Ф.И.О. врача")
    doctor_position = models.CharField(max_length=255, verbose_name="Должность врача")
    medication_name = models.CharField(max_length=255, verbose_name="Лекарственный препарат")
    trn = models.CharField(max_length=255, verbose_name="ТРН")
    international_nonproprietary_name = models.CharField(max_length=255, verbose_name="МНН")
    quantity = models.CharField(max_length=255, verbose_name="Количество")
    payment_percentage = models.CharField(max_length=255, verbose_name="Процент оплаты")

    def __str__(self):
        return f"KvazarRecipe: {self.number} - {self.patient_name}"

    class Meta:
        verbose_name = "Квазар: Рецепт"
        verbose_name_plural = "Квазар: Рецепты"


class KvazarMortality(models.Model):
    series = models.CharField(max_length=255, verbose_name="Серия")
    number = models.CharField(max_length=255, verbose_name="Номер")
    spoiled = models.CharField(max_length=255, verbose_name="ИСПОРЧЕНО")
    duplicate = models.CharField(max_length=255, verbose_name="Дубликат")
    perinatal = models.CharField(max_length=255, verbose_name="Перинатальная")
    issue_date = models.CharField(max_length=255, verbose_name="Дата выдачи")
    type = models.CharField(max_length=255, verbose_name="Тип")
    emd_sent_date = models.CharField(max_length=255, verbose_name="Дата отправки ЭМД")
    emd_status = models.CharField(max_length=255, verbose_name="Статус отправки ЭМД")
    emd_error = models.CharField(max_length=255, verbose_name="ЭМД ошибка")
    creator = models.CharField(max_length=255, verbose_name="Создавший")
    doctor = models.CharField(max_length=255, verbose_name="Врач")
    deceased_name = models.CharField(max_length=255, verbose_name="ФИО умершего(ей)")
    deceased_birth_date = models.CharField(max_length=255, verbose_name="Дата рождения")
    death_date = models.CharField(max_length=255, verbose_name="Дата смерти")
    gender = models.CharField(max_length=255, verbose_name="Пол")
    age = models.CharField(max_length=255, verbose_name="Возраст, лет")
    cause_a = models.CharField(max_length=255, verbose_name="Причина (а)")
    cause_b = models.CharField(max_length=255, verbose_name="Причина (б)")
    cause_c = models.CharField(max_length=255, verbose_name="Причина (в)")
    cause_d = models.CharField(max_length=255, verbose_name="Причина (г)")
    region = models.CharField(max_length=255, verbose_name="Регион")
    district = models.CharField(max_length=255, verbose_name="Район")
    city = models.CharField(max_length=255, verbose_name="Город / Населенный пункт")
    street = models.CharField(max_length=255, verbose_name="Улица")
    house = models.CharField(max_length=255, verbose_name="Дом")
    apartment = models.CharField(max_length=255, verbose_name="Квартира")
    attachment = models.CharField(max_length=255, verbose_name="Прикрепление")
    initial_statistics = models.CharField(max_length=255, verbose_name="Первоначальная (статистика)")

    def __str__(self):
        return f"KvazarDead: {self.series} - {self.deceased_name}"

    class Meta:
        verbose_name = "Квазар: смертность"
        verbose_name_plural = "Квазар: смертность"


class KvazarMedicalCertificate(models.Model):
    certificate_number = models.CharField(max_length=255, verbose_name="Серия и номер справки")
    issue_date = models.CharField(max_length=255, verbose_name="Дата выдачи")
    patient_name = models.CharField(max_length=255, verbose_name="ФИО")
    patient_birth_date = models.CharField(max_length=255, verbose_name="Дата рождения")
    doctor = models.CharField(max_length=255, verbose_name="Врач")
    issuing_organization = models.CharField(max_length=255, verbose_name="Организация выдавшая документ")
    certificate_type = models.CharField(max_length=255, verbose_name="Вид справки")
    conclusion = models.CharField(max_length=255, verbose_name="Заключение")
    status = models.CharField(max_length=255, verbose_name="Статус")
    errors = models.CharField(max_length=255, verbose_name="Ошибки по справке")

    def __str__(self):
        return f"KvazarSpravki: {self.certificate_number} - {self.patient_name}"

    class Meta:
        verbose_name = "Квазар: медицинская справка"
        verbose_name_plural = "Квазар: медицинские справки"
