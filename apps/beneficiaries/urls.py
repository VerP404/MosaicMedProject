from django.urls import path
from . import views

app_name = 'beneficiaries'

urlpatterns = [
    # Страницы
    path('', views.beneficiaries_home_view, name='home'),
    path('list/', views.beneficiaries_list_view, name='list'),
    path('patient/<int:patient_id>/', views.patient_detail_view, name='patient_detail'),
    
    # API endpoints
    path('api/list/', views.beneficiaries_list_api, name='list_api'),
    path('api/patient/<int:patient_id>/', views.patient_detail_api, name='patient_detail_api'),
    path('api/categories/', views.categories_api, name='categories_api'),
    path('api/statistics/', views.statistics_api, name='statistics_api'),
]

