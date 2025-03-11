from django.contrib import admin
from .models import Source, TicketStatus, Goal, Ticket
from unfold.admin import ModelAdmin


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(TicketStatus)
class TicketStatusAdmin(ModelAdmin):
    list_display = ('code', 'name',)
    search_fields = ('code', 'name',)


@admin.register(Goal)
class GoalAdmin(ModelAdmin):
    list_display = ('code', 'name',)
    search_fields = ('code', 'name',)


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = (
        'number', 'patient', 'report_month', 'report_year',
        'formation_date', 'blocked'
    )
    list_filter = (
        'report_year', 'report_month', 'blocked', 'status'
    )
    search_fields = (
        'number', 'patient__last_name', 'patient__first_name', 'patient__snils'
    )
    date_hierarchy = 'formation_date'
