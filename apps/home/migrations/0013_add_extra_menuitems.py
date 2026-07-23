# Добавляем пункты меню для Кадровая служба, Ведение отчетов, Система участков

from django.db import migrations


def add_extra_menu_items(apps, schema_editor):
    MenuItem = apps.get_model('home', 'MenuItem')
    if MenuItem.objects.filter(link='/admin/personnel/').exists():
        return
    MenuItem.objects.create(
        title='Кадровая служба',
        link='/admin/personnel/',
        icon_type='feather',
        icon_name='users',
        order=65,
        is_visible=True,
    )
    MenuItem.objects.create(
        title='Ведение отчетов',
        link='/admin/reports/',
        icon_type='feather',
        icon_name='file-text',
        order=66,
        is_visible=True,
    )
    MenuItem.objects.create(
        title='Система участков',
        link='zones:organizations_list',
        icon_type='feather',
        icon_name='map',
        order=67,
        is_visible=True,
    )


def remove_extra_menu_items(apps, schema_editor):
    MenuItem = apps.get_model('home', 'MenuItem')
    MenuItem.objects.filter(link__in=[
        '/admin/personnel/',
        '/admin/reports/',
        'zones:organizations_list',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_populate_default_menuitems'),
    ]

    operations = [
        migrations.RunPython(add_extra_menu_items, remove_extra_menu_items),
    ]
