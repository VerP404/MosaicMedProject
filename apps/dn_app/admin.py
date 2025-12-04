from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from .models import Person, Encounter, Observation, DataImport


class ObservationInline(TabularInline):
    model = Observation
    extra = 0
    fields = (
        'pdwid', 'plan_month', 'plan_year', 'status', 'actual_date', 
        'talon_number', 'date_begin', 'date_end', 'is_current'
    )
    readonly_fields = ('effective_from',)


class EncounterInline(TabularInline):
    model = Encounter
    extra = 0
    fields = ('pid', 'ldwid', 'ds')
    inlines = [ObservationInline]


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    list_display = ('fio', 'enp', 'dr', 'is_detached', 'last_import_date')
    list_filter = ('is_detached', 'last_import_date')
    search_fields = ('fio', 'enp')
    inlines = [EncounterInline]
    readonly_fields = ('detached_date', 'last_import_date')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('enp', 'fio', 'dr')
        }),
        ('Статус', {
            'fields': ('is_detached', 'detached_date', 'last_import_date')
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['upload_url'] = reverse('dn_app:upload_csv')
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Encounter)
class EncounterAdmin(ModelAdmin):
    list_display = ('person', 'ds', 'ldwid', 'pid')
    list_filter = ('ds',)
    search_fields = ('person__fio', 'person__enp', 'ds', 'ldwid')
    raw_id_fields = ('person',)


@admin.register(Observation)
class ObservationAdmin(ModelAdmin):
    list_display = ('encounter', 'pdwid', 'plan_year', 'plan_month', 'status', 'actual_date', 'is_current')
    list_filter = ('status', 'plan_year', 'is_current', 'plan_month')
    search_fields = ('encounter__person__fio', 'encounter__person__enp', 'pdwid', 'talon_number')
    raw_id_fields = ('encounter', 'import_batch')
    readonly_fields = ('effective_from', 'effective_to')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('encounter', 'pdwid', 'import_batch')
        }),
        ('Планирование', {
            'fields': ('plan_year', 'plan_month', 'date_begin', 'date_end')
        }),
        ('Статус и выполнение', {
            'fields': ('status', 'actual_date', 'talon_number')
        }),
        ('История', {
            'fields': ('is_current', 'effective_from', 'effective_to')
        }),
    )


@admin.register(DataImport)
class DataImportAdmin(ModelAdmin):
    list_display = ('year', 'file_name', 'import_date', 'status', 'total_rows', 'processed_rows')
    list_filter = ('status', 'year', 'import_date')
    search_fields = ('file_name',)
    readonly_fields = (
        'import_date', 'total_rows', 'processed_rows', 'created_persons', 
        'updated_persons', 'created_encounters', 'created_observations', 
        'detached_patients', 'error_message'
    )
    
    fieldsets = (
        ('Информация о загрузке', {
            'fields': ('year', 'file_name', 'file_path', 'import_date', 'status')
        }),
        ('Статистика', {
            'fields': (
                'total_rows', 'processed_rows', 'created_persons', 
                'updated_persons', 'created_encounters', 'created_observations', 
                'detached_patients'
            )
        }),
        ('Ошибки', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Загрузки создаются только через форму загрузки
