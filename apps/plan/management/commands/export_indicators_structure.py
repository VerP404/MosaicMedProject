"""
Management команда для экспорта структуры показателей (GroupIndicators) в JSON.
Используется на базовом сервере для создания фикстуры структуры.
"""
import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.plan.models import GroupIndicators, FilterCondition


class Command(BaseCommand):
    help = 'Экспортирует структуру показателей (GroupIndicators) в JSON файл для синхронизации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Путь к выходному JSON файлу (если не указан, используется папка fixtures)'
        )
        parser.add_argument(
            '--filename',
            type=str,
            default='indicators_structure.json',
            help='Имя файла в папке fixtures (используется если --output не указан)'
        )
        parser.add_argument(
            '--include-filters',
            action='store_true',
            help='Включить фильтры в экспорт'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Год для экспорта фильтров (если указан --include-filters)'
        )

    def handle(self, *args, **options):
        output_file = options.get('output')
        filename = options['filename']
        include_filters = options['include_filters']
        year = options.get('year')

        # Если output не указан, используем папку fixtures приложения
        if not output_file:
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            fixtures_dir = os.path.join(app_dir, 'fixtures')
            os.makedirs(fixtures_dir, exist_ok=True)
            output_file = os.path.join(fixtures_dir, filename)

        # Экспортируем только группы с включенной синхронизацией
        groups = GroupIndicators.objects.filter(sync_enabled=True).order_by('level', 'id')
        
        structure = {
            'version': '1.0',
            'export_date': str(datetime.now()),
            'groups': []
        }

        for group in groups:
            # Если у группы нет external_id, генерируем его
            if not group.external_id:
                import uuid
                group.external_id = str(uuid.uuid4())
                group.save(update_fields=['external_id'])
                self.stdout.write(
                    self.style.WARNING(f'Сгенерирован external_id для группы: {group.name}')
                )
            
            group_data = {
                'external_id': group.external_id,
                'name': group.name,
                'level': group.level,
                'is_distributable': group.is_distributable,
                'parent_external_id': group.parent.external_id if group.parent else None,
            }

            # Добавляем фильтры, если запрошено
            if include_filters:
                filters_query = FilterCondition.objects.filter(group=group)
                if year:
                    filters_query = filters_query.filter(year=year)
                
                group_data['filters'] = []
                for filter_condition in filters_query:
                    group_data['filters'].append({
                        'field_name': filter_condition.field_name,
                        'filter_type': filter_condition.filter_type,
                        'values': filter_condition.values,
                        'year': filter_condition.year,
                    })

            structure['groups'].append(group_data)

        # Сохраняем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно экспортировано {len(structure["groups"])} групп в {output_file}'
            )
        )

