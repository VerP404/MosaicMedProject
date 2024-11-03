# data_import.py
from django.core.management.base import BaseCommand
from apps.data_loader.models.oms_data import DataTypeFieldMapping, DataLoaderConfig, DataType, Category
import json
import os


class Command(BaseCommand):
    help = 'Импорт данных из таблиц Category, DataType, DataTypeFieldMapping и DataLoaderConfig из JSON'

    def handle(self, *args, **kwargs):
        with open('data_updates/data_export.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Импорт данных в таблицу data_loader_category
        for item in data['Category']:
            Category.objects.update_or_create(
                id=item['id'],  # Указываем ID, чтобы сохранить связь
                defaults={
                    'name': item['name'],
                    'description': item.get('description')
                }
            )

        # Импорт данных в таблицу data_loader_datatype
        for item in data['DataType']:
            DataType.objects.update_or_create(
                id=item['id'],  # Указываем ID, чтобы сохранить связь
                defaults={
                    'name': item['name'],
                    'description': item.get('description'),
                    'category_id': item['category_id']
                }
            )

        # Импорт данных в таблицу data_loader_datatypefieldmapping
        for item in data['DataTypeFieldMapping']:
            DataTypeFieldMapping.objects.update_or_create(
                id=item['id'],  # Указываем ID, чтобы сохранить связь
                defaults={
                    'data_type_id': item['data_type_id'],
                    'csv_column_name': item['csv_column_name'],
                    'model_field_name': item['model_field_name']
                }
            )

        # Импорт данных в таблицу data_loader_dataloaderconfig
        for item in data['DataLoaderConfig']:
            DataLoaderConfig.objects.update_or_create(
                id=item['id'],  # Указываем ID, чтобы сохранить связь
                defaults={
                    'table_name': item['table_name'],
                    'column_check': item['column_check'],
                    'columns_for_update': item['columns_for_update'],
                    'encoding': item['encoding'],
                    'delimiter': item['delimiter'],
                    'data_type_id': item['data_type_id']  # Внешний ключ на DataType
                }
            )

        self.stdout.write(self.style.SUCCESS("Данные успешно импортированы из JSON"))
