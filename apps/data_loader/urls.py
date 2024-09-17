from django.urls import path
from .views import UploadView

app_name = 'data_loader'

urlpatterns = [
    path('omsdata/upload/', UploadView.as_view(), name='omsdata_upload'),
]
