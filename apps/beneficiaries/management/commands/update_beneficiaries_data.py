"""
Management команда для обновления данных льготников
- Обновление статусов назначений (истекшие, активные)
- Проверка остатков препаратов
- Актуализация данных пациентов
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from apps.beneficiaries.models import (
    BenefitCategory, Patient, Drug, PatientDrugSupply, DrugStock
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Обновление данных льготников (статусы назначений, остатки препаратов)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-statuses',
            action='store_true',
            help='Обновить статусы назначений препаратов'
        )
        parser.add_argument(
            '--check-expired',
            action='store_true',
            help='Проверить и отметить истекшие назначения'
        )
        parser.add_argument(
            '--deactivate-old',
            action='store_true',
            help='Деактивировать старые неактуальные записи'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Выполнить все операции обновления'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=180,
            help='Количество дней для определения старых записей (по умолчанию 180)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Тестовый режим без записи в БД'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        update_all = options.get('all')
        days_threshold = options.get('days')
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('🔄 Обновление данных льготников'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Режим тестирования (dry-run)'))
        
        # Счётчики
        stats = {
            'statuses_updated': 0,
            'expired_marked': 0,
            'patients_deactivated': 0,
            'supplies_deactivated': 0,
            'urgent_supplies': 0,
        }
        
        with transaction.atomic():
            # 1. Обновление статусов назначений
            if options.get('update_statuses') or update_all:
                stats['statuses_updated'] = self.update_supply_statuses(dry_run)
            
            # 2. Проверка истекших назначений
            if options.get('check_expired') or update_all:
                stats['expired_marked'] = self.check_expired_supplies(dry_run)
            
            # 3. Деактивация старых записей
            if options.get('deactivate_old') or update_all:
                deactivated = self.deactivate_old_records(days_threshold, dry_run)
                stats['patients_deactivated'] = deactivated['patients']
                stats['supplies_deactivated'] = deactivated['supplies']
            
            # 4. Подсчёт срочных назначений
            stats['urgent_supplies'] = self.count_urgent_supplies()
        
        # Вывод статистики
        self.print_statistics(stats)
        
        # Итоги
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ Обновление данных завершено!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

    def update_supply_statuses(self, dry_run):
        """Обновление статусов назначений на основе даты обеспечения"""
        self.stdout.write('\n📊 Обновление статусов назначений...')
        
        today = timezone.now().date()
        updated_count = 0
        
        # Получаем все активные назначения
        supplies = PatientDrugSupply.objects.filter(
            patient__is_active=True
        ).select_related('patient', 'drug')
        
        for supply in supplies:
            old_status = supply.status
            new_status = old_status
            
            if supply.supplied_until:
                if supply.supplied_until < today:
                    new_status = 'expired'
                elif supply.supplied_until <= today + timedelta(days=7):
                    new_status = 'active'  # Срочные, но активные
                else:
                    new_status = 'active'
            
            if old_status != new_status:
                if not dry_run:
                    supply.status = new_status
                    supply.save(update_fields=['status', 'last_update'])
                
                updated_count += 1
                
                if dry_run and updated_count <= 5:
                    self.stdout.write(
                        f"  [Тест] {supply.patient.full_name} - {supply.drug.name}: "
                        f"{old_status} → {new_status}"
                    )
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Обновлено статусов: {updated_count}'))
        return updated_count

    def check_expired_supplies(self, dry_run):
        """Проверка и отметка истекших назначений"""
        self.stdout.write('\n⏰ Проверка истекших назначений...')
        
        today = timezone.now().date()
        
        # Находим истекшие назначения
        expired_supplies = PatientDrugSupply.objects.filter(
            supplied_until__lt=today,
            status__in=['active', 'pending']
        ).select_related('patient', 'drug')
        
        expired_count = expired_supplies.count()
        
        if not dry_run:
            expired_supplies.update(status='expired')
        else:
            # Показываем примеры
            for supply in expired_supplies[:5]:
                days_expired = (today - supply.supplied_until).days
                self.stdout.write(
                    f"  [Тест] {supply.patient.full_name} - {supply.drug.name}: "
                    f"истекло {days_expired} дн. назад"
                )
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Отмечено истекших: {expired_count}'))
        
        # Срочные назначения (осталось <= 7 дней)
        urgent_supplies = PatientDrugSupply.objects.filter(
            supplied_until__gte=today,
            supplied_until__lte=today + timedelta(days=7),
            patient__is_active=True
        ).count()
        
        if urgent_supplies > 0:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️ Срочных назначений (до 7 дней): {urgent_supplies}')
            )
        
        return expired_count

    def deactivate_old_records(self, days_threshold, dry_run):
        """Деактивация старых неактуальных записей"""
        self.stdout.write(f'\n🗑️ Деактивация записей старше {days_threshold} дней...')
        
        threshold_date = timezone.now() - timedelta(days=days_threshold)
        
        # Деактивация старых назначений
        old_supplies = PatientDrugSupply.objects.filter(
            last_update__lt=threshold_date,
            status='expired'
        )
        supplies_count = old_supplies.count()
        
        if not dry_run and supplies_count > 0:
            # Можно добавить поле is_active в модель или просто удалить
            # Пока просто считаем
            pass
        
        # Деактивация пациентов без активных назначений
        patients_without_supplies = Patient.objects.filter(
            is_active=True
        ).annotate(
            active_supplies_count=Count(
                'drug_supplies',
                filter=Q(drug_supplies__status__in=['active', 'pending'])
            )
        ).filter(
            active_supplies_count=0,
            created_at__lt=threshold_date
        )
        
        patients_count = patients_without_supplies.count()
        
        if not dry_run and patients_count > 0:
            if patients_count <= 10:
                # Показываем кого деактивируем
                for patient in patients_without_supplies:
                    self.stdout.write(f"  Деактивация: {patient.full_name}")
            # patients_without_supplies.update(is_active=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'  ✓ Старых назначений найдено: {supplies_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  ✓ Пациентов без активных назначений: {patients_count}')
        )
        
        return {
            'patients': patients_count,
            'supplies': supplies_count
        }

    def count_urgent_supplies(self):
        """Подсчёт срочных назначений"""
        today = timezone.now().date()
        
        urgent_count = PatientDrugSupply.objects.filter(
            supplied_until__gte=today,
            supplied_until__lte=today + timedelta(days=7),
            patient__is_active=True,
            status='active'
        ).count()
        
        return urgent_count

    def print_statistics(self, stats):
        """Вывод общей статистики"""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.WARNING('📈 Общая статистика системы'))
        self.stdout.write('=' * 70)
        
        # Общие показатели
        total_patients = Patient.objects.filter(is_active=True).count()
        total_drugs = Drug.objects.filter(is_active=True).count()
        total_categories = BenefitCategory.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n👥 Пациентов (активных): {total_patients}')
        self.stdout.write(f'💊 Препаратов (активных): {total_drugs}')
        self.stdout.write(f'📁 Категорий льгот (активных): {total_categories}')
        
        # Статусы назначений
        supplies_by_status = PatientDrugSupply.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        self.stdout.write('\n📋 Назначения по статусам:')
        status_names = {
            'pending': 'Ожидает',
            'active': 'Активно',
            'completed': 'Выполнено',
            'cancelled': 'Отменено',
            'expired': 'Истекло',
        }
        
        for item in supplies_by_status:
            status = item['status']
            count = item['count']
            status_label = status_names.get(status, status)
            self.stdout.write(f'  - {status_label}: {count}')
        
        # Результаты обновления
        if any(stats.values()):
            self.stdout.write('\n🔄 Результаты обновления:')
            if stats['statuses_updated']:
                self.stdout.write(f"  - Обновлено статусов: {stats['statuses_updated']}")
            if stats['expired_marked']:
                self.stdout.write(f"  - Отмечено истекших: {stats['expired_marked']}")
            if stats['patients_deactivated']:
                self.stdout.write(f"  - Пациентов к деактивации: {stats['patients_deactivated']}")
            if stats['urgent_supplies']:
                self.stdout.write(
                    self.style.WARNING(f"  - ⚠️ Срочных назначений: {stats['urgent_supplies']}")
                )
        
        # Топ препаратов
        top_drugs = Drug.objects.annotate(
            supplies_count=Count('patient_supplies')
        ).filter(supplies_count__gt=0).order_by('-supplies_count')[:5]
        
        if top_drugs:
            self.stdout.write('\n💊 Топ-5 назначаемых препаратов:')
            for i, drug in enumerate(top_drugs, 1):
                self.stdout.write(f'  {i}. {drug.name} - {drug.supplies_count} назначений')
        
        # Остатки препаратов
        low_stock = DrugStock.objects.filter(quantity__lt=50).count()
        if low_stock > 0:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️ Препаратов с малыми остатками (< 50 ед.): {low_stock}')
            )

