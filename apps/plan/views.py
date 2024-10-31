from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

from .models import GroupIndicators
from ..oms_reference.models import GeneralOMSTarget


def get_group_filters(request, group_id, year):
    try:
        group = GroupIndicators.objects.get(id=group_id)
        filters = group.get_all_filters(year=year)

        filters_data = []
        for filter in filters:
            filters_data.append({
                "field_name": filter.field_name,
                "filter_type": filter.filter_type,
                "values": filter.get_values_list(),
                "year": filter.year
            })

        response_data = {
            "group": group.name,
            "year": year,
            "filters": filters_data
        }

        return JsonResponse(response_data)
    except GroupIndicators.DoesNotExist:
        return JsonResponse({"error": "Group not found"}, status=404)


def get_nested_groups_for_year(request, year):
    """Получить все группы и фильтры для указанного года с учетом вложенности"""

    def get_group_data(group):
        """Рекурсивная функция для построения вложенной структуры"""
        filters = group.get_all_filters(year=year)
        filters_data = [{
            "field_name": f.field_name,
            "filter_type": f.filter_type,
            "values": f.get_values_list(),
            "year": f.year
        } for f in filters]

        return {
            "group_name": group.name,
            "level": group.level,
            "filters": filters_data,
            "subgroups": [get_group_data(subgroup) for subgroup in group.subgroups.all()]
        }

    # Получаем все корневые группы (те, у которых нет родительской)
    root_groups = GroupIndicators.objects.filter(parent__isnull=True)
    data = [get_group_data(group) for group in root_groups]

    return JsonResponse({"year": year, "groups": data})


@staff_member_required  # Ограничиваем доступ к этому представлению только для администраторов
def copy_filters_to_new_year(request, new_year):
    """Копирование фильтров для нового года"""
    current_year = datetime.now().year
    copy_filters_to_new_year(new_year=new_year)
    return JsonResponse({"status": "success", "message": f"Фильтры скопированы с {current_year} на {new_year}"})


def goals_list(request):
    goals = GeneralOMSTarget.objects.values_list('code', flat=True)
    return JsonResponse({"goals": list(goals)})
