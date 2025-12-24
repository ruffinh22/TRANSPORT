"""Modèles pour l'app Employés"""
from apps.common.models import BaseModel
from apps.users.models import User
from django.db import models


class Employee(BaseModel):
    """Modèle pour les employés"""
    DEPARTMENTS = [
        ('DRIVER', 'Chauffeurs'),
        ('OPERATIONS', 'Opérations'),
        ('ADMIN', 'Administration'),
        ('SUPPORT', 'Support'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=50, choices=DEPARTMENTS)
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['employee_id']
