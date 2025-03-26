from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.load_data.models import LoadLog


@admin.register(LoadLog)
class LoadLogAdmin(ModelAdmin):
    list_display = (
        'table_name',
        'start_time',
        'end_time',
        'count_before',
        'count_after',
        'duration',
        'error_occurred',
        'error_code',
        'run_url'
    )
    list_filter = ('table_name', 'error_occurred')
    search_fields = ('table_name', 'error_code')
