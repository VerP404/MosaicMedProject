from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dn_reference", "0004_specialty_instead_of_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="DnServicePricePeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_start", models.DateField(db_index=True, verbose_name="Дата начала действия")),
                ("date_end", models.DateField(blank=True, db_index=True, null=True, verbose_name="Дата окончания действия")),
                ("title", models.CharField(blank=True, default="", max_length=128, verbose_name="Название периода")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={
                "verbose_name": "Период стоимости услуги",
                "verbose_name_plural": "Периоды стоимости услуг",
                "ordering": ["-date_start", "date_end"],
                "unique_together": {("date_start", "date_end")},
            },
        ),
        migrations.CreateModel(
            name="DnServicePrice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Стоимость")),
                (
                    "period",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_prices",
                        to="dn_reference.dnservicepriceperiod",
                        verbose_name="Период",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prices",
                        to="dn_reference.dnservice",
                        verbose_name="Услуга",
                    ),
                ),
            ],
            options={
                "verbose_name": "Стоимость услуги",
                "verbose_name_plural": "Стоимость услуг",
                "ordering": ["service__code", "-period__date_start"],
                "unique_together": {("service", "period")},
            },
        ),
        migrations.AddIndex(
            model_name="dnserviceprice",
            index=models.Index(fields=["service", "period"], name="dn_ref_srv_price_srv_period_idx"),
        ),
        migrations.AddIndex(
            model_name="dnserviceprice",
            index=models.Index(fields=["period"], name="dn_ref_srv_price_period_idx"),
        ),
    ]

