from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from dal import autocomplete

from apps.oms_reference.models import GeneralOMSTarget
from apps.organization.models import Department, Building


class GroupIndicators(models.Model):
    name = models.CharField(max_length=100, verbose_name="Группа")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgroups')
    level = models.IntegerField(default=0, verbose_name="Уровень вложенности")
    is_distributable = models.BooleanField(
        default=False,
        verbose_name="Распределяемый план",
        help_text="Отметьте, если для этой группы требуется распределение по корпусам и отделениям"
    )
    buildings = models.ManyToManyField(
        Building,
        blank=True,
        verbose_name="Корпуса",
        help_text="Укажите корпуса, связанные с этой группой (для распределяемых планов)"
    )
    departments = models.ManyToManyField(
        Department,
        blank=True,
        verbose_name="Отделения",
        help_text="Выберите отделения, доступные для распределения планов"
    )

    def save(self, *args, **kwargs):
        # Устанавливаем уровень вложенности на основе родительской группы
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super(GroupIndicators, self).save(*args, **kwargs)

        if self.is_distributable:
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

        # Проверяем, сохранена ли связанная группа
        if not self.group_id:
            raise ValidationError("Связанная группа должна быть сохранена перед созданием условий фильтра.")

        # Преобразуем значения в список для сравнения
        current_values = sorted(self.get_values_list())

        # Ищем существующие условия с такими же параметрами
        existing_conditions = FilterCondition.objects.filter(
            group=self.group,
            field_name=self.field_name,
            filter_type=self.filter_type,
            year=self.year
        )

        # Исключаем текущую запись из проверки
        if self.pk:
            existing_conditions = existing_conditions.exclude(pk=self.pk)

        # Проверяем совпадение значений
        for condition in existing_conditions:
            if sorted(condition.get_values_list()) == current_values:
                raise ValidationError(
                    "Условие фильтра с такими параметрами и значениями уже существует для данной группы и года.")

    class Meta:
        unique_together = ('group', 'field_name', 'filter_type', 'year')
        verbose_name = "Условие фильтра"
        verbose_name_plural = "Условия фильтра"


class GroupBuildingDepartment(models.Model):
    group = models.ForeignKey(
        GroupIndicators,
        on_delete=models.CASCADE,
        related_name="group_building_departments",
        verbose_name="Группа"
    )
    year = models.PositiveIntegerField(
        verbose_name="Год",
        help_text="Укажите год, к которому относится корпус и отделение"
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="group_building_departments",
        verbose_name="Корпус"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="group_building_departments",
        verbose_name="Отделение"
    )

    class Meta:
        unique_together = ('group', 'year', 'building', 'department')
        verbose_name = "Корпус и отделение группы"
        verbose_name_plural = "Корпуса и отделения группы"

    def __str__(self):
        return f"{self.group.name} ({self.year}) - {self.building.name} - {self.department.name}"


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

    def total_quantity(self):
        return self.monthly_plans.aggregate(total=models.Sum("quantity"))["total"] or 0

    def total_amount(self):
        return self.monthly_plans.aggregate(total=models.Sum("amount"))["total"] or 0


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
        if self.pk:
            original = MonthlyPlan.objects.get(pk=self.pk)
            if original.month != self.month:
                raise ValueError("Номер месяца не может быть изменен.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Удаление записей месячного плана запрещено.")


class BuildingPlan(models.Model):
    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name='building_plans',
        verbose_name="Годовой план"
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='building_plans',
        verbose_name="Корпус"
    )

    class Meta:
        unique_together = ('annual_plan', 'building')
        verbose_name = "План корпуса"
        verbose_name_plural = "Планы корпусов"

    def __str__(self):
        return f"{self.building.name} - {self.annual_plan.year}"

    def clean(self):
        if self.pk:
            total_quantity = sum(
                monthly_plan.quantity for monthly_plan in self.monthly_building_plans.all()
            )
            total_annual_quantity = self.annual_plan.total_quantity()
            if total_quantity > total_annual_quantity:
                raise ValidationError("Сумма планов корпуса превышает план всей организации на год!")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Создание MonthlyBuildingPlan после сохранения BuildingPlan
            for month in range(1, 13):
                MonthlyBuildingPlan.objects.get_or_create(
                    building_plan=self,
                    month=month,
                    defaults={'quantity': 0, 'amount': 0.00}
                )


class MonthlyBuildingPlan(models.Model):
    building_plan = models.ForeignKey(
        BuildingPlan,
        on_delete=models.CASCADE,
        related_name="monthly_building_plans",
        verbose_name="План корпуса"
    )
    month = models.PositiveSmallIntegerField(verbose_name="Месяц")
    quantity = models.PositiveIntegerField(verbose_name="Количество", default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Бюджет", default=0.00)

    class Meta:
        unique_together = ('building_plan', 'month')
        verbose_name = "Месячный план корпуса"
        verbose_name_plural = "Месячные планы корпусов"

    def clean(self):
        # Проверка, что месячный план корпуса согласован с планом организации
        building_plan = self.building_plan
        monthly_plan = building_plan.annual_plan.monthly_plans.filter(month=self.month).first()

        if not monthly_plan:
            raise ValidationError(
                f"Месячный план организации на {self.month}-й месяц отсутствует. Проверьте настройки годового плана.")

        if self.quantity > monthly_plan.quantity:
            raise ValidationError(
                f"План корпуса на {self.month}-й месяц ({self.quantity}) превышает общий план организации ({monthly_plan.quantity})!"
            )
        if self.amount > monthly_plan.amount:
            raise ValidationError(
                f"Бюджет корпуса на {self.month}-й месяц ({self.amount}) превышает общий бюджет организации ({monthly_plan.amount})!"
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Запускает метод clean перед сохранением
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Удаление месячных планов запрещено.")

    def get_total_plan_for_month(self):
        """Возвращает общий план на месяц"""
        monthly_plan = self.building_plan.annual_plan.monthly_plans.filter(month=self.month).first()
        return monthly_plan.quantity if monthly_plan else 0

    def get_current_plan_for_month(self):
        """Возвращает текущий план для этого корпуса и месяца"""
        return MonthlyBuildingPlan.objects.filter(pk=self.pk).first().quantity if self.pk else 0

    def get_used_quantity_for_month(self, exclude_current=True):
        """
        Возвращает уже использованное количество для всех зданий в этот месяц.
        Опционально исключает текущий объект.
        """
        queryset = MonthlyBuildingPlan.objects.filter(
            building_plan__annual_plan=self.building_plan.annual_plan,
            month=self.month
        )
        if exclude_current and self.pk:
            queryset = queryset.exclude(pk=self.pk)
        used_quantity = queryset.aggregate(total=models.Sum('quantity'))['total']
        return used_quantity or 0

    def get_total_with_current_changes(self):
        """
        Возвращает общее использованное количество, включая текущий несохраненный план.
        """
        return self.get_used_quantity_for_month(exclude_current=True) + self.quantity

    def get_remaining_quantity(self):
        """Возвращает остаток, который можно использовать."""
        total_plan = self.get_total_plan_for_month()
        used_quantity = self.get_used_quantity_for_month()
        return total_plan - used_quantity - self.quantity

    def get_total_financial_plan_for_month(self):
        """Возвращает общий финансовый план на месяц"""
        monthly_plan = self.building_plan.annual_plan.monthly_plans.filter(month=self.month).first()
        return monthly_plan.amount if monthly_plan else 0

    def get_used_amount_for_month(self, exclude_current=True):
        """
        Возвращает уже использованный бюджет для всех зданий в этот месяц.
        Опционально исключает текущий объект.
        """
        queryset = MonthlyBuildingPlan.objects.filter(
            building_plan__annual_plan=self.building_plan.annual_plan,
            month=self.month
        )
        if exclude_current and self.pk:
            queryset = queryset.exclude(pk=self.pk)
        used_amount = queryset.aggregate(total=models.Sum('amount'))['total']
        return used_amount or 0

    def get_remaining_budget(self):
        """Возвращает остаток бюджета, который можно использовать."""
        total_plan = self.get_total_financial_plan_for_month()
        used_amount = self.get_used_amount_for_month()
        return total_plan - used_amount - self.amount


class DepartmentPlan(models.Model):
    building_plan = models.ForeignKey(
        BuildingPlan,
        on_delete=models.CASCADE,
        related_name='department_plans',
        verbose_name="План корпуса"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='department_plans',
        verbose_name="Отделение"
    )

    class Meta:
        unique_together = ('building_plan', 'department')
        verbose_name = "План отделения"
        verbose_name_plural = "Планы отделений"

    def __str__(self):
        return f"{self.department.name} - {self.building_plan}"

    def clean(self):
        if self.pk is not None:
            total_department_quantity = sum(
                plan.quantity for plan in self.monthly_department_plans.all()
            )
            total_department_amount = sum(
                plan.amount for plan in self.monthly_department_plans.all()
            )
            building_quantity = sum(
                plan.quantity for plan in self.building_plan.monthly_building_plans.all()
            )
            building_amount = sum(
                plan.amount for plan in self.building_plan.monthly_building_plans.all()
            )

            if total_department_quantity > building_quantity:
                raise ValidationError("Сумма планов отделений превышает план корпуса.")
            if total_department_amount > building_amount:
                raise ValidationError("Сумма бюджетов отделений превышает бюджет корпуса.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            for month in range(1, 13):
                MonthlyDepartmentPlan.objects.get_or_create(
                    department_plan=self,
                    month=month,
                    defaults={'quantity': 0, 'amount': 0.00}
                )

    def get_group_name(self):
        return self.building_plan.annual_plan.group.name

    get_group_name.short_description = "Группа"


class MonthlyDepartmentPlan(models.Model):
    department_plan = models.ForeignKey(
        DepartmentPlan,
        on_delete=models.CASCADE,
        related_name="monthly_department_plans",
        verbose_name="План отделения"
    )
    month = models.PositiveSmallIntegerField(verbose_name="Месяц")
    quantity = models.PositiveIntegerField(verbose_name="Количество", default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Бюджет", default=0.00)

    class Meta:
        unique_together = ('department_plan', 'month')
        verbose_name = "Месячный план отделения"
        verbose_name_plural = "Месячные планы отделений"

    def clean(self):
        department_plan = self.department_plan
        building_monthly_plan = department_plan.building_plan.monthly_building_plans.filter(month=self.month).first()

        if not building_monthly_plan:
            raise ValidationError(
                f"Месячный план корпуса на {self.month}-й месяц отсутствует. Проверьте настройки плана корпуса."
            )

        if self.quantity > building_monthly_plan.quantity:
            raise ValidationError(
                f"План отделения на {self.month}-й месяц ({self.quantity}) превышает план корпуса ({building_monthly_plan.quantity})!"
            )

        if self.amount > building_monthly_plan.amount:
            raise ValidationError(
                f"Бюджет отделения на {self.month}-й месяц ({self.amount}) превышает бюджет корпуса ({building_monthly_plan.amount})!"
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Запускает метод clean перед сохранением
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Удаление месячных планов запрещено.")

    def get_total_plan_for_month(self):
        """Возвращает общий план корпуса на месяц"""
        building_monthly_plan = self.department_plan.building_plan.monthly_building_plans.filter(
            month=self.month).first()
        return building_monthly_plan.quantity if building_monthly_plan else 0

    def get_current_plan_for_month(self):
        """Возвращает текущий сохраненный план для этого отделения и месяца"""
        return MonthlyDepartmentPlan.objects.filter(pk=self.pk).first().quantity if self.pk else 0

    def get_used_quantity_for_month(self, exclude_current=True):
        """Возвращает использованное количество для всех отделений в этот месяц"""
        queryset = MonthlyDepartmentPlan.objects.filter(
            department_plan__building_plan=self.department_plan.building_plan,
            month=self.month
        )
        if exclude_current and self.pk:
            queryset = queryset.exclude(pk=self.pk)
        used_quantity = queryset.aggregate(total=models.Sum('quantity'))['total']
        return used_quantity or 0

    def get_remaining_quantity(self):
        """Возвращает остаток количества"""
        total_plan = self.get_total_plan_for_month()
        used_quantity = self.get_used_quantity_for_month()
        return total_plan - used_quantity - self.quantity

    def get_total_financial_plan_for_month(self):
        """Возвращает общий финансовый план на месяц"""
        building_monthly_plan = self.department_plan.building_plan.monthly_building_plans.filter(
            month=self.month).first()
        return building_monthly_plan.amount if building_monthly_plan else 0

    def get_used_amount_for_month(self, exclude_current=True):
        """Возвращает использованный бюджет для всех отделений в этот месяц"""
        queryset = MonthlyDepartmentPlan.objects.filter(
            department_plan__building_plan=self.department_plan.building_plan,
            month=self.month
        )
        if exclude_current and self.pk:
            queryset = queryset.exclude(pk=self.pk)
        used_amount = queryset.aggregate(total=models.Sum('amount'))['total']
        return used_amount or 0

    def get_remaining_budget(self):
        """Возвращает остаток бюджета"""
        total_plan = self.get_total_financial_plan_for_month()
        used_amount = self.get_used_amount_for_month()
        return total_plan - used_amount - self.amount


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


class ChiefDashboard(models.Model):
    name = models.CharField(verbose_name="Название", max_length=100)
    goal = models.CharField(verbose_name="Цель", max_length=100)
    year = models.IntegerField(verbose_name="Год", default=datetime.now().year)
    plan = models.IntegerField(verbose_name="План", default=0)
    finance = models.DecimalField(verbose_name="Финансы", max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('name', 'goal', 'year')
        verbose_name = "Показатель"
        verbose_name_plural = "Панель главного врача"


