from django.contrib import admin

from apps.data.models.registry.nothospitalized import PatientRegistry


@admin.register(PatientRegistry)
class PatientRegistryAdmin(admin.ModelAdmin):
    list_display = ('number', 'full_name', 'date_of_birth', 'admission_date', 'refusal_reason')
    list_filter = ('referral_method', 'refusal_reason', 'admission_date')
    search_fields = ('full_name', 'phone', 'hospital_name', 'admission_diagnosis')
