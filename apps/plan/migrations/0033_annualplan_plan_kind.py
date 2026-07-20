from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plan", "0032_buildingvolumeprinttemplate"),
    ]

    operations = [
        migrations.AddField(
            model_name="annualplan",
            name="plan_kind",
            field=models.CharField(
                choices=[("internal", "Внутренний"), ("tfoms", "ТФОМС")],
                default="internal",
                help_text="Внутренний план МО или план ТФОМС",
                max_length=16,
                verbose_name="Вид плана",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="annualplan",
            unique_together={("group", "year", "plan_kind")},
        ),
    ]
