from import_export import resources, fields
from import_export.widgets import DateWidget, CharWidget
from .models import DigitalSignature, PostRG014


class DigitalSignatureResource(resources.ModelResource):
    full_name = fields.Field(column_name='ФИО')
    date_of_birth = fields.Field(column_name='Дата рождения')
    position_field = fields.Field(column_name='Должность')
    valid_from_field = fields.Field(column_name='Начало действия', widget=DateWidget(format='%d-%m-%Y'))
    valid_to_field = fields.Field(column_name='Окончание действия', widget=DateWidget(format='%d-%m-%Y'))
    certificate_serial_field = fields.Field(column_name='Серийный номер')
    usage_purpose = fields.Field(column_name='Цель использования')

    class Meta:
        model = DigitalSignature
        fields = (
            'full_name',
            'date_of_birth',
            'position_field',
            'valid_from_field',
            'valid_to_field',
            'certificate_serial_field',
            'usage_purpose',
        )
        export_order = (
            'full_name',
            'date_of_birth',
            'position_field',
            'valid_from_field',
            'valid_to_field',
            'certificate_serial_field',
            'usage_purpose',
        )
        ordering = ('valid_from',)

    def dehydrate_full_name(self, obj):
        return str(obj.person)

    def dehydrate_date_of_birth(self, obj):
        return obj.person.date_of_birth.strftime("%d-%m-%Y") if obj.person.date_of_birth else ""

    def dehydrate_position_field(self, obj):
        return obj.position.description if obj.position else "не указана"

    def dehydrate_valid_from_field(self, obj):
        return obj.valid_from.strftime("%d-%m-%Y") if obj.valid_from else ""

    def dehydrate_valid_to_field(self, obj):
        return obj.valid_to.strftime("%d-%m-%Y") if obj.valid_to else ""

    def dehydrate_certificate_serial_field(self, obj):
        return obj.certificate_serial or ""

    def dehydrate_usage_purpose(self, obj):
        return getattr(obj, 'usage_purpose', None) or "Работа в МИС - подписание ЭМД"


class PostRG014Resource(resources.ModelResource):
    code = fields.Field(
        column_name='code',
        attribute='code',
        widget=CharWidget()
    )
    description = fields.Field(
        column_name='description',
        attribute='description',
        widget=CharWidget()
    )

    class Meta:
        model = PostRG014
        # именно 'code' используем в качестве поля-идентификатора
        import_id_fields = ('code',)
        # указываем, какие поля хотим импортировать/экспортировать
        fields = ('code', 'description')
        skip_unchanged = True
        report_skipped = True
