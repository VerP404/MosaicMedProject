from django.db import models

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
