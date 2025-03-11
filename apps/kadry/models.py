import datetime
from django.db import models
from apps.person.models import PhysicalPerson
from apps.organizations.models import Department


class Employee(models.Model):
    """
    Сотрудник (кадровая запись).
    Физическое лицо – обязательно и может быть использовано только один раз (OneToOne).
    Табельный номер генерируется автоматически, если не задан.
    Статус вычисляется динамически на основе назначений и записей о декрете.
    """
    physical_person = models.OneToOneField(
        PhysicalPerson,
        on_delete=models.CASCADE,
        verbose_name="Физическое лицо"
    )
    payroll_number = models.CharField(
        "Табельный номер",
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return f"{self.physical_person} (ТН: {self.payroll_number})"

    def save(self, *args, **kwargs):
        # Если табельный номер не указан, генерируем его автоматически
        if not self.payroll_number:
            qs = Employee.objects.filter(payroll_number__startswith="авто-")
            max_num = 0
            for emp in qs:
                try:
                    num = int(emp.payroll_number.split('-')[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    continue
            self.payroll_number = f"авто-{max_num + 1}"
        super().save(*args, **kwargs)

    @property
    def status(self):
        """
        Вычисляет статус сотрудника на основе связанных назначений и декретов.
          - Если назначений нет: "Не активен"
          - Если есть активное назначение (без даты окончания) и для него не оформлен текущий декрет: "Активный"
          - Если для активного назначения есть действующий декрет: "Декрет"
          - Если все назначения завершены: "Уволен"
        """
        if not self.appointments.exists():
            return "Не активен"
        today = datetime.date.today()
        active_found = False
        for appt in self.appointments.all():
            if appt.end_date is None:
                # Если у активного назначения оформлен декрет, проверяем, действителен ли он
                ml = appt.maternity_leaves.first()
                if ml:
                    if ml.planned_start_date <= today and (ml.planned_end_date >= today or ml.actual_end_date is None):
                        return "Декрет"
                active_found = True
        if active_found:
            return "Активный"
        return "Уволен"


class Position(models.Model):
    """
    Справочник должностей.
    """
    code = models.CharField("Код должности", max_length=20, unique=True)
    name = models.CharField("Наименование должности", max_length=255)

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"

    def __str__(self):
        return self.name


class Specialty(models.Model):
    """
    Справочник специальностей.
    """
    code = models.CharField("Код специальности", max_length=20, unique=True)
    name = models.CharField("Наименование специальности", max_length=255)

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Справочник профилей.
    """
    code = models.CharField("Код профиля", max_length=20, unique=True)
    name = models.CharField("Наименование профиля", max_length=255)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return self.name


class Appointment(models.Model):
    """
    Назначение сотрудника на должность в отделении.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Сотрудник"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        verbose_name="Должность"
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Специальность"
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Профиль"
    )
    rate = models.DecimalField("Ставка", max_digits=4, decimal_places=2, default=1.0)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отделение"
    )
    start_date = models.DateField("Дата начала")
    end_date = models.DateField("Дата окончания", null=True, blank=True)

    class Meta:
        verbose_name = "Назначение"
        verbose_name_plural = "Назначения"

    def __str__(self):
        return f"{self.employee} – {self.position} ({self.start_date})"


class MaternityLeave(models.Model):
    """
    Декрет (модель для ведения данных о декретном отпуске).
    Привязан к назначению сотрудника.
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="maternity_leaves",
        verbose_name="Назначение"
    )
    start_date = models.DateField("Дата начала")
    planned_end_date = models.DateField("Планируемая дата окончания")
    actual_end_date = models.DateField("Фактическая дата окончания", null=True, blank=True)
    comment = models.TextField("Комментарий", blank=True, null=True)

    class Meta:
        verbose_name = "Декрет"
        verbose_name_plural = "Декреты"

    def __str__(self):
        return f"Декрет для {self.appointment} с {self.start_date} до {self.planned_end_date}"


class DoctorCode(models.Model):
    """
    Код врача, привязанный к назначению.
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="doctor_codes",
        verbose_name="Назначение врача"
    )
    code = models.CharField("Код врача", max_length=255, unique=True)

    class Meta:
        verbose_name = "Код врача"
        verbose_name_plural = "Коды врачей"

    def __str__(self):
        return self.code
