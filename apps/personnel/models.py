from django.db import models


class Specialty(models.Model):
    code = models.CharField("Код специальности", max_length=100, unique=True)
    description = models.CharField("Описание специальности", max_length=255)

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Справочник: Специальности"

    def __str__(self):
        return f"{self.description} ({self.code})"


class Profile(models.Model):
    code = models.CharField("Код профиля", max_length=100, unique=True)
    description = models.CharField("Описание профиля", max_length=255)

    class Meta:
        verbose_name = "Профиль медицинской помощи"
        verbose_name_plural = "Справочник: Профили помощи"

    def __str__(self):
        return f"{self.description} ({self.code})"


class Person(models.Model):
    GENDER_CHOICES = (
        ('M', 'Мужской'),
        ('F', 'Женский'),
    )
    CITIZENSHIP_CHOICES = (
        (1, 'РФ'),
        (2, 'Иностранец'),
    )
    snils = models.CharField("СНИЛС", max_length=11, unique=True)
    inn = models.CharField("ИНН", max_length=12, blank=True, null=True)
    last_name = models.CharField("Фамилия", max_length=255)
    first_name = models.CharField("Имя", max_length=255)
    patronymic = models.CharField("Отчество", max_length=255, blank=True, null=True)
    date_of_birth = models.DateField("Дата рождения")
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField("Электронная почта", blank=True, null=True)
    phone_number = models.CharField("Номер телефона", max_length=20, blank=True, null=True)
    telegram = models.CharField("Телеграм", max_length=100, blank=True, null=True)
    citizenship = models.IntegerField("Гражданство", choices=CITIZENSHIP_CHOICES, default=1)

    class Meta:
        verbose_name = "Физическое лицо"
        verbose_name_plural = "Врачи"

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic or ''}".strip()


class DoctorRecord(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='doctor_records',
        verbose_name="Физическое лицо"
    )
    doctor_code = models.CharField("Код врача", max_length=20)
    start_date = models.DateField("Дата начала работы", blank=True, null=True)
    end_date = models.DateField("Дата окончания работы", blank=True, null=True)
    structural_unit = models.CharField("Структурное подразделение", max_length=255, default='-')
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Профиль медицинской помощи"
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Специальность"
    )
    department = models.ForeignKey(
        'organization.Department',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Отделение"
    )

    class Meta:
        verbose_name = "Запись врача"
        verbose_name_plural = "Журнал врачей"

    def __str__(self):
        return f"Врач {self.person} ({self.specialty})"


class SpecialtyRG014(models.Model):
    code = models.CharField("Код специальности", max_length=10, unique=True)
    description = models.CharField("Наименование специальности", max_length=255)

    class Meta:
        verbose_name = "Специальность RG014"
        verbose_name_plural = "Справочник: Специальности RG014"

    def __str__(self):
        return f"{self.code} - {self.description}"


class PostRG014(models.Model):
    code = models.CharField("Код должности", max_length=10, unique=True)
    description = models.CharField("Наименование должности", max_length=255)

    class Meta:
        verbose_name = "Должность RG014"
        verbose_name_plural = "Справочник: Должности RG014"

    def __str__(self):
        return f"{self.code} - {self.description}"


class RG014(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='rg014_records',
                               verbose_name="Физическое лицо")
    organization = models.ForeignKey('organization.MedicalOrganization', on_delete=models.SET_NULL, null=True,
                                     verbose_name="Медицинская организация")  # Поле для связи с MedicalOrganization
    spec_issue_date = models.DateField("Дата выдачи сертификата или аккредитации")
    spec_name = models.ForeignKey('SpecialtyRG014', on_delete=models.SET_NULL, null=True,
                                  verbose_name="Наименование специальности")
    cert_accred_sign = models.IntegerField("Признак сертификата или аккредитации",
                                           choices=((1, 'Сертификат'), (2, 'Аккредитация')))
    post_name = models.ForeignKey('PostRG014', on_delete=models.SET_NULL, null=True,
                                  verbose_name="Наименование должности")
    hire_date = models.DateField("Дата приёма")
    dismissal_date = models.DateField("Дата увольнения", blank=True, null=True)

    class Meta:
        verbose_name = "Запись RG014"
        verbose_name_plural = "Записи для RG014"

    def __str__(self):
        return f"{self.person} - {self.spec_name} - {self.post_name}"


class DigitalSignature(models.Model):
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='digital_signatures')
    valid_from = models.DateField("Действует с")
    valid_to = models.DateField("Действует по")
    issued_date = models.DateField("Дата передачи врачу", blank=True, null=True)
    revoked_date = models.DateField("Дата аннулирования", blank=True, null=True)

    class Meta:
        verbose_name = "ЭЦП"
        verbose_name_plural = "ЭЦП"

    def __str__(self):
        return f"ЭЦП для {self.person} (Действует с {self.valid_from} по {self.valid_to})"