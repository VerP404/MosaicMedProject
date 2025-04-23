# apps/reports/resources.py

from import_export import resources, fields
from import_export.widgets import (
    ForeignKeyWidget, ManyToManyWidget, DateWidget, CharWidget
)
from .models import Patient, Site, Group


class PatientResource(resources.ModelResource):
    full_name = fields.Field(column_name='ФИО', attribute='full_name', widget=CharWidget())
    date_of_birth = fields.Field(column_name='Дата рождения', attribute='date_of_birth', widget=DateWidget('%d.%m.%Y'))
    gender = fields.Field(column_name='Пол', attribute='gender', widget=CharWidget())
    enp = fields.Field(column_name='ЕНП', attribute='enp', widget=CharWidget())
    address = fields.Field(column_name='Адрес', attribute='address', widget=CharWidget())
    phone = fields.Field(column_name='Телефон', attribute='phone', widget=CharWidget())

    building = fields.Field(
        column_name='Корпус',
        attribute='site',
        widget=ForeignKeyWidget(Site, 'building')
    )
    site = fields.Field(
        column_name='Участок',
        attribute='site',
        widget=ForeignKeyWidget(Site, 'site_name')
    )

    # здесь отдаём только доступные группы
    groups = fields.Field(
        column_name='Группы',
        attribute='groups',
        widget=ManyToManyWidget(Group, field='name', separator=';')
    )
    # поля «родители»
    parents = fields.Field(
        column_name='Родители',
        attribute='parents',
        widget=ManyToManyWidget(Patient, field='full_name', separator=';')
    )

    class Meta:
        model = Patient
        import_id_fields = ('enp',)
        fields = (
            'full_name', 'date_of_birth', 'gender', 'enp',
            'building', 'site', 'address', 'phone',
            'groups', 'parents',
        )
        skip_unchanged = True
        report_skipped = True

    def dehydrate_groups(self, patient):
        user = self.context['request'].user
        qs = patient.groups
        if not user.is_superuser:
            allowed = user.usergroupaccess_set.values_list('group_id', flat=True)
            qs = qs.filter(id__in=allowed)
        return ';'.join(qs.values_list('name', flat=True))

    def dehydrate_parents(self, patient):
        return ';'.join(patient.parents.values_list('full_name', flat=True))
