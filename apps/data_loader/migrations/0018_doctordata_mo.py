# Generated by Django 5.1 on 2024-11-22 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_loader', '0017_alter_iszlsettings_password_people_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctordata',
            name='mo',
            field=models.CharField(default=1, max_length=255, verbose_name='МО'),
            preserve_default=False,
        ),
    ]
