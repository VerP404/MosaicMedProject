from unfold.admin import ModelAdmin

from django.contrib import admin

from apps.dn_matrix import models as m


@admin.register(m.MatrixEdition)
class MatrixEditionAdmin(ModelAdmin):
    list_display = ("code", "title", "status", "effective_from", "effective_to", "max_doctor_visits")
    search_fields = ("code", "title")
    list_filter = ("status",)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ("code",)

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


class EditionFKAdmin(ModelAdmin):
    list_filter = ("edition",)


@admin.register(m.DnSpecialty)
class DnSpecialtyAdmin(EditionFKAdmin):
    list_display = ("code", "title", "edition", "sort_order")
    search_fields = ("code", "title")


@admin.register(m.DnDiagnosisCategory)
class DnDiagnosisCategoryAdmin(EditionFKAdmin):
    list_display = ("code", "title", "edition", "parent")
    search_fields = ("code", "title")


@admin.register(m.DnDiagnosis)
class DnDiagnosisAdmin(EditionFKAdmin):
    list_display = ("mkb_code", "title", "edition", "category")
    search_fields = ("mkb_code", "title")


@admin.register(m.DnDiagnosisSpecialty)
class DnDiagnosisSpecialtyAdmin(ModelAdmin):
    list_display = ("diagnosis", "specialty", "kind")
    list_filter = ("kind",)
    search_fields = ("diagnosis__mkb_code", "specialty__code", "specialty__title")


@admin.register(m.DnDiagnosisGroup)
class DnDiagnosisGroupAdmin(EditionFKAdmin):
    list_display = ("code", "title", "edition", "sort_order")
    search_fields = ("code", "title")


@admin.register(m.DnDiagnosisGroupMembership)
class DnDiagnosisGroupMembershipAdmin(ModelAdmin):
    list_display = ("group", "diagnosis")
    search_fields = ("group__code", "diagnosis__mkb_code")


@admin.register(m.DnService)
class DnServiceAdmin(EditionFKAdmin):
    list_display = ("code", "title", "sex_restriction", "edition", "sort_order")
    list_filter = ("sex_restriction", "edition")
    search_fields = ("code", "title")


@admin.register(m.DnServicePricePeriod)
class DnServicePricePeriodAdmin(EditionFKAdmin):
    list_display = ("code", "edition", "valid_from", "valid_to")


@admin.register(m.DnServicePrice)
class DnServicePriceAdmin(ModelAdmin):
    list_display = ("period", "service", "amount", "currency")
    search_fields = ("service__code", "service__title")


@admin.register(m.DnServiceRequirement)
class DnServiceRequirementAdmin(ModelAdmin):
    list_display = ("service", "specialty", "diagnosis", "diagnosis_group")
    search_fields = ("service__code", "service__title")
