"""Modèles pour l'app Trajets"""
from apps.common.models import BaseModel
from apps.vehicles.models import Vehicle
from django.db import models


class Trip(BaseModel):
    """Modèle pour les trajets"""
    TRIP_STATUS = [
        ('PLANNED', 'Planifié'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Complété'),
        ('CANCELLED', 'Annulé'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='trips')
    departure_location = models.CharField(max_length=100)
    arrival_location = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField(null=True, blank=True)
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRIP_STATUS, default='PLANNED')
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = "Trajet"
        verbose_name_plural = "Trajets"
        ordering = ['-departure_time']
