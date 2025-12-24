"""Modèles pour l'app Colis"""
from apps.common.models import BaseModel
from apps.trips.models import Trip
from apps.users.models import User
from django.db import models


class Parcel(BaseModel):
    """Modèle pour les colis"""
    PARCEL_STATUS = [
        ('PENDING', 'En attente'),
        ('IN_TRANSIT', 'En transit'),
        ('DELIVERED', 'Livré'),
        ('LOST', 'Perdu'),
    ]
    
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name='parcels')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_parcels')
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    description = models.TextField()
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PARCEL_STATUS)
    
    class Meta:
        verbose_name = "Colis"
        verbose_name_plural = "Colis"
        ordering = ['-created_at']
