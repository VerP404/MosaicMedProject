import json
from datetime import datetime

from dal import autocomplete
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from django.db import models
from import_export.widgets import ManyToManyWidget

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.import_export.forms import ImportForm, ExportForm, SelectableFieldsExportForm
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin

from .models import (
    GroupIndicators, FilterCondition, MonthlyPlan, UnifiedFilter, UnifiedFilterCondition,
    AnnualPlan, BuildingPlan, MonthlyBuildingPlan, MonthlyDepartmentPlan, DepartmentPlan,
    GroupBuildingDepartment, ChiefDashboard, MonthlyDoctorPlan, AnnualDoctorPlan
)
from .utils import copy_filters_to_new_year
from ..organization.models import Department, Building


# Форма для модели GroupBuildingDepartment с автодополнением для полей
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


# Инлайн для модели GroupBuildingDepartment
class GroupBuildingDepartmentInline(TabularInline):
    model = GroupBuildingDepartment
    form = GroupBuildingDepartmentForm
    extra = 1
    fields = ['year', 'building', 'department']
    readonly_fields = []


@admin.register(GroupBuildingDepartment)
class GroupBuildingDepartmentAdmin(ModelAdmin):
    form = GroupBuildingDepartmentForm


# Инлайн для модели MonthlyPlan
class MonthlyPlanInline(TabularInline):
    model = MonthlyPlan
    extra = 0  # Не добавлять пустые строки, так как записи уже созданы автоматически
    can_delete = False  # Запрещаем удаление записей
    readonly_fields = ('month',)  # Отображаем месяц как только для чтения
    fields = ('month', 'quantity', 'amount')

    def has_add_permission(self, request, obj=None):
        return False


# Инлайн для FilterCondition
class FilterConditionInline(TabularInline):
    model = FilterCondition
    extra = 1
    fields = ['field_name', 'filter_type', 'values', 'year']
    readonly_fields = ('year',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        else:
            # При добавлении новой записи поле 'year' редактируемое
            return []


# Действие для копирования фильтров на следующий год
def copy_filters_action(modeladmin, request, queryset):
    new_year = datetime.now().year + 1  # Копируем на следующий год
    copy_filters_to_new_year(queryset, new_year)
    modeladmin.message_user(request, f"Фильтры для выбранных групп скопированы на {new_year}", messages.SUCCESS)
copy_filters_action.short_description = "Скопировать фильтры на следующий год для выбранных групп"


# Фильтр по году фильтра
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


# Инлайн для связи с корпусами
class GroupBuildingsInline(TabularInline):
    model = GroupIndicators.buildings.through
    extra = 0
    verbose_name = "Связанный корпус"
    verbose_name_plural = "Связанные корпуса"

class GroupIndicatorsResource(resources.ModelResource):
    # Для поля ManyToMany (корпуса) используем виджет, который работает по id
    buildings = fields.Field(
        column_name='buildings',
        attribute='buildings',
        widget=ManyToManyWidget(Building, field='id')
    )
    # Сериализуем связанные объекты FilterCondition в JSON
    filters = fields.Field(
        column_name='filters'
    )
    # Сериализуем связанные объекты GroupBuildingDepartment в JSON
    group_building_departments = fields.Field(
        column_name='group_building_departments'
    )

    class Meta:
        model = GroupIndicators
        # Если хотите импортировать записи с сохранением своих id (и обновлять их), укажите их здесь
        import_id_fields = ('id',)
        fields = (
            'id', 'name', 'parent', 'level', 'is_distributable',
            'buildings', 'filters', 'group_building_departments'
        )
        skip_unchanged = True
        report_skipped = True

    def dehydrate_filters(self, obj):
        # Собираем все условия фильтра в список словарей
        conditions = []
        for cond in obj.filters.all():
            conditions.append({
                'field_name': cond.field_name,
                'filter_type': cond.filter_type,
                'values': cond.values,
                'year': cond.year,
            })
        return json.dumps(conditions, ensure_ascii=False)

    def dehydrate_group_building_departments(self, obj):
        items = []
        for item in obj.group_building_departments.all():
            items.append({
                'year': item.year,
                'building': item.building.id,  # сохраняем id корпуса
                'department': item.department.id,  # и id отделения
            })
        return json.dumps(items, ensure_ascii=False)

    def before_import_row(self, row, **kwargs):
        # Преобразуем JSON-строки обратно в объекты (списки словарей)
        if 'filters' in row:
            try:
                row['filters'] = json.loads(row['filters'])
            except Exception:
                row['filters'] = []
        if 'group_building_departments' in row:
            try:
                row['group_building_departments'] = json.loads(row['group_building_departments'])
            except Exception:
                row['group_building_departments'] = []
        return row

    def import_obj(self, obj, data, dry_run):
        # Основной импорт объекта (без связанных записей)
        super().import_obj(obj, data, dry_run)
        # Сохраняем импортированные данные во временные атрибуты, чтобы потом использовать при сохранении
        obj._imported_filters = data.get('filters', [])
        obj._imported_group_building_departments = data.get('group_building_departments', [])

    def after_save_instance(self, instance, using_transactions, dry_run):
        if dry_run:
            return
        # Если требуется сохранить связи «с нуля», можно удалить старые связанные записи
        instance.filters.all().delete()
        instance.group_building_departments.all().delete()
        # Создаём новые FilterCondition на основе импортированных данных
        for cond in getattr(instance, '_imported_filters', []):
            FilterCondition.objects.create(
                group=instance,
                field_name=cond.get('field_name'),
                filter_type=cond.get('filter_type'),
                values=cond.get('values'),
                year=cond.get('year'),
            )
        # Создаём GroupBuildingDepartment записи
        for item in getattr(instance, '_imported_group_building_departments', []):
            GroupBuildingDepartment.objects.create(
                group=instance,
                year=item.get('year'),
                building_id=item.get('building'),
                department_id=item.get('department')
            )

# Админка для GroupIndicators с интеграцией импорта/экспорта
@admin.register(GroupIndicators)
class GroupIndicatorsAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_class = GroupIndicatorsResource
    import_form_class = ImportForm
    export_form_class = ExportForm
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
        # Сохраняем объект группы перед обработкой инлайнов
        if not obj.pk:
            obj.save()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        # Сохраняем инлайн-объекты после группы
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, FilterCondition):
                if not instance.group_id:
                    instance.group = form.instance
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()

    def latest_filter_year(self, obj):
        latest_filter = obj.filters.order_by('-year').first()
        return latest_filter.year if latest_filter else "Нет фильтров"

    def view_subgroups(self, obj):
        """Отображает ссылки на подгруппы в виде ссылок"""
        subgroups = obj.subgroups.all()
        if subgroups:
            links = [format_html('<a href="{}">{}</a>',
                                 reverse('admin:plan_groupindicators_change', args=[sub.id]), sub.name)
                     for sub in subgroups]
            return format_html(", ".join(links))
        return "-"
    view_subgroups.short_description = "Вложенные группы"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            readonly_fields = list(readonly_fields) + ['view_subgroups']
        return readonly_fields


# Кастомный автокомплит для модели Department
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


# Админка для AnnualPlan с импортом/экспортом
@admin.register(AnnualPlan)
class AnnualPlanAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('group', 'year',)
    search_fields = ('group__name', 'year',)
    inlines = [MonthlyPlanInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


# Инлайн для MonthlyBuildingPlan
class MonthlyBuildingPlanInline(TabularInline):
    model = MonthlyBuildingPlan
    extra = 0
    readonly_fields = (
        'month',
        'get_total_with_current_changes',
        'get_total_plan_for_month',
        'get_current_plan_for_month',
        'get_remaining_quantity',
        'get_total_financial_plan_for_month',
        'get_used_amount_for_month',
        'get_remaining_budget',
    )
    fields = (
        'month',
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
        return False


# Админка для BuildingPlan с импортом/экспортом
@admin.register(BuildingPlan)
class BuildingPlanAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('annual_plan', 'building')
    inlines = [MonthlyBuildingPlanInline]

    def save_model(self, request, obj, form, change):
        try:
            obj.clean()
        except ValidationError as e:
            self.message_user(request, f"Ошибка валидации: {e}", level=messages.ERROR)
            return
        super().save_model(request, obj, form, change)


# Инлайн для MonthlyDepartmentPlan
class MonthlyDepartmentPlanInline(TabularInline):
    model = MonthlyDepartmentPlan
    extra = 0
    readonly_fields = (
        'month',
        'get_current_plan_for_month',
        'get_total_plan_for_month',
        'get_used_quantity_for_month',
        'get_remaining_quantity',
        'get_total_financial_plan_for_month',
        'get_used_amount_for_month',
        'get_remaining_budget'
    )
    fields = (
        'month',
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


# Форма для модели DepartmentPlan с фильтрацией отделов по зданию
class DepartmentPlanForm(forms.ModelForm):
    class Meta:
        model = DepartmentPlan
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'building_plan' in self.data:
            try:
                building_plan_id = int(self.data.get('building_plan'))
                building_plan = BuildingPlan.objects.get(pk=building_plan_id)
                self.fields['department'].queryset = Department.objects.filter(
                    building=building_plan.building
                )
            except (ValueError, TypeError, BuildingPlan.DoesNotExist):
                self.fields['department'].queryset = Department.objects.none()
        elif self.instance and self.instance.pk and hasattr(self.instance, 'building_plan'):
            self.fields['department'].queryset = Department.objects.filter(
                building=self.instance.building_plan.building
            )
        else:
            self.fields['department'].queryset = Department.objects.none()


# Админка для DepartmentPlan с импортом/экспортом
@admin.register(DepartmentPlan)
class DepartmentPlanAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    form = DepartmentPlanForm
    list_display = ('building_plan', 'department', 'get_group_name')
    fields = ('building_plan', 'department', 'get_group_name')
    readonly_fields = ('get_group_name',)
    inlines = [MonthlyDepartmentPlanInline]


# Инлайн для UnifiedFilterCondition
class UnifiedFilterConditionInline(TabularInline):
    model = UnifiedFilterCondition
    extra = 1
    fields = ['operator', 'field_name', 'filter_type', 'values']


# Админка для UnifiedFilter с импортом/экспортом
@admin.register(UnifiedFilter)
class UnifiedFilterAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('year', 'type', 'combined_conditions')
    search_fields = ('year', 'type',)
    inlines = [UnifiedFilterConditionInline]


# Админка для ChiefDashboard с импортом/экспортом
@admin.register(ChiefDashboard)
class ChiefDashboardAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('name', 'goal', 'year', 'plan', 'finance')
    search_fields = ('name', 'goal', 'year')
    list_filter = ('name', 'goal', 'year')


# Админка для AnnualDoctorPlan с импортом/экспортом
@admin.register(AnnualDoctorPlan)
class AnnualDoctorPlanAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('doctor_record', 'year', 'get_total_quantity', 'get_total_amount')
    search_fields = ('doctor_record__person__last_name', 'doctor_record__doctor_code', 'year')

    def get_total_quantity(self, obj):
        return obj.monthly_doctor_plans.aggregate(total=models.Sum('quantity'))['total'] or 0
    get_total_quantity.short_description = "Общее количество"

    def get_total_amount(self, obj):
        return obj.monthly_doctor_plans.aggregate(total=models.Sum('amount'))['total'] or 0
    get_total_amount.short_description = "Общий бюджет"


# Админка для MonthlyDoctorPlan с импортом/экспортом
@admin.register(MonthlyDoctorPlan)
class MonthlyDoctorPlanAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('annual_doctor_plan', 'month', 'quantity', 'amount')
    list_filter = ('annual_doctor_plan__doctor_record', 'month')
