import json
from datetime import datetime
import io
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, redirect

from dal import autocomplete
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Q, JSONField
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.import_export.forms import ImportForm, ExportForm, SelectableFieldsExportForm
from unfold.decorators import action
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin

from .forms import GroupIndicatorsForm, YearSelectForm, ImportPlansForm
from .models import (
    GroupIndicators, FilterCondition, MonthlyPlan, UnifiedFilter, UnifiedFilterCondition,
    AnnualPlan, BuildingPlan, MonthlyBuildingPlan, MonthlyDepartmentPlan, DepartmentPlan,
    GroupBuildingDepartment, ChiefDashboard, MonthlyDoctorPlan, AnnualDoctorPlan, GoalGroupConfig,
    OrganizationIndicatorConfig
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
                forward=['building', 'year']
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
    extra = 0
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
    extra = 0
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


# Действия для изменения статуса отображения в отчете нарастающе
def enable_cumulative_report_action(modeladmin, request, queryset):
    """Включить отображение в отчете нарастающе для выбранных планов"""
    updated = queryset.update(show_in_cumulative_report=True)
    modeladmin.message_user(
        request,
        f"Включено отображение в отчете нарастающе для {updated} планов.",
        messages.SUCCESS
    )


enable_cumulative_report_action.short_description = "Включить отображение в отчете нарастающе"


def disable_cumulative_report_action(modeladmin, request, queryset):
    """Отключить отображение в отчете нарастающе для выбранных планов"""
    updated = queryset.update(show_in_cumulative_report=False)
    modeladmin.message_user(
        request,
        f"Отключено отображение в отчете нарастающе для {updated} планов.",
        messages.SUCCESS
    )


disable_cumulative_report_action.short_description = "Отключить отображение в отчете нарастающе"


def enable_indicators_report_action(modeladmin, request, queryset):
    """Включить отображение в отчете индикаторов для выбранных планов"""
    updated = queryset.update(show_in_indicators_report=True)
    modeladmin.message_user(
        request,
        f"Включено отображение в отчете индикаторов для {updated} планов.",
        messages.SUCCESS
    )


enable_indicators_report_action.short_description = "Включить отображение в отчете индикаторов"


def disable_indicators_report_action(modeladmin, request, queryset):
    """Отключить отображение в отчете индикаторов для выбранных планов"""
    updated = queryset.update(show_in_indicators_report=False)
    modeladmin.message_user(
        request,
        f"Отключено отображение в отчете индикаторов для {updated} планов.",
        messages.SUCCESS
    )


disable_indicators_report_action.short_description = "Отключить отображение в отчете индикаторов"


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


class NullableForeignKeyWidget(ForeignKeyWidget):
    def get_queryset(self, value, row=None, **kwargs):
        return super().get_queryset(value, row=row, **kwargs)

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        try:
            qs = self.get_queryset(value, row=row, **kwargs)
            return qs.get(**{self.field: value})
        except self.model.DoesNotExist:
            return value


from .resources import GroupIndicatorsResource, UnifiedFilterResource


@admin.register(GroupIndicators)
class GroupIndicatorsAdmin(ModelAdmin, ImportExportModelAdmin):
    form = GroupIndicatorsForm
    autocomplete_fields = ['parent']
    resource_class = GroupIndicatorsResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    ordering = ['parent__name', 'name']
    list_display = ('name', 'parent', 'level', 'is_distributable', 'external_id', 'sync_enabled', 'latest_filter_year', 'view_subgroups')
    list_filter = ('sync_enabled', 'level', FilterYearListFilter, 'is_distributable')
    search_fields = ['name', 'parent__name', 'parent__parent__name', 'external_id']
    inlines = [FilterConditionInline, GroupBuildingDepartmentInline]
    actions = [copy_filters_action]
    filter_horizontal = ('buildings',)
    readonly_fields = ('external_id',)
    fieldsets = (
        (None, {'fields': ('name', 'parent', 'is_distributable')}),
        ('Распределение', {'fields': ('buildings',), 'classes': ('collapse',)}),
    )

    def get_search_results(self, request, queryset, search_term):
        # Сначала сортируем
        queryset = queryset.order_by('parent__name', 'name')

        if search_term:
            # Допустим, хотим искать в name, parent__name, parent__parent__name
            # Можно ещё глубже, если нужно
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(parent__name__icontains=search_term) |
                Q(parent__parent__name__icontains=search_term)
                # ... и так далее ...
            )
        return queryset, False

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.save()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, FilterCondition) and not instance.group_id:
                instance.group = form.instance
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()

    def latest_filter_year(self, obj):
        latest_filter = obj.filters.order_by('-year').first()
        return latest_filter.year if latest_filter else "Нет фильтров"

    def view_subgroups(self, obj):
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
    list_display = ('group', 'year', 'sort_order', 'show_in_cumulative_report', 'show_in_indicators_report', 'external_id', 'has_quantity_plan', 'has_amount_plan')
    list_filter = ('year', 'show_in_cumulative_report', 'show_in_indicators_report')
    search_fields = ('group__name', 'year', 'external_id')
    list_editable = ('sort_order', 'show_in_cumulative_report', 'show_in_indicators_report')
    inlines = [MonthlyPlanInline]
    fields = ('group', 'year', 'sort_order', 'show_in_cumulative_report', 'show_in_indicators_report', 'external_id')
    readonly_fields = ('external_id',)
    actions = [enable_cumulative_report_action, disable_cumulative_report_action, 
               enable_indicators_report_action, disable_indicators_report_action]
    actions_list = ["export_plans", "import_plans"]
    ordering = ['year', 'sort_order', 'group__level', 'group__name']

    def has_quantity_plan(self, obj):
        """
        Возвращает значок "да", если хотя бы один из месячных планов имеет ненулевое количество.
        """
        if obj.monthly_plans.filter(quantity__gt=0).exists():
            return format_html('<img src="/static/admin/img/icon-yes.svg" alt="Да">')
        return format_html('<img src="/static/admin/img/icon-no.svg" alt="Нет">')

    has_quantity_plan.short_description = "План количества"

    def has_amount_plan(self, obj):
        """
        Возвращает значок "да", если хотя бы один из месячных планов имеет ненулевую сумму.
        """
        if obj.monthly_plans.filter(amount__gt=0).exists():
            return format_html('<img src="/static/admin/img/icon-yes.svg" alt="Да">')
        return format_html('<img src="/static/admin/img/icon-no.svg" alt="Нет">')

    has_amount_plan.short_description = "План суммы"

    @action(description="Экспорт планов в Excel", url_path="export-plans", permissions=["export_plans"])
    def export_plans(self, request):
        """Экспорт планов в Excel формат"""
        if request.method == 'POST':
            form = YearSelectForm(request.POST)
            if form.is_valid():
                year = form.cleaned_data['year']
                return self._export_plans_to_excel(year)
        else:
            form = YearSelectForm(initial={'year': datetime.now().year})
        
        context = {
            'form': form,
            'title': 'Экспорт планов',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/plan/export_plans.html', context)

    def _export_plans_to_excel(self, year):
        """Генерирует Excel файл с планами для указанного года"""
        # Получаем все AnnualPlan для года с сортировкой
        annual_plans = AnnualPlan.objects.filter(
            year=year
        ).select_related('group', 'group__parent', 'group__parent__parent').prefetch_related('monthly_plans')
        
        # Сортируем: сначала по sort_order (если указан), потом по иерархии
        def get_sort_key(annual_plan):
            # Если указан sort_order, используем его
            if annual_plan.sort_order is not None:
                return (0, annual_plan.sort_order, '')
            
            # Иначе сортируем по иерархии
            group = annual_plan.group
            # Строим список всех предков от корня до текущей группы
            path_names = []
            current = group
            while current:
                path_names.insert(0, current.name)
                current = current.parent
            
            # Дополняем до максимального уровня (10) пустыми строками для правильной сортировки
            max_levels = 10
            sort_key = tuple(path_names + [''] * (max_levels - len(path_names)))
            return (1, 0, sort_key)  # (1, 0, ...) чтобы sort_order был приоритетнее
        
        # Сортируем annual_plans
        sorted_annual_plans = sorted(annual_plans, key=get_sort_key)
        
        # Создаем список строк для экспорта
        rows = []
        
        for annual_plan in sorted_annual_plans:
            group = annual_plan.group
            # Получаем иерархию группы
            hierarchy = group.get_hierarchy_display()
            
            # Получаем месячные планы
            monthly_plans = annual_plan.monthly_plans.all().order_by('month')
            
            # Строка с объемами (quantity) - всегда первой
            quantity_row = {
                'Показатель': f'{hierarchy} - Объемы',
                'external_id': group.external_id or '',
                'Итого': sum(mp.quantity for mp in monthly_plans),
            }
            for month in range(1, 13):
                mp = monthly_plans.filter(month=month).first()
                quantity_row[f'{month}'] = mp.quantity if mp else 0
            
            # Строка с финансами (amount) - всегда второй
            amount_row = {
                'Показатель': f'{hierarchy} - Финансы',
                'external_id': group.external_id or '',
                'Итого': sum(float(mp.amount) for mp in monthly_plans),
            }
            for month in range(1, 13):
                mp = monthly_plans.filter(month=month).first()
                amount_row[f'{month}'] = float(mp.amount) if mp else 0.0
            
            # Добавляем сначала Объемы, потом Финансы
            rows.append(quantity_row)
            rows.append(amount_row)
        
        # Создаем DataFrame
        df = pd.DataFrame(rows)
        
        # Создаем Excel файл в памяти
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Планы', index=False)
        
        output.seek(0)
        
        # Создаем HTTP ответ
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="plans_{year}.xlsx"'
        return response

    @action(description="Импорт планов из Excel", url_path="import-plans", permissions=["import_plans"])
    def import_plans(self, request):
        """Импорт планов из Excel файла"""
        if request.method == 'POST':
            form = ImportPlansForm(request.POST, request.FILES)
            if form.is_valid():
                year = form.cleaned_data['year']
                file = form.cleaned_data['file']
                
                try:
                    result = self._import_plans_from_excel(file, year)
                    messages.success(request, f'Успешно импортировано: {result["imported"]} строк, обновлено: {result["updated"]} записей')
                    return redirect('admin:plan_annualplan_changelist')
                except Exception as e:
                    messages.error(request, f'Ошибка при импорте: {str(e)}')
        else:
            form = ImportPlansForm(initial={'year': datetime.now().year})
        
        context = {
            'form': form,
            'title': 'Импорт планов',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/plan/import_plans.html', context)

    def _import_plans_from_excel(self, file, year):
        """Импортирует планы из Excel файла"""
        # Читаем Excel файл
        df = pd.read_excel(file)
        
        imported = 0
        updated = 0
        
        # Группируем строки по external_id
        # Создаем словарь: external_id -> {quantity_row, amount_row}
        groups_data = {}
        
        for idx, row in df.iterrows():
            indicator = str(row.get('Показатель', '')).strip()
            external_id = str(row.get('external_id', '')).strip()
            
            if not indicator or not external_id or external_id == 'nan':
                continue
            
            # Инициализируем запись для external_id если её нет
            if external_id not in groups_data:
                groups_data[external_id] = {'quantity_row': None, 'amount_row': None}
            
            # Определяем тип строки (объемы или финансы)
            if indicator.endswith(' - Объемы'):
                groups_data[external_id]['quantity_row'] = row
            elif indicator.endswith(' - Финансы'):
                groups_data[external_id]['amount_row'] = row
        
        # Обрабатываем собранные данные
        for external_id, data in groups_data.items():
            quantity_row = data['quantity_row']
            amount_row = data['amount_row']
            
            # Пропускаем если нет хотя бы одной строки
            if quantity_row is None or amount_row is None:
                continue
            
            # Находим группу по external_id
            try:
                group = GroupIndicators.objects.get(external_id=external_id)
            except GroupIndicators.DoesNotExist:
                # Если не найдено, пропускаем
                continue
            
            # Получаем или создаем AnnualPlan
            annual_plan, created = AnnualPlan.objects.get_or_create(
                group=group,
                year=year,
                defaults={}
            )
            
            if created:
                imported += 1
            else:
                updated += 1
            
            # Обновляем месячные планы
            for month in range(1, 13):
                monthly_plan, _ = MonthlyPlan.objects.get_or_create(
                    annual_plan=annual_plan,
                    month=month,
                    defaults={'quantity': 0, 'amount': 0.00}
                )
                
                # Обновляем количество из строки объемов
                quantity_col = str(month)
                if quantity_col in quantity_row and pd.notna(quantity_row[quantity_col]):
                    try:
                        monthly_plan.quantity = int(float(quantity_row[quantity_col]))
                    except (ValueError, TypeError):
                        monthly_plan.quantity = 0
                
                # Обновляем сумму из строки финансов
                if quantity_col in amount_row and pd.notna(amount_row[quantity_col]):
                    try:
                        monthly_plan.amount = float(amount_row[quantity_col])
                    except (ValueError, TypeError):
                        monthly_plan.amount = 0.00
                
                monthly_plan.save()
        
        return {'imported': imported, 'updated': updated}

    def has_export_plans_permission(self, request):
        return request.user.has_perm('plan.export_plans')
    
    def has_import_plans_permission(self, request):
        return request.user.has_perm('plan.import_plans')


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
    extra = 0
    fields = ['operator', 'field_name', 'filter_type', 'values']


# Админка для UnifiedFilter с импортом/экспортом
@admin.register(UnifiedFilter)
class UnifiedFilterAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_class = UnifiedFilterResource
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


@admin.register(OrganizationIndicatorConfig)
class OrganizationIndicatorConfigAdmin(ModelAdmin):
    list_display = ('group', 'organization_code', 'is_enabled', 'created_at', 'updated_at')
    list_filter = ('is_enabled', 'organization_code', 'created_at')
    search_fields = ('group__name', 'organization_code', 'notes')
    fields = ('group', 'organization_code', 'is_enabled', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('group')


@admin.register(GoalGroupConfig)
class GoalGroupConfigAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ('name', 'groups', 'created_at', 'updated_at')

    formfield_overrides = {
        # Переключаемся на TextField (вместо JSONField)
        models.TextField: {'widget': JSONEditorWidget},
    }