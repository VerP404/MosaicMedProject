from datetime import datetime

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import reverse

from .models import GroupIndicators, FilterCondition, MonthlyPlan, UnifiedFilter, UnifiedFilterCondition, AnnualPlan, \
    BuildingPlan, MonthlyBuildingPlan, MonthlyDepartmentPlan, DepartmentPlan
from .utils import copy_filters_to_new_year


class MonthlyPlanInline(admin.TabularInline):
    model = MonthlyPlan
    extra = 0  # Не добавлять пустые строки, так как записи уже созданы автоматически
    can_delete = False  # Запрещаем удаление записей
    readonly_fields = ('month',)  # Создает пустые строки для каждого месяца
    fields = ('month', 'quantity', 'amount')

    def has_add_permission(self, request, obj=None):
        return False


class FilterConditionInline(admin.TabularInline):
    model = FilterCondition
    extra = 1
    fields = ['field_name', 'filter_type', 'values', 'year']
    readonly_fields = ('year',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        else:
            # При добавлении новой записи поле 'year' не является только для чтения
            return []


# Кнопка для копирования фильтров в новый год
def copy_filters_action(modeladmin, request, queryset):
    new_year = datetime.now().year + 1  # Предполагаем, что копируем на следующий год
    copy_filters_to_new_year(queryset, new_year)
    modeladmin.message_user(request, f"Фильтры для выбранных групп скопированы на {new_year}", messages.SUCCESS)


copy_filters_action.short_description = "Скопировать фильтры на следующий год для выбранных групп"


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
    inlines = [FilterConditionInline]
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


@admin.register(AnnualPlan)
class AnnualPlanAdmin(admin.ModelAdmin):
    list_display = ('group', 'year',)
    search_fields = ('group__name', 'year',)
    inlines = [MonthlyPlanInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class MonthlyBuildingPlanInline(admin.TabularInline):
    model = MonthlyBuildingPlan
    extra = 0
    readonly_fields = ('month',
                       'get_total_with_current_changes',
                       'get_total_plan_for_month',
                       'get_current_plan_for_month',
                       'get_remaining_quantity',
                       'get_total_financial_plan_for_month',
                       'get_used_amount_for_month',
                       'get_remaining_budget',
                       )
    fields = ('month',
              'quantity',
              'amount',
              'get_current_plan_for_month',
              'get_total_plan_for_month',
              'get_total_with_current_changes',
              'get_remaining_quantity',
              'get_total_financial_plan_for_month',
              'get_used_amount_for_month',
              'get_remaining_budget',

              )
    can_delete = False

    def get_total_plan_for_month(self, obj):
        return obj.get_total_plan_for_month()

    get_total_plan_for_month.short_description = "Общий план"

    def get_current_plan_for_month(self, obj):
        return obj.get_current_plan_for_month()

    get_current_plan_for_month.short_description = "План"

    def get_total_with_current_changes(self, obj):
        return obj.get_total_with_current_changes()

    get_total_with_current_changes.short_description = "из него использовано"

    def get_remaining_quantity(self, obj):
        return obj.get_remaining_quantity()

    get_remaining_quantity.short_description = "Остаток"

    def get_total_financial_plan_for_month(self, obj):
        return obj.get_total_financial_plan_for_month()

    get_total_financial_plan_for_month.short_description = "Общий бюджет"

    def get_used_amount_for_month(self, obj):
        return obj.get_used_amount_for_month()

    get_used_amount_for_month.short_description = "из него использовано (фин.)"

    def get_remaining_budget(self, obj):
        return obj.get_remaining_budget()

    get_remaining_budget.short_description = "Остаток (фин.)"

    def has_add_permission(self, request, obj=None):
        return False  # Запрещаем добавление новых записей


@admin.register(BuildingPlan)
class BuildingPlanAdmin(admin.ModelAdmin):
    list_display = ('annual_plan', 'building')
    inlines = [MonthlyBuildingPlanInline]

    def save_model(self, request, obj, form, change):
        try:
            obj.clean()
        except ValidationError as e:
            self.message_user(request, f"Ошибка валидации: {e}", level=messages.ERROR)
            return
        super().save_model(request, obj, form, change)


class MonthlyDepartmentPlanInline(admin.TabularInline):
    model = MonthlyDepartmentPlan
    extra = 0
    readonly_fields = ('month',)  # Поле месяца только для чтения
    can_delete = False  # Запрещаем удаление записей

    def has_add_permission(self, request, obj=None):
        return False  # Запрещаем добавление новых записей


@admin.register(DepartmentPlan)
class DepartmentPlanAdmin(admin.ModelAdmin):
    list_display = ('building_plan', 'department')
    inlines = [MonthlyDepartmentPlanInline]


class UnifiedFilterConditionInline(admin.TabularInline):
    model = UnifiedFilterCondition
    extra = 1
    fields = ['operator', 'field_name', 'filter_type', 'values']


@admin.register(UnifiedFilter)
class UnifiedFilterAdmin(admin.ModelAdmin):
    list_display = ('year', 'type', 'combined_conditions')
    search_fields = ('year', 'type',)
    inlines = [UnifiedFilterConditionInline]
