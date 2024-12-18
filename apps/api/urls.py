from django.urls import path

from apps.api.views import BaseQueryAPI, DDQueryAPI, MISKAUZLPUAPIView, MISKAUZTalonAPIView, PatientRegistryAPI, \
    UpdateRegistryAPIView

app_name = 'api'

urlpatterns = [
    path('base_query/', BaseQueryAPI.as_view(), name='base_query_api'),
    path('dd_query/', DDQueryAPI.as_view(), name='dd_query_api'),
    path('mis_kauz_lpu/', MISKAUZLPUAPIView.as_view(), name='mis_kauz_lpu_api'),
    path('mis_kauz_talon/<int:year>/', MISKAUZTalonAPIView.as_view(), name='mis_kauz_talon_api'),
    path('patient_registry/', PatientRegistryAPI.as_view(), name='patient_registry_api'),
    path('update_registry/', UpdateRegistryAPIView.as_view(), name='update_registry'),

]
