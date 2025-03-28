# Generated by Django 5.1 on 2025-03-11 21:49

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('load_data', '0005_complextalon_created_at_complextalon_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complextalon',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 11, 21, 48, 50, 945953, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='complextalon',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 11, 21, 48, 54, 755553, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sickleavesheet',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 11, 21, 48, 57, 378181, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sickleavesheet',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 11, 21, 49, 0, 954525, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='talon',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 11, 21, 49, 3, 28829, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='talon',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 11, 21, 49, 7, 94462, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
