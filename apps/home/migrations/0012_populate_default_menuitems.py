# Data migration: пункты меню по умолчанию (как в старом сайдбаре)

from django.db import migrations


def create_default_menu(apps, schema_editor):
    MenuItem = apps.get_model('home', 'MenuItem')
    # Родительские пункты (без parent)
    items_data = [
        {'title': 'Главная', 'link': 'home', 'icon_type': 'feather', 'icon_name': 'home', 'order': 10, 'is_visible': True, 'slug': None},
        {'title': 'Реестры пациентов', 'link': '#', 'icon_type': 'feather', 'icon_name': 'clipboard', 'order': 20, 'is_visible': True, 'slug': 'patient-registries'},
        {'title': 'Аналитическая система', 'link': 'dash_url', 'icon_type': 'feather', 'icon_name': 'bar-chart-2', 'order': 30, 'is_visible': True, 'slug': None},
        {'title': 'Панель пациента', 'link': 'peopledash_home', 'icon_type': 'feather', 'icon_name': 'user', 'order': 40, 'is_visible': True, 'slug': None},
        {'title': 'Панель главного врача', 'link': 'dash_chief_url', 'icon_type': 'feather', 'icon_name': 'activity', 'order': 50, 'is_visible': True, 'slug': None},
        {'title': 'Административный сайт', 'link': '/admin/', 'icon_type': 'feather', 'icon_name': 'settings', 'order': 60, 'is_visible': True, 'slug': None},
        {'title': 'Обновление данных', 'link': 'dash_update', 'icon_type': 'feather', 'icon_name': 'upload-cloud', 'order': 70, 'is_visible': True, 'slug': None},
    ]
    created = {}
    for d in items_data:
        data = dict(d)
        slug = data.pop('slug')
        obj = MenuItem.objects.create(**data, slug=slug)
        created[data['title']] = obj

    # Дочерние пункты для "Реестры пациентов"
    parent = created['Реестры пациентов']
    MenuItem.objects.create(
        parent=parent, title='Льготники', link='beneficiaries:home',
        icon_type='fa', icon_name='fa-heart-pulse', order=1, is_visible=True
    )
    MenuItem.objects.create(
        parent=parent, title='Диспансерное наблюдение', link='dn_app:upload_csv',
        icon_type='feather', icon_name='activity', order=2, is_visible=True
    )


def remove_default_menu(apps, schema_editor):
    apps.get_model('home', 'MenuItem').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_menuitem'),
    ]

    operations = [
        migrations.RunPython(create_default_menu, remove_default_menu),
    ]
