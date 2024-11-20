from django.urls import path

from apps.api.views import BaseQueryAPI, DDQueryAPI

app_name = 'api'

urlpatterns = [
    path('base_query/', BaseQueryAPI.as_view(), name='base_query_api'),
    path('dd_query/', DDQueryAPI.as_view(), name='dd_query_api'),
]
