# Generated by Django 5.1 on 2024-10-17 07:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_alter_deleteemd_creation_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SVOMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_name', models.CharField(max_length=100, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=100, verbose_name='Имя')),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Отчество')),
                ('birth_date', models.DateField(verbose_name='Дата рождения')),
                ('enp', models.CharField(max_length=16, unique=True, verbose_name='ЕНП')),
                ('department', models.CharField(max_length=100, verbose_name='Подразделение')),
                ('address', models.TextField(blank=True, null=True, verbose_name='Адрес')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Телефон')),
            ],
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='creation_date',
            field=models.DateField(help_text='Журнал ЭМД: Дата формирования ЭМД', verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='deleteemd',
            name='oid_document',
            field=models.CharField(help_text='Первые цифры Номера в реестре РЭМД. Идентификатор (OID) вида документа в <a href="https://nsi.rosminzdrav.ru/dictionaries/1.2.643.5.1.13.13.11.1520/passport/latest" target="_blank">1.2.643.5.1.13.13.11.1520</a>', max_length=255, verbose_name='OID документа'),
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(verbose_name='Примечание')),
                ('date', models.DateField(verbose_name='Дата')),
                ('svomember', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surveys', to='reports.svomember')),
            ],
        ),
        migrations.CreateModel(
            name='SVOMemberOMSData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('talon', models.CharField(max_length=255, verbose_name='Номер талона')),
                ('goal', models.CharField(blank=True, max_length=255, null=True, verbose_name='Цель лечения')),
                ('treatment_end', models.DateField(blank=True, null=True, verbose_name='Дата окончания лечения')),
                ('main_diagnosis', models.CharField(blank=True, max_length=255, null=True, verbose_name='Основной диагноз')),
                ('svomember', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='oms_data', to='reports.svomember')),
            ],
        ),
        migrations.CreateModel(
            name='SVORelative',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=100, verbose_name='Статус')),
                ('last_name', models.CharField(max_length=100, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=100, verbose_name='Имя')),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Отчество')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Дата рождения')),
                ('enp', models.CharField(blank=True, max_length=16, null=True, unique=True, verbose_name='ЕНП')),
                ('address', models.TextField(blank=True, null=True, verbose_name='Адрес')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Телефон')),
                ('svomember', models.ForeignKey(limit_choices_to={'is_active': True}, on_delete=django.db.models.deletion.CASCADE, to='reports.svomember', verbose_name='Участник СВО')),
            ],
        ),
    ]