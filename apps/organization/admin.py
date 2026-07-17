import json
from datetime import datetime

from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from unfold.admin import TabularInline, ModelAdmin
from unfold.decorators import action

from .forms import ExportPortalStructureForm, ImportNativeStructureForm
from .models import *
from .services.structure_io import (
    build_native_structure,
    build_portal_medical_structure,
    import_native_structure,
)


class DoctorAssignmentInline(TabularInline):
    model = DoctorAssignment
    extra = 0
    fields = ('doctor', 'start_date', 'end_date', 'reason_for_transfer')
    readonly_fields = ('doctor', 'start_date', 'end_date', 'reason_for_transfer')
    ordering = ['-start_date']


@admin.register(Station)
class StationAdmin(ModelAdmin):
    list_display = ('name', 'code', 'department', 'doctor', 'open_date', 'close_date')
    list_filter = ('department',)
    search_fields = ('name', 'code')
    inlines = [DoctorAssignmentInline]

    def get_doctors_list(self, obj):
        return ", ".join(
            f"{assignment.doctor} (с {assignment.start_date} по {assignment.end_date or 'настоящее время'})"
            for assignment in obj.doctor_assignments.all().order_by('-start_date')
        )

    get_doctors_list.short_description = "История врачей на участке"


@admin.register(MedicalOrganization)
class MedicalOrganizationAdmin(ModelAdmin):
    list_display = ('name', 'code_mo', 'name_kvazar', 'name_miskauz', 'address', 'phone_number', 'email')
    search_fields = ('name', 'address')
    ordering = ('name',)
    actions_list = [
        "export_portal_structure",
        "export_native_structure",
        "import_native_structure_action",
    ]

    def has_add_permission(self, request):
        count = MedicalOrganization.objects.all().count()
        if count >= 1:
            return False
        return True

    def _json_download(self, payload: dict, filename: str) -> HttpResponse:
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        response = HttpResponse(content, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(
        description=_("Скачать для Portal"),
        url_path="export-portal-structure",
        permissions=["export_portal_structure"],
    )
    def export_portal_structure(self, request: HttpRequest):
        """Экспорт в medical_structure.json Portal — скачивание в браузер."""
        form = ExportPortalStructureForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            try:
                merge_from = None
                merge_file = form.cleaned_data.get('merge_file')
                if merge_file:
                    merge_from = json.load(merge_file)

                payload = build_portal_medical_structure(
                    region_code=form.cleaned_data['region_code'],
                    region_name=form.cleaned_data['region_name'],
                    org_code=form.cleaned_data.get('org_code') or None,
                    merge_from=merge_from,
                )
                org_code = payload['regions'][0]['organizations'][0]['org_code']
                stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"medical_structure_portal_{org_code}_{stamp}.json"
                return self._json_download(payload, filename)
            except Exception as exc:
                messages.error(request, f'Ошибка экспорта: {exc}')

        context = {
            'form': form,
            'title': 'Экспорт структуры для MosaicPortal',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/organization/export_portal_structure.html', context)

    @action(
        description=_("Скачать native JSON"),
        url_path="export-native-structure",
        permissions=["export_native_structure"],
    )
    def export_native_structure(self, request: HttpRequest):
        """Полный снимок структуры MedProject — скачивание в браузер."""
        try:
            payload = build_native_structure()
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            code = (payload.get('organization') or {}).get('code_mo') or 'mo'
            filename = f"organization_structure_medproject_{code}_{stamp}.json"
            return self._json_download(payload, filename)
        except Exception as exc:
            messages.error(request, f'Ошибка экспорта: {exc}')
            return redirect('admin:organization_medicalorganization_changelist')

    @action(
        description=_("Импорт native JSON"),
        url_path="import-native-structure",
        permissions=["import_native_structure"],
    )
    def import_native_structure_action(self, request: HttpRequest):
        """Импорт native JSON, загруженного через браузер."""
        form = ImportNativeStructureForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            try:
                data = json.load(form.cleaned_data['file'])
                stats = import_native_structure(
                    data,
                    clear_tree=form.cleaned_data.get('clear_tree', False),
                    link_doctors=form.cleaned_data.get('link_doctors', True),
                )
                messages.success(
                    request,
                    (
                        'Структура импортирована: '
                        f"корпусов={stats['buildings']}, отделений={stats['departments']}, "
                        f"ОМС={stats['oms']}, Квазар={stats['kvazar']}, МИСКАУЗ={stats['miskauz']}, "
                        f"участков={stats['stations']}, назначений={stats['assignments']}"
                    ),
                )
                return redirect('admin:organization_medicalorganization_changelist')
            except Exception as exc:
                messages.error(request, f'Ошибка импорта: {exc}')

        context = {
            'form': form,
            'title': 'Импорт структуры MedProject',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/organization/import_native_structure.html', context)

    def has_export_portal_structure_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_export_native_structure_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_import_native_structure_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff


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
