from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dn_reference", "0003_remove_profile_specialty_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="dnservicerequirement",
            name="specialty",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="requirements",
                to="dn_reference.dnspecialty",
                verbose_name="Специальность",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="dnservicerequirement",
            unique_together={("service", "group", "specialty")},
        ),
        migrations.RemoveField(
            model_name="dnservicerequirement",
            name="profile",
        ),
        migrations.DeleteModel(
            name="DnProfile",
        ),
    ]

