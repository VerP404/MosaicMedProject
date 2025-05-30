# Generated by Django 5.1 on 2025-03-17 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0010_alter_recipe_inn_alter_recipe_medicinal_product_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MortalityRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('series', models.CharField(default='-', max_length=255, verbose_name='Серия')),
                ('number', models.CharField(default='-', max_length=255, verbose_name='Номер')),
                ('damaged', models.CharField(default='-', max_length=255, verbose_name='ИСПОРЧЕНО')),
                ('duplicate', models.CharField(default='-', max_length=255, verbose_name='Дубликат')),
                ('perinatal', models.CharField(default='-', max_length=255, verbose_name='Перинатальная')),
                ('issue_date', models.CharField(default='-', max_length=255, verbose_name='Дата выдачи')),
                ('recipe_type', models.CharField(default='-', max_length=255, verbose_name='Тип рецепта')),
                ('emd_sending_date', models.CharField(default='-', max_length=255, verbose_name='Дата отправки ЭМД')),
                ('emd_sending_status', models.CharField(default='-', max_length=255, verbose_name='Статус отправки ЭМД')),
                ('emd_error', models.TextField(default='-', verbose_name='ЭМД ошибка')),
                ('creator', models.CharField(default='-', max_length=255, verbose_name='Создавший')),
                ('doctor', models.CharField(default='-', max_length=255, verbose_name='Врач')),
                ('deceased_full_name', models.CharField(default='-', max_length=255, verbose_name='ФИО умершего(ей)')),
                ('birth_date', models.CharField(default='-', max_length=255, verbose_name='Дата рождения')),
                ('death_date', models.CharField(default='-', max_length=255, verbose_name='Дата смерти')),
                ('gender', models.CharField(default='-', max_length=255, verbose_name='Пол')),
                ('age', models.CharField(default='-', max_length=255, verbose_name='Возраст, лет')),
                ('initial_statistic', models.CharField(default='-', max_length=255, verbose_name='Первоначальная (статистика)')),
                ('reason_a', models.CharField(default='-', max_length=255, verbose_name='Причина (а)')),
                ('reason_b', models.CharField(default='-', max_length=255, verbose_name='Причина (б)')),
                ('reason_c', models.CharField(default='-', max_length=255, verbose_name='Причина (в)')),
                ('reason_d', models.CharField(default='-', max_length=255, verbose_name='Причина (г)')),
                ('region', models.CharField(default='-', max_length=255, verbose_name='Регион')),
                ('district', models.CharField(default='-', max_length=255, verbose_name='Район')),
                ('city_or_locality', models.CharField(default='-', max_length=255, verbose_name='Город / Населенный пункт')),
                ('street', models.CharField(default='-', max_length=255, verbose_name='Улица')),
                ('house', models.CharField(default='-', max_length=255, verbose_name='Дом')),
                ('apartment', models.CharField(default='-', max_length=255, verbose_name='Квартира')),
                ('attachment', models.CharField(default='-', max_length=255, verbose_name='Прикрепление')),
                ('additional_number', models.CharField(default='-', max_length=255, verbose_name='Номер (доп.)')),
                ('additional_issue_date', models.CharField(default='-', max_length=255, verbose_name='Дата выдачи (доп.)')),
                ('additional_initial_statistic', models.CharField(default='-', max_length=255, verbose_name='Первоначальная (статистика) (доп.)')),
            ],
            options={
                'verbose_name': 'Смертность',
                'verbose_name_plural': 'Смертность',
                'db_table': 'load_data_death',
                'unique_together': {('series', 'number')},
            },
        ),
    ]
