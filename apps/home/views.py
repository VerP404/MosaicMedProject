from django.shortcuts import render
import requests
from django.http import JsonResponse

from apps.home.models import *
from apps.organization.models import MedicalOrganization


def home(request):
    main_settings = MainSettings.objects.first()  # Получите настройки
    organization = MedicalOrganization.objects.first()

    # Формируем динамические URL на основе текущего хоста (актуально при смене подсети/IP)
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    host_only = host.split(':')[0]

    dash_url = f"{scheme}://{host_only}:{main_settings.dash_port}"
    dash_chief_url = f"{scheme}://{host_only}:{main_settings.dash_chief_port}"

    return render(request, 'home/home.html', {
        'main_settings': main_settings,
        'organization': organization,
        'dash_url': dash_url,
        'dash_chief_url': dash_chief_url,
    })


def check_system_status(request):
    try:
        settings = MainSettings.objects.first()

        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        host_only = host.split(':')[0]

        # Проверка доступности Django приложения (по текущему хосту)
        django_status = 'unknown'
        try:
            django_url = f"{scheme}://{host_only}:{settings.main_app_port}"
            response = requests.get(django_url, timeout=5)
            if response.status_code == 200:
                django_status = 'Django is running'
            else:
                django_status = f'Django returned status code: {response.status_code}'
        except requests.exceptions.RequestException as e:
            django_status = f'Django is down: {str(e)}'

        # Проверка доступности Dash приложения (по текущему хосту)
        dash_status = 'unknown'
        try:
            dash_url = f"{scheme}://{host_only}:{settings.dash_port}"
            response = requests.get(dash_url, timeout=5)
            if response.status_code == 200:
                dash_status = 'Dash is running'
            else:
                dash_status = f'Dash returned status code: {response.status_code}'
        except requests.exceptions.RequestException as e:
            dash_status = f'Dash is down: {str(e)}'

        data = {
            'django_status': django_status,
            'dash_status': dash_status,
        }

        return JsonResponse(data)

    except MainSettings.DoesNotExist:
        return JsonResponse({'error': 'Settings not found'}, status=500)
