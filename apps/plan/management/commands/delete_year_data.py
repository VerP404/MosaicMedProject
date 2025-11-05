"""
Management команда для удаления всех данных выбранного года.
Удаляет FilterCondition, AnnualPlan и все связанные планы (MonthlyPlan, BuildingPlan, DepartmentPlan и т.д.)
"""
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from apps.plan.models import (
    FilterCondition,
    AnnualPlan,
    MonthlyPlan,
    BuildingPlan,
    MonthlyBuildingPlan,
    DepartmentPlan,
    MonthlyDepartmentPlan,
    GroupBuildingDepartment,
    GroupIndicators,
)


class Command(BaseCommand):
    help = 'Удаляет все данные выбранного года (FilterCondition, AnnualPlan и все связанные планы)'

    def add_arguments(self, parser):
        parser.add_argument(
            'year',
            type=int,
            help='Год, данные которого нужно удалить'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет удалено без сохранения изменений'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Удалить без дополнительных подтверждений'
        )
        parser.add_argument(
            '--delete-unused-groups',
            action='store_true',
            help='Удалить группы, которые используются ТОЛЬКО для удаляемого года (опасно!)'
        )

    def handle(self, *args, **options):
        year = options['year']
        dry_run = options['dry_run']
        force = options['force']
        delete_unused_groups = options['delete_unused_groups']

        if dry_run:
            self.stdout.write(self.style.WARNING('Режим проверки (dry-run). Изменения не будут сохранены.'))
            self.stdout.write('')

        # Подсчитываем что будет удалено
        stats = self._count_deletions(year, delete_unused_groups)

        # Показываем статистику
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING(f'Удаление данных за {year} год'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        
        self.stdout.write('Будет удалено:')
        self.stdout.write(f'  • FilterCondition: {stats["filters"]} записей')
        self.stdout.write(f'  • AnnualPlan: {stats["annual_plans"]} записей')
        self.stdout.write(f'  • MonthlyPlan: {stats["monthly_plans"]} записей')
        self.stdout.write(f'  • BuildingPlan: {stats["building_plans"]} записей')
        self.stdout.write(f'  • MonthlyBuildingPlan: {stats["monthly_building_plans"]} записей')
        self.stdout.write(f'  • DepartmentPlan: {stats["department_plans"]} записей')
        self.stdout.write(f'  • MonthlyDepartmentPlan: {stats["monthly_department_plans"]} записей')
        self.stdout.write(f'  • GroupBuildingDepartment: {stats["group_building_departments"]} записей')
        if delete_unused_groups:
            self.stdout.write(f'  • GroupIndicators (неиспользуемые): {stats["unused_groups"]} записей')
        self.stdout.write('')
        
        total = sum(v for k, v in stats.items() if k != 'unused_groups') + (stats.get('unused_groups', 0) if delete_unused_groups else 0)
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Нет данных для удаления за указанный год.'))
            return

        self.stdout.write(self.style.ERROR(f'ВСЕГО: {total} записей будет удалено!'))
        self.stdout.write('')

        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('=' * 70))
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОВЕРКИ (DRY-RUN) - Изменения НЕ будут сохранены'))
            self.stdout.write(self.style.WARNING('=' * 70))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Для реального удаления запустите команду БЕЗ флага --dry-run:'))
            self.stdout.write(self.style.SUCCESS(f'  python manage.py delete_year_data {year}'))
            return

        # Подтверждение
        if not force:
            self.stdout.write(self.style.ERROR('⚠️  ВНИМАНИЕ: Это действие необратимо!'))
            self.stdout.write(self.style.ERROR('Все данные за указанный год будут удалены.'))
            self.stdout.write('')
            confirm = input(f'Введите год ({year}) для подтверждения удаления: ')
            
            if confirm != str(year):
                self.stdout.write(self.style.ERROR('Отменено. Год не совпадает.'))
                return

        # Выполняем удаление в транзакции
        with transaction.atomic():
            deleted_stats = self._delete_year_data(year, delete_unused_groups)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('Удаление завершено'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write('Удалено:')
            self.stdout.write(f'  • FilterCondition: {deleted_stats["filters"]} записей')
            self.stdout.write(f'  • AnnualPlan: {deleted_stats["annual_plans"]} записей')
            self.stdout.write(f'  • MonthlyPlan: {deleted_stats["monthly_plans"]} записей')
            self.stdout.write(f'  • BuildingPlan: {deleted_stats["building_plans"]} записей')
            self.stdout.write(f'  • MonthlyBuildingPlan: {deleted_stats["monthly_building_plans"]} записей')
            self.stdout.write(f'  • DepartmentPlan: {deleted_stats["department_plans"]} записей')
            self.stdout.write(f'  • MonthlyDepartmentPlan: {deleted_stats["monthly_department_plans"]} записей')
            self.stdout.write(f'  • GroupBuildingDepartment: {deleted_stats["group_building_departments"]} записей')
            if delete_unused_groups and deleted_stats.get('unused_groups', 0) > 0:
                self.stdout.write(f'  • GroupIndicators (неиспользуемые): {deleted_stats["unused_groups"]} записей')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Всего удалено: {sum(deleted_stats.values())} записей'))

    def _count_deletions(self, year, delete_unused_groups=False):
        """Подсчитывает количество записей, которые будут удалены"""
        stats = {}
        
        # FilterCondition
        stats['filters'] = FilterCondition.objects.filter(year=year).count()
        
        # AnnualPlan
        annual_plans = AnnualPlan.objects.filter(year=year)
        stats['annual_plans'] = annual_plans.count()
        
        # MonthlyPlan (через AnnualPlan)
        stats['monthly_plans'] = MonthlyPlan.objects.filter(annual_plan__year=year).count()
        
        # BuildingPlan и связанные
        building_plans = BuildingPlan.objects.filter(annual_plan__year=year)
        stats['building_plans'] = building_plans.count()
        
        # MonthlyBuildingPlan
        stats['monthly_building_plans'] = MonthlyBuildingPlan.objects.filter(
            building_plan__annual_plan__year=year
        ).count()
        
        # DepartmentPlan
        stats['department_plans'] = DepartmentPlan.objects.filter(
            building_plan__annual_plan__year=year
        ).count()
        
        # MonthlyDepartmentPlan
        stats['monthly_department_plans'] = MonthlyDepartmentPlan.objects.filter(
            department_plan__building_plan__annual_plan__year=year
        ).count()
        
        # GroupBuildingDepartment
        stats['group_building_departments'] = GroupBuildingDepartment.objects.filter(year=year).count()
        
        # Неиспользуемые группы (используются только для удаляемого года)
        if delete_unused_groups:
            # Группы, которые имеют AnnualPlan только для удаляемого года
            unused_groups = []
            for group in GroupIndicators.objects.filter(annual_plans__year=year).distinct():
                # Проверяем, что у группы есть планы ТОЛЬКО для удаляемого года
                total_plans = group.annual_plans.count()
                plans_for_this_year = group.annual_plans.filter(year=year).count()
                
                # Если все планы только для удаляемого года
                if total_plans == plans_for_this_year and total_plans > 0:
                    # Проверяем, что нет фильтров для других годов
                    if not FilterCondition.objects.filter(group=group).exclude(year=year).exists():
                        unused_groups.append(group.id)
            
            stats['unused_groups'] = len(unused_groups)
        else:
            stats['unused_groups'] = 0
        
        return stats

    def _delete_year_data(self, year, delete_unused_groups=False):
        """Удаляет все данные за указанный год"""
        deleted_stats = {}
        
        # 1. Удаляем FilterCondition
        filters_qs = FilterCondition.objects.filter(year=year)
        deleted_stats['filters'] = filters_qs.count()
        filters_qs.delete()
        
        # 2. Удаляем GroupBuildingDepartment
        gbd_qs = GroupBuildingDepartment.objects.filter(year=year)
        deleted_stats['group_building_departments'] = gbd_qs.count()
        gbd_qs.delete()
        
        # 3. Подсчитываем все связанные данные перед удалением
        annual_plans = AnnualPlan.objects.filter(year=year)
        deleted_stats['annual_plans'] = annual_plans.count()
        
        # Подсчитываем MonthlyPlan (обход переопределенного delete через queryset)
        monthly_plans_qs = MonthlyPlan.objects.filter(annual_plan__year=year)
        deleted_stats['monthly_plans'] = monthly_plans_qs.count()
        
        # Подсчитываем BuildingPlan и связанные планы
        building_plans = BuildingPlan.objects.filter(annual_plan__year=year)
        deleted_stats['building_plans'] = building_plans.count()
        
        # MonthlyBuildingPlan (обход переопределенного delete)
        monthly_building_plans_qs = MonthlyBuildingPlan.objects.filter(
            building_plan__annual_plan__year=year
        )
        deleted_stats['monthly_building_plans'] = monthly_building_plans_qs.count()
        
        # DepartmentPlan
        department_plans = DepartmentPlan.objects.filter(building_plan__annual_plan__year=year)
        deleted_stats['department_plans'] = department_plans.count()
        
        # MonthlyDepartmentPlan (обход переопределенного delete)
        monthly_department_plans_qs = MonthlyDepartmentPlan.objects.filter(
            department_plan__building_plan__annual_plan__year=year
        )
        deleted_stats['monthly_department_plans'] = monthly_department_plans_qs.count()
        
        # 4. Удаляем в правильном порядке (от дочерних к родительским)
        # Удаляем MonthlyDepartmentPlan через queryset (обход переопределенного delete)
        monthly_department_plans_qs.delete()
        
        # Удаляем DepartmentPlan
        department_plans.delete()
        
        # Удаляем MonthlyBuildingPlan через queryset (обход переопределенного delete)
        monthly_building_plans_qs.delete()
        
        # Удаляем BuildingPlan
        building_plans.delete()
        
        # Удаляем MonthlyPlan через queryset (обход переопределенного delete)
        monthly_plans_qs.delete()
        
        # Удаляем AnnualPlan в последнюю очередь
        annual_plans.delete()
        
        # 5. Удаляем неиспользуемые группы (если запрошено)
        if delete_unused_groups:
            unused_group_ids = []
            for group in GroupIndicators.objects.filter(annual_plans__year=year).distinct():
                # Проверяем, что у группы есть планы ТОЛЬКО для удаляемого года
                total_plans = group.annual_plans.count()
                plans_for_this_year = group.annual_plans.filter(year=year).count()
                
                # Если все планы только для удаляемого года
                if total_plans == plans_for_this_year and total_plans > 0:
                    # Проверяем, что нет фильтров для других годов
                    if not FilterCondition.objects.filter(group=group).exclude(year=year).exists():
                        unused_group_ids.append(group.id)
            
            if unused_group_ids:
                unused_groups = GroupIndicators.objects.filter(id__in=unused_group_ids)
                deleted_stats['unused_groups'] = unused_groups.count()
                unused_groups.delete()
            else:
                deleted_stats['unused_groups'] = 0
        else:
            deleted_stats['unused_groups'] = 0
        
        return deleted_stats

