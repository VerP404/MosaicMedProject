# urls.py
from django.urls import path

from apps.data_loader.views import *

app_name = 'data_loader'

urlpatterns = [
    path('upload/', upload_file_view, name='upload_file'),
    path('upload/success/', lambda request: render(request, 'data_loader/upload_success.html'), name='upload_success'),
]