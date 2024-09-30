# apps.dash_app/views.py
from django.shortcuts import render


def economic_dashboard(request):
    context = {
        'current_module': 'economic',
    }
    return render(request, 'home/economic/dashboard.html', context)


def mosaicmed_view(request):
    return render(request, 'dash_app/mosaicmed.html')
