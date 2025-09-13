from datetime import datetime, date

from django.db import models
from django.db.models import Count

from apps.organization.models import MedicalOrganization
from apps.personnel.models import DoctorRecord
from apps.load_data.models import Talon


def _get_active_doctors_count() -> int:
    today = date.today()
    return DoctorRecord.objects.filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    ).distinct("person").count()


def _get_talons_per_year():
    qs = (
        Talon.objects
        .exclude(report_year__isnull=True)
        .exclude(report_year="-")
        .values("report_year")
        .annotate(total=Count("id"))
    )
    # Преобразуем в отсортированный список словарей по году (как число)
    data = []
    for row in qs:
        try:
            year_int = int(row["report_year"])
        except ValueError:
            continue
        data.append({"year": year_int, "total": row["total"]})
    data.sort(key=lambda x: x["year"])  # возрастание по году
    return data


def dashboard_callback(request, context):
    org = MedicalOrganization.objects.first()
    doctors_count = _get_active_doctors_count()
    talons_yearly = _get_talons_per_year()
    talons_total = sum(x["total"] for x in talons_yearly)

    context.update({
        "org_name": org.name if org else "Медицинская организация",
        "app_version": "3.2",
        "current_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "doctors_count": doctors_count,
        "talons_total": talons_total,
        "talons_yearly": talons_yearly,
    })
    return context


