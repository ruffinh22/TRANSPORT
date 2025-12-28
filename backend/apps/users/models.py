"""Modèles utilisateurs et authentification"""
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.common.models import BaseModel, Role, AuditTrail
import logging

logger = logging.getLogger(__name__)


class UserManager(DjangoUserManager):
    """Manager personnalisé pour User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Créer un utilisateur avec email"""
        if not email:
            raise ValueError('Email est obligatoire')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Créer l'audit trail
        AuditTrail.objects.create(
            user=user,
            model_name='User',
            object_id=str(user.id),
            action='CREATE',
            new_values={'email': email}
        )
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Créer un super utilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    """Modèle utilisateur personnalisé"""
    
    class DocumentType(models.TextChoices):
        CNI = 'CNI', _('Carte Nationale d\'Identité')
        PASSPORT = 'PASSPORT', _('Passeport')
        DRIVER_LICENSE = 'DRIVER_LICENSE', _('Permis de Conduire')
        BUSINESS_LICENSE = 'BUSINESS_LICENSE', _('Licence Professionnelle')
    
    class Gender(models.TextChoices):
        MALE = 'M', _('Homme')
        FEMALE = 'F', _('Femme')
        OTHER = 'O', _('Autre')
    
    # Remplacer username par email
    username = None
    email = models.EmailField(unique=True, db_index=True)
    
    # Override groups et permissions pour éviter les clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True
    )
    
    # Profil utilisateur
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Numéro de téléphone invalide'
    )
    phone = models.CharField(
        max_length=20,
        validators=[phone_regex],
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        null=True,
        blank=True
    )
    
    # Identité légale
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        null=True,
        blank=True
    )
    document_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    document_issue_date = models.DateField(null=True, blank=True)
    document_expiry_date = models.DateField(null=True, blank=True)
    
    # Localisation
    country = models.CharField(max_length=100, default='Cameroun')
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Rôles et permissions
    roles = models.ManyToManyField(
        Role,
        related_name='users',
        blank=True
    )
    
    # Profil entreprise (pour les chauffeurs, employés)
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    company_name = models.CharField(max_length=255, null=True, blank=True)
    company_registration = models.CharField(max_length=100, null=True, blank=True)
    
    # Bancaire
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    bank_account = models.CharField(max_length=50, null=True, blank=True)
    bank_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Préférences
    language = models.CharField(
        max_length=10,
        choices=[('fr', 'Français'), ('en', 'English')],
        default='fr'
    )
    timezone = models.CharField(
        max_length=100,
        default='Africa/Douala'
    )
    
    # Notifications
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)
    notify_push = models.BooleanField(default=True)
    
    # Vérification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    document_verified = models.BooleanField(default=False)
    document_verified_at = models.DateTimeField(null=True, blank=True)
    document_verified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    
    # Photos
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        null=True,
        blank=True
    )
    document_photo = models.ImageField(
        upload_to='documents/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    # Statuts
    is_active = models.BooleanField(default=True, db_index=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(null=True, blank=True)
    blocked_at = models.DateTimeField(null=True, blank=True)
    
    # Authentification
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Termes et conditions
    accepted_terms_at = models.DateTimeField(null=True, blank=True)
    accepted_privacy_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['is_active', 'is_blocked']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Retourner le nom complet"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retourner le prénom"""
        return self.first_name
    
    def has_role(self, role_code):
        """Vérifier si l'utilisateur a un rôle spécifique"""
        return self.roles.filter(code=role_code, is_active=True).exists()
    
    def has_permission(self, permission_code):
        """Vérifier si l'utilisateur a une permission spécifique"""
        # Via les rôles
        for role in self.roles.filter(is_active=True):
            if permission_code in role.permissions:
                return True
        return False
    
    def block(self, reason=''):
        """Bloquer l'utilisateur"""
        self.is_blocked = True
        self.block_reason = reason
        self.blocked_at = timezone.now()
        self.save(update_fields=['is_blocked', 'block_reason', 'blocked_at', 'updated_at'])
        
        logger.warning(f"User {self.email} blocked: {reason}")
    
    def unblock(self):
        """Débloquer l'utilisateur"""
        self.is_blocked = False
        self.block_reason = None
        self.blocked_at = None
        self.save(update_fields=['is_blocked', 'block_reason', 'blocked_at', 'updated_at'])
        
        logger.info(f"User {self.email} unblocked")
    
    def verify_email(self):
        """Marquer l'email comme vérifié"""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verified', 'email_verified_at', 'updated_at'])
    
    def verify_phone(self):
        """Marquer le téléphone comme vérifié"""
        self.phone_verified = True
        self.phone_verified_at = timezone.now()
        self.save(update_fields=['phone_verified', 'phone_verified_at', 'updated_at'])
    
    def verify_document(self, verified_by):
        """Marquer le document comme vérifié"""
        self.document_verified = True
        self.document_verified_at = timezone.now()
        self.document_verified_by = verified_by
        self.save(update_fields=[
            'document_verified', 'document_verified_at',
            'document_verified_by', 'updated_at'
        ])
    
    def lock_login(self):
        """Verrouiller le compte après trop de tentatives"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'locked_until', 'updated_at'])
    
    def unlock_login(self):
        """Réinitialiser les tentatives de connexion"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until', 'updated_at'])
    
    @property
    def is_fully_verified(self):
        """Vérifier si l'utilisateur est entièrement vérifié"""
        return (
            self.email_verified and
            self.phone_verified and
            self.document_verified
        )


class UserSession(BaseModel):
    """Gérer les sessions utilisateurs"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    refresh_token = models.TextField(unique=True)
    ip_address = models.GenericIPAddressField()
    device_name = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    logged_out_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['refresh_token']),
        ]
    
    def __str__(self):
        return f"Session {self.user.email} - {self.device_name or 'Unknown'}"
    
    def is_expired(self):
        """Vérifier si la session a expiré"""
        return timezone.now() > self.expires_at
    
    def logout(self):
        """Terminer la session"""
        self.is_active = False
        self.logged_out_at = timezone.now()
        self.save(update_fields=['is_active', 'logged_out_at', 'updated_at'])
