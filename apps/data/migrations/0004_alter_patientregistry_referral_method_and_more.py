# Generated by Django 5.1 on 2024-12-18 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_alter_patientregistry_refusal_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientregistry',
            name='referral_method',
            field=models.CharField(choices=[('ССМП', 'ССМП'), ('Самообращение', 'Самообращение')], max_length=20, verbose_name='Способ обращения'),
        ),
        migrations.AlterField(
            model_name='patientregistry',
            name='refusal_reason',
            field=models.CharField(choices=[('Нет показаний для госпитализации', 'Нет показаний для госпитализации'), ('Отказ пациента (законного представителя)', 'Отказ пациента (законного представителя)')], max_length=50, verbose_name='Причина отказа в госпитализации'),
        ),
    ]