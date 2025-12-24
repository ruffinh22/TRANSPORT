"""Modèles pour l'app Revenus"""
from apps.common.models import BaseModel
from django.db import models


class Revenue(BaseModel):
    """Modèle pour les revenus"""
    date = models.DateField(db_index=True)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    tickets_count = models.IntegerField(default=0)
    parcels_count = models.IntegerField(default=0)
    expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        verbose_name = "Revenu"
        verbose_name_plural = "Revenus"
        ordering = ['-date']
        unique_together = ['date']
