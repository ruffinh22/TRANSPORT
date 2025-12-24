"""Views pour l'app Parcels"""
from rest_framework import viewsets
from .models import Parcel
from .serializers import ParcelSerializer


class ParcelViewSet(viewsets.ModelViewSet):
    queryset = Parcel.objects.all()
    serializer_class = ParcelSerializer
    filterset_fields = ['status', 'trip']
    search_fields = ['sender__email', 'recipient_name']
