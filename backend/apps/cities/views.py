"""Views pour l'app Cities"""
from rest_framework import viewsets
from .models import City
from .serializers import CitySerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    filterset_fields = ['region', 'is_active']
    search_fields = ['name', 'address']
