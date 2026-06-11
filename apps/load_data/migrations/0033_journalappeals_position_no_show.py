from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0032_talon_smo_tfoms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journalappeals',
            name='position',
            field=models.CharField(default='-', max_length=512, verbose_name='Должность'),
        ),
        migrations.AlterField(
            model_name='journalappeals',
            name='no_show',
            field=models.CharField(default='-', max_length=128, verbose_name='Не явился'),
        ),
    ]
