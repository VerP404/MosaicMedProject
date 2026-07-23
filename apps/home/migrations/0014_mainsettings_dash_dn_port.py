# Generated manually for dash_dn (порт отдельного приложения «Подбор услуг ДН»)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0013_add_extra_menuitems'),
    ]

    operations = [
        migrations.AddField(
            model_name='mainsettings',
            name='dash_dn_port',
            field=models.PositiveIntegerField(
                default=7777,
                verbose_name='Порт Dash «Подбор услуг ДН» (dash_dn)',
                help_text='Отдельное приложение на том же IP/хосте, что и основной сайт (например :7777).',
            ),
        ),
    ]
