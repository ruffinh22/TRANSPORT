"""Modèles pour l'app Villes"""
from apps.common.models import BaseModel, Location
from django.db import models


class City(Location):
    """Modèle étendant Location pour les villes"""
    population = models.IntegerField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ['name']
