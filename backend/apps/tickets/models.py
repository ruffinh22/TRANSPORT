"""Modèles pour l'app Billets"""
from apps.common.models import BaseModel
from apps.trips.models import Trip
from apps.users.models import User
from django.db import models


class Ticket(BaseModel):
    """Modèle pour les billets"""
    TICKET_STATUS = [
        ('AVAILABLE', 'Disponible'),
        ('BOOKED', 'Réservé'),
        ('CONFIRMED', 'Confirmé'),
        ('USED', 'Utilisé'),
        ('CANCELLED', 'Annulé'),
    ]
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='tickets')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    seat_number = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=TICKET_STATUS)
    
    class Meta:
        verbose_name = "Billet"
        verbose_name_plural = "Billets"
        unique_together = ['trip', 'seat_number']
        ordering = ['-created_at']
