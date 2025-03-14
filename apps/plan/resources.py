import json
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import GroupIndicators, FilterCondition


class NullableForeignKeyWidget(ForeignKeyWidget):
    def get_queryset(self, value, row=None, **kwargs):
        return super().get_queryset(value, row=row, **kwargs)

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        try:
            qs = self.get_queryset(value, row=row, **kwargs)
            return qs.get(**{self.field: value})
        except self.model.DoesNotExist:
            return value


class GroupIndicatorsResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=NullableForeignKeyWidget(GroupIndicators, 'id')
    )
    # Указываем attribute=None, чтобы это поле рассматривалось как виртуальное
    filters = fields.Field(
        column_name='filters',
        attribute='_imported_filters'
    )

    class Meta:
        model = GroupIndicators
        import_id_fields = ('id',)
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
        parent_value = data.get('parent')
        if parent_value and not isinstance(parent_value, GroupIndicators):
            obj._imported_parent = parent_value
            data['parent'] = None
        super().import_obj(obj, data, dry_run)
        obj._imported_filters = data.get('filters', [])

    def after_save_instance(self, instance, row, **kwargs):
        if kwargs.get('dry_run'):
            return
        if hasattr(instance, '_imported_parent'):
            try:
                parent_instance = GroupIndicators.objects.get(pk=instance._imported_parent)
                instance.parent = parent_instance
                instance.save()
            except GroupIndicators.DoesNotExist:
                pass
        FilterCondition.objects.filter(group=instance).delete()
        for cond in getattr(instance, '_imported_filters', []):
            if isinstance(cond, dict) and all(k in cond for k in ['field_name', 'filter_type', 'values', 'year']):
                fc = FilterCondition.objects.create(
                    group=instance,
                    field_name=cond['field_name'],
                    filter_type=cond['filter_type'],
                    values=cond['values'],
                    year=cond['year'],
                )