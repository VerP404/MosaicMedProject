# apps.dash_app/views.py
from django.shortcuts import render


def dash_view(request):
    return render(request, 'dash_app/dash_app.html')

def economic_dashboard(request):
    return render(request, 'home/economic/dashboard.html')

