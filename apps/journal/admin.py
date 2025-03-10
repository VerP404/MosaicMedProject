from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Q
from unfold.admin import ModelAdmin

from .models import (
    Person, Employee, Article, Source, Category, Corpus,
    Appeal, CitizenAppeal, QuestionCode
)


# --- Пользовательское действие --- #
def check_and_update_deadlines(modeladmin, request, queryset):
    """
    Пересчитывает статус (compute_status) у выбранных обращений
    и сохраняет изменения, если статус изменился.
    """
    today = timezone.now().date()
    updated_count = 0
    for appeal in queryset:
        old_status = appeal.status
        new_status = appeal.compute_status()
        if new_status != old_status:
            appeal.status = new_status
            appeal.save(update_fields=['status'])
            updated_count += 1
    modeladmin.message_user(request, f"Обновлено статусов: {updated_count}")


check_and_update_deadlines.short_description = "Проверить и обновить статусы у выбранных обращений"


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    icon_name = "fa-user"  # Иконка из FontAwesome
    list_display = ('last_name', 'first_name', 'middle_name', 'birth_date', 'email', 'phone_number')
    search_fields = ('last_name', 'first_name', 'middle_name', 'email', 'phone_number')
    # Пример добавления кнопки в список (ссылку можно определить через именованный URL или метод)
    list_buttons = [
        {
            "label": "Добавить Person",
            "url": "add",  # ключевое слово 'add' заменится на URL добавления записи
            "css_class": "btn btn-primary",
        }
    ]


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    icon_name = "fa-users"
    list_display = ('person', 'is_responsible', 'is_executor')
    list_filter = ('is_responsible', 'is_executor')
    search_fields = ('person__last_name', 'person__first_name')
    list_buttons = [
        {
            "label": "Добавить Employee",
            "url": "add",
            "css_class": "btn btn-success",
        }
    ]


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    icon_name = "fa-file-text"
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_buttons = [
        {
            "label": "Новый Article",
            "url": "add",
            "css_class": "btn btn-info",
        }
    ]


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    icon_name = "fa-link"
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    icon_name = "fa-tags"
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Corpus)
class CorpusAdmin(ModelAdmin):
    icon_name = "fa-building"
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(QuestionCode)
class QuestionCodeAdmin(ModelAdmin):
    icon_name = "fa-question-circle"
    list_display = ('code', 'title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'title')


class AppealAdminForm(forms.ModelForm):
    class Meta:
        model = Appeal
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        # Фильтруем ответственных
        self.fields['responsible'].queryset = Employee.objects.filter(
            is_responsible=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gt=today)
        )
        # Фильтруем исполнителей
        self.fields['executors'].queryset = Employee.objects.filter(
            is_executor=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gt=today)
        )
        # Исключаем текущую запись из списка связанных обращений
        if self.instance.pk:
            self.fields['related_appeals'].queryset = Appeal.objects.exclude(pk=self.instance.pk)


@admin.register(Appeal)
class AppealAdmin(ModelAdmin):
    icon_name = "fa-envelope"
    autocomplete_fields = ['applicant', 'patients']
    form = AppealAdminForm
    list_display = (
        'id',
        'applicant',
        'colored_status',
        'display_corpus',
        'display_responsible',
        'display_executors',
        'registration_date',
        'response_deadline',
        'answer_date',
        'outgoing_number',
    )
    list_display_links = ("id", "applicant",)
    list_filter = (
        'status',
        'registration_date',
        ('corpus', RelatedOnlyFieldListFilter),
        ('responsible', RelatedOnlyFieldListFilter),
        ('executors', RelatedOnlyFieldListFilter),
    )
    search_fields = ('applicant__last_name', 'applicant__first_name')
    filter_horizontal = (
        'patients', 'sources', 'categories',
        'responsible', 'executors', 'related_appeals'
    )
    actions = [check_and_update_deadlines]
    # Пример: добавление дополнительных кнопок в списке объектов
    list_buttons = [
        {
            "label": "Обновить статусы",
            "action": "check_and_update_deadlines",  # можно привязать к действию
            "css_class": "btn btn-warning",
        }
    ]
    # Пример: добавление кнопок в форме изменения (detail view)
    detail_buttons = [
        {
            "label": "Сохранить и добавить ещё",
            "action": "save_and_add_another",
            "css_class": "btn btn-primary",
        }
    ]

    def colored_status(self, obj):
        color_map = {
            'не распределено': 'gray',
            'в работе': 'orange',
            'сегодня срок ответа': 'blue',
            'просрочено': 'red',
            'отработано': 'green',
        }
        color = color_map.get(obj.status, 'black')
        return format_html(
            '<strong><span style="color: {};">{}</span></strong>',
            color,
            obj.get_status_display()
        )

    colored_status.short_description = "Статус"

    def display_corpus(self, obj):
        return obj.corpus.name if obj.corpus else '-'

    display_corpus.short_description = "Корпус"

    def display_responsible(self, obj):
        if obj.pk:
            return ", ".join(str(emp) for emp in obj.responsible.all()) or '-'
        return '-'

    display_responsible.short_description = "Ответственные"

    def display_executors(self, obj):
        if obj.pk:
            return ", ".join(str(emp) for emp in obj.executors.all()) or '-'
        return '-'

    display_executors.short_description = "Исполнители"


class CitizenAppealAdminForm(forms.ModelForm):
    class Meta:
        model = CitizenAppeal
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'registration_date' in self.fields:
            self.fields['registration_date'].disabled = True

        if self.instance and self.instance.appeal:
            appeal = self.instance.appeal
            employees = list(appeal.responsible.all()) + list(appeal.executors.all())
            positions = sorted(set(emp.position for emp in employees if emp.position))
            choices = [('', '--- Выберите должность ---')] + [(pos, pos) for pos in positions]
            self.fields['selected_responsible'] = forms.ChoiceField(choices=choices, required=False)
        else:
            self.fields['selected_responsible'] = forms.ChoiceField(choices=[], required=False)


def sync_citizen_appeals(modeladmin, request, queryset):
    updated = 0
    for ca in queryset:
        appeal = ca.appeal
        if ca.registration_date != appeal.registration_date:
            ca.registration_date = appeal.registration_date
            ca.save(update_fields=["registration_date"])
            updated += 1
    modeladmin.message_user(request, f"Синхронизировано {updated} записей.")


sync_citizen_appeals.short_description = "Синхронизировать CitizenAppeal с данными Appeal"


@admin.register(CitizenAppeal)
class CitizenAppealAdmin(ModelAdmin):
    icon_name = "fa-file-alt"
    form = CitizenAppealAdminForm
    readonly_fields = ('registration_date',)
    list_display = (
        "number_pp",
        "appeal",
        "institution_registration_number",
        "registration_date",
        "display_selected_responsible",
    )
    list_display_links = ("number_pp", "appeal",)
    search_fields = ("number_pp", "institution_registration_number")
    actions = [sync_citizen_appeals]
    fieldsets = (

        ("Основные реквизиты", {
            "classes": ("two-columns",),
            "fields": (
                "appeal",
                "number_pp",
                "registration_date",
                "institution_registration_number",
                "source",
            ),
        }),
        ("Сопроводительные документы", {
            "classes": ("two-columns",),
            "fields": (
                "dzvo_cover_letter_reg_number",
                "dzvo_cover_letter_date",
            ),
        }),
        ("Вид и кратность обращения", {
            "classes": ("three-columns",),
            "fields": (
                "appeal_type",
                "frequency",
                "question_code",
            ),
        }),
        ("Должность ответственного", {
            "classes": ("two-columns",),
            "fields": (
                "selected_responsible",
            ),
        }),
        ("Информация по рассмотрению", {
            "classes": ("one-columns",),
            "fields": (
                "retrieved_by_commission",
                "retrieved_on_place",
                "retrieved_with_applicant",
            ),
        }),
        ("Рассмотрение и меры: Поддержано", {
            "classes": ("three-columns",),
            "fields": (
                "supported_measures_taken",
                "supported_measures_taken_rebuke",
                "supported_measures_taken_comment",
                "supported_measures_taken_deprivation_payments",
                "supported_measures_taken_holding_meeting",
                "supported_measures_taken_other",
                "supported_without_measures",
            ),
        }),
        ("Рассмотрение и меры: Другое", {
            "classes": ("three-columns",),
            "fields": (
                "explained",
                "not_supported",
                "answer_author",
                "Left_unanswered_author",
                "directed_by_competence",

            ),
        }),
        ("Информация по рассмотрению", {
            "classes": ("three-columns",),
            "fields": (
                "term_consideration_extended",
                "answer_signed_head",
                "answer_signed_deputy_head",
            ),
        }),
        ("Формы ответа заявителю", {
            "fields": (
                "in_writing",
                "in_electronic_document",
            ),
        }),
        ("Статья 8", {
            "classes": ("three-columns",),
            "fields": (
                "article_eight_closed",
                "article_eight_until",
            ),
        }),
        ("Статья 10", {
            "classes": ("three-columns",),
            "fields": (
                "article_ten_closed",
                "article_ten_until",
            ),
        }),
        ("Обращение, поступившее непосредственно в учреждение", {
            "classes": ("three-columns",),
            "fields": (
                "received_institution_closed",
                "received_institution_until",
            ),
        }),
    )

    def display_selected_responsible(self, obj):
        return obj.selected_responsible

    display_selected_responsible.short_description = "Должность ответственного"

    def has_add_permission(self, request):
        return False
