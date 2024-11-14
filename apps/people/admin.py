from django.contrib import admin

from apps.people.models import ISZLPeopleReport


@admin.register(ISZLPeopleReport)
class StationAdmin(admin.ModelAdmin):
    list_display = ('date_report', 'people', 'smo', 'ss_doctor', 'lpuuch')
    list_filter = ('date_report', 'smo', 'ss_doctor', 'lpuuch')
    search_fields = ('people', 'lpuuch')
