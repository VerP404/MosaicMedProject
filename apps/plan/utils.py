from datetime import datetime

from apps.plan.models import (
    GroupIndicators,
    FilterCondition,
    AnnualPlan,
    MonthlyPlan,
    BuildingPlan,
    MonthlyBuildingPlan,
    DepartmentPlan,
    MonthlyDepartmentPlan,
)


def copy_filters_to_new_year(groups_queryset, new_year):
    """Копирование фильтров выбранных групп в новый год (источник = текущий год)."""
    source_year = datetime.now().year
    return copy_filters_from_year_to_year(groups_queryset, source_year, new_year)


def copy_filters_from_year_to_year(groups_queryset, source_year, target_year):
    """
    Копирование условий фильтрации (FilterCondition) выбранных групп с года source_year на год target_year.
    Возвращает dict: copied_count, groups_count.
    """
    if source_year == target_year:
        return {'error': 'Год-источник и год-назначение должны отличаться.', 'copied_count': 0, 'groups_count': 0}
    copied_count = 0
    for group in groups_queryset:
        source_filters = group.filters.filter(year=source_year)
        for fc in source_filters:
            if not FilterCondition.objects.filter(
                group=group,
                field_name=fc.field_name,
                filter_type=fc.filter_type,
                year=target_year,
            ).exists():
                fc.pk = None
                fc.year = target_year
                fc.save()
                copied_count += 1
        if source_filters.exists():
            AnnualPlan.objects.get_or_create(group=group, year=target_year)
    return {'copied_count': copied_count, 'groups_count': groups_queryset.count(), 'error': None}


def copy_plans_to_year(source_year, target_year):
    """
    Копирует все планы (AnnualPlan + MonthlyPlan, BuildingPlan, DepartmentPlan и их месячные значения)
    с года source_year на год target_year.
    Возвращает dict: created_annual, updated_annual, created_monthly, updated_monthly.
    """
    if source_year == target_year:
        return {'error': 'Год-источник и год-назначение должны отличаться.'}

    stats = {'created_annual': 0, 'updated_annual': 0, 'created_monthly': 0, 'updated_monthly': 0}

    source_plans = AnnualPlan.objects.filter(year=source_year).select_related('group').prefetch_related(
        'monthly_plans',
        'building_plans__monthly_building_plans',
        'building_plans__department_plans__monthly_department_plans',
    )

    for ap_src in source_plans:
        ap_dst, created = AnnualPlan.objects.get_or_create(
            group=ap_src.group,
            year=target_year,
            defaults={
                'show_in_cumulative_report': ap_src.show_in_cumulative_report,
                'show_in_indicators_report': ap_src.show_in_indicators_report,
                'sort_order': ap_src.sort_order,
            },
        )
        if created:
            stats['created_annual'] += 1
        else:
            stats['updated_annual'] += 1

        # Копируем месячные планы организации (quantity, amount)
        for mp_src in ap_src.monthly_plans.all():
            mp_dst, mp_created = MonthlyPlan.objects.get_or_create(
                annual_plan=ap_dst,
                month=mp_src.month,
                defaults={'quantity': 0, 'amount': 0.00},
            )
            mp_dst.quantity = mp_src.quantity
            mp_dst.amount = mp_src.amount
            mp_dst.save()
            if mp_created:
                stats['created_monthly'] += 1
            else:
                stats['updated_monthly'] += 1

        # Копируем планы по корпусам и отделениям (если есть)
        for bp_src in ap_src.building_plans.all():
            bp_dst = BuildingPlan.objects.filter(annual_plan=ap_dst, building=bp_src.building).first()
            if not bp_dst:
                continue
            for mbp_src in bp_src.monthly_building_plans.all():
                mbp_dst = MonthlyBuildingPlan.objects.filter(
                    building_plan=bp_dst, month=mbp_src.month
                ).first()
                if mbp_dst:
                    mbp_dst.quantity = mbp_src.quantity
                    mbp_dst.amount = mbp_src.amount
                    mbp_dst.save()

            for dp_src in bp_src.department_plans.all():
                dp_dst = DepartmentPlan.objects.filter(
                    building_plan=bp_dst, department=dp_src.department
                ).first()
                if not dp_dst:
                    continue
                for mdp_src in dp_src.monthly_department_plans.all():
                    mdp_dst = MonthlyDepartmentPlan.objects.filter(
                        department_plan=dp_dst, month=mdp_src.month
                    ).first()
                    if mdp_dst:
                        mdp_dst.quantity = mdp_src.quantity
                        mdp_dst.amount = mdp_src.amount
                        mdp_dst.save()

    return stats
