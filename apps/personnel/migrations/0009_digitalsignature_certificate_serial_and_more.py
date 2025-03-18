import django.db.models.deletion
from django.db import migrations, models


def fill_digital_signature_defaults(apps, schema_editor):
    DigitalSignature = apps.get_model("personnel", "DigitalSignature")
    PostRG014 = apps.get_model("personnel", "PostRG014")
    # Получаем или создаём запись с кодом '000' и описанием "не указана"
    default_position, created = PostRG014.objects.get_or_create(
        code='000',
        defaults={'description': 'не указана'}
    )

    for ds in DigitalSignature.objects.all():
        # Если valid_from заполнено и certificate_serial пустое, генерируем его по шаблону YY-MM-XXX
        if ds.valid_from and not ds.certificate_serial:
            year = ds.valid_from.year % 100  # двухзначный год
            month = ds.valid_from.month      # месяц
            # Определяем порядковый номер для данного valid_from:
            count = DigitalSignature.objects.filter(
                valid_from=ds.valid_from, certificate_serial__gt=''
            ).count() + 1
            ds.certificate_serial = f"{year:02d}-{month:02d}-{count:03d}"
        # Если поле должности не заполнено, присваиваем default_position
        if not ds.position:
            ds.position = default_position
        ds.save()


def reverse_fill_digital_signature_defaults(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('personnel', '0008_alter_doctorreportingrecord_doctor_records'),
    ]

    operations = [
        # Добавляем новое поле certificate_serial с пустым значением по умолчанию
        migrations.AddField(
            model_name='digitalsignature',
            name='certificate_serial',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Серийный номер сертификата'),
        ),
        # Добавляем новое поле position, разрешая NULL для существующих записей
        migrations.AddField(
            model_name='digitalsignature',
            name='position',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='personnel.postrg014', verbose_name='Должность'),
        ),
        migrations.AlterField(
            model_name='digitalsignature',
            name='scan',
            field=models.FileField(blank=True, null=True, upload_to='digital_signatures', verbose_name='Скан выписки'),
        ),
        # Заполняем для существующих записей certificate_serial и position
        migrations.RunPython(fill_digital_signature_defaults, reverse_fill_digital_signature_defaults),
        # Теперь меняем поле position на обязательное
        migrations.AlterField(
            model_name='digitalsignature',
            name='position',
            field=models.ForeignKey(null=False, on_delete=django.db.models.deletion.PROTECT, to='personnel.postrg014', verbose_name='Должность'),
        ),
    ]
