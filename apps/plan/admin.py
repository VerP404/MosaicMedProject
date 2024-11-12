from datetime import datetime

from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse

from .models import GroupIndicators, FilterCondition, MonthlyPlan, UnifiedFilter, UnifiedFilterCondition
from .utils import copy_filters_to_new_year


class MonthlyPlanInline(admin.TabularInline):
    model = MonthlyPlan
    extra = 0  # Не добавлять пустые строки, так как записи уже созданы автоматически
    can_delete = False  # Запрещаем удаление записей
    readonly_fields = ('month',)  # Создает пустые строки для каждого месяца
    fields = ('month', 'quantity', 'amount')


class FilterConditionInline(admin.TabularInline):
    model = FilterCondition
    extra = 1
    fields = ['field_name', 'filter_type', 'values', 'year']


# Кнопка для копирования фильтров в новый год
def copy_filters_action(modeladmin, request, queryset):
    new_year = datetime.now().year + 1  # Предположим, что копирование в следующий год
    copy_filters_to_new_year(new_year)
    modeladmin.message_user(request, f"Фильтры скопированы на {new_year}", messages.SUCCESS)


copy_filters_action.short_description = "Скопировать фильтры на следующий год"


class FilterYearListFilter(admin.SimpleListFilter):
    title = 'Год фильтра'
    parameter_name = 'filter_year'

    def lookups(self, request, model_admin):
        years = FilterCondition.objects.values_list('year', flat=True).distinct()
        return [(year, year) for year in sorted(years)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(filters__year=self.value()).distinct()
        return queryset


@admin.register(GroupIndicators)
class GroupIndicatorsAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'level', 'latest_filter_year', 'view_subgroups')
    list_filter = ('level', FilterYearListFilter)
    search_fields = ('name',)
    inlines = [FilterConditionInline, MonthlyPlanInline]
    actions = [copy_filters_action]

    def latest_filter_year(self, obj):
        # Метод для отображения последнего года фильтра
        latest_filter = obj.filters.order_by('-year').first()
        return latest_filter.year if latest_filter else "Нет фильтров"

    def view_subgroups(self, obj):
        """Отображает ссылки на подгруппы в виде ссылок в списке"""
        subgroups = obj.subgroups.all()
        if subgroups:
            links = [format_html('<a href="{}">{}</a>',
                                 reverse('admin:plan_groupindicators_change', args=[sub.id]), sub.name)
                     for sub in subgroups]
            return format_html(", ".join(links))
        return "-"

    view_subgroups.short_description = "Вложенные группы"

    def get_readonly_fields(self, request, obj=None):
        """Добавление поля с подгруппами на страницу редактирования"""
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            readonly_fields = list(readonly_fields) + ['view_subgroups']
        return readonly_fields


class UnifiedFilterConditionInline(admin.TabularInline):
    model = UnifiedFilterCondition
    extra = 1
    fields = ['operator', 'field_name', 'filter_type', 'values']


@admin.register(UnifiedFilter)
class UnifiedFilterAdmin(admin.ModelAdmin):
    list_display = ('year', 'type', 'combined_conditions')
    search_fields = ('year', 'type',)
    inlines = [UnifiedFilterConditionInline]
