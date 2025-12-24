"""Modèles pour l'app Paiements"""
from apps.common.models import BaseModel
from apps.users.models import User
from django.db import models


class Payment(BaseModel):
    """Modèle pour les paiements"""
    PAYMENT_METHODS = [
        ('CARD', 'Carte bancaire'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('BANK_TRANSFER', 'Virement bancaire'),
        ('CASH', 'Espèces'),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
        ('REFUNDED', 'Remboursé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']
