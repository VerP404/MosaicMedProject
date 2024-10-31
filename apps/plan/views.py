from django.http import JsonResponse

from .models import FilterCondition, GroupIndicators, OptionsForReportFilters


def build_filter_conditions(group):
    # Получаем все фильтры для данной группы и всех родительских групп
    filters = group.get_all_filters()
    conditions = []

    for filter in filters:
        field = filter.field_name
        values = filter.get_values_list()

        # Основное условие
        if filter.filter_type == 'exact':
            conditions.append(f"{field} = '{values[0]}'")
        elif filter.filter_type == 'in':
            values_str = ', '.join(f"'{v}'" for v in values)
            conditions.append(f"{field} IN ({values_str})")
        elif filter.filter_type == 'like':
            like_conditions = " OR ".join(f"{field} LIKE '%{v}%'" for v in values)
            conditions.append(f"({like_conditions})")

    return " AND ".join(conditions) if conditions else ""


def report_data(request, year):
    def get_hierarchical_groups(group=None, level=0):
        groups = GroupIndicators.objects.filter(parent=group) if group else GroupIndicators.objects.filter(
            parent__isnull=True)
        result = []

        for g in groups:
            filters = [f"{f.field_name} ({f.get_filter_type_display()}): {f.values}" for f in g.filters.all()]
            group_data = {
                "id": g.id,
                "name": g.name,
                "level": g.level,
                "filters": filters,
                "subgroups": get_hierarchical_groups(g, level + 1),
            }
            result.append(group_data)

        return result

    # Получение данных отчета по заданному году
    report_data = [
        {
            "group_id": report.group.id,
            "group_name": report.group.name,
            "year": report.year,
            "purpose": report.purpose,
            "sum_values": report.sum_values,
            "visits": report.visits,
            "profile_mp": report.profile_mp,
        }
        for report in OptionsForReportFilters.objects.filter(year=year)
    ]

    return JsonResponse({
        "groups": get_hierarchical_groups(),
        "data": report_data,
    })
