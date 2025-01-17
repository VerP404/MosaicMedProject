# Generated by Django 5.1 on 2024-10-07 07:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Категория')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Описание категории')),
            ],
            options={
                'verbose_name': 'Категория данных',
                'verbose_name_plural': 'Категории данных',
            },
        ),
        migrations.CreateModel(
            name='DetailedData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('talon_number', models.CharField(max_length=255, verbose_name='Номер талона')),
                ('account_number', models.CharField(max_length=255, verbose_name='Счет')),
                ('upload_date', models.CharField(max_length=255, verbose_name='Дата выгрузки')),
                ('status', models.CharField(max_length=255, verbose_name='Статус')),
                ('mo', models.CharField(max_length=255, verbose_name='МО')),
                ('start_date', models.CharField(max_length=255, verbose_name='Дата начала')),
                ('end_date', models.CharField(max_length=255, verbose_name='Дата окончания')),
                ('policy_series', models.CharField(max_length=255, verbose_name='Серия полиса')),
                ('policy_number', models.CharField(max_length=255, verbose_name='Номер полиса')),
                ('enp', models.CharField(max_length=255, verbose_name='ЕНП')),
                ('last_name', models.CharField(max_length=255, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=255, verbose_name='Имя')),
                ('middle_name', models.CharField(max_length=255, verbose_name='Отчество')),
                ('insurance_org', models.CharField(max_length=255, verbose_name='Страховая организация')),
                ('gender', models.CharField(max_length=255, verbose_name='Пол')),
                ('birth_date', models.CharField(max_length=255, verbose_name='Дата рождения')),
                ('talon_type', models.CharField(max_length=255, verbose_name='Тип талона')),
                ('main_diagnosis', models.CharField(max_length=255, verbose_name='Основной диагноз')),
                ('additional_diagnosis', models.CharField(max_length=255, verbose_name='Сопутствующий диагноз')),
                ('health_group', models.CharField(max_length=255, verbose_name='Группа здоровья')),
                ('doctor_code', models.CharField(max_length=255, verbose_name='Доктор (Код)')),
                ('doctor_name', models.CharField(max_length=255, verbose_name='Доктор (ФИО)')),
                ('cost', models.CharField(max_length=255, verbose_name='Стоимость')),
                ('service_name', models.CharField(max_length=255, verbose_name='Название услуги')),
                ('service_code', models.CharField(max_length=255, verbose_name='Номенклатурный код услуги')),
                ('service_doctor_code', models.CharField(max_length=255, verbose_name='Доктор-Услуги (Код)')),
                ('service_doctor_name', models.CharField(max_length=255, verbose_name='Доктор-Услуги (ФИО)')),
                ('service_date', models.CharField(max_length=255, verbose_name='Дата-Услуги')),
                ('service_status', models.CharField(max_length=255, verbose_name='Статус-Услуги')),
                ('route', models.CharField(max_length=255, verbose_name='Маршрут')),
                ('service_department', models.CharField(max_length=255, verbose_name='Подразделение врача-Услуги')),
                ('external_mo_code', models.CharField(max_length=255, verbose_name='Код МО (при оказ.услуги в другой МО)')),
            ],
            options={
                'verbose_name': 'ОМС: Детализация',
                'verbose_name_plural': 'ОМС: Детализация',
            },
        ),
        migrations.CreateModel(
            name='DoctorData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snils', models.CharField(max_length=255, verbose_name='СНИЛС')),
                ('doctor_code', models.CharField(max_length=255, verbose_name='Код врача')),
                ('last_name', models.CharField(max_length=255, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=255, verbose_name='Имя')),
                ('middle_name', models.CharField(max_length=255, verbose_name='Отчество')),
                ('birth_date', models.CharField(max_length=255, verbose_name='Дата рождения')),
                ('gender', models.CharField(max_length=255, verbose_name='Пол')),
                ('start_date', models.CharField(max_length=255, verbose_name='Дата начала работы')),
                ('end_date', models.CharField(max_length=255, verbose_name='Дата окончания работы')),
                ('department', models.CharField(max_length=255, verbose_name='Структурное подразделение')),
                ('medical_profile_code', models.CharField(max_length=255, verbose_name='Код профиля медпомощи')),
                ('specialty_code', models.CharField(max_length=255, verbose_name='Код специальности')),
                ('department_code', models.CharField(max_length=255, verbose_name='Код отделения')),
                ('comment', models.CharField(max_length=255, verbose_name='Комментарий')),
            ],
            options={
                'verbose_name': 'ОМС: Врач',
                'verbose_name_plural': 'ОМС: Врачи',
            },
        ),
        migrations.CreateModel(
            name='KvazarSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Квазар: Настройка',
                'verbose_name_plural': 'Квазар: Настройки',
            },
        ),
        migrations.CreateModel(
            name='OMSData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('talon', models.CharField(max_length=255, unique=True)),
                ('source', models.CharField(max_length=255)),
                ('source_id', models.CharField(max_length=255)),
                ('account_number', models.CharField(max_length=255)),
                ('upload_date', models.CharField(max_length=255)),
                ('cancellation_reason', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(max_length=255)),
                ('talon_type', models.CharField(max_length=255)),
                ('goal', models.CharField(blank=True, max_length=255, null=True)),
                ('federal_goal', models.CharField(blank=True, max_length=255, null=True)),
                ('patient', models.CharField(max_length=255)),
                ('birth_date', models.CharField(max_length=255)),
                ('age', models.CharField(max_length=255)),
                ('gender', models.CharField(max_length=50)),
                ('policy', models.CharField(max_length=255)),
                ('smo_code', models.CharField(max_length=255)),
                ('insurance', models.CharField(max_length=255)),
                ('enp', models.CharField(max_length=255)),
                ('treatment_start', models.CharField(max_length=255)),
                ('treatment_end', models.CharField(max_length=255)),
                ('doctor', models.CharField(max_length=255)),
                ('doctor_profile', models.CharField(max_length=255)),
                ('staff_position', models.CharField(max_length=255)),
                ('department', models.CharField(max_length=255)),
                ('care_conditions', models.CharField(max_length=255)),
                ('medical_assistance_type', models.CharField(max_length=255)),
                ('disease_type', models.CharField(max_length=255)),
                ('main_disease_character', models.CharField(max_length=255)),
                ('visits', models.CharField(max_length=255)),
                ('mo_visits', models.CharField(max_length=255)),
                ('home_visits', models.CharField(max_length=255)),
                ('case', models.CharField(max_length=255)),
                ('main_diagnosis', models.CharField(max_length=255)),
                ('additional_diagnosis', models.CharField(blank=True, max_length=500, null=True)),
                ('mp_profile', models.CharField(max_length=255)),
                ('bed_profile', models.CharField(max_length=255)),
                ('dispensary_monitoring', models.CharField(max_length=255)),
                ('specialty', models.CharField(max_length=255)),
                ('outcome', models.CharField(max_length=255)),
                ('result', models.CharField(max_length=255)),
                ('operator', models.CharField(max_length=255)),
                ('initial_input_date', models.CharField(max_length=255)),
                ('last_change_date', models.CharField(max_length=255)),
                ('tariff', models.CharField(max_length=255)),
                ('amount', models.CharField(max_length=255)),
                ('paid', models.CharField(max_length=255)),
                ('payment_type', models.CharField(max_length=255)),
                ('sanctions', models.CharField(blank=True, max_length=255, null=True)),
                ('ksg', models.CharField(blank=True, max_length=255, null=True)),
                ('kz', models.CharField(blank=True, max_length=255, null=True)),
                ('therapy_schema_code', models.CharField(blank=True, max_length=255, null=True)),
                ('uet', models.CharField(blank=True, max_length=255, null=True)),
                ('classification_criterion', models.CharField(blank=True, max_length=255, null=True)),
                ('shrm', models.CharField(blank=True, max_length=255, null=True)),
                ('directing_mo', models.CharField(blank=True, max_length=255, null=True)),
                ('payment_method_code', models.CharField(blank=True, max_length=255, null=True)),
                ('newborn', models.CharField(blank=True, max_length=255, null=True)),
                ('representative', models.CharField(blank=True, max_length=255, null=True)),
                ('additional_status_info', models.CharField(blank=True, max_length=1500, null=True)),
                ('kslp', models.CharField(blank=True, max_length=255, null=True)),
                ('payment_source', models.CharField(blank=True, max_length=255, null=True)),
                ('report_period', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'ОМС: Талон',
                'verbose_name_plural': 'ОМС: Талоны',
            },
        ),
        migrations.CreateModel(
            name='OMSSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'ОМС: Настройка',
                'verbose_name_plural': 'ОМС: Настройки',
            },
        ),
        migrations.CreateModel(
            name='DataType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Тип данных')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Описание типа данных')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='types', to='data_loader.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Тип данных',
                'verbose_name_plural': 'Типы данных',
            },
        ),
        migrations.CreateModel(
            name='DataImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csv_file', models.FileField(blank=True, null=True, upload_to='oms_data_imports/', verbose_name='CSV файл')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('added_count', models.IntegerField(default=0, verbose_name='Количество добавленных записей')),
                ('updated_count', models.IntegerField(default=0, verbose_name='Количество обновленных записей')),
                ('error_count', models.IntegerField(default=0, verbose_name='Количество ошибок')),
                ('data_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_loader.datatype', verbose_name='Тип данных')),
            ],
            options={
                'verbose_name': 'Импорт данных',
                'verbose_name_plural': 'Импорт данных',
            },
        ),
        migrations.CreateModel(
            name='DataTypeFieldMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csv_column_name', models.CharField(max_length=255, verbose_name='Название столбца в CSV')),
                ('model_field_name', models.CharField(max_length=255, verbose_name='Название поля в модели')),
                ('data_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='field_mappings', to='data_loader.datatype', verbose_name='Тип данных')),
            ],
            options={
                'verbose_name': 'Соответствие полей',
                'verbose_name_plural': 'Соответствия полей',
            },
        ),
    ]
