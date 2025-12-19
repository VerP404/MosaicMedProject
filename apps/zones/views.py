from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import Organization, Address, OrganizationAddress, Corpus, Site, SiteType


@login_required
def organizations_list(request):
    """Список организаций с картой."""
    organizations = Organization.objects.filter(is_active=True).select_related('address')
    
    # Подготавливаем данные для карты
    organizations_data = []
    for org in organizations:
        org_data = {
            'id': org.id,
            'code': org.code,
            'name': org.name,
            'polygon': org.polygon,
            'color': org.color or '#3388ff',
            'address_count': org.organization_addresses.count(),
        }
        if org.address:
            org_data['center'] = [org.address.longitude, org.address.latitude]
        organizations_data.append(org_data)
    
    context = {
        'organizations': organizations,
        'organizations_data': json.dumps(organizations_data),
    }
    return render(request, 'zones/organizations_list.html', context)


@login_required
def organization_detail(request, pk):
    """Детальная страница организации с картой для редактирования полигона."""
    organization = get_object_or_404(Organization, pk=pk)
    
    # Получаем корпуса организации
    corpora = organization.corpora.filter(is_active=True).select_related('address')
    
    # Получаем адреса внутри полигона
    addresses_in_polygon = organization.get_addresses_in_polygon()
    assigned_addresses = Address.objects.filter(
        organization_links__organization=organization
    ).distinct()
    
    # Пагинация для адресов
    paginator = Paginator(assigned_addresses, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Подготавливаем данные для карты
    organization_data = {
        'id': organization.id,
        'code': organization.code,
        'name': organization.name,
        'polygon': organization.polygon,
        'color': organization.color or '#3388ff',
    }
    
    # Адреса для отображения на карте
    addresses_data = []
    for addr in addresses_in_polygon[:500]:  # Ограничиваем для производительности
        is_assigned = assigned_addresses.filter(id=addr.id).exists()
        addresses_data.append({
            'id': addr.id,
            'street': addr.street,
            'housenumber': addr.housenumber,
            'city': addr.city,
            'coordinates': [addr.longitude, addr.latitude],
            'is_assigned': is_assigned,
        })
    
    context = {
        'organization': organization,
        'corpora': corpora,
        'addresses_in_polygon': addresses_in_polygon,
        'assigned_addresses': assigned_addresses,
        'page_obj': page_obj,
        'organization_data': json.dumps(organization_data),
        'addresses_data': json.dumps(addresses_data),
    }
    return render(request, 'zones/organization_detail.html', context)


@login_required
@require_http_methods(["POST"])
def organization_update_polygon(request, pk):
    """Обновление полигона организации через AJAX."""
    organization = get_object_or_404(Organization, pk=pk)
    
    try:
        data = json.loads(request.body)
        polygon = data.get('polygon')
        
        if not polygon:
            return JsonResponse({'success': False, 'error': 'Полигон не указан'}, status=400)
        
        organization.polygon = polygon
        organization.save()
        
        # Автоматически привязываем адреса
        assigned_count = organization.assign_addresses_in_polygon()
        
        return JsonResponse({
            'success': True,
            'assigned_count': assigned_count,
            'message': f'Полигон обновлен. Привязано адресов: {assigned_count}'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def organization_assign_addresses(request, pk):
    """Явное обновление привязок адресов внутри полигона организации."""
    organization = get_object_or_404(Organization, pk=pk)

    try:
        assigned_count = organization.assign_addresses_in_polygon()
        total_in_polygon = organization.get_addresses_in_polygon().count()
        total_assigned = organization.organization_addresses.count()

        return JsonResponse({
            'success': True,
            'assigned_count': assigned_count,
            'total_in_polygon': total_in_polygon,
            'total_assigned': total_assigned,
            'message': (
                f'Привязано новых адресов: {assigned_count}. '
                f'Всего в полигоне: {total_in_polygon}. '
                f'Всего привязано: {total_assigned}.'
            )
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def organization_addresses(request, pk):
    """API для получения адресов организации."""
    organization = get_object_or_404(Organization, pk=pk)
    
    addresses = Address.objects.filter(
        organization_links__organization=organization
    ).values('id', 'street', 'housenumber', 'city', 'longitude', 'latitude')
    
    return JsonResponse({
        'addresses': list(addresses)
    })


@login_required
@require_http_methods(["GET"])
def search_addresses(request):
    """Поиск адресов для автокомплита."""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    addresses = Address.objects.filter(
        Q(street__icontains=query) |
        Q(housenumber__icontains=query) |
        Q(city__icontains=query)
    ).exclude(longitude__isnull=True, latitude__isnull=True)[:20]
    
    results = []
    for addr in addresses:
        results.append({
            'id': addr.id,
            'text': f"{addr.street} {addr.housenumber}, {addr.city}".strip(),
            'coordinates': [addr.longitude, addr.latitude] if addr.longitude and addr.latitude else None,
        })
    
    return JsonResponse({'results': results})


@login_required
def organization_view(request, pk):
    """Страница просмотра организации с картой и фильтрами (только просмотр, без редактирования)."""
    organization = get_object_or_404(Organization, pk=pk)
    
    # Получаем все корпуса организации
    corpora = organization.corpora.filter(is_active=True).select_related('address').prefetch_related('sites')
    
    # Получаем все участки всех корпусов
    sites = Site.objects.filter(corpus__organization=organization, is_active=True).select_related('type', 'corpus')
    
    # Получаем все типы участков
    site_types = SiteType.objects.all()
    
    # Получаем все адреса организации
    assigned_addresses = Address.objects.filter(
        organization_links__organization=organization
    ).distinct()
    
    # Пагинация для адресов
    paginator = Paginator(assigned_addresses, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Подготавливаем данные для карты - организация
    organization_data = {
        'id': organization.id,
        'code': organization.code,
        'name': organization.name,
        'polygon': organization.polygon,
        'color': organization.color or '#3388ff',
    }
    
    # Подготавливаем данные для карты - корпуса
    corpora_data = []
    for corpus in corpora:
        corpus_info = {
            'id': corpus.id,
            'name': corpus.name,
            'color': corpus.color or '#ff6b6b',
        }
        
        # Адрес корпуса
        if corpus.address:
            corpus_info['address'] = {
                'id': corpus.address.id,
                'street': corpus.address.street,
                'housenumber': corpus.address.housenumber,
                'coordinates': [corpus.address.longitude, corpus.address.latitude],
            }
        
        # Вычисленный полигон корпуса
        computed_polygon = corpus.get_computed_polygon()
        if computed_polygon:
            corpus_info['polygon'] = computed_polygon
        
        corpora_data.append(corpus_info)
    
    # Подготавливаем данные для карты - участки
    sites_data = []
    for site in sites:
        if site.polygon:
            coords = site.get_polygon_coords()
            if coords:
                # Получаем адреса участка
                site_addresses = Address.objects.filter(
                    site_links__site=site
                ).values('id', 'street', 'housenumber', 'longitude', 'latitude')
                
                sites_data.append({
                    'id': site.id,
                    'name': site.name,
                    'corpus_id': site.corpus.id,
                    'corpus_name': site.corpus.name,
                    'type_code': site.type.code,
                    'type_name': site.type.name,
                    'polygon': coords,
                    'color': site.color or '#4ecdc4',
                    'addresses': list(site_addresses),
                    'address_count': site.site_addresses.count(),
                })
    
    # Подготавливаем данные для карты - нераспределенные адреса организации
    # (привязаны к организации, но не привязаны ни к одному участку)
    site_address_ids = set(
        Address.objects.filter(site_links__site__corpus__organization=organization)
        .values_list('id', flat=True)
        .distinct()
    )
    
    unallocated_addresses = assigned_addresses.exclude(id__in=site_address_ids)

    unallocated_addresses_data = []
    # Убираем лимит на количество нераспределённых адресов для отображения
    for addr in unallocated_addresses:
        if addr.longitude and addr.latitude:
            unallocated_addresses_data.append({
                'id': addr.id,
                'street': addr.street,
                'housenumber': addr.housenumber,
                'city': addr.city,
                'coordinates': [addr.longitude, addr.latitude],
            })
    
    context = {
        'organization': organization,
        'corpora': corpora,
        'sites': sites,
        'site_types': site_types,
        'assigned_addresses': assigned_addresses,
        'page_obj': page_obj,
        'organization_data': json.dumps(organization_data),
        'corpora_data': json.dumps(corpora_data),
        'sites_data': json.dumps(sites_data),
        'unallocated_addresses_data': json.dumps(unallocated_addresses_data),
        'unallocated_count': unallocated_addresses.count(),
    }
    return render(request, 'zones/organization_view.html', context)


@login_required
def corpus_detail(request, pk):
    """Детальная страница корпуса с картой участков."""
    corpus = get_object_or_404(Corpus, pk=pk)
    
    # Получаем все участки корпуса
    sites = corpus.sites.filter(is_active=True).select_related('type')
    
    # Получаем все типы участков для фильтрации
    site_types = SiteType.objects.all()
    
    # Подготавливаем данные для карты
    corpus_data = {
        'id': corpus.id,
        'name': corpus.name,
        'color': corpus.color or '#ff6b6b',
    }
    
    # Данные организации (для отображения границ)
    organization_data = {
        'name': corpus.organization.name,
        'polygon': corpus.organization.polygon,
        'color': corpus.organization.color or '#3388ff',
    }
    
    # Адрес корпуса (маркер)
    if corpus.address:
        corpus_data['address'] = {
            'id': corpus.address.id,
            'street': corpus.address.street,
            'housenumber': corpus.address.housenumber,
            'coordinates': [corpus.address.longitude, corpus.address.latitude],
        }
    
    # Вычисленный полигон корпуса
    computed_polygon = corpus.get_computed_polygon()
    if computed_polygon:
        corpus_data['polygon'] = computed_polygon
    
    # Участки для отображения на карте
    sites_data = []
    for site in sites:
        if site.polygon:
            coords = site.get_polygon_coords()
            if coords:
                # Получаем адреса участка
                site_addresses = Address.objects.filter(
                    site_links__site=site
                ).values('id', 'street', 'housenumber', 'longitude', 'latitude')
                
                sites_data.append({
                    'id': site.id,
                    'name': site.name,
                    'type_code': site.type.code,
                    'type_name': site.type.name,
                    'polygon': coords,
                    'color': site.color or '#4ecdc4',
                    'addresses': list(site_addresses),
                    'address_count': site.site_addresses.count(),
                })
    
    # Получаем нераспределенные адреса (привязаны к организации, но не привязаны к участкам корпуса)
    organization_address_ids = set(
        Address.objects.filter(organization_links__organization=corpus.organization)
        .values_list('id', flat=True)
        .distinct()
    )
    
    site_address_ids = set(
        Address.objects.filter(site_links__site__corpus=corpus)
        .values_list('id', flat=True)
        .distinct()
    )
    
    unallocated_addresses = Address.objects.filter(
        id__in=organization_address_ids
    ).exclude(id__in=site_address_ids)
    
    # Подготавливаем данные для карты - нераспределенные адреса
    unallocated_addresses_data = []
    for addr in unallocated_addresses[:500]:  # Ограничиваем для производительности
        if addr.longitude and addr.latitude:
            unallocated_addresses_data.append({
                'id': addr.id,
                'street': addr.street,
                'housenumber': addr.housenumber,
                'city': addr.city,
                'coordinates': [addr.longitude, addr.latitude],
            })
    
    context = {
        'corpus': corpus,
        'sites': sites,
        'site_types': site_types,
        'corpus_data': json.dumps(corpus_data),
        'organization_data': json.dumps(organization_data),
        'sites_data': json.dumps(sites_data),
        'unallocated_addresses_data': json.dumps(unallocated_addresses_data),
        'unallocated_count': unallocated_addresses.count(),
    }
    return render(request, 'zones/corpus_detail.html', context)


@login_required
@require_http_methods(["POST"])
def site_create_or_update(request, corpus_pk):
    """Создание или обновление участка через AJAX."""
    corpus = get_object_or_404(Corpus, pk=corpus_pk)
    
    try:
        data = json.loads(request.body)
        site_id = data.get('id')  # Если есть ID, обновляем, иначе создаем
        
        site_type_code = data.get('type_code')
        if not site_type_code:
            return JsonResponse({'success': False, 'error': 'Тип участка не указан'}, status=400)
        
        site_type = get_object_or_404(SiteType, code=site_type_code)
        
        name = data.get('name', '')
        if not name:
            return JsonResponse({'success': False, 'error': 'Название участка не указано'}, status=400)
        
        polygon = data.get('polygon')
        color = data.get('color', '#4ecdc4')
        description = data.get('description', '')
        
        if site_id:
            # Обновление существующего участка
            site = get_object_or_404(Site, pk=site_id, corpus=corpus)
            site.name = name
            site.type = site_type
            site.polygon = polygon
            site.color = color
            site.description = description
        else:
            # Создание нового участка
            site = Site(
                corpus=corpus,
                name=name,
                type=site_type,
                polygon=polygon,
                color=color,
                description=description,
            )
        
        site.save()
        
        return JsonResponse({
            'success': True,
            'site_id': site.id,
            'message': 'Участок сохранен успешно'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def site_detail(request, pk):
    """Получение данных участка для редактирования."""
    site = get_object_or_404(Site, pk=pk)
    
    # Получаем адреса участка
    site_addresses = Address.objects.filter(
        site_links__site=site
    ).values('id', 'street', 'housenumber', 'city', 'longitude', 'latitude')
    
    return JsonResponse({
        'id': site.id,
        'name': site.name,
        'type_code': site.type.code,
        'type_name': site.type.name,
        'polygon': site.polygon,
        'color': site.color or '#4ecdc4',
        'description': site.description or '',
        'address_count': site.site_addresses.count(),
        'addresses': list(site_addresses),
        'area': site.area,
    })


@login_required
@require_http_methods(["POST"])
def site_delete(request, pk):
    """Удаление участка."""
    site = get_object_or_404(Site, pk=pk)
    corpus_id = site.corpus.id
    
    try:
        site.delete()
        return JsonResponse({
            'success': True,
            'message': 'Участок удален успешно',
            'corpus_id': corpus_id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def site_assign_addresses(request, pk):
    """Привязка адресов к участку."""
    site = get_object_or_404(Site, pk=pk)
    
    try:
        assigned_count = site.assign_addresses_in_polygon()
        return JsonResponse({
            'success': True,
            'assigned_count': assigned_count,
            'message': f'Привязано адресов: {assigned_count}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def site_addresses(request, pk):
    """Получение списка адресов участка."""
    site = get_object_or_404(Site, pk=pk)
    
    addresses = Address.objects.filter(
        site_links__site=site
    ).values('id', 'street', 'housenumber', 'city', 'longitude', 'latitude')
    
    return JsonResponse({
        'addresses': list(addresses),
        'count': addresses.count()
    })
