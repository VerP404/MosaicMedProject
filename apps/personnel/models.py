import os
from datetime import datetime, date

from django.core.exceptions import ValidationError
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
    # Добавляем связь с группами Telegram (связь ManyToMany)
    telegram_groups = models.ManyToManyField(
        "home.TelegramGroup",
        blank=True,
        verbose_name="Телеграм группы",
        related_name="persons"
    )

    class Meta:
        verbose_name = "Физическое лицо"
        verbose_name_plural = "Физические лица"
        ordering = ['last_name', 'first_name']

    @property
    def is_on_maternity_leave(self):
        """
        Проверяет, есть ли активный декретный период для сотрудника.
        """
        today = datetime.now().date()
        return self.maternity_leaves.filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today),
            start_date__lte=today
        ).exists()

    @property
    def is_doctor(self):
        qs = self.doctor_records.all()
        if not qs.exists():
            return "Нет"
        today = date.today()
        # Если найдётся хотя бы одна активная запись – считаем, что врач работает
        if qs.filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)).exists():
            return "Да"
        return "Уволен"

    @property
    def is_staff(self):
        try:
            staff = self.staff_record
        except StaffRecord.DoesNotExist:
            return "Нет"
        today = date.today()
        if staff.end_date is None or staff.end_date >= today:
            return "Да"
        return "Уволен"
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
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Отделение"
    )

    class Meta:
        verbose_name = "Запись врача"
        verbose_name_plural = "Журнал врачей"

    def __str__(self):
        return f"{self.person} ({self.specialty}) - {self.doctor_code}: {self.structural_unit} {self.start_date}-{self.end_date}"


class StaffRecord(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="staff_records")
    position = models.ForeignKey('PostRG014', on_delete=models.PROTECT, verbose_name="Должность")
    department = models.ForeignKey('organization.Department', on_delete=models.SET_NULL, null=True, verbose_name="Отделение")
    start_date = models.DateField("Дата начала работы")
    end_date = models.DateField("Дата окончания работы", blank=True, null=True)

    class Meta:
        verbose_name = "Запись сотрудника"
        verbose_name_plural = "Записи сотрудника"

    def __str__(self):
        return f"{self.person} - {self.position}: {self.department} {self.start_date}-{self.end_date}"

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
        ordering = ["description"]

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


def digital_signature_upload_path(instance, filename):
    """
    Создает путь для сохранения файлов сканов, привязанный к ID человека.
    Пример: uploads/digital_signatures/{person_id}/{filename}
    """
    return os.path.join(
        'digital_signatures', str(instance.person.id), filename
    )


class DigitalSignature(models.Model):
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='digital_signatures')
    application_date = models.DateField("Дата заявления", blank=True, null=True)
    valid_from = models.DateField("Действует с", blank=True, null=True)
    valid_to = models.DateField("Действует по", blank=True, null=True)

    issued_date = models.DateField("Дата передачи врачу", blank=True, null=True)
    revoked_date = models.DateField("Дата аннулирования", blank=True, null=True)
    scan = models.FileField(
        "Скан выписки",
        upload_to=digital_signature_upload_path,
        blank=True,
        null=True
    )
    scan_uploaded_at = models.DateTimeField(
        "Дата загрузки скана",
        blank=True,
        null=True
    )
    added_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    certificate_serial = models.CharField("Серийный номер сертификата", max_length=50, blank=True, default='')
    position = models.ForeignKey('PostRG014', on_delete=models.PROTECT, verbose_name="Должность")

    class Meta:
        verbose_name = "ЭЦП"
        verbose_name_plural = "ЭЦП"

    def save(self, *args, **kwargs):
        # Если загружен скан, но поле scan_uploaded_at ещё не заполнено – заполняем его
        if self.scan and not self.scan_uploaded_at:
            self.scan_uploaded_at = datetime.now()

        # Если valid_from заполнено и серийный номер ещё пуст, генерируем его по шаблону YY-MM-XXX
        if self.valid_from and not self.certificate_serial:
            # Двухзначный год и месяц
            year = self.valid_from.year % 100
            month = self.valid_from.month
            # Подсчитываем, сколько уже существует записей с таким же valid_from (исключая текущую, если обновляем)
            count = DigitalSignature.objects.filter(valid_from=self.valid_from).exclude(pk=self.pk).count() + 1
            self.certificate_serial = f"{year:02d}-{month:02d}-{count:03d}"

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Если одно из полей valid_from/valid_to заполнено, оба должны быть
        if (self.valid_from and not self.valid_to) or (self.valid_to and not self.valid_from):
            raise ValidationError({
                'valid_from': 'Если указано одно из полей (Действует с или Действует по), то оба должны быть заполнены.',
                'valid_to': 'Если указано одно из полей (Действует с или Действует по), то оба должны быть заполнены.',
            })

    def __str__(self):
        return f"ЭЦП для {self.person} (Действует с {self.valid_from} по {self.valid_to})"


class MaternityLeave(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='maternity_leaves',
        verbose_name="Физическое лицо"
    )
    start_date = models.DateField("Дата начала декрета")
    end_date = models.DateField("Дата окончания декрета", blank=True, null=True)
    note = models.TextField("Примечание", blank=True, null=True)

    class Meta:
        verbose_name = "Декрет"
        verbose_name_plural = "Декреты"
        ordering = ['start_date']

    def __str__(self):
        return f"Декрет с {self.start_date} по {self.end_date or 'настоящее время'} ({self.person})"


class DoctorReportingRecord(models.Model):
    """
    Модель, которая описывает, как "собирать" врача для отчётов:
    - Кто (person) + в каком отделении (department)
    - Какие DoctorRecord (M2M), чтобы можно было указать сразу несколько кодов/записей
      врача для одного и того же Person
    - Период действия (start_date, end_date) — в какие даты (а значит и месяцы) этот
      сборный "врач" считается активным для отчётов
    - Ставка (fte), если нужно учитывать, что врач работает не на 1.0 ставку
    """
    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.CASCADE,
        verbose_name="Физическое лицо"
    )
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.CASCADE,
        verbose_name="Отделение"
    )
    # Многие DoctorRecord (M2M), но все должны принадлежать тому же Person
    doctor_records = models.ManyToManyField(
        'personnel.DoctorRecord',
        related_name='reporting_records',
        verbose_name="Записи врача (DoctorRecord)",
        blank=True
    )

    # Период действия (включительно). Если end_date не задана, считаем, что действует
    # "до бесконечности" или пока аналитик не укажет окончание.
    start_date = models.DateField("Дата начала включения в отчеты")
    end_date = models.DateField(
        "Дата окончания включения в отчеты",
        blank=True,
        null=True,
        help_text="Если не указано, считается без ограничения по дате"
    )

    # Ставка, если нужно (FTE). Можно вынести в другое место, но для удобства храним здесь.
    fte = models.DecimalField("Ставка (FTE)", max_digits=3, decimal_places=2, default=1.00)

    class Meta:
        verbose_name = "Запись для отчётности врача"
        verbose_name_plural = "Записи для отчётности врачей"

    def __str__(self):
        end_str = self.end_date.strftime('%Y-%m-%d') if self.end_date else '…'
        return (
            f"Отчётная запись: {self.person} ({self.department.name}), "
            f"{self.start_date} - {end_str}, FTE={self.fte}"
        )

    def clean(self):
        super().clean()
        # 1) Проверяем только если объект уже сохранён (pk != None)
        if self.pk:
            doctor_records_qs = self.doctor_records.all()
            for dr in doctor_records_qs:
                if dr.person != self.person:
                    raise ValidationError(
                        f"DoctorRecord {dr.doctor_code} принадлежит физлицу {dr.person}, "
                        f"а должно быть {self.person}."
                    )

        # 2) Если end_date указана, проверяем, что она >= start_date
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("Дата окончания не может быть раньше даты начала.")

    def is_active_for_date(self, check_date: date) -> bool:
        """
        Проверить, активна ли эта запись для конкретной календарной даты.
        """
        if self.end_date:
            return self.start_date <= check_date <= self.end_date
        else:
            return check_date >= self.start_date

    def active_months(self):
        """
        Возвращает список (year, month), в которых эта запись считается активной.
        Если end_date = None, то до "бесконечности",
        обычно аналитик сам ограничивает расчёт, например, текущим периодом.
        """
        if not self.end_date:
            # Допустим, условимся возвращать месяцы до текущего?
            # Или можно вернуть пустой список, или до какого-то максимально разумного года.
            # Тут уже бизнес-логика, как вы хотите обрабатывать "открытые" периоды.
            max_date = date.today()
        else:
            max_date = self.end_date

        start = self.start_date.replace(day=1)  # начало месяца
        end = max_date.replace(day=1)  # тоже начало месяца
        current = start

        results = []
        while current <= end:
            results.append((current.year, current.month))
            # Прибавляем один месяц
            # Простейший способ: если это декабрь, переносим на январь следующего года
            year = current.year
            month = current.month
            if month == 12:
                current = date(year + 1, 1, 1)
            else:
                current = date(year, month + 1, 1)

        return results
