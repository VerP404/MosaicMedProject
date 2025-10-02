from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    DeleteEmdViewSet, 
    InvalidationReasonViewSet, 
    MedicalOrganizationViewSet,
    MedicalOrganizationOMSTargetViewSet,
    UserViewSet
)

router = DefaultRouter()
router.register(r'delete-emd', DeleteEmdViewSet)
router.register(r'invalidation-reasons', InvalidationReasonViewSet)
router.register(r'medical-organizations', MedicalOrganizationViewSet)
router.register(r'oms-targets', MedicalOrganizationOMSTargetViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
