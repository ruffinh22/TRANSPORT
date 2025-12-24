"""URLs pour l'app Revenues"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RevenueViewSet

router = DefaultRouter()
router.register(r'', RevenueViewSet, basename='revenue')

urlpatterns = [
    path('', include(router.urls)),
]
