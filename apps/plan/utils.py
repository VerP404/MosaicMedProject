from datetime import datetime

from apps.plan.models import GroupIndicators


def copy_filters_to_new_year(new_year):
    """Копирование фильтров всех групп в новый год"""
    current_year = datetime.now().year
    for group in GroupIndicators.objects.all():
        # Получаем текущие фильтры для группы и года
        current_filters = group.get_all_filters(year=current_year)

        # Копируем каждый фильтр
        for filter in current_filters:
            filter.pk = None  # Сбрасываем первичный ключ для создания копии
            filter.year = new_year  # Устанавливаем новый год
            filter.save()
