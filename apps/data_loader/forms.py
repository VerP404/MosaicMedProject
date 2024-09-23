from django.forms import ModelForm

from apps.data_loader.models.oms_data import *


class OMSDataImportForm(ModelForm):
    class Meta:
        model = OMSDataImport
        fields = ('csv_file',)
