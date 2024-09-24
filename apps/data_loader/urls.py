# urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from apps.data_loader.views import *

app_name = 'data_loader'

urlpatterns = [
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
