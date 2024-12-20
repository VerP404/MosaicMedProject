# Generated by Django 5.1 on 2024-11-12 07:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0008_unifiedfilter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unifiedfilter',
            name='field_name',
        ),
        migrations.RemoveField(
            model_name='unifiedfilter',
            name='filter_type',
        ),
        migrations.RemoveField(
            model_name='unifiedfilter',
            name='values',
        ),
        migrations.CreateModel(
            name='UnifiedFilterCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=100, verbose_name='Поле для фильтрации')),
                ('filter_type', models.CharField(choices=[('exact', 'Точное соответствие (=)'), ('in', 'В списке (IN)'), ('like', 'Похож на (LIKE)'), ('not_like', 'Не содержит (NOT LIKE)')], max_length=10, verbose_name='Тип фильтра')),
                ('values', models.TextField(verbose_name='Значения (через запятую)')),
                ('filter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='plan.unifiedfilter', verbose_name='Фильтр')),
            ],
            options={
                'verbose_name': 'Условие фильтра',
                'verbose_name_plural': 'Условия фильтра',
            },
        ),
    ]
