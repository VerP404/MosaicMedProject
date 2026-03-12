from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dn_reference", "0002_dnprofile_and_requirements_by_profile"),
    ]

    operations = [
        migrations.DeleteModel(
            name="DnProfileSpecialty",
        ),
    ]
