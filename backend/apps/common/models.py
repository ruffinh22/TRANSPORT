"""
Common models pour tous les modules
Fournit les modèles de base avec timestamps, soft delete, audit trail
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """Classe abstraite de base pour tous les modèles"""
    
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete - marquer le record comme supprimé"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])
    
    def restore(self):
        """Restaurer un record soft deleted"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])
    
    @classmethod
    def active_objects(cls):
        """Retourner les records non supprimés"""
        return cls.objects.filter(deleted_at__isnull=True)


class AuditTrail(BaseModel):
    """Enregistrer les modifications pour audit"""
    
    class ActionChoices(models.TextChoices):
        CREATE = 'CREATE', _('Création')
        UPDATE = 'UPDATE', _('Modification')
        DELETE = 'DELETE', _('Suppression')
        RESTORE = 'RESTORE', _('Restauration')
        LOGIN = 'LOGIN', _('Connexion')
        LOGOUT = 'LOGOUT', _('Déconnexion')
        EXPORT = 'EXPORT', _('Export')
        IMPORT = 'IMPORT', _('Import')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_trails'
    )
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=100, db_index=True)
    action = models.CharField(
        max_length=20,
        choices=ActionChoices.choices,
        db_index=True
    )
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.model_name}({self.object_id}) - {self.action} by {self.user}"


class Role(BaseModel):
    """Rôles pour RBAC - 7 rôles du cahier des charges TKF"""
    
    class RoleType(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Administrateur')
        ADMIN = 'ADMIN', _('Administrateur Système')
        MANAGER = 'MANAGER', _('Manager Opérations')
        COMPTABLE = 'COMPTABLE', _('Comptable / Manager Finance')
        GUICHETIER = 'GUICHETIER', _('Guichetier')
        CHAUFFEUR = 'CHAUFFEUR', _('Chauffeur')
        CONTROLEUR = 'CONTROLEUR', _('Contrôleur')
        GESTIONNAIRE_COURRIER = 'GESTIONNAIRE_COURRIER', _('Gestionnaire Courrier')
    
    code = models.CharField(
        max_length=50,
        unique=True,
        choices=RoleType.choices,
        db_index=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, help_text='Liste des permissions')
    is_active = models.BooleanField(default=True, db_index=True)
    is_system = models.BooleanField(
        default=False,
        help_text='Rôle système - ne peut pas être supprimé'
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Permission(BaseModel):
    """Permissions granulaires"""
    
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    module = models.CharField(
        max_length=50,
        choices=[
            ('USERS', 'Gestion Utilisateurs'),
            ('VEHICLES', 'Gestion Véhicules'),
            ('TRIPS', 'Gestion Trajets'),
            ('TICKETS', 'Gestion Billets'),
            ('PARCELS', 'Gestion Colis'),
            ('PAYMENTS', 'Gestion Paiements'),
            ('REPORTS', 'Gestion Rapports'),
            ('SETTINGS', 'Paramètres Système'),
        ],
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        ordering = ['module', 'code']
        unique_together = ['module', 'code']
    
    def __str__(self):
        return f"{self.module} - {self.code}"


class SystemLog(BaseModel):
    """Logs système pour monitoring et debugging"""
    
    class LogLevel(models.TextChoices):
        DEBUG = 'DEBUG', _('Debug')
        INFO = 'INFO', _('Info')
        WARNING = 'WARNING', _('Avertissement')
        ERROR = 'ERROR', _('Erreur')
        CRITICAL = 'CRITICAL', _('Critique')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(
        max_length=20,
        choices=LogLevel.choices,
        db_index=True
    )
    message = models.TextField()
    module = models.CharField(max_length=100, db_index=True)
    function_name = models.CharField(max_length=100, null=True, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    exception = models.TextField(null=True, blank=True)
    context = models.JSONField(default=dict, null=True, blank=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.module} - {self.message[:50]}"


class Notification(BaseModel):
    """Notifications utilisateurs"""
    
    class NotificationType(models.TextChoices):
        TRIP_BOOKING = 'TRIP_BOOKING', _('Réservation Trajet')
        TRIP_REMINDER = 'TRIP_REMINDER', _('Rappel Trajet')
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', _('Paiement Réussi')
        PAYMENT_FAILED = 'PAYMENT_FAILED', _('Paiement Échoué')
        PARCEL_UPDATE = 'PARCEL_UPDATE', _('Mise à jour Colis')
        REFUND = 'REFUND', _('Remboursement')
        ALERT = 'ALERT', _('Alerte')
        INFO = 'INFO', _('Information')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, null=True, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    def __str__(self):
        return f"{self.notification_type} - {self.title}"


class FileStorage(BaseModel):
    """Gestion des fichiers uploadés"""
    
    class FileType(models.TextChoices):
        IMAGE = 'IMAGE', _('Image')
        DOCUMENT = 'DOCUMENT', _('Document')
        VIDEO = 'VIDEO', _('Vidéo')
        AUDIO = 'AUDIO', _('Audio')
        PDF = 'PDF', _('PDF')
        EXCEL = 'EXCEL', _('Excel')
        OTHER = 'OTHER', _('Autre')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, choices=FileType.choices)
    file_size = models.BigIntegerField()  # en bytes
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files'
    )
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.file_name


class Location(BaseModel):
    """Localisations géographiques"""
    
    name = models.CharField(max_length=100, unique=True, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255)
    city_name = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Cameroun')
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        ordering = ['city_name', 'name']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['city_name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.city_name})"
