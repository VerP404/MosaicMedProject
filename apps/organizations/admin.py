from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from .models import (
    Organization,
    ActiveOrganization,
    Building,
    Department,
    Station,
    SourceSystem,
    RelatedDepartment, StationDoctorAssignment
)


# Inline для отделений внутри корпуса
class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 1


# Inline для записи связи с внешними системами внутри отделения
class RelatedDepartmentInline(admin.TabularInline):
    model = RelatedDepartment
    extra = 1


class StationDoctorAssignmentInline(admin.TabularInline):
    model = StationDoctorAssignment
    extra = 0
    fields = ('doctor', 'appointment_date', 'removal_date')
    verbose_name = 'Назначение врача'
    verbose_name_plural = 'Назначения врачей'


def get_active_organization():
    """
    Возвращает объект организации из ActiveOrganization,
    для которого is_active=True. Если активной организации нет – возвращает None.
    """
    active = ActiveOrganization.objects.filter(is_active=True).first()
    if active:
        return active.organization
    return None


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code_mo', 'oid_mo', 'region')
    list_filter = ('region',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        active_org = get_active_organization()
        if active_org:
            qs = qs.filter(pk=active_org.pk)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Если вдруг понадобится выбрать организацию в форме (например, в related inlines),
        то здесь ограничим выбор только активной организацией.
        """
        if db_field.name == "organization":
            active_org = get_active_organization()
            if active_org:
                kwargs["queryset"] = Organization.objects.filter(pk=active_org.pk)
                kwargs["initial"] = active_org
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ActiveOrganization)
class ActiveOrganizationAdmin(admin.ModelAdmin):
    list_display = ('organization', 'is_active')
    list_editable = ('is_active',)
    list_display_links = ('organization',)  # organization остаётся ссылкой для перехода в форму редактирования

    def has_add_permission(self, request):
        # Если уже существует запись, добавление новых запрещено.
        count = ActiveOrganization.objects.count()
        return count < 1


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')
    list_filter = (('organization', RelatedOnlyFieldListFilter),)
    inlines = [DepartmentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        active_org = get_active_organization()
        if active_org:
            qs = qs.filter(organization=active_org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор организации для корпуса только активной организацией.
        """
        if db_field.name == "organization":
            active_org = get_active_organization()
            if active_org:
                kwargs["queryset"] = Organization.objects.filter(pk=active_org.pk)
                kwargs["initial"] = active_org
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'building')
    list_filter = (('building', RelatedOnlyFieldListFilter),)
    inlines = [RelatedDepartmentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        active_org = get_active_organization()
        if active_org:
            qs = qs.filter(building__organization=active_org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор корпуса для отделения только корпусами активной организации.
        """
        if db_field.name == "building":
            active_org = get_active_organization()
            if active_org:
                kwargs["queryset"] = Building.objects.filter(organization=active_org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department')
    search_fields = ('name', 'code')
    list_filter = (('department__building', RelatedOnlyFieldListFilter),)
    inlines = [StationDoctorAssignmentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        active_org = get_active_organization()
        if active_org:
            qs = qs.filter(department__building__organization=active_org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор отделения для участка только теми, что принадлежат корпусам активной организации.
        """
        if db_field.name == "department":
            active_org = get_active_organization()
            if active_org:
                kwargs["queryset"] = Department.objects.filter(building__organization=active_org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(SourceSystem)
class SourceSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
