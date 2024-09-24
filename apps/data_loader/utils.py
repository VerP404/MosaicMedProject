# apps/data_loader/utils.py
from apps.data_loader.selenium_script import logger


def process_csv_file(file_path):
    import csv
    from .models.oms_data import OMSData
    from .admin import OMS_DATA_CSV_TO_MODEL_MAPPING

    added_count = 0
    updated_count = 0
    error_count = 0

    with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')
        for row in reader:
            oms_data = {}
            for csv_field, model_field in OMS_DATA_CSV_TO_MODEL_MAPPING.items():
                oms_data[model_field] = row.get(csv_field, '')

            try:
                obj, created = OMSData.objects.update_or_create(
                    talon=oms_data['talon'],
                    defaults=oms_data
                )
                if created:
                    added_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке строки: {row}", exc_info=True)
                error_count += 1

    return added_count, updated_count, error_count
