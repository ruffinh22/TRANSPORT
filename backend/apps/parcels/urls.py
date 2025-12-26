"""URLs pour l'app Parcels"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParcelViewSet, ParcelCategoryViewSet, ParcelInsuranceViewSet, ParcelTrackingViewSet

router = DefaultRouter()
router.register(r'parcels', ParcelViewSet, basename='parcel')
router.register(r'categories', ParcelCategoryViewSet, basename='parcel-category')
router.register(r'insurance', ParcelInsuranceViewSet, basename='parcel-insurance')
router.register(r'tracking', ParcelTrackingViewSet, basename='parcel-tracking')

urlpatterns = [
    path('', include(router.urls)),
]
