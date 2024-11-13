from django.urls import path, re_path
from . import views
from .views import dynamic_page, dynamic_page_get_data

urlpatterns = [
    path('', views.index, name='peopledash_home'),
    path('get_report_datetime/', views.get_report_datetime, name='get_report_datetime'),
    path('upload_data/', views.upload_data, name='upload_data'),
    path('api/registered_patients/', views.registered_patients_api, name='registered_patients_api'),
    re_path(r'^get_data_(?P<path>[\w-]+)/$', dynamic_page_get_data, name='dynamic_page_get_data'),

    re_path(r'^(?P<path>[\w-]+)/$', dynamic_page, name='dynamic_page'),

]
