from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_loader', '0028_omsdata_smo_tfoms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='omsdata',
            name='additional_diagnosis',
            field=models.CharField(blank=True, default='-', max_length=1500, null=True),
        ),
    ]
