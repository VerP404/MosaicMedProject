from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0030_alter_kvazaranalysisorder_diagnosis_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalappeals',
            name='procedure',
            field=models.CharField(default='-', max_length=255, verbose_name='Процедура'),
        ),
        migrations.AlterUniqueTogether(
            name='journalappeals',
            unique_together={('enp', 'acceptance_date', 'procedure', 'employee_last_name')},
        ),
    ]
