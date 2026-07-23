# Generated manually for finance_plan_unit

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0014_mainsettings_dash_dn_port"),
    ]

    operations = [
        migrations.AddField(
            model_name="mainsettings",
            name="finance_plan_unit",
            field=models.CharField(
                choices=[("rubles", "Рубли"), ("thousands", "Тысячи рублей")],
                default="rubles",
                help_text=(
                    "В базе план и факт всегда в рублях. "
                    "Настройка задаёт единицу ввода планов и отображения по умолчанию в отчётах "
                    "(руб. или тыс. руб.). На страницах можно переключить просмотр."
                ),
                max_length=16,
                verbose_name="Единица финансов (план/отчёты)",
            ),
        ),
    ]
