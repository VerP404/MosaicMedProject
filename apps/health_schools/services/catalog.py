from __future__ import annotations

from apps.health_schools.models import HealthSchool
from apps.health_schools.services.matching import SchoolSpec


def spec_from_model(row: HealthSchool) -> SchoolSpec:
    return SchoolSpec(
        number=int(row.number),
        name=row.name,
        group_name=row.group_name,
        mkb_rule=row.mkb_rule,
        visits=int(row.visits),
        duration=row.duration,
        tariff=str(row.tariff),
        service_code=row.service_code,
        service_title=row.service_title,
        period_years=int(row.period_years),
        criterion=row.criterion,
        min_age=row.min_age,
        max_age=row.max_age,
    )


def active_catalog() -> list[SchoolSpec]:
    rows = HealthSchool.objects.filter(is_active=True).order_by("number")
    return [spec_from_model(r) for r in rows]
