# Generated by Django 5.1 on 2024-11-14 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_loader', '0014_dataimport_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataloaderconfig',
            name='clear_all_rows',
            field=models.BooleanField(default=False, verbose_name='Очистить всю таблицу при загрузке'),
        ),
    ]