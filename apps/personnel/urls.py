from django.urls import path

from apps.personnel.views import *

urlpatterns = [
    path('specialty-autocomplete/', SpecialtyAutocomplete.as_view(), name='specialty-autocomplete'),
    path('post-autocomplete/', PostAutocomplete.as_view(), name='post-autocomplete'),
    path('department-autocomplete/', DepartmentAutocomplete.as_view(), name='department-autocomplete'),

]
