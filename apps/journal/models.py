from django.db import models
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

class Person(models.Model):
    last_name = models.CharField("Фамилия", max_length=50)
    first_name = models.CharField("Имя", max_length=50)
    middle_name = models.CharField("Отчество", null=True, blank=True, max_length=50)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    email = models.EmailField("Электронная почта", unique=True, null=True, blank=True)
    phone_number = models.CharField("Телефон", max_length=11, unique=True, null=True, blank=True)

    def __str__(self):
        formatted_birth_date = self.birth_date.strftime("%d-%m-%Y") if self.birth_date else ""
        return f"{self.last_name} {self.first_name} {self.middle_name or ''} {formatted_birth_date}".strip()
    class Meta:
        verbose_name = "Персона"
        verbose_name_plural = "Персоны"


class Employee(models.Model):
    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name="Персона"
    )
    is_responsible = models.BooleanField("Ответственный", default=False)
    is_executor = models.BooleanField("Исполнитель", default=False)

    def __str__(self):
        initials = f"{self.person.first_name[0]}.{self.person.middle_name[0]}." if self.person.middle_name else f"{self.person.first_name[0]}."
        return f"{self.person.last_name} {initials} (Сотрудник)"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class Article(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"


class Source(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"


class Category(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Corpus(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"


class Appeal(models.Model):
    STATUS_CHOICES = [
        ('не распределено', 'Не распределено'),
        ('в работе', 'В работе'),
        ('сегодня срок ответа', 'Сегодня срок ответа'),
        ('просрочено', 'Просрочено'),
        ('отработано', 'Отработано'),
    ]
    applicant = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="appeals_as_applicant",
        verbose_name="Заявитель"
    )
    patients = models.ManyToManyField(
        Person,
        blank=True,
        related_name="appeals_as_patient",
        verbose_name="Пациенты"
    )
    # Статус вычисляется автоматически и не редактируется вручную
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        editable=False,
        default='не распределено'
    )
    registration_date = models.DateField("Дата регистрации", auto_now_add=True)
    article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Статья"
    )
    sources = models.ManyToManyField(
        Source,
        blank=True,
        verbose_name="Источник"
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        verbose_name="Категория"
    )
    corpus = models.ForeignKey(
        Corpus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Корпус"
    )
    responsible = models.ManyToManyField(
        Employee,
        blank=True,
        related_name="appeals_as_responsible",
        verbose_name="Ответственные"
    )
    executors = models.ManyToManyField(
        Employee,
        blank=True,
        related_name="appeals_as_executor",
        verbose_name="Исполнители"
    )
    related_appeals = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        verbose_name="Связанные обращения"
    )
    # Новые поля
    response_deadline = models.DateField("Дата срока ответа", null=True, blank=True)
    answer_date = models.DateField("Дата ответа", null=True, blank=True)
    outgoing_number = models.CharField("Номер исходящего письма", max_length=50, null=True, blank=True)

    def compute_status(self):
        """
        Логика вычисления статуса:
          - Если дата ответа заполнена – 'отработано'
          - Если отсутствует хотя бы один из параметров (ответственные, исполнители, корпус или срок ответа) – 'не распределено'
          - Если дата срока ответа равна сегодняшней – 'сегодня срок ответа'
          - Если срок ответа прошёл, а дата ответа не заполнена – 'просрочено'
          - В остальных случаях – 'в работе'
        """
        today = timezone.now().date()
        if self.answer_date:
            return "отработано"
        # Проверка наличия обязательных параметров
        responsible_count = self.responsible.count() if self.pk else 0
        executor_count = self.executors.count() if self.pk else 0
        if responsible_count == 0 or executor_count == 0 or not self.corpus or not self.response_deadline:
            return "не распределено"
        if self.response_deadline == today:
            return "сегодня срок ответа"
        if self.response_deadline < today:
            return "просрочено"
        return "в работе"

    def save(self, *args, **kwargs):
        self.status = self.compute_status()
        super().save(*args, **kwargs)

    def __str__(self):
        applicant_name = f"{self.applicant.last_name} {self.applicant.first_name[0]}.{self.applicant.middle_name[0] if self.applicant.middle_name else ''}."
        formatted_date = self.registration_date.strftime("%d.%m.%Y")
        return f"Обращение #{self.id} - {applicant_name}: {formatted_date}"

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"


@receiver(m2m_changed, sender=Appeal.responsible.through)
def update_status_responsible(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.status = instance.compute_status()
        instance.save()


@receiver(m2m_changed, sender=Appeal.executors.through)
def update_status_executors(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.status = instance.compute_status()
        instance.save()
