from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Person, Encounter, Observation


class ObservationInline(TabularInline):
    model = Observation
    extra = 0
    # Можно задать поля, которые будут отображаться:
    fields = (
        'pdwid', 'plan_month', 'plan_year', 'date_begin', 'date_end', 'effective_from', 'effective_to', 'is_current')
    readonly_fields = ('effective_from',)


class EncounterInline(TabularInline):
    model = Encounter
    extra = 0
    fields = ('pid', 'ldwid', 'ds')
    inlines = [ObservationInline]


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    list_display = ('fio', 'enp', 'dr')
    search_fields = ('fio', 'enp')
    inlines = [EncounterInline]
