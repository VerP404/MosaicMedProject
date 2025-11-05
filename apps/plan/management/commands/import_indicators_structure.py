"""
Management команда для импорта структуры показателей (GroupIndicators) из JSON.
Используется на клиентских серверах для синхронизации структуры с базовым сервером.
"""
import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from apps.plan.models import GroupIndicators, FilterCondition


class Command(BaseCommand):
    help = 'Импортирует структуру показателей (GroupIndicators) из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file',
            type=str,
            nargs='?',
            help='Путь к входному JSON файлу (если не указан, используется из папки fixtures)'
        )
        parser.add_argument(
            '--filename',
            type=str,
            default='indicators_structure.json',
            help='Имя файла в папке fixtures (используется если input_file не указан)'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Обновлять существующие группы, если они найдены по external_id'
        )
        parser.add_argument(
            '--delete-missing',
            action='store_true',
            help='Удалять группы, которых нет в импортируемом файле (опасно!)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без сохранения изменений'
        )

    def handle(self, *args, **options):
        input_file = options.get('input_file')
        filename = options['filename']
        update_existing = options['update_existing']
        delete_missing = options['delete_missing']
        dry_run = options['dry_run']

        # Если input_file не указан, используем папку fixtures приложения
        if not input_file:
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            fixtures_dir = os.path.join(app_dir, 'fixtures')
            input_file = os.path.join(fixtures_dir, filename)
            
            if not os.path.exists(input_file):
                self.stdout.write(
                    self.style.ERROR(f'Файл {input_file} не найден. Укажите путь к файлу или поместите файл в папку fixtures.')
                )
                return

        if dry_run:
            self.stdout.write(self.style.WARNING('Режим проверки (dry-run). Изменения не будут сохранены.'))

        # Загружаем структуру из файла
        with open(input_file, 'r', encoding='utf-8') as f:
            structure = json.load(f)

        if 'groups' not in structure:
            self.stdout.write(self.style.ERROR('Некорректный формат файла: отсутствует ключ "groups"'))
            return

        # Создаем словарь для быстрого поиска групп по external_id
        groups_by_external_id = {
            group.external_id: group
            for group in GroupIndicators.objects.all()
            if group.external_id
        }

        imported_external_ids = set()
        # Словарь для групп, которые будут созданы в этом импорте (для обработки parent_external_id)
        new_groups_cache = {}

        with transaction.atomic():
            # Импортируем группы в несколько проходов: сначала родители, потом дочерние
            groups_data = structure['groups']
            
            # Сортируем по уровню, чтобы сначала обработать родительские группы
            groups_data.sort(key=lambda x: x.get('level', 0))

            # Проходим по группам несколько раз, пока все не будут обработаны
            max_iterations = 10  # Защита от бесконечного цикла
            iteration = 0
            remaining_groups = groups_data.copy()

            while remaining_groups and iteration < max_iterations:
                iteration += 1
                processed_in_iteration = []

                for group_data in remaining_groups:
                    external_id = group_data.get('external_id')
                    if not external_id:
                        self.stdout.write(
                            self.style.WARNING(f'Пропущена группа без external_id: {group_data.get("name")}')
                        )
                        processed_in_iteration.append(group_data)
                        continue

                    # Проверяем, можем ли мы обработать эту группу (родитель должен быть уже обработан)
                    parent_external_id = group_data.get('parent_external_id')
                    can_process = True
                    
                    if parent_external_id:
                        # Проверяем, есть ли родитель в базе или в кэше новых групп
                        parent_exists = (
                            parent_external_id in groups_by_external_id or
                            parent_external_id in new_groups_cache
                        )
                        if not parent_exists:
                            # Родитель еще не обработан, пропускаем эту группу на этой итерации
                            can_process = False

                    if not can_process:
                        continue

                    imported_external_ids.add(external_id)
                    
                    # Ищем существующую группу по external_id
                    existing_group = groups_by_external_id.get(external_id)

                    if existing_group:
                        if update_existing:
                            # Обновляем существующую группу
                            existing_group.name = group_data['name']
                            existing_group.level = group_data.get('level', 1)
                            existing_group.is_distributable = group_data.get('is_distributable', False)
                            
                            # Обрабатываем родителя
                            if parent_external_id:
                                # Ищем родителя в базе или в кэше
                                parent_group = (
                                    groups_by_external_id.get(parent_external_id) or
                                    new_groups_cache.get(parent_external_id)
                                )
                                if parent_group:
                                    existing_group.parent = parent_group
                                else:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'Родительская группа с external_id={parent_external_id} не найдена для группы {existing_group.name}'
                                        )
                                    )
                            else:
                                existing_group.parent = None

                            if not dry_run:
                                existing_group.save()
                            
                            self.stdout.write(
                                self.style.SUCCESS(f'Обновлена группа: {existing_group.name}')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'Пропущена существующая группа: {existing_group.name} (используйте --update-existing)')
                            )
                    else:
                        # Создаем новую группу
                        parent_group = None
                        if parent_external_id:
                            # Ищем родителя в базе или в кэше
                            parent_group = (
                                groups_by_external_id.get(parent_external_id) or
                                new_groups_cache.get(parent_external_id)
                            )

                        new_group = GroupIndicators(
                            external_id=external_id,
                            name=group_data['name'],
                            level=group_data.get('level', 1),
                            is_distributable=group_data.get('is_distributable', False),
                            parent=parent_group,
                            sync_enabled=True  # Включаем синхронизацию для импортированных групп
                        )

                        if not dry_run:
                            new_group.save()
                            groups_by_external_id[external_id] = new_group
                            new_groups_cache[external_id] = new_group
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'Создана группа: {new_group.name}')
                        )

                    # Импортируем фильтры, если они есть
                    if 'filters' in group_data:
                        group = existing_group if existing_group else (new_group if not dry_run else None)
                        if group and not dry_run:
                            # Удаляем только те фильтры, которые точно соответствуют импортируемым
                            # (учитывая group, field_name, filter_type, year)
                            # Это устраняет дубликаты, но сохраняет фильтры для других годов
                            for filter_data in group_data['filters']:
                                filter_year = filter_data.get('year', datetime.now().year)
                                
                                # Удаляем все дубликаты для конкретной комбинации полей
                                # (может быть несколько записей с одинаковыми полями - это и есть дубликаты)
                                FilterCondition.objects.filter(
                                    group=group,
                                    field_name=filter_data['field_name'],
                                    filter_type=filter_data['filter_type'],
                                    year=filter_year
                                ).delete()
                                
                                # Создаем новую запись из импорта
                                FilterCondition.objects.create(
                                    group=group,
                                    field_name=filter_data['field_name'],
                                    filter_type=filter_data['filter_type'],
                                    year=filter_year,
                                    values=filter_data['values'],
                                )

                    processed_in_iteration.append(group_data)

                # Удаляем обработанные группы
                for group_data in processed_in_iteration:
                    remaining_groups.remove(group_data)

            # Предупреждаем, если остались необработанные группы
            if remaining_groups:
                self.stdout.write(
                    self.style.ERROR(
                        f'Не удалось обработать {len(remaining_groups)} групп. Возможно, нарушена иерархия parent_external_id.'
                    )
                )

            # Удаляем отсутствующие группы, если запрошено
            if delete_missing:
                existing_external_ids = set(groups_by_external_id.keys())
                missing_external_ids = existing_external_ids - imported_external_ids
                
                for external_id in missing_external_ids:
                    group = groups_by_external_id[external_id]
                    if not dry_run:
                        group.delete()
                    self.stdout.write(
                        self.style.WARNING(f'Удалена отсутствующая группа: {group.name}')
                    )

            if dry_run:
                # Откатываем транзакцию в режиме dry-run
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING('Транзакция откачена (dry-run режим)'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Импорт завершен. Обработано групп: {len(imported_external_ids)}'
            )
        )

