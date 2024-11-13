from .views import *
from django.urls import path

from ..data_loader.views import get_table_row_counts

urlpatterns = [
    path('', home, name='home'),
    path('status-server/', check_system_status, name='check_system_status'),
    path('status-table/', get_table_row_counts, name='get_table_row_counts'),
]
