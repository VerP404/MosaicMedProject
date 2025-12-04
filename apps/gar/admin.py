from django.contrib import admin
from .models import GarAddress, GarLoadHistory


@admin.register(GarAddress)
class GarAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'region_code', 'area', 'city', 'settlement', 'street', 'house', 'apartment')
    list_filter = ('region_code', 'area', 'city')
    search_fields = ('street', 'house', 'apartment', 'postal_code')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50


@admin.register(GarLoadHistory)
class GarLoadHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'region_code', 'status', 'records_loaded', 'started_at', 'completed_at')
    list_filter = ('status', 'region_code')
    readonly_fields = ('started_at', 'completed_at', 'error_message')
    list_per_page = 50



