from datetime import datetime

from apps.plan.models import GroupIndicators, FilterCondition, AnnualPlan


def copy_filters_to_new_year(groups_queryset, new_year):
    """Копирование фильтров выбранных групп в новый год"""
    current_year = datetime.now().year
    for group in groups_queryset:
        # Получаем текущие фильтры для группы и года
        current_filters = group.filters.filter(year=current_year)

        # Копируем каждый фильтр
        for filter in current_filters:
            # Проверяем, существует ли уже такой фильтр в новом году
            if not FilterCondition.objects.filter(
                    group=group,
                    field_name=filter.field_name,
                    filter_type=filter.filter_type,
                    year=new_year
            ).exists():
                filter.pk = None  # Сбрасываем первичный ключ для создания копии
                filter.year = new_year  # Устанавливаем новый год
                filter.save()

        # Убедимся, что AnnualPlan существует для нового года
        AnnualPlan.objects.get_or_create(group=group, year=new_year)
