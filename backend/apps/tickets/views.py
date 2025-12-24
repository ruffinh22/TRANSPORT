"""Views pour l'app Tickets"""
from rest_framework import viewsets
from .models import Ticket
from .serializers import TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    filterset_fields = ['status', 'trip']
    search_fields = ['passenger__email']
