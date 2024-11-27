from dal import autocomplete
from django.urls import path
from . import views
from ..organization.models import Building, Department
from ..plan.admin import DepartmentAutocomplete

urlpatterns = [
    path('api/group_filters/<int:year>/', views.get_nested_groups_for_year, name='get_nested_groups_for_year'),
    path('api/copy_filters/<int:new_year>/', views.copy_filters_to_new_year, name='copy_filters_to_new_year'),
    path('api/goals/', views.goals_list, name='goals_list'),
    path('building-autocomplete/', autocomplete.Select2QuerySetView.as_view(model=Building),name='building-autocomplete'),
    path('department-autocomplete/', DepartmentAutocomplete.as_view(), name='department-autocomplete'),

]
