# Generated by Django 5.1 on 2024-11-14 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_loader', '0016_iszlsettings_password_people_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iszlsettings',
            name='password_people',
            field=models.CharField(default='-', max_length=255, verbose_name='Пароль ИСЗЛ:Население'),
        ),
        migrations.AlterField(
            model_name='iszlsettings',
            name='user_people',
            field=models.CharField(default='-', max_length=255, verbose_name='Пользователь ИСЗЛ:Население'),
        ),
    ]