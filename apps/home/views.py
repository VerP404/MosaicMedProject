from django.shortcuts import render

from apps.home.models import *
from apps.organization.models import MedicalOrganization
from apps.peopledash.models import Organization


def home(request):
    main_settings = MainSettings.objects.first()  # Получите настройки
    organization = MedicalOrganization.objects.first()
    return render(request, 'home/home.html', {
        'main_settings': main_settings,
        'organization': organization,
    })
