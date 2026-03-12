from __future__ import annotations

from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Полное обновление dn_reference из файлов: 168н, свод услуг, usl_spec."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-path",
            type=str,
            default=None,
            help="Базовая папка с файлами (по умолчанию apps/dn_reference/data)",
        )

    def handle(self, *args, **options):
        if options["base_path"]:
            base_path = Path(options["base_path"]).resolve()
        else:
            base_path = Path(__file__).resolve().parent.parent.parent / "data"

        if not base_path.exists():
            raise CommandError(f"Папка не найдена: {base_path}")

        diagnosis_file = base_path / "диагнозы по 168н.xlsx"
        services_file = base_path / "свод услуг.xlsx"
        usl_spec_path = base_path / "usl_spec"

        if not diagnosis_file.exists():
            raise CommandError(f"Не найден файл: {diagnosis_file}")
        if not services_file.exists():
            raise CommandError(f"Не найден файл: {services_file}")
        if not usl_spec_path.exists():
            raise CommandError(f"Не найдена папка: {usl_spec_path}")

        self.stdout.write(self.style.WARNING("Очистка и полное обновление dn_reference из файлов..."))

        call_command(
            "shell",
            "-c",
            (
                "from apps.dn_reference.models import "
                "DnDiagnosisSpecialty,DnDiagnosisGroupMembership,DnServiceRequirement,"
                "DnServicePrice,DnServicePricePeriod,DnDiagnosis,DnDiagnosisCategory,"
                "DnDiagnosisGroup,DnService,DnSpecialty; "
                "DnDiagnosisSpecialty.objects.all().delete(); "
                "DnDiagnosisGroupMembership.objects.all().delete(); "
                "DnServiceRequirement.objects.all().delete(); "
                "DnServicePrice.objects.all().delete(); "
                "DnServicePricePeriod.objects.all().delete(); "
                "DnDiagnosis.objects.all().delete(); "
                "DnDiagnosisCategory.objects.all().delete(); "
                "DnDiagnosisGroup.objects.all().delete(); "
                "DnService.objects.all().delete(); "
                "DnSpecialty.objects.all().delete(); "
                "print('dn_reference cleared')"
            ),
            stdout=self.stdout,
        )

        call_command(
            "import_dn_diagnoses_168n",
            str(diagnosis_file),
            "--sheet",
            "Лист1",
            stdout=self.stdout,
        )
        call_command(
            "import_dn_services_catalog",
            str(services_file),
            stdout=self.stdout,
        )
        call_command(
            "import_dn_usl_spec",
            "--path",
            str(usl_spec_path),
            "--clear",
            stdout=self.stdout,
        )

        self.stdout.write(self.style.SUCCESS("dn_reference успешно обновлен из файлов."))

