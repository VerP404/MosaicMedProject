from django.contrib import messages
from django.db import models, IntegrityError
from django.db.models import Max
from django.utils import timezone
from django.db.models.signals import m2m_changed, post_save
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
        verbose_name_plural = "Справочник: физические лица"


class Employee(models.Model):
    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name="Персона"
    )
    position = models.CharField("Должность", max_length=255, null=True, blank=True)
    start_date = models.DateField("Дата начала работы", null=True, blank=True)
    end_date = models.DateField("Дата окончания работы", null=True, blank=True)
    is_responsible = models.BooleanField("Ответственный", default=False)
    is_executor = models.BooleanField("Исполнитель", default=False)

    def __str__(self):
        initials = f"{self.person.first_name[0]}.{self.person.middle_name[0]}." if self.person.middle_name else f"{self.person.first_name[0]}."
        return f"{self.person.last_name} {initials} (Сотрудник)"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Справочник: сотрудники"


class Article(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Справочник: статьи"


class Source(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Справочник: источники"


class Category(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Справочник: категории"


class Corpus(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание")
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Справочник: корпуса"


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
    registration_date = models.DateField("Дата регистрации", default=timezone.now)
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
        verbose_name_plural = "Журнал обращений"

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except IntegrityError as e:
            messages.error(request, f"Ошибка сохранения: {str(e)}")


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


class QuestionCode(models.Model):
    code = models.CharField("Код", max_length=50, unique=True)
    title = models.CharField("Название", max_length=255)
    is_active = models.BooleanField("Действует", default=True)

    def __str__(self):
        return f"{self.code} – {self.title}"

    class Meta:
        verbose_name = "Код вопроса"
        verbose_name_plural = "Справочник: коды вопросов"


class CitizenAppeal(models.Model):
    appeal = models.ForeignKey('Appeal', on_delete=models.CASCADE, verbose_name="Обращение")

    # 1
    number_pp = models.IntegerField("№ п/п", unique_for_year="registration_date", help_text="Порядковый номер в журнале")
    # 2
    registration_date = models.DateField("Дата регистрации в учреждении", editable=False)
    # 3
    institution_registration_number = models.CharField("Рег. № обращения учреждения", max_length=100, unique=True,
                                                       help_text="регистрационный № обращения учреждения")

    # 4
    SOURCE_CHOICES = [
        ("mz_vo", "МЗ ВО"),
        ("zayavitel", "От заявителя"),
    ]
    source = models.CharField("Источник поступления", max_length=20, choices=SOURCE_CHOICES, blank=True)
    # 5.1
    dzvo_cover_letter_reg_number = models.CharField("Рег. № сопроводительного письма ДЗ ВО", max_length=100, blank=True,
                                                    null=True)
    # 5.2
    dzvo_cover_letter_date = models.DateField("Дата сопроводительного письма ДЗ ВО к обращению", blank=True, null=True)
    # 6
    APPEAL_TYPE_CHOICES = [
        ("blagodarnost", "Благодарность"),
        ("zhaloba", "Жалоба"),
        ("zayavlenie", "Заявление"),
    ]
    appeal_type = models.CharField("Вид обращения", max_length=20, choices=APPEAL_TYPE_CHOICES, blank=True)
    # 7
    FREQUENCY_CHOICES = [
        ("pervichnoe", "Первичное"),
        ("povtornoe", "Повторное"),
        ("neodnokratnoe", "Неоднократное"),
    ]
    frequency = models.CharField("Кратность поступления", max_length=20, choices=FREQUENCY_CHOICES, blank=True)

    # 8
    question_code = models.ForeignKey('QuestionCode', on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="Код вопроса")

    # 9 - Добавляем поле "Должность ответственного"
    selected_responsible = models.CharField(
        "Должность ответственного",
        max_length=255,
        blank=True,
        null=True,
        help_text="Выберите должность из списка, сформированного по сотрудникам обращения"
    )

    # 10 - Информация по рассмотрению
    # 10.1
    retrieved_by_commission = models.BooleanField("Проверено комиссионно", default=False)
    # 10.2
    retrieved_on_place = models.BooleanField("Проверено с выездом на место", default=False)
    # 10.3
    retrieved_with_applicant = models.BooleanField("Рассмотрено с участием заявителя ", default=False)

    # 11 - С результатом рассмотрения
    # 11.1 - рассмотрено  по существу
    # 11.1.1 - "Поддержано"
    # 11.1.1.1 - "поддержано, меры приняты"
    supported_measures_taken = models.BooleanField("поддержано, меры приняты", default=False)
    # 11.1.1.2 - принятые меры
    # 11.1.1.2.1
    supported_measures_taken_rebuke = models.BooleanField("поддержано, меры приняты: выговор", default=False)
    # 11.1.1.2.2
    supported_measures_taken_comment = models.BooleanField("поддержано, меры приняты: замечание", default=False)
    # 11.1.1.2.3
    supported_measures_taken_deprivation_payments = models.BooleanField(
        "поддержано, меры приняты: лишение стимулирующих выплат", default=False)
    # 11.1.1.2.4
    supported_measures_taken_holding_meeting = models.BooleanField("поддержано, меры приняты: проведение совещания",
                                                                   default=False)
    # 11.1.1.2.5
    supported_measures_taken_other = models.BooleanField("поддержано, меры приняты: иное", default=False)

    # 11.1.1.3
    supported_without_measures = models.BooleanField("поддержано без принятия мер", default=False)
    # 11.1.2
    explained = models.BooleanField("Разъяснено", default=False)
    # 11.1.3
    not_supported = models.BooleanField("Не поддержано", default=False)
    # 11.2
    answer_author = models.BooleanField("Дан ответ автору", default=False)
    # 11.3
    Left_unanswered_author = models.BooleanField("Оставлено без ответа автору", default=False)
    # 12
    directed_by_competence = models.BooleanField("Направлено по компетенции", default=False)
    # 13 - Информация по рассмотрению
    # 13.1
    term_consideration_extended = models.BooleanField("Срок рассмотрения продлен", default=False)
    # 13.2
    answer_signed_head = models.BooleanField("Ответ подписан руководителем ", default=False)
    # 13.3
    answer_signed_deputy_head = models.BooleanField("Ответ подписан заместителем руководителя", default=False)
    # 14
    # 14.1
    in_writing = models.BooleanField("В письменной форме", default=False)
    # 14.2
    in_electronic_document = models.BooleanField("В форме электронного документа", default=False)

    # 15 - Обращение поступившее из ДЗ ВО рассмотрено
    # 15.1 - по статье 8 Федерального закона от 02.05.2006 № 59-ФЗ
    # 15.1.1
    article_eight_closed = models.DateField("Статья 8: закрыто (дата)", blank=True, null=True)
    # 15.1.2
    article_eight_until = models.DateField("Статья 8: находится в работе (до)", blank=True, null=True)
    # 15.2 - по статье 10 Федерального закона от 02.05.2006 № 59-ФЗ
    # 15.2.1
    article_ten_closed = models.DateField("Статья 10: закрыто (дата)", blank=True, null=True)
    # 15.2.2
    article_ten_until = models.DateField("Статья 10: находится в работе (до)", blank=True, null=True)
    # 16 - Обращение, поступившее непосредственно в учреждение
    # 16.1
    received_institution_closed = models.DateField("Поступившее в учреждение: закрыто (дата)",
                                                   blank=True, null=True)
    # 16.2
    received_institution_until = models.DateField("Поступившее в учреждение: находится в работе (до)",
                                                  blank=True, null=True)

    def __str__(self):
        return f"Журнал #{self.number_pp} / {self.institution_registration_number}"

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Журнал письменных обращений"
    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except IntegrityError as e:
            messages.error(request, f"Ошибка сохранения: {str(e)}")

@receiver(post_save, sender=Appeal)
def create_or_update_citizen_appeal(sender, instance, created, **kwargs):
    from .models import CitizenAppeal
    year = instance.registration_date.year
    max_number = CitizenAppeal.objects.filter(registration_date__year=year).aggregate(Max('number_pp'))['number_pp__max'] or 0
    new_number = max_number + 1

    defaults = {
        'registration_date': instance.registration_date,
        'number_pp': new_number,
    }
    try:
        ca, ca_created = CitizenAppeal.objects.update_or_create(
            appeal=instance,
            defaults=defaults
        )
    except IntegrityError as e:
        # Логирование ошибки вместо падения приложения.
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка создания CitizenAppeal для обращения {instance.id}: {e}")

