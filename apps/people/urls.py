from django.urls import path
from .views import people_report_view, generate_iszl_report

app_name = 'people'

urlpatterns = [
    path('people-report/', people_report_view, name='people_report'),
    path('generate-iszl-report/', generate_iszl_report, name='generate_iszl_report'),
]
