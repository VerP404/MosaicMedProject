from django.urls import path
from .views import people_report_view

app_name = 'people'

urlpatterns = [
    path('people-report/', people_report_view, name='people_report'),
]
