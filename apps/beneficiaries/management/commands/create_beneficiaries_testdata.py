"""
Management команда для создания тестовых данных для системы льготников
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.beneficiaries.models import (
    BenefitCategory, Patient, Drug, PatientDrugSupply, DrugStock
)


class Command(BaseCommand):
    help = 'Создание тестовых данных для системы льготников'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Начинаем создание тестовых данных...'))
        
        # Создаем категории льгот
        categories = self.create_benefit_categories()
        self.stdout.write(self.style.SUCCESS(f'✓ Создано категорий льгот: {len(categories)}'))
        
        # Создаем препараты
        drugs = self.create_drugs()
        self.stdout.write(self.style.SUCCESS(f'✓ Создано препаратов: {len(drugs)}'))
        
        # Создаем остатки препаратов
        self.create_drug_stocks(drugs)
        self.stdout.write(self.style.SUCCESS(f'✓ Созданы остатки препаратов'))
        
        # Создаем пациентов
        patients = self.create_patients(categories)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано пациентов: {len(patients)}'))
        
        # Создаем назначения
        supplies_count = self.create_drug_supplies(patients, drugs)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано назначений: {supplies_count}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.WARNING('\n📋 Статистика:'))
        self.stdout.write(f'   - Категорий льгот: {len(categories)}')
        self.stdout.write(f'   - Препаратов: {len(drugs)}')
        self.stdout.write(f'   - Пациентов: {len(patients)}')
        self.stdout.write(f'   - Назначений: {supplies_count}')
        self.stdout.write(self.style.SUCCESS('\n🌐 Откройте: http://localhost:8000/beneficiaries/'))

    def create_benefit_categories(self):
        """Создание категорий льгот"""
        categories_data = [
            {
                'name': 'Федеральная льгота',
                'code': 'FED',
                'description': 'Федеральные льготники',
                'default_coverage_percentage': 100,
                'financing_source': 'Федеральный бюджет',
                'is_for_children': False,
            },
            {
                'name': 'Региональная льгота',
                'code': 'REG',
                'description': 'Региональные льготники',
                'default_coverage_percentage': 100,
                'financing_source': 'Региональный бюджет',
                'is_for_children': False,
            },
            {
                'name': 'Льгота для детей',
                'code': 'CHILD',
                'description': 'Льготы для детей',
                'default_coverage_percentage': 100,
                'financing_source': 'Федеральный бюджет',
                'is_for_children': True,
            },
            {
                'name': 'Орфанные заболевания',
                'code': 'ORPHAN',
                'description': 'Редкие (орфанные) заболевания',
                'default_coverage_percentage': 100,
                'financing_source': 'Федеральный бюджет',
                'is_for_children': False,
            },
        ]
        
        categories = []
        for data in categories_data:
            category, created = BenefitCategory.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            categories.append(category)
        
        return categories

    def create_drugs(self):
        """Создание препаратов"""
        drugs_data = [
            {
                'name': 'Аспирин',
                'inn': 'Ацетилсалициловая кислота',
                'code': 'ASP001',
                'active_substance': 'Ацетилсалициловая кислота',
                'dosage_form': 'Таблетки',
                'dosage': '100 мг',
                'manufacturer': 'ООО Фармстандарт',
                'country': 'Россия',
                'atc_code': 'N02BA01',
            },
            {
                'name': 'Инсулин',
                'inn': 'Инсулин человеческий',
                'code': 'INS001',
                'active_substance': 'Инсулин',
                'dosage_form': 'Раствор для инъекций',
                'dosage': '100 МЕ/мл',
                'manufacturer': 'Novo Nordisk',
                'country': 'Дания',
                'atc_code': 'A10AB01',
            },
            {
                'name': 'Эналаприл',
                'inn': 'Эналаприл',
                'code': 'ENA001',
                'active_substance': 'Эналаприл',
                'dosage_form': 'Таблетки',
                'dosage': '10 мг',
                'manufacturer': 'ОАО Акрихин',
                'country': 'Россия',
                'atc_code': 'C09AA02',
            },
            {
                'name': 'Метформин',
                'inn': 'Метформин',
                'code': 'MET001',
                'active_substance': 'Метформин',
                'dosage_form': 'Таблетки',
                'dosage': '500 мг',
                'manufacturer': 'ЗАО Канонфарма',
                'country': 'Россия',
                'atc_code': 'A10BA02',
            },
            {
                'name': 'Амоксициллин',
                'inn': 'Амоксициллин',
                'code': 'AMO001',
                'active_substance': 'Амоксициллин',
                'dosage_form': 'Капсулы',
                'dosage': '500 мг',
                'manufacturer': 'ООО Синтез',
                'country': 'Россия',
                'atc_code': 'J01CA04',
            },
        ]
        
        drugs = []
        for data in drugs_data:
            drug, created = Drug.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            drugs.append(drug)
        
        return drugs

    def create_drug_stocks(self, drugs):
        """Создание остатков препаратов"""
        import random
        
        for drug in drugs:
            DrugStock.objects.get_or_create(
                drug=drug,
                defaults={'quantity': random.randint(50, 500)}
            )

    def create_patients(self, categories):
        """Создание пациентов"""
        patients_data = [
            {
                'full_name': 'Иванов Иван Иванович',
                'birth_date': datetime(1955, 3, 15),
                'snils': '123-456-789 00',
                'enp': '1234567890123456',
                'diagnosis_code': 'E11',
                'diagnosis_name': 'Сахарный диабет 2 типа',
                'address': 'г. Воронеж, ул. Ленина, д. 1, кв. 1',
                'phone': '+7 (900) 111-11-11',
            },
            {
                'full_name': 'Петрова Мария Сергеевна',
                'birth_date': datetime(1960, 7, 20),
                'snils': '234-567-890 11',
                'enp': '2345678901234567',
                'diagnosis_code': 'I10',
                'diagnosis_name': 'Гипертоническая болезнь',
                'address': 'г. Воронеж, ул. Пушкина, д. 5, кв. 12',
                'phone': '+7 (900) 222-22-22',
            },
            {
                'full_name': 'Сидоров Петр Александрович',
                'birth_date': datetime(1948, 12, 1),
                'snils': '345-678-901 22',
                'enp': '3456789012345678',
                'diagnosis_code': 'I20',
                'diagnosis_name': 'Стенокардия',
                'address': 'г. Воронеж, ул. Кольцовская, д. 10, кв. 5',
                'phone': '+7 (900) 333-33-33',
            },
            {
                'full_name': 'Козлова Анна Дмитриевна',
                'birth_date': datetime(2010, 5, 10),
                'snils': '456-789-012 33',
                'enp': '4567890123456789',
                'diagnosis_code': 'J45',
                'diagnosis_name': 'Бронхиальная астма',
                'address': 'г. Воронеж, ул. Студенческая, д. 3, кв. 20',
                'phone': '+7 (900) 444-44-44',
            },
            {
                'full_name': 'Смирнов Алексей Викторович',
                'birth_date': datetime(1965, 9, 25),
                'snils': '567-890-123 44',
                'enp': '5678901234567890',
                'diagnosis_code': 'M06',
                'diagnosis_name': 'Ревматоидный артрит',
                'address': 'г. Воронеж, ул. Плехановская, д. 15, кв. 8',
                'phone': '+7 (900) 555-55-55',
            },
        ]
        
        patients = []
        import random
        
        for data in patients_data:
            # Выбираем категорию в зависимости от возраста
            age = (datetime.now().date() - data['birth_date'].date()).days // 365
            if age < 18:
                category = [c for c in categories if c.is_for_children][0]
            else:
                category = random.choice([c for c in categories if not c.is_for_children])
            
            patient, created = Patient.objects.get_or_create(
                snils=data['snils'],
                defaults={
                    **data,
                    'benefit_category': category,
                    'is_active': True,
                }
            )
            patients.append(patient)
        
        return patients

    def create_drug_supplies(self, patients, drugs):
        """Создание назначений препаратов"""
        import random
        
        supplies_count = 0
        today = timezone.now().date()
        
        # Матрица соответствия диагнозов и препаратов
        diagnosis_drugs = {
            'E11': ['INS001', 'MET001'],  # Диабет
            'I10': ['ENA001'],  # Гипертония
            'I20': ['ASP001', 'ENA001'],  # Стенокардия
            'J45': ['AMO001'],  # Астма
            'M06': ['ASP001'],  # Артрит
        }
        
        for patient in patients:
            # Определяем препараты для пациента по диагнозу
            drug_codes = diagnosis_drugs.get(patient.diagnosis_code, ['ASP001'])
            patient_drugs = [d for d in drugs if d.code in drug_codes]
            
            for drug in patient_drugs:
                # Случайное количество дней до истечения (от -10 до +60)
                days_offset = random.choice([
                    -10, -5, -2,  # Истекшие
                    2, 5, 7,  # Срочные
                    15, 30, 45, 60  # Нормальные
                ])
                
                # Определяем статус
                if days_offset < 0:
                    status = 'expired'
                elif days_offset <= 7:
                    status = 'active'
                else:
                    status = 'active'
                
                supply, created = PatientDrugSupply.objects.get_or_create(
                    patient=patient,
                    drug=drug,
                    defaults={
                        'monthly_need': f'{random.randint(1, 3)} упаковки',
                        'dose_regimen': f'{random.randint(1, 3)} раз в день',
                        'prescribed': f'{random.randint(1, 3)} упаковки',
                        'prescription_date': today - timedelta(days=30),
                        'issue_date': today - timedelta(days=25),
                        'supplied_until': today + timedelta(days=days_offset),
                        'status': status,
                        'doctor_name': random.choice([
                            'Доктор А.А. Смирнов',
                            'Доктор Б.Б. Иванова',
                            'Доктор В.В. Петров',
                        ]),
                        'recipe_number': f'Р-{random.randint(100000, 999999)}',
                        'note': random.choice([
                            '',
                            'Требуется контроль',
                            'Особое внимание',
                            '',
                        ]),
                    }
                )
                if created:
                    supplies_count += 1
        
        return supplies_count

