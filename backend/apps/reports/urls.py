"""URLs pour l'app Reports"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditTrailViewSet, AdvancedStatisticsViewSet

router = DefaultRouter()
router.register(r'audit-trails', AuditTrailViewSet, basename='audit-trail')
router.register(r'statistics', AdvancedStatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
]
