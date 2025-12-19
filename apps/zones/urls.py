from django.urls import path
from . import views

app_name = 'zones'

urlpatterns = [
    path('', views.organizations_list, name='organizations_list'),
    path('organization/<int:pk>/', views.organization_detail, name='organization_detail'),
    path('organization/<int:pk>/view/', views.organization_view, name='organization_view'),
    path('organization/<int:pk>/update-polygon/', views.organization_update_polygon, name='organization_update_polygon'),
    path('organization/<int:pk>/assign-addresses/', views.organization_assign_addresses, name='organization_assign_addresses'),
    path('organization/<int:pk>/addresses/', views.organization_addresses, name='organization_addresses'),
    path('corpus/<int:pk>/', views.corpus_detail, name='corpus_detail'),
    path('corpus/<int:corpus_pk>/site/', views.site_create_or_update, name='site_create_or_update'),
    path('site/<int:pk>/', views.site_detail, name='site_detail'),
    path('site/<int:pk>/delete/', views.site_delete, name='site_delete'),
    path('site/<int:pk>/assign-addresses/', views.site_assign_addresses, name='site_assign_addresses'),
    path('site/<int:pk>/addresses/', views.site_addresses, name='site_addresses'),
    path('api/search-addresses/', views.search_addresses, name='search_addresses'),
]
