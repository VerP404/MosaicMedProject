from unfold.admin import ModelAdmin

from django.contrib import admin

from apps.health_schools.models import HealthSchool


@admin.register(HealthSchool)
class HealthSchoolAdmin(ModelAdmin):
    list_display = (
        "number",
        "name",
        "visits",
        "service_code",
        "period_years",
        "criterion",
        "min_age",
        "max_age",
        "is_active",
    )
    list_editable = ("period_years", "is_active")
    list_filter = ("criterion", "is_active", "group_name")
    search_fields = ("name", "mkb_rule", "service_code", "service_title")
    ordering = ("number",)
