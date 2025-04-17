# apps/reports/admin/resources.py

from import_export import resources, fields
from import_export.widgets import (
    ForeignKeyWidget,
    ManyToManyWidget,
    DateWidget,
    CharWidget,
)
from .models import Patient, Site, Group

class PatientResource(resources.ModelResource):
    # Явно объявляем все поля с русскими заголовками
    full_name = fields.Field(
        column_name='ФИО',
        attribute='full_name',
        widget=CharWidget()
    )
    date_of_birth = fields.Field(
        column_name='Дата рождения',
        attribute='date_of_birth',
        widget=DateWidget(format='%d.%m.%Y')
    )
    gender = fields.Field(
        column_name='Пол',
        attribute='gender',
        widget=CharWidget()
    )
    enp = fields.Field(
        column_name='ЕНП',
        attribute='enp',
        widget=CharWidget()
    )
    address = fields.Field(
        column_name='Адрес',
        attribute='address',
        widget=CharWidget()
    )
    phone = fields.Field(
        column_name='Телефон',
        attribute='phone',
        widget=CharWidget()
    )

    # «Корпус» (Site.building)
    building = fields.Field(
        column_name='Корпус',
        attribute='site',
        widget=ForeignKeyWidget(Site, 'building')
    )
    # «Участок» (Site.site_name)
    site = fields.Field(
        column_name='Участок',
        attribute='site',
        widget=ForeignKeyWidget(Site, 'site_name')
    )

    # «Группы» (ManyToMany через ;)
    groups = fields.Field(
        column_name='Группы',
        attribute='groups',
        widget=ManyToManyWidget(Group, field='name', separator=';')
    )

    class Meta:
        model = Patient
        import_id_fields = ('enp',)
        fields = (
            'full_name',
            'date_of_birth',
            'gender',
            'enp',
            'building',
            'site',
            'address',
            'phone',
            'groups',
        )
        skip_unchanged = True
        report_skipped = True
        # порядок колонок в экспорт-файле будет таким же, как в fields
