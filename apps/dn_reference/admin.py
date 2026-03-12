from io import StringIO

from django.contrib import admin
from django.core.management import call_command
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
    list_display = ("code", "name", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("order", "code")
    inlines = (DnServiceRequirementInline, DnServicePriceInline)
    actions = ("refresh_dn_reference_from_files",)

    @admin.action(description="Обновить все справочники ДН из файлов")
    def refresh_dn_reference_from_files(self, request, queryset):
        output = StringIO()
        try:
            call_command("refresh_dn_reference", stdout=output)
            self.message_user(
                request,
                "Справочники ДН успешно обновлены из файлов.",
            )
        except Exception as exc:
            self.message_user(
                request,
                f"Ошибка обновления справочников ДН: {exc}",
                level="error",
            )


@admin.register(DnServicePricePeriod)
class DnServicePricePeriodAdmin(ModelAdmin):
    list_display = ("title", "date_start", "date_end", "is_active")
    list_filter = ("is_active",)
    ordering = ("-date_start", "date_end")

