from django.urls import reverse

from .models import MainSettings, MenuItem
from apps.organization.models import MedicalOrganization


def _resolve_menu_link(link, dash_url, dash_chief_url):
    """Преобразует поле link пункта меню в итоговый URL."""
    if not link or link == '#':
        return '#'
    if link == 'dash_url':
        return dash_url or '#'
    if link == 'dash_chief_url':
        return dash_chief_url or '#'
    if link == 'dash_update':
        return (dash_url or '#') + '/admin/admin_update_data'
    if link.startswith('/') or link.startswith('http'):
        return link
    try:
        return reverse(link)
    except Exception:
        return '#'


def _visible_menu_links():
    """Множество значений link всех видимых пунктов меню (для главной страницы)."""
    links = set()
    for item in MenuItem.objects.filter(is_visible=True).exclude(link='').exclude(link='#'):
        links.add(item.link)
    return links


def _build_sidebar_menu(dash_url, dash_chief_url):
    """Собирает список пунктов меню для сайдбара (только видимые)."""
    top_items = MenuItem.objects.filter(parent=None, is_visible=True).order_by('order')
    menu_items = []
    for item in top_items:
        url = _resolve_menu_link(item.link, dash_url, dash_chief_url)
        children_data = []
        for child in item.children.filter(is_visible=True).order_by('order'):
            children_data.append({
                'title': child.title,
                'url': _resolve_menu_link(child.link, dash_url, dash_chief_url),
                'icon_type': child.icon_type,
                'icon_name': child.icon_name,
            })
        menu_items.append({
            'title': item.title,
            'url': url,
            'icon_type': item.icon_type,
            'icon_name': item.icon_name,
            'slug': item.slug or f'menu-{item.pk}',
            'children': children_data,
        })
    return menu_items


def portal_context(request):
    """Context processor для передачи переменных портала во все шаблоны"""
    dash_url = '#'
    dash_chief_url = '#'
    try:
        main_settings = MainSettings.objects.first()
        organization = MedicalOrganization.objects.first()
        
        if main_settings and request:
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            host_only = host.split(':')[0]
            dash_url = f"{scheme}://{host_only}:{main_settings.dash_port}"
            dash_chief_url = f"{scheme}://{host_only}:{main_settings.dash_chief_port}"
        
        sidebar_menu = _build_sidebar_menu(dash_url, dash_chief_url)
        visible_links = _visible_menu_links()
        return {
            'main_settings': main_settings,
            'organization': organization,
            'dash_url': dash_url,
            'dash_chief_url': dash_chief_url,
            'sidebar_menu': sidebar_menu,
            'visible_menu_links': visible_links,
        }
    except Exception:
        pass

    return {
        'main_settings': None,
        'organization': None,
        'dash_url': '#',
        'dash_chief_url': '#',
        'sidebar_menu': _build_sidebar_menu('#', '#'),
        'visible_menu_links': _visible_menu_links(),
    }
