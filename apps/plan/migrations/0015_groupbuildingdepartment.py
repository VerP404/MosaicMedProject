# Generated by Django 5.1 on 2024-11-27 20:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0005_station_doctorassignment'),
        ('plan', '0014_groupindicators_buildings_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupBuildingDepartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(help_text='Укажите год, к которому относится корпус и отделение', verbose_name='Год')),
                ('building', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_building_departments', to='organization.building', verbose_name='Корпус')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_building_departments', to='organization.department', verbose_name='Отделение')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_building_departments', to='plan.groupindicators', verbose_name='Группа')),
            ],
            options={
                'verbose_name': 'Корпус и отделение группы',
                'verbose_name_plural': 'Корпуса и отделения группы',
                'unique_together': {('group', 'year', 'building', 'department')},
            },
        ),
    ]