from django.shortcuts import render

from apps.home.models import *


def home(request):
    main_settings = MainSettings.objects.first()  # Получите настройки
    return render(request, 'home/home.html', {'main_settings': main_settings})
