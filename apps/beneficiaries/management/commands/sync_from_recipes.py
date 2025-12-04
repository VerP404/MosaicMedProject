"""
Management команда для синхронизации пациентов-льготников из load_data.Recipe
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from typing import Tuple
import logging

from apps.load_data.models import Recipe
from apps.beneficiaries.models import BenefitCategory, Patient, Drug, PatientDrugSupply

logger = logging.getLogger(__name__)


def normalize_snils(snils: str) -> str:
    """Нормализует СНИЛС"""
    if not snils or snils.strip() in ("-", ""):
        return ""
    
    # Убираем все нецифровые символы
    digits = ''.join(filter(str.isdigit, str(snils)))
    
    if len(digits) != 11:
        return ""
    
    # Форматируем в стандартный вид
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]} {digits[9:11]}"


def parse_date(date_str: str):
    """Парсит дату из строки"""
    if not date_str or date_str == "-":
        return None
    
    date_str = str(date_str).strip()[:10]
    
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    return None


class Command(BaseCommand):
    help = "Синхронизация льготников и препаратов из таблицы Recipe"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Ограничить количество обрабатываемых рецептов'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Тестовый режим без записи в БД'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        dry_run = options.get('dry_run')
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Синхронизация льготников из рецептов'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        # Получаем рецепты
        recipes = Recipe.objects.all()
        if limit:
            recipes = recipes[:limit]
        
        total_recipes = recipes.count()
        self.stdout.write(f'📋 Найдено рецептов: {total_recipes}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Режим тестирования (dry-run)'))
        
        # Счётчики
        stats = {
            'categories_created': 0,
            'patients_created': 0,
            'patients_updated': 0,
            'drugs_created': 0,
            'supplies_created': 0,
            'errors': 0
        }
        
        # Синхронизация
        with transaction.atomic():
            # 1. Синхронизируем категории льгот
            categories = self.sync_benefit_categories(recipes, dry_run)
            stats['categories_created'] = len(categories)
            
            # 2. Синхронизируем препараты
            drugs = self.sync_drugs(recipes, dry_run)
            stats['drugs_created'] = len(drugs)
            
            # 3. Синхронизируем пациентов
            patients_stats = self.sync_patients(recipes, categories, dry_run)
            stats['patients_created'] = patients_stats['created']
            stats['patients_updated'] = patients_stats['updated']
            
            # 4. Синхронизируем назначения
            supplies_stats = self.sync_drug_supplies(recipes, drugs, dry_run)
            stats['supplies_created'] = supplies_stats['created']
            stats['errors'] = supplies_stats['errors']
        
        # Итоги
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ Синхронизация завершена!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Категорий создано: {stats["categories_created"]}')
        self.stdout.write(f'Препаратов создано: {stats["drugs_created"]}')
        self.stdout.write(f'Пациентов создано: {stats["patients_created"]}')
        self.stdout.write(f'Пациентов обновлено: {stats["patients_updated"]}')
        self.stdout.write(f'Назначений создано: {stats["supplies_created"]}')
        if stats['errors'] > 0:
            self.stdout.write(self.style.WARNING(f'⚠️ Ошибок: {stats["errors"]}'))

    def sync_benefit_categories(self, recipes, dry_run):
        """Синхронизация категорий льгот"""
        self.stdout.write('\n📁 Синхронизация категорий льгот...')
        
        categories = {}
        for recipe in recipes:
            cat_name = recipe.benefit_category_name
            cat_type = recipe.benefit_category_type
            financing = recipe.financing_source
            
            if cat_name and cat_name != "-":
                key = cat_name
                if key not in categories:
                    categories[key] = {
                        'name': cat_name,
                        'type': cat_type if cat_type != "-" else "",
                        'financing': financing if financing != "-" else ""
                    }
        
        created_categories = {}
        for key, data in categories.items():
            if not dry_run:
                category, created = BenefitCategory.objects.get_or_create(
                    name=data['name'],
                    defaults={
                        'code': data['type'][:50] if data['type'] else "",
                        'financing_source': data['financing']
                    }
                )
                created_categories[key] = category
            else:
                self.stdout.write(f"  [Тест] Создать: {data['name']}")
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Обработано категорий: {len(categories)}'))
        return created_categories

    def sync_drugs(self, recipes, dry_run):
        """Синхронизация препаратов"""
        self.stdout.write('\n💊 Синхронизация препаратов...')
        
        drugs = {}
        for recipe in recipes:
            drug_name = recipe.medicinal_product
            inn = recipe.inn
            trn = recipe.trn
            
            if drug_name and drug_name != "-":
                key = drug_name
                if key not in drugs:
                    drugs[key] = {
                        'name': drug_name,
                        'inn': inn if inn != "-" else "",
                        'code': trn if trn != "-" else ""
                    }
        
        created_drugs = {}
        for key, data in drugs.items():
            if not dry_run:
                drug, created = Drug.objects.get_or_create(
                    name=data['name'],
                    defaults={
                        'inn': data['inn'],
                        'code': data['code']
                    }
                )
                created_drugs[key] = drug
            else:
                self.stdout.write(f"  [Тест] Создать: {data['name']}")
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Обработано препаратов: {len(drugs)}'))
        return created_drugs

    def sync_patients(self, recipes, categories, dry_run):
        """Синхронизация пациентов"""
        self.stdout.write('\n👥 Синхронизация пациентов...')
        
        patients = {}
        for recipe in recipes:
            snils = normalize_snils(recipe.patient_snils)
            if not snils:
                continue
            
            if snils not in patients:
                patients[snils] = {
                    'full_name': recipe.patient_full_name,
                    'birth_date': parse_date(recipe.patient_birth_date),
                    'snils': snils,
                    'diagnosis_code': recipe.diagnosis_code if recipe.diagnosis_code != "-" else "",
                    'diagnosis_name': recipe.diagnosis_name if recipe.diagnosis_name != "-" else "",
                    'benefit_category_name': recipe.benefit_category_name if recipe.benefit_category_name != "-" else None
                }
        
        created = 0
        updated = 0
        
        for snils, data in patients.items():
            if dry_run:
                self.stdout.write(f"  [Тест] Создать/обновить: {data['full_name']}")
                continue
            
            # Ищем категорию
            category = None
            if data['benefit_category_name'] and data['benefit_category_name'] in categories:
                category = categories[data['benefit_category_name']]
            
            # Создаём или обновляем пациента
            patient, is_created = Patient.objects.update_or_create(
                snils=snils,
                defaults={
                    'full_name': data['full_name'],
                    'birth_date': data['birth_date'] or timezone.now().date(),
                    'diagnosis_code': data['diagnosis_code'],
                    'diagnosis_name': data['diagnosis_name'],
                    'benefit_category': category,
                    'is_active': True
                }
            )
            
            if is_created:
                created += 1
            else:
                updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Пациентов создано: {created}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Пациентов обновлено: {updated}'))
        
        return {'created': created, 'updated': updated}

    def sync_drug_supplies(self, recipes, drugs, dry_run):
        """Синхронизация назначений препаратов"""
        self.stdout.write('\n📝 Синхронизация назначений...')
        
        created = 0
        errors = 0
        
        for recipe in recipes:
            try:
                snils = normalize_snils(recipe.patient_snils)
                if not snils:
                    continue
                
                drug_name = recipe.medicinal_product
                if not drug_name or drug_name == "-":
                    continue
                
                if dry_run:
                    if created < 5:  # Показываем только первые 5 для теста
                        self.stdout.write(f"  [Тест] Создать назначение: {recipe.patient_full_name} → {drug_name}")
                    created += 1
                    continue
                
                # Находим пациента и препарат
                try:
                    patient = Patient.objects.get(snils=snils)
                except Patient.DoesNotExist:
                    continue
                
                drug = drugs.get(drug_name)
                if not drug:
                    continue
                
                # Парсим даты
                prescription_date = parse_date(recipe.date)
                supplied_until = parse_date(recipe.validity_period)
                
                # Создаём или обновляем назначение
                supply, is_created = PatientDrugSupply.objects.update_or_create(
                    patient=patient,
                    drug=drug,
                    defaults={
                        'monthly_need': recipe.quantity_total_prescribed,
                        'prescribed': recipe.quantity_total_prescribed,
                        'prescription_date': prescription_date or timezone.now().date(),
                        'supplied_until': supplied_until,
                        'doctor_name': recipe.doctor_full_name if recipe.doctor_full_name != "-" else "",
                        'recipe_number': recipe.number,
                        'status': 'active' if supplied_until and supplied_until >= timezone.now().date() else 'expired'
                    }
                )
                
                if is_created:
                    created += 1
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # Показываем только первые 5 ошибок
                    logger.error(f"Ошибка обработки рецепта {recipe.number}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Назначений создано/обновлено: {created}'))
        if errors > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠️ Ошибок: {errors}'))
        
        return {'created': created, 'errors': errors}

