# apps.data_loader.urls
from django.urls import path

from apps.data_loader.views import *

app_name = 'data_loader'

urlpatterns = [
    path('upload-dashboard/', data_upload_dashboard, name='data_upload_dashboard'),
    path('upload-file/<int:data_type_id>/', upload_file, name='upload_file'),
    path('refresh-message/<int:data_type_id>/', refresh_message, name='refresh_message'),

]
