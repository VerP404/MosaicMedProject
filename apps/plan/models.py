from datetime import datetime

from django.db import models

from apps.oms_reference.models import GeneralOMSTarget


class GroupIndicators(models.Model):
    name = models.CharField(max_length=100, verbose_name="Группа")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgroups')
    level = models.IntegerField(default=0, verbose_name="Уровень вложенности")

    def save(self, *args, **kwargs):
        # Устанавливаем уровень вложенности на основе родительской группы
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super(GroupIndicators, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    @classmethod
    def get_groups_for_year(cls, year):
        """Получение всех групп и их фильтров для заданного года"""
        groups_data = []
        for group in cls.objects.all():
            filters = group.get_all_filters(year=year)  # Получаем фильтры с учетом года
            filters_data = [{
                "field_name": f.field_name,
                "filter_type": f.filter_type,
                "values": f.get_values_list(),
                "year": f.year
            } for f in filters]
            groups_data.append({
                "group_name": group.name,
                "filters": filters_data,
            })
        return groups_data

    def get_all_filters(self, year=None):
        """Получение всех фильтров для группы и ее родителей, учитывая год"""
        filters = self.filters.filter(year=year)

        if not filters.exists() and year:
            # Если фильтров для текущего года нет, пытаемся получить для предыдущего доступного года
            latest_year = self.filters.filter(year__lt=year).order_by('-year').first()
            if latest_year:
                filters = self.filters.filter(year=latest_year.year)

        if self.parent:
            filters |= self.parent.get_all_filters(year=year)  # Объединяем фильтры с родительскими

        return filters


class FilterCondition(models.Model):
    FILTER_TYPES = [
        ('exact', 'Точное соответствие (=)'),
        ('in', 'В списке (IN)'),
        ('like', 'Похож на (LIKE)'),
    ]

    group = models.ForeignKey(GroupIndicators, on_delete=models.CASCADE, related_name="filters")
    field_name = models.CharField(max_length=100, verbose_name="Поле фильтрации")
    filter_type = models.CharField(max_length=10, choices=FILTER_TYPES, verbose_name="Тип фильтра")
    values = models.TextField(verbose_name="Значения (через запятую)")
    year = models.IntegerField(default=datetime.now().year, verbose_name="Год действия фильтра")

    def __str__(self):
        return f"{self.group.name} - {self.field_name} ({self.get_filter_type_display()}) - {self.year}"

    def get_values_list(self):
        return [v.strip() for v in self.values.split(",")]
