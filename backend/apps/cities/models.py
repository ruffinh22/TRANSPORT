"""Modèles pour l'app Villes"""
from apps.common.models import BaseModel, Location
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class City(Location):
    """Modèle étendant Location pour les villes"""
    population = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Population de la ville"
    )
    region = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Région administrative"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Code postal ou code de la ville"
    )
    description = models.TextField(
        null=True, 
        blank=True,
        help_text="Description détaillée de la ville"
    )
    # Routes
    is_hub = models.BooleanField(
        default=False,
        help_text="Indique si c'est un hub majeur"
    )
    has_parking = models.BooleanField(
        default=False,
        help_text="Disponibilité d'un parking"
    )
    has_terminal = models.BooleanField(
        default=False,
        help_text="Disponibilité d'un terminal"
    )
    # Statistiques
    trip_count = models.IntegerField(
        default=0,
        help_text="Nombre de trajets"
    )
    annual_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.0,
        help_text="Chiffre d'affaires annuel (CFA)"
    )
    
    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ['name']
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['is_hub']),
        ]

    def __str__(self):
        return f"{self.name} ({self.region})"

    @property
    def is_operational(self):
        """Vérifie si la ville est opérationnelle"""
        return self.is_active and (self.is_hub or self.has_terminal)

    def update_statistics(self):
        """Met à jour les statistiques de la ville"""
        from apps.trips.models import Trip
        from apps.payments.models import Payment
        
        # Comptage des trajets
        self.trip_count = Trip.objects.filter(
            models.Q(departure_city=self.name) | 
            models.Q(arrival_city=self.name)
        ).count()
        
        # Calcul du chiffre d'affaires
        revenues = Payment.objects.filter(
            trip__departure_city=self.name,
            status='completed'
        ).values_list('amount', flat=True)
        self.annual_revenue = sum(revenues) if revenues else 0.0
        
        self.save(update_fields=['trip_count', 'annual_revenue'])
