from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DnDiagnosisCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True, verbose_name="Категория")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={
                "verbose_name": "Категория диагнозов (168н)",
                "verbose_name_plural": "Категории диагнозов (168н)",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="DnDiagnosisGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True, verbose_name="Код группы")),
                ("title", models.CharField(blank=True, default="", max_length=255, verbose_name="Название")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("rule", models.TextField(blank=True, default="", verbose_name="Правило (исходный заголовок)")),
            ],
            options={
                "verbose_name": "Группа диагнозов (матрица услуг)",
                "verbose_name_plural": "Группы диагнозов (матрица услуг)",
                "ordering": ["order", "code"],
            },
        ),
        migrations.CreateModel(
            name="DnService",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="Код услуги")),
                ("name", models.CharField(max_length=512, verbose_name="Наименование услуги")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={
                "verbose_name": "Услуга ДН",
                "verbose_name_plural": "Услуги ДН",
                "ordering": ["order", "code"],
            },
        ),
        migrations.CreateModel(
            name="DnSpecialty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True, verbose_name="Специальность")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={
                "verbose_name": "Специальность (ДН)",
                "verbose_name_plural": "Специальности (ДН)",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="DnDiagnosis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=32, unique=True, verbose_name="Код МКБ")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="diagnoses",
                        to="dn_reference.dndiagnosiscategory",
                        verbose_name="Категория (168н)",
                    ),
                ),
            ],
            options={
                "verbose_name": "Диагноз (168н)",
                "verbose_name_plural": "Диагнозы (168н)",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="DnDiagnosisGroupMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                (
                    "diagnosis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_memberships",
                        to="dn_reference.dndiagnosis",
                        verbose_name="Диагноз",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="dn_reference.dndiagnosisgroup",
                        verbose_name="Группа",
                    ),
                ),
            ],
            options={
                "verbose_name": "Диагноз в группе",
                "verbose_name_plural": "Диагнозы в группах",
                "unique_together": {("group", "diagnosis")},
            },
        ),
        migrations.CreateModel(
            name="DnDiagnosisSpecialty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("primary", "Основная"), ("joint", "Совместная")], max_length=16, verbose_name="Источник")),
                (
                    "diagnosis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="specialties",
                        to="dn_reference.dndiagnosis",
                        verbose_name="Диагноз",
                    ),
                ),
                (
                    "specialty",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="diagnoses",
                        to="dn_reference.dnspecialty",
                        verbose_name="Специальность",
                    ),
                ),
            ],
            options={
                "verbose_name": "Диагноз ↔ Специальность (168н)",
                "verbose_name_plural": "Диагноз ↔ Специальности (168н)",
                "unique_together": {("diagnosis", "specialty", "source")},
            },
        ),
        migrations.CreateModel(
            name="DnServiceRequirement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_required", models.BooleanField(default=True, verbose_name="Требуется")),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requirements",
                        to="dn_reference.dndiagnosisgroup",
                        verbose_name="Группа диагнозов",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requirements",
                        to="dn_reference.dnservice",
                        verbose_name="Услуга",
                    ),
                ),
            ],
            options={
                "verbose_name": "Требование услуги по группе",
                "verbose_name_plural": "Требования услуг по группам",
                "unique_together": {("service", "group")},
            },
        ),
        migrations.AddIndex(
            model_name="dndiagnosisgroupmembership",
            index=models.Index(fields=["group", "is_active"], name="dn_ref_grp_mem_grp_act_idx"),
        ),
        migrations.AddIndex(
            model_name="dndiagnosisgroupmembership",
            index=models.Index(fields=["diagnosis", "is_active"], name="dn_ref_grp_mem_diag_act_idx"),
        ),
        migrations.AddIndex(
            model_name="dndiagnosisspecialty",
            index=models.Index(fields=["specialty", "source"], name="dn_ref_diag_spec_spec_src_idx"),
        ),
        migrations.AddIndex(
            model_name="dndiagnosisspecialty",
            index=models.Index(fields=["diagnosis", "source"], name="dn_ref_diag_spec_diag_src_idx"),
        ),
        migrations.AddIndex(
            model_name="dnservicerequirement",
            index=models.Index(fields=["group", "is_required"], name="dn_ref_srv_req_grp_req_idx"),
        ),
        migrations.AddIndex(
            model_name="dnservicerequirement",
            index=models.Index(fields=["service", "is_required"], name="dn_ref_srv_req_srv_req_idx"),
        ),
    ]

