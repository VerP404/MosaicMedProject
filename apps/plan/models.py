from datetime import datetime

from django.core.exceptions import ValidationError
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

        current_year = datetime.now().year
        AnnualPlan.objects.get_or_create(group=self, year=current_year)

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # После сохранения FilterCondition, убедимся, что AnnualPlan существует
        annual_plan, created = AnnualPlan.objects.get_or_create(group=self.group, year=self.year)
        if created:
            # Если AnnualPlan был создан, MonthlyPlan создадутся автоматически в его методе save()
            pass

    def clean(self):
        super().clean()
        # Проверяем, есть ли уже запись с такими же полями
        existing = FilterCondition.objects.filter(
            group=self.group,
            field_name=self.field_name,
            filter_type=self.filter_type,
            year=self.year
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError("Условие фильтра с такими параметрами уже существует для данной группы и года.")

    class Meta:
        unique_together = ('group', 'field_name', 'filter_type', 'year')
        verbose_name = "Условие фильтра"
        verbose_name_plural = "Условия фильтра"


class AnnualPlan(models.Model):
    group = models.ForeignKey(GroupIndicators, on_delete=models.CASCADE, related_name="annual_plans",
                              verbose_name="Группа")
    year = models.PositiveIntegerField(verbose_name="Год")

    class Meta:
        unique_together = ('group', 'year')
        verbose_name = "План на год"
        verbose_name_plural = "Планы на год"

    def __str__(self):
        return f"{self.group.name} - {self.year}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Убедимся, что записи MonthlyPlan существуют для каждого месяца
        for month in range(1, 13):
            MonthlyPlan.objects.get_or_create(annual_plan=self, month=month, defaults={'quantity': 0, 'amount': 0.00})


class MonthlyPlan(models.Model):
    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name="monthly_plans",
        verbose_name="Годовой план"
    )
    month = models.PositiveSmallIntegerField(verbose_name="Месяц")
    quantity = models.PositiveIntegerField(verbose_name="Количество", default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Деньги", default=0.00)

    class Meta:
        unique_together = ('annual_plan', 'month')
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
        # Получаем условия с их операторами и объединяем в строку
        conditions = self.conditions.all()
        combined_query = ""
        for index, condition in enumerate(conditions):
            condition_query = f"{condition.field_name} {condition.filter_type} {condition.values}"
            if index > 0:
                # Добавляем оператор перед условием, начиная со второго условия
                combined_query += f" {condition.operator} "
            combined_query += condition_query
        return combined_query

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
        ('<', 'Меньше (<)'),
        ('>', 'Больше (>)'),
    ]
    OPERATOR_CHOICES = [
        ('AND', 'И'),
        ('OR', 'ИЛИ'),
    ]
    filter = models.ForeignKey(UnifiedFilter, on_delete=models.CASCADE, related_name="conditions",
                               verbose_name="Фильтр")
    field_name = models.CharField(max_length=100, verbose_name="Поле для фильтрации")
    filter_type = models.CharField(max_length=10, choices=FILTER_TYPES, verbose_name="Тип фильтра")
    values = models.TextField(verbose_name="Значения (через запятую)")
    operator = models.CharField(max_length=3, choices=OPERATOR_CHOICES, default='AND', verbose_name="Оператор")

    class Meta:
        verbose_name = "Условие фильтра"
        verbose_name_plural = "Условия фильтра"

    def __str__(self):
        return f"{self.field_name} ({self.filter_type}): {self.values}"
