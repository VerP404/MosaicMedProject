"""
Management команда для генерации external_id для существующих записей GroupIndicators и AnnualPlan.
Используется для заполнения external_id для данных, которые были созданы до добавления этого поля.
"""
import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.plan.models import GroupIndicators, AnnualPlan


class Command(BaseCommand):
    help = 'Генерирует external_id для существующих записей GroupIndicators и AnnualPlan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без сохранения изменений'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перегенерировать external_id даже для записей, у которых он уже есть'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('Режим проверки (dry-run). Изменения не будут сохранены.'))

        with transaction.atomic():
            # Генерируем external_id для GroupIndicators
            if force:
                groups_to_process = GroupIndicators.objects.all()
            else:
                groups_to_process = GroupIndicators.objects.filter(external_id__isnull=True)
            
            groups_count = 0
            for group in groups_to_process:
                if force or not group.external_id:
                    new_external_id = str(uuid.uuid4())
                    if not dry_run:
                        group.external_id = new_external_id
                        group.save(update_fields=['external_id'])
                    groups_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Группа "{group.name}": external_id = {new_external_id}')
                    )

            # Генерируем external_id для AnnualPlan
            if force:
                plans_to_process = AnnualPlan.objects.all()
            else:
                plans_to_process = AnnualPlan.objects.filter(external_id__isnull=True)
            
            plans_count = 0
            for plan in plans_to_process:
                if force or not plan.external_id:
                    new_external_id = str(uuid.uuid4())
                    if not dry_run:
                        plan.external_id = new_external_id
                        plan.save(update_fields=['external_id'])
                    plans_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'План "{plan.group.name} - {plan.year}": external_id = {new_external_id}')
                    )

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(f'Транзакция откачена (dry-run режим). Будет обновлено: {groups_count} групп, {plans_count} планов')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно обновлено: {groups_count} групп, {plans_count} планов'
                    )
                )

