"""Views pour l'app Vehicles"""
from rest_framework import viewsets
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filterset_fields = ['vehicle_type', 'is_active']
    search_fields = ['registration_number', 'brand', 'model']
