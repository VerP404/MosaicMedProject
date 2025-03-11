from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from apps.organizations.models import ActiveOrganization, Department
from .models import (
    Employee, Position, Specialty, Profile,
    Appointment, MaternityLeave, DoctorCode
)


def get_active_organization():
    """
    Возвращает объект организации, установленный как активный.
    Если активной организации нет – возвращает None.
    """
    active_record = ActiveOrganization.objects.filter(is_active=True).first()
    if active_record:
        return active_record.organization
    return None


# Inline для назначений в карточке сотрудника
class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0  # пустые формы не отображаются автоматически
    fields = ('position', 'specialty', 'profile', 'rate', 'department', 'start_date', 'end_date')
    verbose_name = "Назначение"
    verbose_name_plural = "Назначения"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('physical_person', 'payroll_number', 'status')
    search_fields = ('physical_person__last_name', 'physical_person__first_name', 'payroll_number')
    autocomplete_fields = ('physical_person',)
    inlines = [AppointmentInline]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


# Inline для декрета в назначении
class MaternityLeaveInline(admin.TabularInline):
    model = MaternityLeave
    extra = 0
    fields = ('start_date', 'planned_end_date', 'actual_end_date', 'comment')
    verbose_name = "Декрет"
    verbose_name_plural = "Декреты"


# Inline для кода врача в назначении
class DoctorCodeInline(admin.TabularInline):
    model = DoctorCode
    extra = 0
    fields = ('code',)
    verbose_name = "Код врача"
    verbose_name_plural = "Коды врачей"


class ActiveDepartmentListFilter(SimpleListFilter):
    title = 'Отделение (активное)'
    parameter_name = 'department'

    def lookups(self, request, model_admin):
        active_org = get_active_organization()
        if active_org:
            qs = Department.objects.filter(building__organization=active_org)
        else:
            qs = Department.objects.none()
        # Возвращаем список кортежей: (pk, имя отделения)
        return [(dept.pk, dept.name) for dept in qs.order_by('name')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department__pk=self.value())
        return queryset


class ActiveBuildingListFilter(SimpleListFilter):
    title = 'Корпус (активный)'
    parameter_name = 'building'

    def lookups(self, request, model_admin):
        active_org = get_active_organization()
        if active_org:
            # Получаем список уникальных корпусов, связанных с отделениями активной организации
            qs = Department.objects.filter(building__organization=active_org).values_list('building__id',
                                                                                          'building__name').distinct()
            return [(item[0], item[1]) for item in qs]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department__building__id=self.value())
        return queryset


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'position', 'department', 'start_date', 'end_date')
    # Добавляем фильтры: по позиции, по отделению (активный) и по корпусу (активный), а также по дате начала
    list_filter = ('position', ActiveDepartmentListFilter, ActiveBuildingListFilter, 'start_date')
    search_fields = ('employee__physical_person__last_name', 'position__name')
    inlines = [MaternityLeaveInline, DoctorCodeInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "department":
            active_org = get_active_organization()
            if active_org:
                # Ограничиваем выбор отделений через связь: Department -> Building -> organization
                kwargs["queryset"] = Department.objects.filter(building__organization=active_org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
