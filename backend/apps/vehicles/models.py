"""Modèles pour l'app Véhicules"""
from apps.common.models import BaseModel
from django.db import models


class Vehicle(BaseModel):
    """Modèle pour les véhicules"""
    VEHICLE_TYPES = [
        ('BUS', 'Bus'),
        ('MINIBUS', 'Minibus'),
        ('TRUCK', 'Camion'),
        ('VAN', 'Van'),
    ]
    
    registration_number = models.CharField(max_length=50, unique=True, db_index=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    capacity = models.IntegerField()  # Nombre de places
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['registration_number']
