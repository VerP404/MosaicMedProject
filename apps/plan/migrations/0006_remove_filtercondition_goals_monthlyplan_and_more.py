# Generated by Django 5.1 on 2024-10-31 23:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0005_filtercondition_goals'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filtercondition',
            name='goals',
        ),
        migrations.CreateModel(
            name='MonthlyPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveSmallIntegerField(verbose_name='Месяц')),
                ('quantity', models.PositiveIntegerField(verbose_name='Количество')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Деньги')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_plans', to='plan.groupindicators', verbose_name='Группа')),
            ],
            options={
                'verbose_name': 'План на месяц',
                'verbose_name_plural': 'Планы на месяц',
                'unique_together': {('group', 'month')},
            },
        ),
        migrations.DeleteModel(
            name='OptionsForReportFilters',
        ),
    ]