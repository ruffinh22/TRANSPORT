"""URLs pour l'app Parcels"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParcelViewSet

router = DefaultRouter()
router.register(r'', ParcelViewSet, basename='parcel')

urlpatterns = [
    path('', include(router.urls)),
]
