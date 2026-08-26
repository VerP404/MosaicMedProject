from django.core.management.base import BaseCommand, CommandError

from apps.dn_app.services.iszl_sync import DNBulkSync, resolve_plan_year, resolve_plan_years


class Command(BaseCommand):
    help = "Bulk sync load_data_dispansery_iszl -> dn_app (Person/DnLine) + OMS facts"

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, default=0, help="PlanYear; 0 = auto current")
        parser.add_argument(
            "--all-years",
            action="store_true",
            help="Sync all PlanYears in bronze (slower)",
        )

    def handle(self, *args, **options):
        try:
            if options.get("all_years"):
                years = resolve_plan_years(None)
            else:
                years = [resolve_plan_year(options.get("year") or None)]
        except ValueError as e:
            raise CommandError(str(e)) from e

        self.stdout.write(f"Bulk sync years: {years}")
        for year in years:
            self.stdout.write(f"--- {year} ---")
            sync = DNBulkSync(year=year)
            ok, message = sync.process()
            self.stdout.write(message)
            self.stdout.write(str(sync.stats))
            if not ok:
                raise CommandError(message)
        self.stdout.write(self.style.SUCCESS("Done"))
