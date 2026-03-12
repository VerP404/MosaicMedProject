from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dn_reference", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DnProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=128, unique=True, verbose_name="Код профиля")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={
                "verbose_name": "Профиль ДН",
                "verbose_name_plural": "Профили ДН",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="DnProfileSpecialty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile_specialties",
                        to="dn_reference.dnprofile",
                        verbose_name="Профиль",
                    ),
                ),
                (
                    "specialty",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile_specialties",
                        to="dn_reference.dnspecialty",
                        verbose_name="Специальность",
                    ),
                ),
            ],
            options={
                "verbose_name": "Профиль ↔ Специальность",
                "verbose_name_plural": "Профили ↔ Специальности",
                "unique_together": {("profile", "specialty")},
            },
        ),
        migrations.AlterField(
            model_name="dndiagnosisgroup",
            name="code",
            field=models.CharField(max_length=256, unique=True, verbose_name="Код группы"),
        ),
        migrations.AlterField(
            model_name="dnservice",
            name="code",
            field=models.CharField(db_index=True, max_length=128, unique=True, verbose_name="Код услуги"),
        ),
        migrations.AddField(
            model_name="dnservicerequirement",
            name="profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="requirements",
                to="dn_reference.dnprofile",
                verbose_name="Профиль",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="dnservicerequirement",
            unique_together={("service", "group", "profile")},
        ),
    ]
