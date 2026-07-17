from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0030_alter_annualdoctorplan_year_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildingIndicatorReportPreset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название')),
                ('config', models.JSONField(blank=True, default=dict, help_text='JSON: indicator_ids, building_ids, layout, metric, payment_type, unique_flag, require_building_plan, columns', verbose_name='Конфигурация')),
                ('notes', models.TextField(blank=True, default='', verbose_name='Примечания')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата изменения')),
            ],
            options={
                'verbose_name': 'Пресет отчёта по корпусам',
                'verbose_name_plural': 'Пресеты отчётов по корпусам',
                'ordering': ['name'],
            },
        ),
    ]
