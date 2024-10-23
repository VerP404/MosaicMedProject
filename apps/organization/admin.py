from django.contrib import admin
from .models import *


@admin.register(MedicalOrganization)
class MedicalOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code_mo', 'name_kvazar', 'name_miskauz', 'address', 'phone_number', 'email')
    search_fields = ('name', 'address')

    # Ограничение на создание только одной записи
    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = MedicalOrganization.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'additional_name', 'organization', 'address', 'name_kvazar', 'name_miskauz')
    list_filter = ('organization',)
    search_fields = ('name', 'additional_name', 'address')
    list_editable = ('additional_name', 'name_kvazar', 'name_miskauz')


class OMSDepartmentInline(admin.TabularInline):
    formfield_overrides = {
        models.CharField: {'widget': admin.widgets.AdminTextInputWidget(attrs={'style': 'width: 100%;'})},
    }
    model = OMSDepartment
    extra = 1


class KvazarDepartmentInline(admin.TabularInline):
    formfield_overrides = {
        models.CharField: {'widget': admin.widgets.AdminTextInputWidget(attrs={'style': 'width: 100%;'})},
    }
    model = KvazarDepartment
    extra = 1


class MiskauzDepartmentInline(admin.TabularInline):
    formfield_overrides = {
        models.CharField: {'widget': admin.widgets.AdminTextInputWidget(attrs={'style': 'width: 100%;'})},
    }
    model = MiskauzDepartment
    extra = 1


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'additional_name', 'building')
    list_filter = ('building',)
    search_fields = ('name',)

    inlines = [OMSDepartmentInline, KvazarDepartmentInline, MiskauzDepartmentInline]

    formfield_overrides = {
        models.CharField: {'widget': admin.widgets.AdminTextInputWidget(attrs={'style': 'width: 100%;'})},
    }
