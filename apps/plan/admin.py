from datetime import datetime

from dal import autocomplete
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from django.db import models

from .models import GroupIndicators, FilterCondition, MonthlyPlan, UnifiedFilter, UnifiedFilterCondition, AnnualPlan, \
    BuildingPlan, MonthlyBuildingPlan, MonthlyDepartmentPlan, DepartmentPlan, GroupBuildingDepartment, ChiefDashboard, \
    MonthlyDoctorPlan, AnnualDoctorPlan
from .utils import copy_filters_to_new_year
from ..organization.models import Department


class GroupBuildingDepartmentForm(forms.ModelForm):
    class Meta:
        model = GroupBuildingDepartment
        fields = ['year', 'building', 'department']
        widgets = {
            'building': autocomplete.ModelSelect2(url='building-autocomplete'),
            'department': autocomplete.ModelSelect2(
                url='department-autocomplete',
                forward=['building', 'year']  # Передача зависимых значений
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'building' in self.data:
            try:
                building_id = int(self.data.get('building'))
                self.fields['department'].queryset = Department.objects.filter(building_id=building_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['department'].queryset = self.instance.building.departments.all()
        else:
            self.fields['department'].queryset = Department.objects.none()


class GroupBuildingDepartmentInline(admin.TabularInline):
    model = GroupBuildingDepartment
    form = GroupBuildingDepartmentForm
    extra = 1
    fields = ['year', 'building', 'department']
    readonly_fields = []


@admin.register(GroupBuildingDepartment)
class GroupBuildingDepartmentAdmin(admin.ModelAdmin):
    form = GroupBuildingDepartmentForm


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


class GroupBuildingsInline(admin.TabularInline):
    model = GroupIndicators.buildings.through
    extra = 0
    verbose_name = "Связанный корпус"
    verbose_name_plural = "Связанные корпуса"


@admin.register(GroupIndicators)
class GroupIndicatorsAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'level', 'is_distributable', 'latest_filter_year', 'view_subgroups')
    list_filter = ('level', FilterYearListFilter)
    search_fields = ('name',)
    inlines = [FilterConditionInline, GroupBuildingDepartmentInline]
    actions = [copy_filters_action]
    filter_horizontal = ('buildings',)
    fieldsets = (
        (None, {
            'fields': ('name', 'parent', 'is_distributable')
        }),
        ('Распределение', {
            'fields': ('buildings',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Сохраняем объект группы перед обработкой инлайнов.
        """
        if not obj.pk:
            obj.save()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Переопределяем сохранение формы, чтобы убедиться, что инлайн-объекты сохраняются только после группы.
        """
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, FilterCondition):
                # Убедимся, что у FilterCondition есть связанная группа
                if not instance.group_id:
                    instance.group = form.instance  # Связываем с группой
            instance.save()
        formset.save_m2m()

        # Проверяем удаленные объекты и удаляем их явно
        for obj in formset.deleted_objects:
            obj.delete()

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


class DepartmentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Department.objects.all()

        building = self.forwarded.get('building', None)
        year = self.forwarded.get('year', None)

        if building:
            qs = qs.filter(group_building_departments__building_id=building)

        if year:
            qs = qs.filter(group_building_departments__year=year)

        return qs.distinct()


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

    get_total_financial_plan_for_month.short_description = "План (фин.)"

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
    readonly_fields = ('month',
                       'get_current_plan_for_month',
                       'get_total_plan_for_month',
                       'get_used_quantity_for_month',
                       'get_remaining_quantity',
                       'get_total_financial_plan_for_month',
                       'get_used_amount_for_month',
                       'get_remaining_budget')
    fields = ('month',
              'quantity',
              'amount',
              'get_current_plan_for_month',
              'get_total_plan_for_month',
              'get_used_quantity_for_month',
              'get_remaining_quantity',
              'get_total_financial_plan_for_month',
              'get_used_amount_for_month',
              'get_remaining_budget'
              )
    can_delete = False

    def get_total_plan_for_month(self, obj):
        return obj.get_total_plan_for_month()

    get_total_plan_for_month.short_description = "Общий план"

    def get_current_plan_for_month(self, obj):
        return obj.get_current_plan_for_month()

    get_current_plan_for_month.short_description = "План"

    def get_used_quantity_for_month(self, obj):
        return obj.get_used_quantity_for_month()

    get_used_quantity_for_month.short_description = "из него использовано"

    def get_remaining_quantity(self, obj):
        return obj.get_remaining_quantity()

    get_remaining_quantity.short_description = "Остаток"

    def get_total_financial_plan_for_month(self, obj):
        return obj.get_total_financial_plan_for_month()

    get_total_financial_plan_for_month.short_description = "План (фин.)"

    def get_used_amount_for_month(self, obj):
        return obj.get_used_amount_for_month()

    get_used_amount_for_month.short_description = "из него использовано (фин.)"

    def get_remaining_budget(self, obj):
        return obj.get_remaining_budget()

    get_remaining_budget.short_description = "Остаток (фин.)"

    def has_add_permission(self, request, obj=None):
        return False


class DepartmentPlanForm(forms.ModelForm):
    class Meta:
        model = DepartmentPlan
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Если значение передано в POST (или GET) данных:
        if 'building_plan' in self.data:
            try:
                building_plan_id = int(self.data.get('building_plan'))
                building_plan = BuildingPlan.objects.get(pk=building_plan_id)
                # Фильтруем отделения по зданию, связанному с выбранным планом корпуса
                self.fields['department'].queryset = Department.objects.filter(
                    building=building_plan.building
                )
            except (ValueError, TypeError, BuildingPlan.DoesNotExist):
                self.fields['department'].queryset = Department.objects.none()
        elif self.instance and self.instance.pk and hasattr(self.instance, 'building_plan'):
            # Если редактируем существующую запись
            self.fields['department'].queryset = Department.objects.filter(
                building=self.instance.building_plan.building
            )
        else:
            # Если ни self.data, ни instance не содержат building_plan
            self.fields['department'].queryset = Department.objects.none()


@admin.register(DepartmentPlan)
class DepartmentPlanAdmin(admin.ModelAdmin):
    form = DepartmentPlanForm
    list_display = ('building_plan', 'department', 'get_group_name')
    fields = ('building_plan', 'department', 'get_group_name')
    readonly_fields = ('get_group_name',)
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


@admin.register(ChiefDashboard)
class ChiefDashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal', 'year', 'plan', 'finance')
    search_fields = ('name', 'goal', 'year')
    list_filter = ('name', 'goal', 'year')


@admin.register(AnnualDoctorPlan)
class AnnualDoctorPlanAdmin(admin.ModelAdmin):
    list_display = ('doctor_record', 'year', 'get_total_quantity', 'get_total_amount')
    search_fields = ('doctor_record__person__last_name', 'doctor_record__doctor_code', 'year')

    def get_total_quantity(self, obj):
        return obj.monthly_doctor_plans.aggregate(total=models.Sum('quantity'))['total'] or 0

    get_total_quantity.short_description = "Общее количество"

    def get_total_amount(self, obj):
        return obj.monthly_doctor_plans.aggregate(total=models.Sum('amount'))['total'] or 0

    get_total_amount.short_description = "Общий бюджет"


@admin.register(MonthlyDoctorPlan)
class MonthlyDoctorPlanAdmin(admin.ModelAdmin):
    list_display = ('annual_doctor_plan', 'month', 'quantity', 'amount')
    list_filter = ('annual_doctor_plan__doctor_record', 'month')
