"""Views pour l'app Revenues"""
from rest_framework import viewsets
from .models import Revenue
from .serializers import RevenueSerializer


class RevenueViewSet(viewsets.ModelViewSet):
    queryset = Revenue.objects.all()
    serializer_class = RevenueSerializer
    filterset_fields = ['date']
    ordering = ['-date']
