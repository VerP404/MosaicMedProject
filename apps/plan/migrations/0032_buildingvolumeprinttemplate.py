from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plan", "0031_buildingindicatorreportpreset"),
    ]

    operations = [
        migrations.CreateModel(
            name="BuildingVolumePrintTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True, verbose_name="Название")),
                (
                    "config",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "JSON: columns, page_orientation, "
                            "sections[{title, items[{indicator_id, short_title, show_of_year}]}]"
                        ),
                        verbose_name="Конфигурация",
                    ),
                ),
                ("notes", models.TextField(blank=True, default="", verbose_name="Примечания")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата изменения")),
            ],
            options={
                "verbose_name": "Шаблон печатного бланка по корпусам",
                "verbose_name_plural": "Шаблоны печатных бланков по корпусам",
                "ordering": ["name"],
            },
        ),
    ]
