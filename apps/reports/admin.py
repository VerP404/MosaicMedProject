from datetime import datetime

import openpyxl
from django.contrib import admin
from django.http import HttpResponse
from import_export.admin import ImportExportModelAdmin

from unfold.admin import ModelAdmin

from apps.reports.models import DeleteEmd, InvalidationReason, SVOMember, SVOMemberOMSData, PatientAction, Patient, \
    Site, ActionType, Group, DPChildDetail, UserGroupAccess
from apps.reports.resources import PatientResource


@admin.register(DeleteEmd)
class DeleteEmdAdmin(ModelAdmin):
    list_display = ('oid_medical_organization', 'oid_document', 'goal', 'added_date')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # при редактировании объекта
            return self.readonly_fields + ('oid_medical_organization',)
        return self.readonly_fields


@admin.register(InvalidationReason)
class InvalidationReasonAdmin(ModelAdmin):
    list_display = ('reason_text',)


def update_oms_data_action(modeladmin, request, queryset):
    """
    Действие для обновления данных участников СВО на основе информации из OMSData.
    """
    for member in queryset:
        member.update_oms_data()
    modeladmin.message_user(request, "Данные успешно обновлены для выбранных участников.")


update_oms_data_action.short_description = "Обновить данные из OMSData"


def export_to_excel_action(modeladmin, request, queryset):
    """
    Действие для экспорта данных участников СВО в Excel.
    """
    # Создаем новый workbook и активируем его
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Участники СВО"

    # Добавляем заголовки
    ws.append(['№', 'ФИО', 'Дата рождения', 'Подразделение', 'Адрес', 'Телефон', 'Цели', 'Диагнозы'])

    # Заполняем данные для каждого участника
    for idx, member in enumerate(queryset, start=1):
        # Получаем цели и диагнозы, если есть связанные записи
        goals = ', '.join([data.goal for data in member.oms_data.all() if data.goal])
        diagnoses = ', '.join([data.main_diagnosis for data in member.oms_data.all() if data.main_diagnosis])

        # Преобразуем дату рождения в формат дд.мм.гггг
        birth_date_formatted = member.birth_date.strftime('%d.%m.%Y') if member.birth_date else ''

        # Заполняем строку данными
        ws.append([
            idx,
            f"{member.last_name} {member.first_name} {member.middle_name}",  # ФИО
            birth_date_formatted,  # Дата рождения в формате дд.мм.гггг
            member.department,  # Подразделение
            member.address,  # Адрес
            member.phone,  # Телефон
            goals,  # Цели
            diagnoses  # Диагнозы
        ])

    # Получаем текущую дату в формате ддммгггг
    current_date = datetime.now().strftime('%d%m%Y')

    # Формируем имя файла с текущей датой
    filename = f"SVO_{current_date}.xlsx"

    # Создаем HTTP-ответ с Excel-файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Сохраняем workbook в HTTP-ответ
    wb.save(response)
    return response


export_to_excel_action.short_description = "Выгрузить данные в Excel"


def export_dv4_opv_report_action(modeladmin, request, queryset):
    """
    Действие для экспорта данных о пациентах с целью ДВ4 и ОПВ в Excel.
    """
    # Создаем новый workbook и активируем его
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчет по целям ДВ4 и ОПВ"

    # Добавляем заголовки
    ws.append(['Цель', 'Количество пациентов'])

    # Считаем общее количество пациентов
    total_patients = queryset.count()

    # Считаем количество пациентов с целью "ДВ4" и "ОПВ"
    dv4_count = SVOMemberOMSData.objects.filter(svomember__in=queryset, goal='ДВ4').count()
    opv_count = SVOMemberOMSData.objects.filter(svomember__in=queryset, goal='ОПВ').count()

    # Добавляем данные в отчет
    ws.append(['Всего пациентов', total_patients])
    ws.append(['Пациенты с целью ДВ4', dv4_count])
    ws.append(['Пациенты с целью ОПВ', opv_count])

    # Получаем текущую дату в формате ддммгггг
    current_date = datetime.now().strftime('%d%m%Y')

    # Формируем имя файла с текущей датой
    filename = f"SVO_DV4_OPV_{current_date}.xlsx"

    # Создаем HTTP-ответ с Excel-файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    # Сохраняем workbook в HTTP-ответ
    wb.save(response)
    return response


export_dv4_opv_report_action.short_description = "Выгрузить отчет по ДВ4 и ОПВ"


class SVOMemberOMSDataInline(admin.TabularInline):
    model = SVOMemberOMSData
    extra = 0  # Не показывать пустые строки для новых записей
    readonly_fields = ('talon', 'goal', 'treatment_end', 'main_diagnosis')


class HasDV4OrOPVFilter(admin.SimpleListFilter):
    """
    Кастомный фильтр, проверяющий наличие целей "ДВ4" или "ОПВ" у участников СВО.
    """
    title = 'Наличие цели ДВ4/ОПВ'
    parameter_name = 'has_dv4_opv'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(oms_data__goal__in=['ДВ4', 'ОПВ']).distinct()
        if self.value() == 'no':
            return queryset.exclude(oms_data__goal__in=['ДВ4', 'ОПВ']).distinct()
        return queryset


@admin.register(SVOMember)
class SVOMemberAdmin(ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'phone', 'enp', 'department', 'has_dv4_opv')
    search_fields = ('last_name', 'first_name', 'enp')
    list_filter = ('department', HasDV4OrOPVFilter, 'enp')
    inlines = [SVOMemberOMSDataInline]  # Inline для связанной модели OMS данных
    actions = [update_oms_data_action, export_to_excel_action, export_dv4_opv_report_action]  # Действия админки

    def has_dv4_opv(self, obj):
        """
        Проверяет, есть ли у участника цель "ДВ4" или "ОПВ".
        """
        return obj.oms_data.filter(goal__in=['ДВ4', 'ОПВ']).exists()

    has_dv4_opv.boolean = True
    has_dv4_opv.short_description = 'ДВ4/ОПВ'

    def save_model(self, request, obj, form, change):
        """
        Сохраняем участника СВО и обновляем OMS данные, если изменилось что-то.
        """
        super().save_model(request, obj, form, change)
        obj.update_oms_data()  # Вызов метода для обновления данных из OMSData


# Новый отчет
# 1) Inline для ActionType в админке Группы:
class ActionTypeInline(admin.TabularInline):
    model = ActionType
    extra = 1
    # Если хотите, можно добавить поля, которые будут редактироваться:
    fields = ('name',)


# Регистрируем Group без отдельной регистрации ActionType;
# теперь действия (ActionType) создаются/редактируются прямо в группе (inline).
@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [ActionTypeInline]


# 2) Участки: добавить фильтр по корпусам:
@admin.register(Site)
class SiteAdmin(ModelAdmin):
    list_display = ('building', 'site_name')
    search_fields = ('building', 'site_name')
    list_filter = ('building',)  # Фильтр по корпусам


# 3) Пациент: добавить отображение категорий (групп),
#    сделать инлайн с действиями (PatientAction),
#    при этом нужно понимать, к какой группе относится действие.
class PatientActionInline(admin.TabularInline):
    model = PatientAction
    extra = 0
    # Отобразим поле, чтобы видеть группу действия (только для чтения)
    readonly_fields = ('action_group',)
    fields = ('action_group', 'action', 'done', 'done_datetime', 'comment')
    ordering = ('done_datetime',)
    ordering_field = 'done_datetime'

    def action_group(self, obj):
        """
        Показываем группу, к которой относится выбранный ActionType.
        """
        if obj.action:
            return obj.action.group.name
        return "-"

    action_group.short_description = 'Группа действия'


class DPChildDetailInline(admin.StackedInline):
    model = DPChildDetail
    can_delete = False
    extra = 0
    verbose_name = 'Детали ЛЛО'
    verbose_name_plural = 'Дети‑инвалиды ЛЛО: детали'
    readonly_fields = ('created', 'modified', 'created_by')
    ordering_field = None



@admin.register(Patient)
class PatientAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = PatientResource  # указываем ресурс
    list_display = ('full_name', 'date_of_birth', 'enp', 'gender', 'phone', 'site', 'is_parent', 'get_groups')
    list_filter = ('gender', 'groups', 'site')
    list_editable = ('is_parent',)
    search_fields = ('full_name', 'phone', 'address', 'enp')

    # inlines = [PatientActionInline]  # ваш inline для PatientAction

    def get_parents(self, obj):
        return ", ".join(p.full_name for p in obj.parents.all())

    get_parents.short_description = 'Родители'

    def get_groups(self, obj):
        return ", ".join(g.name for g in obj.groups.all())

    get_groups.short_description = 'Группы'

    def get_inline_instances(self, request, obj=None):
        """
        Динамически подключаем инлайны в зависимости от прав:
          - patient_action: если есть perm 'reports.view_patientaction'
          - dp_detail:      если есть perm 'reports.view_dpchilddetail'
        """
        inlines = []
        if request.user.has_perm('reports.view_patientaction'):
            inlines.append(PatientActionInline(self.model, self.admin_site))
        if request.user.has_perm('reports.view_dpchilddetail'):
            inlines.append(DPChildDetailInline(self.model, self.admin_site))
        return inlines

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # показываем только пациентов из тех групп, к которым у user есть доступ
        allowed = request.user.usergroupaccess_set.values_list('group_id', flat=True)
        return qs.filter(groups__in=allowed).distinct()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'groups' and not request.user.is_superuser:
            allowed = request.user.usergroupaccess_set.values_list('group_id', flat=True)
            kwargs['queryset'] = db_field.related_model.objects.filter(id__in=allowed)
        if db_field.name == 'parents':
            kwargs['queryset'] = Patient.objects.filter(is_parent=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # импорт/экспорт
    def get_export_queryset(self, request, queryset):
        if request.user.is_superuser:
            return queryset
        allowed = request.user.usergroupaccess_set.values_list('group_id', flat=True)
        return queryset.filter(groups__in=allowed).distinct()

    def get_export_resource_kwargs(self, request, *args, **kwargs):
        return {'context': {'request': request}}


@admin.register(DPChildDetail)
class DPChildDetailAdmin(ModelAdmin):
    readonly_fields = ('created', 'modified', 'created_by')
    exclude = ()  # если хотите вовсе скрыть created_by из форм

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
