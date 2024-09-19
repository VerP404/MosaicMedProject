# admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.data_loader.models.oms_data import OMSData
from apps.data_loader.resources.oms_data import OMSDataResource


@admin.register(OMSData)
class OMSDataAdmin(ImportExportModelAdmin):
    resource_class = OMSDataResource
