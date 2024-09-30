from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from apps.dash_app.views import *

from apps.dash_app.dash import app2
from apps.dash_app.MosaicMed.app import app


# from apps.dash_app.dash2 import app3


app_name = 'dash_app'

urlpatterns = [
    path('mosaicmed/', mosaicmed_view, name='mosaicmed'),
    path('economic/dashboard/', economic_dashboard, name='economic_dashboard'),
]
