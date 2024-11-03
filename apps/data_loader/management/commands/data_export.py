# data_export.py
from django.core.management.base import BaseCommand
import json
import os

from apps.data_loader.models.oms_data import DataTypeFieldMapping, DataLoaderConfig, DataType, Category


class Command(BaseCommand):
    help = 'Экспорт данных из таблиц Category, DataType, DataTypeFieldMapping и DataLoaderConfig в JSON'

    def handle(self, *args, **kwargs):
        # Экспорт всех полей из таблицы data_loader_category
        categories = list(Category.objects.values(
            'id',            # ID категории
            'name',          # Имя категории
            'description'    # Описание категории
        ))

        # Экспорт всех полей из таблицы data_loader_datatype
        datatypes = list(DataType.objects.values(
            'id',            # ID типа данных
            'name',          # Имя типа данных
            'description',   # Описание типа данных
            'category_id'    # Внешний ключ на категорию
        ))

        # Экспорт всех полей из таблицы data_loader_datatypefieldmapping
        field_mappings = list(DataTypeFieldMapping.objects.values(
            'id',                   # ID записи
            'data_type_id',         # Внешний ключ на DataType
            'csv_column_name',      # Название столбца в CSV
            'model_field_name'      # Название поля в модели
        ))

        # Экспорт всех полей из таблицы data_loader_dataloaderconfig
        dataloader_configs = list(DataLoaderConfig.objects.values(
            'id',                 # ID конфигурации
            'table_name',         # Имя таблицы
            'column_check',       # Столбец для проверки
            'columns_for_update', # Столбцы для обновления
            'encoding',           # Кодировка файла
            'delimiter',          # Разделитель
            'data_type_id'        # Внешний ключ на DataType
        ))

        data = {
            "Category": categories,
            "DataType": datatypes,
            "DataTypeFieldMapping": field_mappings,
            "DataLoaderConfig": dataloader_configs,
        }

        # Сохранение JSON в папку data_updates
        os.makedirs('data_updates', exist_ok=True)
        with open('data_updates/data_export.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(self.style.SUCCESS("Данные успешно экспортированы в data_updates/data_export.json"))