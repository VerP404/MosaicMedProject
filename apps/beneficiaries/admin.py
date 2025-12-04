from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import Patient, BenefitCategory, Drug, PatientDrugSupply, DrugStock


@admin.register(BenefitCategory)
class BenefitCategoryAdmin(ModelAdmin):
    list_display = ("name", "code", "is_for_children", "default_coverage_percentage", "is_active", "created_at")
    search_fields = ("name", "code", "description")
    list_filter = ("is_active", "is_for_children")
    ordering = ['name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description')
        }),
        ('Настройки', {
            'fields': ('default_coverage_percentage', 'financing_source', 'is_for_children', 'is_active')
        }),
    )


@admin.register(Patient)
class PatientAdmin(ModelAdmin):
    list_display = (
        "full_name", "age_display", "birth_date", "snils", "enp", 
        "benefit_category", "diagnosis_code", "is_active_display"
    )
    search_fields = ("full_name", "snils", "enp", "diagnosis_code", "phone")
    list_filter = ("benefit_category", "is_active", "benefit_category__is_for_children")
    ordering = ['full_name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'birth_date', 'snils', 'enp')
        }),
        ('Льготная категория', {
            'fields': ('benefit_category',)
        }),
        ('Диагноз', {
            'fields': ('diagnosis_code', 'diagnosis_name')
        }),
        ('Контактная информация', {
            'fields': ('address', 'phone')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )
    
    def age_display(self, obj):
        return f"{obj.age} лет"
    age_display.short_description = 'Возраст'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Активен</span>')
        else:
            return format_html('<span style="color: red;">✗ Неактивен</span>')
    is_active_display.short_description = 'Активность'


@admin.register(Drug)
class DrugAdmin(ModelAdmin):
    list_display = ("name", "inn", "code", "active_substance", "manufacturer", "is_active", "created_at")
    search_fields = ("name", "inn", "code", "active_substance", "manufacturer")
    list_filter = ("is_active", "dosage_form", "country")
    ordering = ['name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'inn', 'code', 'active_substance', 'atc_code')
        }),
        ('Характеристики', {
            'fields': ('dosage_form', 'dosage', 'manufacturer', 'country')
        }),
        ('Дополнительно', {
            'fields': ('description', 'is_active')
        }),
    )


@admin.register(PatientDrugSupply)
class PatientDrugSupplyAdmin(ModelAdmin):
    list_display = (
        "patient", "drug", "monthly_need", "prescribed", "prescription_date", 
        "supplied_until", "days_remaining_display", "status_display", "last_update"
    )
    search_fields = ("patient__full_name", "drug__name", "doctor_name", "recipe_number")
    list_filter = ("status", "prescription_date", "supplied_until")
    ordering = ['-last_update']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('patient', 'drug', 'status')
        }),
        ('Назначение', {
            'fields': ('monthly_need', 'dose_regimen', 'prescribed', 'doctor_name', 'recipe_number')
        }),
        ('Даты', {
            'fields': ('prescription_date', 'issue_date', 'supplied_until')
        }),
        ('Дополнительно', {
            'fields': ('note',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'active': 'green',
            'completed': 'blue',
            'cancelled': 'red',
            'expired': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    
    def days_remaining_display(self, obj):
        if obj.supplied_until:
            from django.utils import timezone
            today = timezone.now().date()
            days = (obj.supplied_until - today).days
            
            if days < 0:
                return format_html('<span style="color: red;">Истекло ({} дн.)</span>', abs(days))
            elif days <= 7:
                return format_html('<span style="color: orange;">⚠ {} дн.</span>', days)
            else:
                return format_html('<span style="color: green;">{} дн.</span>', days)
        return '-'
    days_remaining_display.short_description = 'Осталось дней'


@admin.register(DrugStock)
class DrugStockAdmin(ModelAdmin):
    list_display = ("drug", "quantity_display", "updated_at")
    search_fields = ("drug__name",)
    ordering = ['drug__name']
    
    def quantity_display(self, obj):
        if obj.quantity == 0:
            return format_html('<span style="color: red;">Нет в наличии</span>')
        elif obj.quantity < 10:
            return format_html('<span style="color: orange;">⚠ {} ед.</span>', obj.quantity)
        else:
            return format_html('<span style="color: green;">{} ед.</span>', obj.quantity)
    quantity_display.short_description = 'Количество'
