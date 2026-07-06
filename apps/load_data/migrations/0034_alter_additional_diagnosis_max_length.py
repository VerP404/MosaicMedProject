from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0033_journalappeals_position_no_show'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complextalon',
            name='additional_diagnosis',
            field=models.CharField(blank=True, default='-', max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='detailedmedicalexamination',
            name='additional_diagnosis',
            field=models.CharField(default='-', max_length=1500, verbose_name='Сопутствующий диагноз'),
        ),
        migrations.AlterField(
            model_name='talon',
            name='additional_diagnosis',
            field=models.CharField(blank=True, default='-', max_length=1500, null=True),
        ),
    ]
