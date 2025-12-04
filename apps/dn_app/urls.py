# apps.dn_app.urls
from django.urls import path

from apps.dn_app.views import upload_csv

app_name = 'dn_app'

urlpatterns = [
    path('upload-csv/', upload_csv, name='upload_csv'),
]


