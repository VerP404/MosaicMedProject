from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_loader', '0027_kvazaranalysisorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='omsdata',
            name='smo_tfoms',
            field=models.CharField(default='-', max_length=255, verbose_name='СМО от ТФОМС'),
        ),
    ]
