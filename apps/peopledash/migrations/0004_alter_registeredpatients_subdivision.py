# Generated by Django 5.1 on 2024-11-13 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peopledash', '0003_registeredpatients_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registeredpatients',
            name='subdivision',
            field=models.CharField(max_length=255),
        ),
    ]
