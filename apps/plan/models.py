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

        # Проверка и создание записей для каждого месяца
        if not self.monthly_plans.exists():
            for month in range(1, 13):
                MonthlyPlan.objects.create(group=self, month=month, quantity=0, amount=0.00)

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
        ('not_like', 'Не содержит (NOT LIKE)'),
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


# models.py
class MonthlyPlan(models.Model):
    group = models.ForeignKey(GroupIndicators, on_delete=models.CASCADE, related_name="monthly_plans",
                              verbose_name="Группа")
    month = models.PositiveSmallIntegerField(verbose_name="Месяц")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Деньги")

    class Meta:
        unique_together = ('group', 'month')
        verbose_name = "План на месяц"
        verbose_name_plural = "Планы на месяц"

    def save(self, *args, **kwargs):
        # Запрещаем изменение номера месяца
        if self.pk is not None:
            original = MonthlyPlan.objects.get(pk=self.pk)
            if original.month != self.month:
                raise ValueError("Номер месяца не может быть изменен.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Удаление записей месячного плана запрещено.")


class UnifiedFilter(models.Model):
    year = models.IntegerField(verbose_name="Год")
    type = models.CharField(max_length=50, verbose_name="Тип")

    def combined_conditions(self):
        # Используем self.conditions.all() вместо unifiedfiltercondition_set
        conditions = self.conditions.all()
        return " and ".join([
            f"{condition.field_name} {condition.filter_type} {condition.values}"
            for condition in conditions
        ])
    combined_conditions.short_description = "Индикаторы"
    class Meta:
        verbose_name = "Общий фильтр"
        verbose_name_plural = "Общие фильтры"

    def __str__(self):
        return f"{self.year} - {self.type}"


class UnifiedFilterCondition(models.Model):
    FILTER_TYPES = [
        ('exact', 'Точное соответствие (=)'),
        ('in', 'В списке (IN)'),
        ('like', 'Похож на (LIKE)'),
        ('not_like', 'Не содержит (NOT LIKE)'),
    ]

    filter = models.ForeignKey(UnifiedFilter, on_delete=models.CASCADE, related_name="conditions",
                               verbose_name="Фильтр")
    field_name = models.CharField(max_length=100, verbose_name="Поле для фильтрации")
    filter_type = models.CharField(max_length=10, choices=FILTER_TYPES, verbose_name="Тип фильтра")
    values = models.TextField(verbose_name="Значения (через запятую)")

    class Meta:
        verbose_name = "Условие фильтра"
        verbose_name_plural = "Условия фильтра"

    def __str__(self):
        return f"{self.field_name} ({self.filter_type}): {self.values}"

