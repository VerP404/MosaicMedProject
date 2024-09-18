# urls.py
from django.urls import path
from . import views

app_name = 'data_loader'

urlpatterns = [
    path('omsdata/upload/', views.upload_file, name='data_loader_omsdata_upload'),
    path('task_status/<str:task_id>/', views.task_status, name='task_status'),
]
