from django.db import models

from apps.data_loader.models.oms_data import OMSData
from apps.oms_reference.models import MedicalOrganizationOMSTarget
from apps.organization.models import MedicalOrganization


class InvalidationReason(models.Model):
    reason_text = models.CharField(max_length=255, verbose_name="Причина признания ЭМД не актуальным")

    def __str__(self):
        return self.reason_text

    class Meta:
        verbose_name = "Справочник: ЭМД - причина"
        verbose_name_plural = "Справочник: ЭМД - причины"


class DeleteEmd(models.Model):
    oid_medical_organization = models.ForeignKey(MedicalOrganization, on_delete=models.PROTECT,
                                                 verbose_name="OID Медицинской организации", default=1)
    oid_document = models.CharField(
        max_length=255,
        verbose_name="OID документа",
        help_text='Первые цифры Номера в реестре РЭМД. Идентификатор (OID) вида документа в <a href="https://nsi.rosminzdrav.ru/dictionaries/1.2.643.5.1.13.13.11.1520/passport/latest" target="_blank">1.2.643.5.1.13.13.11.1520</a>'
    )
    creation_date = models.DateField(verbose_name="Дата создания", help_text="Журнал ЭМД: Дата формирования ЭМД")
    registration_date = models.DateField(verbose_name="Дата регистрации",
                                         help_text="Журнал ЭМД: Дата отправки в РИР.РЭМД")
    reestr_number = models.CharField(max_length=255, verbose_name="Номер в реестре РЭМД",
                                     help_text="Журнал ЭМД: Регистрационный номер")
    local_identifier = models.CharField(max_length=255, verbose_name="Локальный идентификатор",
                                        help_text="Журнал ЭМД:Сохранить документ в файл. Название файла xml при "
                                                  "сохранении. Пример: 3e765e5d-acfc-4e44-b834-7a876acbe40c")
    reason_not_actual = models.ForeignKey(InvalidationReason, on_delete=models.CASCADE,
                                          verbose_name="Причина признания ЭМД не актуальным",
                                          help_text="Выберите причину аннулирования записи")
    document_number = models.CharField(max_length=255, verbose_name="Номер документа, оформленного взамен", null=True,
                                       blank=True,
                                       help_text="При наличии документа, выданного взамен. Журнал ЭМД: ИД")
    added_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")
    patient = models.CharField(max_length=255, verbose_name="Пациент", help_text="Введите ФИО пациента")
    date_of_birth = models.DateField(verbose_name="Дата рождения", help_text="Введите дату рождения пациента")
    enp = models.CharField(max_length=16, verbose_name="ЕНП", help_text="Введите ЕНП пациента")
    goal = models.ForeignKey(MedicalOrganizationOMSTarget, on_delete=models.CASCADE, verbose_name="Цель ОМС",
                             limit_choices_to={'is_active': True}, help_text="Выберите актуальную цель ОМС")
    treatment_end = models.DateField(verbose_name="Окончание лечения", help_text="Укажите дату завершения лечения")

    def __str__(self):
        return f"{self.oid_medical_organization} - {self.oid_document}"

    class Meta:
        verbose_name = "ЭМД: аннулирование"
        verbose_name_plural = "ЭМД: аннулирование"


class SVOMember(models.Model):
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    middle_name = models.CharField(max_length=100, verbose_name="Отчество", blank=True, null=True)
    birth_date = models.DateField(verbose_name="Дата рождения")
    enp = models.CharField(max_length=16, verbose_name="ЕНП")
    department = models.CharField(max_length=100, verbose_name="Подразделение")
    address = models.TextField(verbose_name="Адрес", blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)

    def update_oms_data(self):
        """
        Обновляет данные участника СВО на основе информации из таблицы OMSData по ЕНП.
        Создает или обновляет записи в SVOMemberOMSData, если ЕНП состоит из 16 символов.
        """
        # Проверяем, что длина ENP равна 16 символам
        if len(self.enp) != 16:
            # Если длина не равна 16, пропускаем обновление
            return

        # Если длина ENP корректна, производим сопоставление
        oms_entries = OMSData.objects.filter(enp=self.enp)

        for entry in oms_entries:
            SVOMemberOMSData.objects.update_or_create(
                svomember=self,
                talon=entry.talon,
                defaults={
                    'goal': entry.goal,
                    'treatment_end': entry.treatment_end,
                    'main_diagnosis': entry.main_diagnosis
                }
            )

    class Meta:
        verbose_name = "СВО: Участники"
        verbose_name_plural = "СВО: Участники"
        constraints = [
            models.UniqueConstraint(fields=['last_name', 'enp'], name='unique_last_name_enp')
        ]

class SVORelative(models.Model):
    svomember = models.ForeignKey(SVOMember, on_delete=models.CASCADE, verbose_name="Участник СВО",
                                  limit_choices_to={'is_active': True})
    status = models.CharField(max_length=100, verbose_name="Статус")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    middle_name = models.CharField(max_length=100, verbose_name="Отчество", blank=True, null=True)
    birth_date = models.DateField(verbose_name="Дата рождения", blank=True, null=True)
    enp = models.CharField(max_length=16, unique=True, verbose_name="ЕНП", blank=True, null=True)
    address = models.TextField(verbose_name="Адрес", blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)

    class Meta:
        verbose_name = "СВО: Родственники"
        verbose_name_plural = "СВО: Родственники"


class Survey(models.Model):
    svomember = models.ForeignKey(SVOMember, on_delete=models.CASCADE, related_name='surveys')
    note = models.TextField(verbose_name="Примечание")
    date = models.DateField(verbose_name="Дата")

    def __str__(self):
        return f"Опрос {self.svomember} от {self.date}"


class SVOMemberOMSData(models.Model):
    svomember = models.ForeignKey('SVOMember', on_delete=models.CASCADE, related_name='oms_data')
    talon = models.CharField(max_length=255, verbose_name="Номер талона")
    goal = models.CharField(max_length=255, blank=True, null=True, verbose_name="Цель лечения")
    treatment_end = models.CharField(max_length=255, blank=True, null=True, verbose_name="Дата окончания лечения")
    main_diagnosis = models.CharField(max_length=255, blank=True, null=True, verbose_name="Основной диагноз")

    def __str__(self):
        return f"Талон {self.talon} - {self.svomember}"
