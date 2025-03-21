# Generated by Django 5.1 on 2025-03-19 06:09

import apps.personnel.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0009_digitalsignature_certificate_serial_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='person',
            options={'ordering': ['last_name', 'first_name'], 'verbose_name': 'Физическое лицо', 'verbose_name_plural': 'Врачи'},
        ),
        migrations.AlterModelOptions(
            name='postrg014',
            options={'ordering': ['description'], 'verbose_name': 'Должность RG014', 'verbose_name_plural': 'Справочник: Должности RG014'},
        ),
        migrations.AlterField(
            model_name='digitalsignature',
            name='scan',
            field=models.FileField(blank=True, null=True, upload_to=apps.personnel.models.digital_signature_upload_path, verbose_name='Скан выписки'),
        ),
    ]
