from django.urls import path
from . import views

urlpatterns = [
    path('api/group_filters/<int:year>/', views.get_nested_groups_for_year, name='get_nested_groups_for_year'),
    path('api/copy_filters/<int:new_year>/', views.copy_filters_to_new_year, name='copy_filters_to_new_year'),
    path('api/goals/', views.goals_list, name='goals_list'),
]
