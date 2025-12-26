"""Modèles pour l'app Colis"""
from apps.common.models import BaseModel
from apps.trips.models import Trip
from apps.users.models import User
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class ParcelCategory(models.Model):
    """Catégories de colis"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_fragile = models.BooleanField(default=False)
    requires_signature = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Catégorie de colis"
        verbose_name_plural = "Catégories de colis"
    
    def __str__(self):
        return self.name


class Parcel(BaseModel):
    """Modèle pour les colis"""
    PARCEL_STATUS = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Accepté'),
        ('IN_TRANSIT', 'En transit'),
        ('DELIVERED', 'Livré'),
        ('LOST', 'Perdu'),
        ('RETURNED', 'Retourné'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyen'),
        ('HIGH', 'Élevé'),
        ('URGENT', 'Urgent'),
    ]
    
    # Relations
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name='parcels')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_parcels')
    category = models.ForeignKey(ParcelCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Destinataire
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    recipient_email = models.EmailField(blank=True)
    
    # Contenu
    description = models.TextField()
    weight = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    dimensions = models.CharField(max_length=100, blank=True, help_text="Longueur x Largeur x Hauteur")
    
    # Tarification
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    weight_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fragile_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Statut et priorité
    status = models.CharField(max_length=20, choices=PARCEL_STATUS, default='PENDING')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Suivi
    is_fragile = models.BooleanField(default=False)
    requires_signature = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Assurance
    is_insured = models.BooleanField(default=False)
    insurance_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    insurance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = "Colis"
        verbose_name_plural = "Colis"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['trip', 'status']),
        ]
    
    def __str__(self):
        return f"Colis {self.tracking_number}"
    
    def calculate_total_price(self):
        """Calcule le prix total du colis"""
        total = self.base_price + self.weight_surcharge
        if self.is_fragile:
            total += self.fragile_fee
        if self.is_insured:
            total += self.insurance_fee
        return total
    
    def save(self, *args, **kwargs):
        # Générer le numéro de suivi si absent
        if not self.tracking_number:
            import uuid
            self.tracking_number = f"PKG-{uuid.uuid4().hex[:10].upper()}"
        
        # Calculer le prix total
        self.total_price = self.calculate_total_price()
        
        super().save(*args, **kwargs)


class ParcelTracking(BaseModel):
    """Historique de suivi des colis"""
    STATUS_CHOICES = [
        ('SCANNED', 'Numérisé'),
        ('COLLECTED', 'Collecté'),
        ('IN_TRANSIT', 'En transit'),
        ('OUT_FOR_DELIVERY', 'Livraison en cours'),
        ('DELIVERED', 'Livré'),
        ('FAILED', 'Tentative échouée'),
        ('RETURNED', 'Retourné'),
    ]
    
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcel_tracking_updates')
    
    class Meta:
        verbose_name = "Suivi de colis"
        verbose_name_plural = "Suivis de colis"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.parcel.tracking_number} - {self.status}"


class ParcelInsurance(models.Model):
    """Modèle pour l'assurance des colis"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Pourcentage de couverture")
    max_coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Assurance colis"
        verbose_name_plural = "Assurances colis"
    
    def __str__(self):
        return self.name
