# Generated by Django 5.1 on 2024-10-31 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oms_reference', '0002_statusweboms'),
        ('plan', '0004_filtercondition_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='filtercondition',
            name='goals',
            field=models.ManyToManyField(blank=True, to='oms_reference.generalomstarget', verbose_name='Цели ОМС'),
        ),
    ]
