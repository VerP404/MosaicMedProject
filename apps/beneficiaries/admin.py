from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Patient, BenefitCategory, Drug, PatientDrugSupply, DrugStock

@admin.register(BenefitCategory)
class BenefitCategoryAdmin(ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)

@admin.register(Patient)
class PatientAdmin(ModelAdmin):
    list_display = ("full_name", "birth_date", "snils", "enp", "benefit_category", "diagnosis_code", "is_active")
    search_fields = ("full_name", "snils", "enp", "diagnosis_code")
    list_filter = ("benefit_category", "is_active")

@admin.register(Drug)
class DrugAdmin(ModelAdmin):
    list_display = ("name", "inn", "code", "is_active")
    search_fields = ("name", "inn", "code")
    list_filter = ("is_active",)

@admin.register(PatientDrugSupply)
class PatientDrugSupplyAdmin(ModelAdmin):
    list_display = ("patient", "drug", "monthly_need", "prescribed", "prescription_date", "supplied_until", "last_update")
    search_fields = ("patient__full_name", "drug__name")
    list_filter = ("drug", "prescription_date", "supplied_until")

@admin.register(DrugStock)
class DrugStockAdmin(ModelAdmin):
    list_display = ("drug", "quantity", "updated_at")
    search_fields = ("drug__name",)
