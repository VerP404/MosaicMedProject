# Generated by Django 5.1 on 2024-11-13 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peopledash', '0002_alter_building_name_alter_page_path_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='registeredpatients',
            name='organization',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
