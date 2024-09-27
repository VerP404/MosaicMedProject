# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView, RedirectView

from apps.dash_app.dash import app2
from apps.dash_app.MosaicMed.app import app
from apps.dash_app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/home/', permanent=False), name='index'),
    path('', include('apps.home.urls')),
    path('', include('apps.data_loader.urls', namespace='data_loader')),
    path('dash/', TemplateView.as_view(template_name='dash_app/dash_app.html'), name='dash_app'),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),

    path('mosaicmed/', mosaicmed_view, name='mosaicmed'),
    path('economic/dashboard/', economic_dashboard, name='economic_dashboard'),
]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
