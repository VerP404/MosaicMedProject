# Generated by Django 5.1 on 2024-10-09 11:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_loader', '0005_dataloaderconfig'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dataloaderconfig',
            options={'verbose_name': 'Конфигуратор импорта таблиц', 'verbose_name_plural': 'Конфигуратор импорта'},
        ),
    ]