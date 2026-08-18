from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0034_alter_additional_diagnosis_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kvazaranalysisorder',
            name='number',
            field=models.TextField(unique=True, verbose_name='Номер'),
        ),
        migrations.AlterField(
            model_name='kvazaranalysisorder',
            name='doctor',
            field=models.TextField(default='-', verbose_name='Врач'),
        ),
        migrations.AlterField(
            model_name='kvazaranalysisorder',
            name='operator',
            field=models.TextField(default='-', verbose_name='Оператор'),
        ),
        migrations.AlterField(
            model_name='kvazaranalysisorder',
            name='diagnosis',
            field=models.TextField(default='-', verbose_name='Диагноз'),
        ),
    ]
