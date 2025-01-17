# Generated by Django 5.1 on 2024-10-09 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peopledash', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='building',
            name='name',
            field=models.CharField(max_length=250, unique=True, verbose_name='Названия корпуса для группировки подразделений из Статистики Квазар'),
        ),
        migrations.AlterField(
            model_name='page',
            name='path',
            field=models.CharField(max_length=250, unique=True, verbose_name='Путь отображаемый в браузерной ссылке на страницу(на английском)'),
        ),
        migrations.AlterField(
            model_name='page',
            name='subdivision',
            field=models.CharField(max_length=250, verbose_name='Подпись на странице корпуса. Должно быть такое же как и в подключенном корпусе выше!'),
        ),
        migrations.AlterField(
            model_name='page',
            name='title',
            field=models.CharField(max_length=250, verbose_name='Заголовок. Показывает то что будет написано в списке подразделений на главной странице'),
        ),
        migrations.AlterField(
            model_name='specialty',
            name='name',
            field=models.CharField(max_length=500, unique=True),
        ),
        migrations.AlterField(
            model_name='subdivision',
            name='name',
            field=models.CharField(max_length=500, unique=True),
        ),
    ]
