from django.urls import path
from . import views

urlpatterns = [
    path('api/report_data/<int:year>/', views.report_data, name='report_data'),
]
