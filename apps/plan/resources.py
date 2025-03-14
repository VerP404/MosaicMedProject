import json
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import GroupIndicators, FilterCondition

class NullableForeignKeyWidget(ForeignKeyWidget):
    def get_queryset(self, value, row=None, **kwargs):
        return super().get_queryset(value, row=row, **kwargs)

    def clean(self, value, row=None, **kwargs):
        """
        Простой виджет, который при отсутствии записи возвращает "сырое" значение (строку или число),
        а не пытается вызывать ошибку.
        """
        if not value:
            return None
        try:
            qs = self.get_queryset(value, row=row, **kwargs)
            return qs.get(**{self.field: value})
        except self.model.DoesNotExist:
            # Возвращаем "сырое" значение, чтобы сохранить его во временный атрибут
            return value

class GroupIndicatorsResource(resources.ModelResource):
    # ВАЖНО: attribute=None, чтобы django-import-export не трогал это поле
    parent = fields.Field(
        column_name='parent',
        attribute=None,  # <--- ключевой момент!
        widget=NullableForeignKeyWidget(GroupIndicators, 'id')
    )

    # Поле filters обрабатывается как виртуальное;
    # значение сохраняется во временном атрибуте _imported_filters
    filters = fields.Field(
        column_name='filters',
        attribute='_imported_filters'
    )

    class Meta:
        model = GroupIndicators
        import_id_fields = ('name',)
        fields = ('id', 'name', 'parent', 'filters')
        skip_unchanged = False
        report_skipped = True

    def dehydrate_filters(self, obj):
        conditions = []
        for cond in obj.filters.all():
            conditions.append({
                'field_name': cond.field_name,
                'filter_type': cond.filter_type,
                'values': cond.values,
                'year': cond.year,
            })
        return json.dumps(conditions, ensure_ascii=False)

    def before_import_row(self, row, **kwargs):
        """
        Преобразуем содержимое колонки filters из строки в JSON
        """
        if 'filters' in row and row['filters']:
            try:
                s = row['filters'].replace('""', '"')
                row['filters'] = json.loads(s)
            except Exception:
                row['filters'] = []
        else:
            row['filters'] = []
        return row

    def import_obj(self, obj, data, dry_run):
        """
        Вместо прямого присвоения obj.parent мы запоминаем идентификатор
        во временном атрибуте obj._imported_parent, чтобы потом
        корректно установить связь во втором проходе (after_import).
        """
        parent_value = data.get('parent')
        if parent_value and not isinstance(parent_value, GroupIndicators):
            # Если в CSV лежит, например, '3', а не объект GroupIndicators
            obj._imported_parent = parent_value
        # filters тоже сохраняем во временном атрибуте
        obj._imported_filters = data.get('filters', [])

        # Убираем parent из data, чтобы django-import-export не пытался сам что-то делать
        data['parent'] = None
        super().import_obj(obj, data, dry_run)

    def after_save_instance(self, instance, row, **kwargs):
        """
        Создаём FilterCondition для импортированной записи.
        Привязка к родителю — во втором проходе (after_import).
        """
        if kwargs.get('dry_run'):
            return

        # Удаляем старые условия и пересоздаём
        FilterCondition.objects.filter(group=instance).delete()
        for cond in getattr(instance, '_imported_filters', []):
            if isinstance(cond, dict) and all(k in cond for k in ['field_name', 'filter_type', 'values', 'year']):
                FilterCondition.objects.create(
                    group=instance,
                    field_name=cond['field_name'],
                    filter_type=cond['filter_type'],
                    values=cond['values'],
                    year=cond['year'],
                )

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """
        Второй проход: ищем родителя по сохранённому _imported_parent
        и устанавливаем связь (obj.parent = parent_instance).
        """
        if dry_run:
            return

        for obj in GroupIndicators.objects.all():
            if hasattr(obj, '_imported_parent'):
                parent_id = obj._imported_parent
                # Пытаемся найти родительский объект по ID
                try:
                    parent_instance = GroupIndicators.objects.get(pk=parent_id)
                    obj.parent = parent_instance
                    obj.save()
                except GroupIndicators.DoesNotExist:
                    # Если родителя нет — просто пропускаем или логируем
                    pass
                # Удаляем временный атрибут, чтобы не мешался
                del obj._imported_parent
