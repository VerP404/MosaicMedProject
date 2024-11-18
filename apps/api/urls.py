from django.urls import path

from apps.api.views import BaseQueryAPI

app_name = 'api'

urlpatterns = [
    path('base_query/', BaseQueryAPI.as_view(), name='base_query_api'),
]
