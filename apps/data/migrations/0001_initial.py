# Generated by Django 5.1 on 2024-11-28 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OMS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('talon', models.CharField(blank=True, max_length=255, null=True, verbose_name='Талон')),
                ('is_update', models.BooleanField(default=True, verbose_name='Обновление')),
                ('source_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='ID источника')),
                ('source', models.CharField(blank=True, max_length=255, null=True, verbose_name='Источник')),
                ('report_month', models.CharField(blank=True, max_length=255, null=True, verbose_name='Месяц отчета')),
                ('report_month_number', models.IntegerField(blank=True, null=True, verbose_name='Номер месяца отчета')),
                ('report_year', models.IntegerField(blank=True, null=True, verbose_name='Год отчета')),
                ('status', models.CharField(blank=True, max_length=255, null=True, verbose_name='Статус')),
                ('id_goal', models.CharField(blank=True, max_length=255, null=True, verbose_name='ID цели')),
                ('goal', models.CharField(blank=True, max_length=255, null=True, verbose_name='Цель')),
                ('target_categories', models.TextField(blank=True, null=True, verbose_name='Категории целей')),
                ('patient_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='ID пациента')),
                ('patient', models.CharField(blank=True, max_length=255, null=True, verbose_name='Пациент')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Дата рождения')),
                ('age', models.IntegerField(blank=True, null=True, verbose_name='Возраст')),
                ('gender', models.CharField(blank=True, max_length=10, null=True, verbose_name='Пол')),
                ('enp', models.CharField(blank=True, max_length=255, null=True, verbose_name='ЕНП')),
                ('smo_code', models.CharField(blank=True, max_length=255, null=True, verbose_name='Код СМО')),
                ('inogorodniy', models.BooleanField(default=False, verbose_name='Иногородний')),
                ('treatment_start', models.DateField(blank=True, null=True, verbose_name='Дата начала лечения')),
                ('treatment_end', models.DateField(blank=True, null=True, verbose_name='Дата окончания лечения')),
                ('visits', models.IntegerField(blank=True, null=True, verbose_name='Посещения')),
                ('mo_visits', models.IntegerField(blank=True, null=True, verbose_name='Посещения в МО')),
                ('home_visits', models.IntegerField(blank=True, null=True, verbose_name='Посещения на дому')),
                ('diagnosis', models.CharField(blank=True, max_length=255, null=True, verbose_name='Диагнозы')),
                ('main_diagnosis_code', models.CharField(blank=True, max_length=255, null=True, verbose_name='Основной диагноз (код)')),
                ('additional_diagnosis_codes', models.TextField(blank=True, null=True, verbose_name='Дополнительные диагнозы (коды)')),
                ('initial_input_date', models.DateField(blank=True, null=True, verbose_name='Дата ввода')),
                ('last_change_date', models.DateField(blank=True, null=True, verbose_name='Дата последнего изменения')),
                ('amount_numeric', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Сумма')),
                ('sanctions', models.CharField(blank=True, max_length=255, null=True, verbose_name='Санкции')),
                ('ksg', models.CharField(blank=True, max_length=255, null=True, verbose_name='КСГ')),
                ('department_id', models.IntegerField(blank=True, null=True, verbose_name='ID отделения')),
                ('department', models.CharField(blank=True, max_length=255, null=True, verbose_name='Отделение')),
                ('building_id', models.IntegerField(blank=True, null=True, verbose_name='ID корпуса')),
                ('building', models.CharField(blank=True, max_length=255, null=True, verbose_name='Корпус')),
                ('doctor_code', models.CharField(blank=True, max_length=255, null=True, verbose_name='Код врача')),
                ('doctor_id', models.IntegerField(blank=True, null=True, verbose_name='ID врача')),
                ('doctor', models.CharField(blank=True, max_length=255, null=True, verbose_name='Врач')),
                ('specialty', models.CharField(blank=True, max_length=255, null=True, verbose_name='Специальность')),
                ('profile', models.CharField(blank=True, max_length=255, null=True, verbose_name='Профиль')),
                ('profile_id', models.IntegerField(blank=True, null=True, verbose_name='ID профиля')),
                ('id_health_group', models.IntegerField(blank=True, null=True, verbose_name='ID группы здоровья')),
                ('health_group', models.CharField(blank=True, max_length=255, null=True, verbose_name='Группа здоровья')),
            ],
            options={
                'verbose_name': 'Запись ОМС',
                'verbose_name_plural': 'Записи ОМС',
            },
        ),
    ]