from django.db import models


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

    def get_all_filters(self):
        """Рекурсивное получение всех фильтров, включая фильтры родительских групп."""
        filters = list(self.filters.all())
        if self.parent:
            filters.extend(self.parent.get_all_filters())
        return filters


class OptionsForReportFilters(models.Model):
    group = models.ForeignKey(GroupIndicators, on_delete=models.CASCADE, verbose_name="Группа")
    year = models.IntegerField(verbose_name="Год отчета")
    purpose = models.CharField(max_length=50, verbose_name="Цель")
    sum_values = models.TextField(null=True, blank=True, verbose_name="Сумма")
    visits = models.IntegerField(null=True, blank=True, verbose_name="Посещения на дому")
    profile_mp = models.CharField(max_length=50, null=True, blank=True, verbose_name="Профиль МП")

    def __str__(self):
        return f"{self.group} - {self.year}"


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

    def __str__(self):
        return f"{self.group.name} - {self.field_name} ({self.get_filter_type_display()})"

    def get_values_list(self):
        return [v.strip() for v in self.values.split(",")]
