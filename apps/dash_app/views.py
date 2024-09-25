# apps.dash_app/views.py
from django.shortcuts import render


def dash_view(request):
    return render(request, 'dash_app/dash_app.html')

def economic_dashboard(request):
    context = {
        'current_module': 'economic',  # Указываем текущий модуль
    }
    return render(request, 'home/economic/dashboard.html', context)

