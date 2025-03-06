from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Person, Employee, Article, Source, Category, Corpus,
    Appeal
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
class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'birth_date', 'email', 'phone_number')
    search_fields = ('last_name', 'first_name', 'middle_name', 'email', 'phone_number')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('person', 'is_responsible', 'is_executor')
    list_filter = ('is_responsible', 'is_executor')
    search_fields = ('person__last_name', 'person__first_name')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    """
    Админка для обращений.
    """

    # Показываем цветной статус
    def colored_status(self, obj):
        """Отображаем статус цветом для наглядности."""
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

    # Отображаем корпус
    def display_corpus(self, obj):
        return obj.corpus.name if obj.corpus else '-'
    display_corpus.short_description = "Корпус"

    # Отображаем список ответственных
    def display_responsible(self, obj):
        if obj.pk:
            # Список связанных сотрудников
            return ", ".join(str(emp) for emp in obj.responsible.all()) or '-'
        return '-'
    display_responsible.short_description = "Ответственные"

    # Отображаем список исполнителей
    def display_executors(self, obj):
        if obj.pk:
            return ", ".join(str(emp) for emp in obj.executors.all()) or '-'
        return '-'
    display_executors.short_description = "Исполнители"

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

    # Фильтры (по статусу, дате, корпусу, ответственным, исполнителям)
    list_filter = (
        'status',
        'registration_date',
        ('corpus', RelatedOnlyFieldListFilter),
        ('responsible', RelatedOnlyFieldListFilter),
        ('executors', RelatedOnlyFieldListFilter),
    )

    search_fields = ('applicant__last_name', 'applicant__first_name')

    # Поля с множественными связями (M2M) отображаем через горизонтальные фильтры
    filter_horizontal = (
        'patients', 'sources', 'categories',
        'responsible', 'executors', 'related_appeals'
    )

    # Подключаем наше пользовательское действие
    actions = [check_and_update_deadlines]
