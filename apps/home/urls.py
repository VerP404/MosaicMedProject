from .views import *
from django.urls import path

urlpatterns = [
    path('', home, name='home'),
    path('status/', check_system_status, name='check_system_status'),  # api для опроса сервера на работоспособность
]
