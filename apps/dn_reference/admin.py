from io import StringIO

from django.contrib import admin, messages
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.urls import path, reverse
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    DnDiagnosis,
    DnDiagnosisCategory,
    DnDiagnosisGroup,
    DnDiagnosisGroupMembership,
    DnDiagnosisSpecialty,
    DnService,
    DnServicePrice,
    DnServicePricePeriod,
    DnServiceRequirement,
    DnSpecialty,
)


@admin.register(DnDiagnosisCategory)
class DnDiagnosisCategoryAdmin(ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(DnSpecialty)
class DnSpecialtyAdmin(ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


class DnDiagnosisSpecialtyInline(TabularInline):
    model = DnDiagnosisSpecialty
    extra = 0
    fields = ("specialty", "source")


@admin.register(DnDiagnosis)
class DnDiagnosisAdmin(ModelAdmin):
    list_display = ("code", "category", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("code",)
    inlines = (DnDiagnosisSpecialtyInline,)


class DnDiagnosisGroupMembershipInline(TabularInline):
    model = DnDiagnosisGroupMembership
    extra = 0
    fields = ("diagnosis", "is_active")


@admin.register(DnDiagnosisGroup)
class DnDiagnosisGroupAdmin(ModelAdmin):
    list_display = ("code", "title", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "title", "rule")
    ordering = ("order", "code")
    inlines = (DnDiagnosisGroupMembershipInline,)


class DnServiceRequirementInline(TabularInline):
    model = DnServiceRequirement
    extra = 0
    fields = ("group", "specialty", "is_required")


class DnServicePriceInline(TabularInline):
    model = DnServicePrice
    extra = 0
    fields = ("period", "price")


@admin.register(DnService)
class DnServiceAdmin(ModelAdmin):
    change_list_template = "admin/dn_reference/dnservice/change_list.html"
    list_display = ("code", "name", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("order", "code")
    inlines = (DnServiceRequirementInline, DnServicePriceInline)

    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path(
                "refresh-from-files/",
                self.admin_site.admin_view(self.refresh_from_files_view),
                name="dn_reference_dnservice_refresh_from_files",
            ),
        ]
        return extra_urls + urls

    def refresh_from_files_view(self, request):
        if not self.has_change_permission(request):
            return redirect("admin:dn_reference_dnservice_changelist")

        if request.method == "POST":
            output = StringIO()
            try:
                call_command("refresh_dn_reference", stdout=output, stderr=output)
            except Exception as exc:
                self.message_user(
                    request,
                    f"Ошибка обновления справочников ДН: {exc}",
                    level=messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    "Справочники ДН успешно обновлены из файлов.",
                    level=messages.SUCCESS,
                )
            return redirect("admin:dn_reference_dnservice_changelist")

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Обновить справочники ДН из файлов",
            "subtitle": "Команда полностью пересоздаст данные dn_reference из файлов в apps/dn_reference/data.",
            "changelist_url": reverse("admin:dn_reference_dnservice_changelist"),
        }
        return render(request, "admin/dn_reference/refresh_from_files.html", context)


@admin.register(DnServicePricePeriod)
class DnServicePricePeriodAdmin(ModelAdmin):
    list_display = ("title", "date_start", "date_end", "is_active")
    list_filter = ("is_active",)
    ordering = ("-date_start", "date_end")

