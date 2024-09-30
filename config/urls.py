# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView, RedirectView
from apps.dash_app.views import *



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.home.urls')),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
    path('data_loader/', include('apps.data_loader.urls', namespace='data_loader')),
    path('dash_app/', include('apps.dash_app.urls')),

]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
