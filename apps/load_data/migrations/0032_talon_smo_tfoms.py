from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0031_journalappeals_procedure'),
    ]

    operations = [
        migrations.AddField(
            model_name='talon',
            name='smo_tfoms',
            field=models.CharField(default='-', max_length=255, verbose_name='СМО от ТФОМС'),
        ),
        migrations.AddField(
            model_name='complextalon',
            name='smo_tfoms',
            field=models.CharField(default='-', max_length=255, verbose_name='СМО от ТФОМС'),
        ),
    ]
