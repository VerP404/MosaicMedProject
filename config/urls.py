from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView

from apps.dash_app.dash import app
from apps.dash_app.views import economic_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.home.urls')),
    path('', include('apps.data_loader.urls', namespace='data_loader')),

    path('dash/', TemplateView.as_view(template_name='dash_app/dash_app.html'), name='dash_app'),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),

    path('economic/dashboard/', economic_dashboard, name='economic_dashboard'),
]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
