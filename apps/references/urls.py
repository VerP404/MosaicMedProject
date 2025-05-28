from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'references'

urlpatterns = [
    path('api/mkb10/', views.MKB10ListView.as_view(), name='mkb10_list'),
    path('api/mkb10/<str:code>/', views.MKB10DetailView.as_view(), name='mkb10_detail'),
    path('api/mkb10/<str:code>/children/', views.MKB10ChildrenView.as_view(), name='mkb10_children'),
] 