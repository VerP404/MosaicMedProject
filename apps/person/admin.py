from django.contrib import admin
from .models import Insurance, InsurancePolicy, PhysicalPerson, AttachmentPeriod
from .forms import InsurancePolicyInlineFormSet


# Inline для полисов физического лица
class InsurancePolicyInline(admin.TabularInline):
    model = InsurancePolicy
    formset = InsurancePolicyInlineFormSet
    extra = 1
    fields = ('enp', 'start_date', 'end_date', 'insurance')
    verbose_name = "Полис"
    verbose_name_plural = "Полисы"


@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    # Полисы редактируются через inline, поэтому отдельную админку для InsurancePolicy регистрировать не будем.


@admin.register(PhysicalPerson)
class PhysicalPersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birth_date', 'snils')
    search_fields = ('last_name', 'first_name', 'snils', 'phone')
    inlines = [InsurancePolicyInline]


@admin.register(AttachmentPeriod)
class AttachmentPeriodAdmin(admin.ModelAdmin):
    list_display = ('physical_person', 'report_date', 'station', 'start_date', 'end_date', 'enp')
    search_fields = (
        'physical_person__last_name',
        'physical_person__first_name',
        'enp',
    )
    list_filter = ('report_date', 'station')
    autocomplete_fields = ('physical_person', 'station')
