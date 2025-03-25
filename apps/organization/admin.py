from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from unfold.admin import TabularInline, ModelAdmin

from .models import *
from import_export import resources


class DoctorAssignmentInline(TabularInline):
    model = DoctorAssignment
    extra = 0  # Убираем лишние пустые строки для добавления
    fields = ('doctor', 'start_date', 'end_date', 'reason_for_transfer')
    readonly_fields = ('doctor', 'start_date', 'end_date', 'reason_for_transfer')
    ordering = ['-start_date']  # Сортировка от новых к старым назначениям


@admin.register(Station)
class StationAdmin(ModelAdmin):
    list_display = ('name', 'code', 'department', 'doctor', 'open_date', 'close_date')
    list_filter = ('department',)
    search_fields = ('name', 'code')
    inlines = [DoctorAssignmentInline]  # Включаем инлайн для всех назначений врачей

    def get_doctors_list(self, obj):
        # Метод для отображения всех врачей, работавших на участке
        return ", ".join(
            f"{assignment.doctor} (с {assignment.start_date} по {assignment.end_date or 'настоящее время'})"
            for assignment in obj.doctor_assignments.all().order_by('-start_date')
        )

    get_doctors_list.short_description = "История врачей на участке"  # Название столбца в админке


@admin.register(MedicalOrganization)
class MedicalOrganizationAdmin(ModelAdmin):
    list_display = ('name', 'code_mo', 'name_kvazar', 'name_miskauz', 'address', 'phone_number', 'email')
    search_fields = ('name', 'address')
    ordering = ('name',)

    # Ограничение на создание только одной записи
    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = MedicalOrganization.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание


@admin.register(Building)
class BuildingAdmin(ModelAdmin):
    list_display = ('name', 'additional_name', 'organization', 'address', 'name_kvazar', 'name_miskauz')
    list_filter = ('organization',)
    search_fields = ('name', 'additional_name', 'address')
    list_editable = ('additional_name', 'name_kvazar', 'name_miskauz')


class OMSDepartmentInline(TabularInline):
    model = OMSDepartment
    extra = 1


class KvazarDepartmentInline(TabularInline):
    model = KvazarDepartment
    extra = 1


class MiskauzDepartmentInline(TabularInline):
    model = MiskauzDepartment
    extra = 1


class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = ('name', 'additional_name', 'building')
    list_filter = ('building',)
    search_fields = ('name',)
    resource_class = DepartmentResource

    inlines = [OMSDepartmentInline, KvazarDepartmentInline, MiskauzDepartmentInline]
