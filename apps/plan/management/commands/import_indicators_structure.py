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

        # Информация о безопасности данных
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                '✓ БЕЗОПАСНОСТЬ: Показатели (AnnualPlan) и планы НЕ будут удалены при обновлении фильтров.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '✓ Обновляются только условия фильтрации (FilterCondition) для указанных годов.'
            )
        )
        if delete_missing:
            self.stdout.write('')
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  ВНИМАНИЕ: Используется флаг --delete-missing. Группы, отсутствующие в файле, будут УДАЛЕНЫ вместе со всеми показателями!'
                )
            )
        self.stdout.write('')

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

        # Проверяем существующие группы без external_id
        groups_without_external_id = GroupIndicators.objects.filter(external_id__isnull=True).count()
        if groups_without_external_id > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'В базе найдено {groups_without_external_id} групп без external_id. '
                    f'Они не будут синхронизированы и останутся в базе (возможны дубли).'
                )
            )

        # Проверяем возможные дубли по имени (группы с одинаковым именем, но разными external_id)
        imported_names = {g.get('name'): g.get('external_id') for g in structure['groups']}
        existing_groups = GroupIndicators.objects.all()
        potential_duplicates = []
        for group in existing_groups:
            if group.external_id and group.external_id not in [g.get('external_id') for g in structure['groups']]:
                # Группа с external_id, но не в импортируемом файле
                if group.name in imported_names:
                    potential_duplicates.append({
                        'name': group.name,
                        'external_id': group.external_id,
                        'imported_external_id': imported_names[group.name]
                    })
        
        if potential_duplicates:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Обнаружено {len(potential_duplicates)} потенциальных дублей по имени:'
                )
            )
            for dup in potential_duplicates[:5]:
                self.stdout.write(
                    self.style.WARNING(
                        f'  - "{dup["name"]}": существующий external_id={dup["external_id"]}, '
                        f'импортируемый external_id={dup["imported_external_id"]}'
                    )
                )
            if len(potential_duplicates) > 5:
                self.stdout.write(
                    self.style.WARNING(f'  ... и еще {len(potential_duplicates) - 5} дублей')
                )
            self.stdout.write(
                self.style.WARNING(
                    '  Существующая группа останется в базе, будет создана новая с импортируемым external_id.'
                )
            )
            self.stdout.write('')

        imported_external_ids = set()
        # Словарь для групп, которые будут созданы в этом импорте (для обработки parent_external_id)
        new_groups_cache = {}
        # Счетчики для статистики
        created_groups = set()
        updated_groups = set()

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
                            # В режиме dry-run показываем отладочную информацию
                            if dry_run and iteration == max_iterations:
                                group_name = group_data.get('name', 'Без имени')
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  Пропущена "{group_name}": родитель {parent_external_id} не найден'
                                    )
                                )

                    if not can_process:
                        continue

                    imported_external_ids.add(external_id)
                    
                    # Ищем существующую группу по external_id
                    existing_group = groups_by_external_id.get(external_id)

                    if existing_group:
                        if update_existing:
                            # Проверяем связанные данные перед обновлением
                            annual_plans_count = existing_group.annual_plans.count()
                            filters_count = existing_group.filters.count()
                            
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
                            
                            updated_groups.add(external_id)
                            
                            # Показываем информацию о связанных данных
                            info_parts = []
                            if annual_plans_count > 0:
                                info_parts.append(f'{annual_plans_count} год. планов')
                            if filters_count > 0:
                                info_parts.append(f'{filters_count} фильтров')
                            
                            info_text = f' (сохранено: {", ".join(info_parts)})' if info_parts else ''
                            self.stdout.write(
                                self.style.SUCCESS(f'Обновлена группа: {existing_group.name}{info_text}')
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

                        # В режиме dry-run тоже добавляем в кэш, чтобы дочерние группы могли найти родителя
                        # но не сохраняем в базу
                        if not dry_run:
                            new_group.save()
                            groups_by_external_id[external_id] = new_group
                        
                        # Добавляем в кэш в любом случае (для dry-run тоже)
                        new_groups_cache[external_id] = new_group
                        created_groups.add(external_id)
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'Создана группа: {new_group.name}')
                        )

                    # Импортируем фильтры, если они есть
                    # Фильтры обновляем всегда, если группа существует (даже если группа не обновляется)
                    if 'filters' in group_data:
                        # Определяем группу для обновления фильтров
                        group = None
                        if existing_group:
                            # Для существующей группы фильтры обновляем всегда
                            group = existing_group
                        elif not dry_run:
                            # Для новой группы фильтры обновляем всегда (если не dry-run)
                            group = new_group
                        
                        if group and not dry_run:
                            # Проверяем, что у группы есть планы (показатели) - они НЕ будут удалены
                            annual_plans_count = group.annual_plans.count()
                            
                            # Собираем все годы из импортируемых фильтров
                            import_years = set()
                            for filter_data in group_data['filters']:
                                filter_year = filter_data.get('year', datetime.now().year)
                                import_years.add(filter_year)
                            
                            # Получаем все существующие фильтры для группы и импортируемых годов
                            existing_filters = FilterCondition.objects.filter(
                                group=group,
                                year__in=import_years
                            )
                            
                            # Создаем множество ключей существующих фильтров для быстрого сравнения
                            # Ключ: (field_name, filter_type, year, values)
                            existing_keys = set()
                            existing_by_key = {}
                            for f in existing_filters:
                                key = (f.field_name, f.filter_type, f.year, f.values)
                                existing_keys.add(key)
                                existing_by_key[key] = f
                            
                            # Создаем множество ключей импортируемых фильтров
                            import_keys = set()
                            import_by_key = {}
                            for filter_data in group_data['filters']:
                                filter_year = filter_data.get('year', datetime.now().year)
                                key = (
                                    filter_data['field_name'],
                                    filter_data['filter_type'],
                                    filter_year,
                                    filter_data['values']
                                )
                                import_keys.add(key)
                                import_by_key[key] = filter_data
                            
                            # Определяем, что нужно удалить и создать
                            # Фильтры с одинаковыми ключами (field_name, filter_type, year, values) не трогаем
                            to_delete = existing_keys - import_keys  # Есть в базе, но нет в импорте
                            to_create = import_keys - existing_keys  # Есть в импорте, но нет в базе
                            unchanged = existing_keys & import_keys  # Есть и там, и там - не трогаем
                            
                            # Удаляем фильтры, которых нет в импорте
                            deleted_count = 0
                            for key in to_delete:
                                existing_by_key[key].delete()
                                deleted_count += 1
                            
                            # Создаем новые фильтры
                            created_count = 0
                            for key in to_create:
                                filter_data = import_by_key[key]
                                FilterCondition.objects.create(
                                    group=group,
                                    field_name=filter_data['field_name'],
                                    filter_type=filter_data['filter_type'],
                                    year=filter_data.get('year', datetime.now().year),
                                    values=filter_data['values'],
                                )
                                created_count += 1
                            
                            # Показываем информацию о фильтрах
                            if deleted_count > 0 or created_count > 0:
                                info_parts = []
                                if deleted_count > 0:
                                    info_parts.append(f'удалено {deleted_count}')
                                if created_count > 0:
                                    info_parts.append(f'создано {created_count}')
                                if unchanged:
                                    info_parts.append(f'без изменений {len(unchanged)}')
                                if annual_plans_count > 0:
                                    info_parts.append(f'показатели сохранены ({annual_plans_count} год. планов)')
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'    → Фильтры для {", ".join(map(str, sorted(import_years)))} года: '
                                        f'{", ".join(info_parts)}'
                                    )
                                )

                    processed_in_iteration.append(group_data)

                # Удаляем обработанные группы
                for group_data in processed_in_iteration:
                    remaining_groups.remove(group_data)

            # Предупреждаем, если остались необработанные группы
            if remaining_groups:
                self.stdout.write('')
                self.stdout.write(
                    self.style.ERROR(
                        f'Не удалось обработать {len(remaining_groups)} групп. Возможно, нарушена иерархия parent_external_id.'
                    )
                )
                # Показываем первые несколько примеров для диагностики
                for i, group_data in enumerate(remaining_groups[:5]):
                    parent_id = group_data.get('parent_external_id')
                    group_name = group_data.get('name', 'Без имени')
                    if parent_id:
                        # Проверяем, есть ли родитель в импортируемых данных
                        parent_in_file = any(
                            g.get('external_id') == parent_id 
                            for g in structure['groups']
                        )
                        if not parent_in_file:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  - "{group_name}": родитель с external_id={parent_id} отсутствует в файле'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  - "{group_name}": родитель с external_id={parent_id} не обработан'
                                )
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  - "{group_name}": нет внешнего ID')
                        )
                if len(remaining_groups) > 5:
                    self.stdout.write(
                        self.style.WARNING(f'  ... и еще {len(remaining_groups) - 5} групп')
                    )

            # Удаляем отсутствующие группы, если запрошено
            if delete_missing:
                existing_external_ids = set(groups_by_external_id.keys())
                missing_external_ids = existing_external_ids - imported_external_ids
                
                if missing_external_ids:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  ВНИМАНИЕ: Будет удалено {len(missing_external_ids)} групп, которых нет в импортируемом файле. '
                            f'Все связанные планы и данные будут удалены!'
                        )
                    )
                
                for external_id in missing_external_ids:
                    group = groups_by_external_id[external_id]
                    # Подсчитываем связанные данные
                    annual_plans_count = group.annual_plans.count()
                    filters_count = group.filters.count()
                    
                    if not dry_run:
                        group.delete()
                    
                    info_parts = []
                    if annual_plans_count > 0:
                        info_parts.append(f'{annual_plans_count} год. планов')
                    if filters_count > 0:
                        info_parts.append(f'{filters_count} фильтров')
                    
                    info_text = f' (удалено: {", ".join(info_parts)})' if info_parts else ''
                    self.stdout.write(
                        self.style.WARNING(f'Удалена отсутствующая группа: {group.name}{info_text}')
                    )

            if dry_run:
                # Откатываем транзакцию в режиме dry-run
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING('Транзакция откачена (dry-run режим)'))

        # Итоговая статистика
        created_count = len(created_groups)
        updated_count = len(updated_groups)
        skipped_count = len(imported_external_ids) - created_count - updated_count
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Импорт завершен'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Всего обработано групп: {len(imported_external_ids)}')
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Создано новых: {created_count}'))
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Обновлено: {updated_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠ Пропущено (без --update-existing): {skipped_count}'))
        if groups_without_external_id > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠ Групп без external_id (не синхронизированы): {groups_without_external_id}'
                )
            )
        self.stdout.write('')

