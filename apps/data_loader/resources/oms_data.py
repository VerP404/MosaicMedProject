import pandas as pd
from import_export import resources
from apps.data_loader.models.oms_data import OMSData
from django.contrib import messages

class OMSDataResource(resources.ModelResource):
    class Meta:
        model = OMSData

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        request = kwargs.get('request')

        # Загрузка файла с pandas
        try:
            df = pd.read_csv('path_to_file', sep=';', low_memory=False, na_values="-", dtype='str')
        except Exception as e:
            error_message = f"Ошибка при чтении файла: {str(e)}"
            if request:
                messages.error(request, error_message)
            raise ValueError(error_message)

        # Если количество колонок неверное
        if len(df.columns) != 53:
            error_message = f"Ошибка импорта: Ожидалось 53 столбца, но найдено {len(df.columns)}."
            if request:
                messages.error(request, error_message)
            raise ValueError(error_message)
