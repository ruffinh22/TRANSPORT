"""Modèles pour l'app Employés"""
from apps.common.models import BaseModel
from apps.users.models import User
from django.db import models


class Employee(BaseModel):
    """Modèle complet pour les employés TKF"""
    
    ROLE_CHOICES = [
        ('driver', 'Chauffeur'),
        ('receiver', 'Receveur'),
        ('cashier', 'Guichetier'),
        ('controller', 'Contrôleur'),
        ('mail_agent', 'Agent Courrier'),
        ('admin', 'Administrateur'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('on_leave', 'En congé'),
        ('suspended', 'Suspendu'),
        ('retired', 'Retraité'),
    ]
    
    # Informations de base
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    
    # Informations professionnelles
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=12, decimal_places=2, help_text="Salaire mensuel de base en FCFA")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Pourcentage de commission (ex: 5.00 pour 5%)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Localisation
    city = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Documents
    document_type = models.CharField(max_length=50, default='national_id', help_text="Type de document d'identité")
    document_id = models.CharField(max_length=50, unique=True, db_index=True)
    document_expiry = models.DateField(null=True, blank=True)
    
    # Références utilisateur
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee')
    
    # Historique
    trips_completed = models.IntegerField(default=0, help_text="Nombre de trajets effectués")
    parcels_delivered = models.IntegerField(default=0, help_text="Nombre de colis livrés (pour agents courrier)")
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Revenus totaux cumulés")
    
    # Métadonnées
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['role', 'status']),
            models.Index(fields=['hire_date']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_available(self):
        """Vérifie si l'employé est disponible pour une affectation"""
        return self.status == 'active'


class EmployeeLeave(BaseModel):
    """Modèle pour gérer les congés des employés"""
    
    LEAVE_TYPES = [
        ('annual', 'Congé annuel'),
        ('sick', 'Congé maladie'),
        ('maternity', 'Congé maternité'),
        ('unpaid', 'Congé non payé'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.IntegerField(help_text="Nombre de jours de congé")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leaves_approved')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Congé employé"
        verbose_name_plural = "Congés employés"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()}"


class EmployeePayroll(BaseModel):
    """Modèle pour gérer les fiches de paie"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('paid', 'Payé'),
        ('cancelled', 'Annulé'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    year = models.IntegerField(db_index=True)
    month = models.IntegerField(db_index=True)  # 1-12
    
    # Salaire de base
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Bonus et primes
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Déductions
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Avance sur salaire
    
    # Total
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Statut et dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True, help_text="Mobile Money, Virement, etc.")
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Fiche de paie"
        verbose_name_plural = "Fiches de paie"
        ordering = ['-year', '-month']
        unique_together = ['employee', 'year', 'month']
        indexes = [
            models.Index(fields=['employee', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.month}/{self.year}"


class EmployeePerformance(BaseModel):
    """Modèle pour évaluer la performance des employés"""
    
    RATING_CHOICES = [
        (1, 'Très mauvais'),
        (2, 'Mauvais'),
        (3, 'Moyen'),
        (4, 'Bon'),
        (5, 'Très bon'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews')
    evaluation_date = models.DateField()
    evaluator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='evaluations_given')
    
    # Critères d'évaluation
    punctuality = models.IntegerField(choices=RATING_CHOICES, help_text="Ponctualité et assiduité")
    professionalism = models.IntegerField(choices=RATING_CHOICES, help_text="Professionnalisme et comportement")
    quality_of_work = models.IntegerField(choices=RATING_CHOICES, help_text="Qualité du travail effectué")
    teamwork = models.IntegerField(choices=RATING_CHOICES, help_text="Capacité à travailler en équipe")
    initiative = models.IntegerField(choices=RATING_CHOICES, help_text="Prise d'initiative et créativité")
    
    # Moyenne
    overall_rating = models.FloatField(help_text="Note moyenne de performance")
    
    # Commentaires
    comments = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Évaluation de performance"
        verbose_name_plural = "Évaluations de performance"
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Évaluation {self.evaluation_date}"
