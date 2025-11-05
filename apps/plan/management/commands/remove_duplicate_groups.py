"""
Management команда для удаления дублей групп индикаторов.
Находит группы с одинаковыми именами, но разными external_id, и удаляет дубли,
перенося все данные (планы, фильтры) на группу с правильным external_id из импорта.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from collections import defaultdict
from apps.plan.models import (
    GroupIndicators,
    FilterCondition,
    AnnualPlan,
    MonthlyPlan,
    BuildingPlan,
    MonthlyBuildingPlan,
    DepartmentPlan,
    MonthlyDepartmentPlan,
    GroupBuildingDepartment,
)


class Command(BaseCommand):
    help = 'Удаляет дубли групп индикаторов, перенося данные на группы с правильным external_id'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без сохранения изменений'
        )
        parser.add_argument(
            '--keep-synced',
            action='store_true',
            help='Оставлять группы с sync_enabled=True (импортированные)'
        )
        parser.add_argument(
            '--fixtures-file',
            type=str,
            default='apps/plan/fixtures/indicators_structure.json',
            help='Путь к файлу fixtures для определения правильных external_id'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_synced = options['keep_synced']
        fixtures_file = options['fixtures_file']

        if dry_run:
            self.stdout.write(self.style.WARNING('Режим проверки (dry-run). Изменения не будут сохранены.'))
            self.stdout.write('')

        # Загружаем правильные external_id из файла fixtures
        correct_external_ids = self._load_correct_external_ids(fixtures_file)

        # Находим дубли по имени
        duplicates = self._find_duplicates(keep_synced)

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('Дублей не найдено. База в порядке.'))
            return

        # Показываем статистику
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Найдены дубли групп индикаторов'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        total_duplicates = 0
        for name, groups in duplicates.items():
            # Определяем основную группу
            main_group = self._select_main_group(groups, correct_external_ids.get(name))
            duplicate_groups = [g for g in groups if g.id != main_group.id]
            
            self.stdout.write(f'"{name}": {len(groups)} групп')
            self.stdout.write(f'  → ОСНОВНАЯ (ID: {main_group.id}, external_id: {main_group.external_id})')
            for group in duplicate_groups:
                self.stdout.write(f'  ✗ УДАЛИТЬ (ID: {group.id}, external_id: {group.external_id})')
            total_duplicates += len(duplicate_groups)

        self.stdout.write('')
        self.stdout.write(self.style.ERROR(f'Будет удалено {total_duplicates} дублей'))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('Режим dry-run. Для реального удаления запустите команду без --dry-run'))
            return

        # Подтверждение
        self.stdout.write(self.style.ERROR('⚠️  ВНИМАНИЕ: Это действие удалит дубли групп!'))
        self.stdout.write(self.style.ERROR('Все данные (планы, фильтры) будут перенесены на основную группу.'))
        self.stdout.write('')
        confirm = input('Введите "ДА" для подтверждения: ')
        
        if confirm != 'ДА':
            self.stdout.write(self.style.ERROR('Отменено.'))
            return

        # Выполняем удаление дублей в транзакции
        with transaction.atomic():
            deleted_count = self._remove_duplicates(duplicates, correct_external_ids)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('Удаление дублей завершено'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Удалено {deleted_count} дублей'))
            self.stdout.write(self.style.SUCCESS('Все данные перенесены на основные группы'))

    def _load_correct_external_ids(self, fixtures_file):
        """Загружает правильные external_id из файла fixtures"""
        correct_ids = {}
        
        # Определяем полный путь к файлу
        if not os.path.isabs(fixtures_file):
            # Относительный путь от корня проекта
            from django.conf import settings
            project_root = settings.BASE_DIR
            fixtures_file = os.path.join(project_root, fixtures_file)
        
        if not os.path.exists(fixtures_file):
            self.stdout.write(
                self.style.WARNING(f'Файл fixtures не найден: {fixtures_file}')
            )
            return correct_ids
        
        try:
            with open(fixtures_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'groups' in data:
                for group_data in data['groups']:
                    name = group_data.get('name')
                    external_id = group_data.get('external_id')
                    if name and external_id:
                        correct_ids[name] = external_id
            
            self.stdout.write(
                self.style.SUCCESS(f'Загружено {len(correct_ids)} правильных external_id из файла')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке fixtures: {e}')
            )
        
        return correct_ids

    def _find_duplicates(self, keep_synced=False):
        """Находит дубли групп по имени"""
        # Группируем по имени
        groups_by_name = defaultdict(list)
        
        all_groups = GroupIndicators.objects.all()
        if keep_synced:
            # Если keep_synced=True, оставляем группы с sync_enabled=True
            all_groups = all_groups.order_by('-sync_enabled', 'id')
        
        for group in all_groups:
            groups_by_name[group.name].append(group)
        
        # Оставляем только дубли (где больше 1 группы с одинаковым именем)
        duplicates = {
            name: groups
            for name, groups in groups_by_name.items()
            if len(groups) > 1
        }
        
        return duplicates

    def _select_main_group(self, groups, correct_external_id=None):
        """Выбирает основную группу из дублей"""
        # Если есть правильный external_id из файла, ищем группу с ним
        if correct_external_id:
            for group in groups:
                if group.external_id == correct_external_id:
                    return group
        
        # Если нет правильного external_id, ищем группу с external_id и sync_enabled=True
        for group in groups:
            if group.external_id and group.sync_enabled:
                return group
        
        # Если нет, берем первую группу с external_id
        for group in groups:
            if group.external_id:
                return group
        
        # Если совсем нет, берем первую группу
        return groups[0]

    def _remove_duplicates(self, duplicates, correct_external_ids=None):
        """Удаляет дубли, перенося данные на основную группу"""
        if correct_external_ids is None:
            correct_external_ids = {}
        
        deleted_count = 0
        
        for name, groups in duplicates.items():
            # Определяем основную группу
            main_group = self._select_main_group(groups, correct_external_ids.get(name))
            duplicate_groups = [g for g in groups if g.id != main_group.id]
            
            self.stdout.write(f'Обрабатываем "{name}": основная группа ID={main_group.id} (external_id={main_group.external_id})')
            
            # Переносим данные с дублей на основную группу
            for dup_group in duplicate_groups:
                self.stdout.write(f'  → Переносим данные с группы ID={dup_group.id} на ID={main_group.id}')
                
                # 1. Переносим FilterCondition
                FilterCondition.objects.filter(group=dup_group).update(group=main_group)
                
                # 2. Переносим AnnualPlan (если нет конфликтов)
                for annual_plan in AnnualPlan.objects.filter(group=dup_group):
                    # Проверяем, нет ли уже плана для этого года
                    existing_plan = AnnualPlan.objects.filter(
                        group=main_group,
                        year=annual_plan.year
                    ).first()
                    
                    if existing_plan:
                        # Если план уже есть, переносим месячные планы
                        # Удаляем конфликтующие месячные планы и переносим данные
                        for monthly_plan in MonthlyPlan.objects.filter(annual_plan=annual_plan):
                            existing_monthly = MonthlyPlan.objects.filter(
                                annual_plan=existing_plan,
                                month=monthly_plan.month
                            ).first()
                            
                            if existing_monthly:
                                # Если месячный план уже есть, обновляем данные
                                existing_monthly.quantity += monthly_plan.quantity
                                existing_monthly.amount += monthly_plan.amount
                                existing_monthly.save()
                                # Удаляем дубль через queryset (обход переопределенного delete)
                                MonthlyPlan.objects.filter(id=monthly_plan.id).delete()
                            else:
                                # Переносим месячный план
                                monthly_plan.annual_plan = existing_plan
                                monthly_plan.save()
                        
                        # Переносим BuildingPlan
                        for building_plan in BuildingPlan.objects.filter(annual_plan=annual_plan):
                            existing_bp = BuildingPlan.objects.filter(
                                annual_plan=existing_plan,
                                building=building_plan.building
                            ).first()
                            
                            if existing_bp:
                                # Переносим MonthlyBuildingPlan
                                MonthlyBuildingPlan.objects.filter(
                                    building_plan=building_plan
                                ).update(building_plan=existing_bp)
                                
                                # Переносим DepartmentPlan
                                for dept_plan in DepartmentPlan.objects.filter(building_plan=building_plan):
                                    existing_dp = DepartmentPlan.objects.filter(
                                        building_plan=existing_bp,
                                        department=dept_plan.department
                                    ).first()
                                    
                                    if existing_dp:
                                        MonthlyDepartmentPlan.objects.filter(
                                            department_plan=dept_plan
                                        ).update(department_plan=existing_dp)
                                        dept_plan.delete()
                                    else:
                                        dept_plan.building_plan = existing_bp
                                        dept_plan.save()
                                
                                building_plan.delete()
                            else:
                                building_plan.annual_plan = existing_plan
                                building_plan.save()
                        
                        # Удаляем дубль AnnualPlan
                        annual_plan.delete()
                    else:
                        # Если плана нет, переносим AnnualPlan
                        annual_plan.group = main_group
                        annual_plan.save()
                
                # 3. Переносим GroupBuildingDepartment
                GroupBuildingDepartment.objects.filter(group=dup_group).update(group=main_group)
                
                # 4. Удаляем дубль группы (каскадно удалятся связи через M2M)
                dup_group.delete()
                deleted_count += 1
                
                self.stdout.write(f'  ✓ Группа ID={dup_group.id} удалена')
        
        return deleted_count

