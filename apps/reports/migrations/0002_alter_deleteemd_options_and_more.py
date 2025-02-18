# Generated by Django 5.1 on 2024-10-10 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='deleteemd',
            options={'verbose_name': 'ЭМД: аннулирование', 'verbose_name_plural': 'ЭМД: аннулирование'},
        ),
        migrations.AlterModelOptions(
            name='invalidationreason',
            options={'verbose_name': 'Справочник: ЭМД - причина', 'verbose_name_plural': 'Справочник: ЭМД - причины'},
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='added_date',
            field=models.DateField(auto_now_add=True, verbose_name='Дата добавления'),
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='creation_date',
            field=models.DateField(verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='date_of_birth',
            field=models.DateField(verbose_name='Дата рождения'),
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='registration_date',
            field=models.DateField(verbose_name='Дата регистрации'),
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='treatment_end',
            field=models.DateField(verbose_name='Окончание лечения'),
        ),
    ]
