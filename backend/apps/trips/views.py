"""Views pour l'app Trips"""
from rest_framework import viewsets
from .models import Trip
from .serializers import TripSerializer


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    filterset_fields = ['status', 'vehicle']
    search_fields = ['departure_location', 'arrival_location']
