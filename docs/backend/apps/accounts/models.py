# apps/accounts/models.py
# ========================

import uuid
import secrets
import os
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.core.validators import (
    MinValueValidator, MaxValueValidator, 
    RegexValidator, FileExtensionValidator
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    """Manager personnalisé pour les utilisateurs."""
    
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        if not username:
            raise ValueError(_('Le nom d\'utilisateur est obligatoire'))
            
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('kyc_status', 'approved')
        return self.create_user(username, email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        return self.get(username=username)

# apps/accounts/models.py
# Remplacez votre classe User par celle-ci (version complète)

class User(AbstractUser):
    """Modèle utilisateur personnalisé pour RUMO RUSH."""
    
    # Statuts KYC
    KYC_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('under_review', _('En cours de vérification')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('expired', _('Expiré')),
    ]
    
    # Langues supportées - AJOUTÉ
    LANGUAGE_CHOICES = [
        ('fr', _('Français')),
        ('en', _('English')),
        ('es', _('Español')),
        ('zh', _('中文')),
    ]
    
    # Devises supportées
    CURRENCY_CHOICES = [
        ('FCFA', 'FCFA'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]
    
    # Champs de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('Adresse email'), unique=True)
    
    # Champs supplémentaires
    phone_number = models.CharField(
        _('Numéro de téléphone'),
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message=_('Format de numéro invalide. Ex: +33612345678')
        )]
    )
    date_of_birth = models.DateField(_('Date de naissance'), null=True, blank=True)
    country = models.CharField(_('Pays'), max_length=100, blank=True)
    city = models.CharField(_('Ville'), max_length=100, blank=True)
    address = models.TextField(_('Adresse complète'), blank=True)
    
    # Préférences - AJOUTÉ
    preferred_language = models.CharField(
        _('Langue préférée'),
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='fr'
    )
    timezone = models.CharField(_('Fuseau horaire'), max_length=50, default='UTC')
    preferred_currency = models.CharField(
        _('Devise préférée'), 
        max_length=5, 
        choices=CURRENCY_CHOICES,
        default='FCFA'
    )
    
    # Soldes multi-devises
    balance_fcfa = models.DecimalField(
        _('Solde FCFA'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    balance_eur = models.DecimalField(
        _('Solde EUR'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    balance_usd = models.DecimalField(
        _('Solde USD'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Vérifications
    is_verified = models.BooleanField(_('Email vérifié'), default=False)
    kyc_status = models.CharField(
        _('Statut KYC'),
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default='pending'
    )
    kyc_submitted_at = models.DateTimeField(_('KYC soumis le'), null=True, blank=True)
    kyc_reviewed_at = models.DateTimeField(_('KYC vérifié le'), null=True, blank=True)
    kyc_rejection_reason = models.TextField(_('Raison du rejet KYC'), blank=True)
    
    # Système de parrainage
    referral_code = models.CharField(
        _('Code de parrainage'),
        max_length=10,
        unique=True,
        blank=True,
        help_text=_('Code unique pour parrainer d\'autres utilisateurs')
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_users',
        verbose_name=_('Parrainé par')
    )
    
    # Sécurité
    last_login_ip = models.GenericIPAddressField(
        _('Dernière IP de connexion'), 
        null=True, 
        blank=True
    )
    failed_login_attempts = models.PositiveIntegerField(
        _('Tentatives de connexion échouées'), 
        default=0
    )
    account_locked_until = models.DateTimeField(
        _('Compte verrouillé jusqu\'au'), 
        null=True, 
        blank=True
    )
    
    # Métadonnées temporelles
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    last_activity = models.DateTimeField(_('Dernière activité'), null=True, blank=True)
    
    # Préférences de jeu
    auto_match = models.BooleanField(
        _('Matchmaking automatique'), 
        default=True,
        help_text=_('Rejoindre automatiquement les parties disponibles')
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['country']),
            models.Index(fields=['is_verified', 'kyc_status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance_fcfa__gte=0),
                name='positive_balance_fcfa'
            ),
            models.CheckConstraint(
                check=models.Q(balance_eur__gte=0),
                name='positive_balance_eur'
            ),
            models.CheckConstraint(
                check=models.Q(balance_usd__gte=0),
                name='positive_balance_usd'
            ),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def save(self, *args, **kwargs):
        """Override save pour validations personnalisées."""
        # Générer un code de parrainage unique
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        # Valider l'âge (18+ ans)
        if self.date_of_birth:
            age = self.calculate_age()
            if age < 18:
                raise ValidationError(
                    _('Vous devez avoir au moins 18 ans pour vous inscrire.')
                )
        
        # Normaliser l'email
        if self.email:
            self.email = self.email.lower().strip()
        
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Générer un code de parrainage unique."""
        while True:
            code = secrets.token_urlsafe(6).upper()[:8]
            prohibited = ['FUCK', 'SHIT', '0O0O', 'IIII']
            if not any(p in code for p in prohibited):
                if not User.objects.filter(referral_code=code).exists():
                    return code
    
    def calculate_age(self):
        """Calculer l'âge de l'utilisateur."""
        if not self.date_of_birth:
            return None
        
        today = timezone.now().date()
        return (today - self.date_of_birth).days // 365
    
    # CORRECTION: Ajouter la méthode get_balance manquante
    def get_balance(self, currency=None):
        """
        Obtenir le solde de l'utilisateur pour une devise donnée.
        
        Args:
            currency (str): Code de la devise ('FCFA', 'EUR', 'USD'). 
                          Si None, utilise la devise préférée.
        
        Returns:
            Decimal: Le solde dans la devise demandée
        """
        if currency is None:
            currency = self.preferred_currency
        
        currency = currency.upper()
        
        if currency == 'FCFA':
            return self.balance_fcfa
        elif currency == 'EUR':
            return self.balance_eur
        elif currency == 'USD':
            return self.balance_usd
        else:
            # Par défaut, retourner le solde FCFA
            return self.balance_fcfa
    
    def update_balance(self, currency, amount, operation='add'):
        """
        Mettre à jour le solde de l'utilisateur.
        
        Args:
            currency (str): Code de la devise
            amount (Decimal): Montant à ajouter/retirer
            operation (str): 'add', 'subtract', ou 'set'
        
        Returns:
            Decimal: Le nouveau solde
        """
        currency = currency.upper()
        
        # Déterminer le champ de balance
        if currency == 'FCFA':
            balance_field = 'balance_fcfa'
        elif currency == 'EUR':
            balance_field = 'balance_eur'
        elif currency == 'USD':
            balance_field = 'balance_usd'
        else:
            raise ValueError(f"Devise non supportée: {currency}")
        
        current_balance = getattr(self, balance_field)
        
        # Calculer le nouveau solde
        if operation == 'add':
            new_balance = current_balance + amount
        elif operation == 'subtract':
            new_balance = current_balance - amount
        elif operation == 'set':
            new_balance = amount
        else:
            raise ValueError(f"Opération non supportée: {operation}")
        
        # Vérifier que le solde ne devient pas négatif
        if new_balance < 0:
            raise ValueError("Le solde ne peut pas devenir négatif")
        
        # Mettre à jour le solde
        setattr(self, balance_field, new_balance)
        self.save(update_fields=[balance_field])
        
        return new_balance
    
    def has_sufficient_balance(self, currency, amount):
        """
        Vérifier si l'utilisateur a un solde suffisant.
        
        Args:
            currency (str): Code de la devise
            amount (Decimal): Montant à vérifier
        
        Returns:
            bool: True si le solde est suffisant
        """
        current_balance = self.get_balance(currency)
        return current_balance >= amount
    
    @property
    def full_name(self):
        """Nom complet de l'utilisateur."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        """Âge calculé."""
        return self.calculate_age()
    
    @property
    def total_balance_fcfa(self):
        """Calculer le solde total converti en FCFA."""
        # Taux de change approximatifs
        exchange_rates = {
            'FCFA': 1,
            'EUR': 655.957,
            'USD': 590.0,
        }
        
        total = (
            self.balance_fcfa + 
            (self.balance_eur * Decimal(str(exchange_rates['EUR']))) +
            (self.balance_usd * Decimal(str(exchange_rates['USD'])))
        )
        
        return total
    
    def reset_failed_login(self):
        """Réinitialiser les tentatives de connexion échouées."""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])

    def is_account_locked(self):  # ✅ AJOUTEZ CECI
        """Vérifie si le compte est actuellement verrouillé."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False

    def unlock_account(self):  # ✅ ET CECI
        """Déverrouiller le compte."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])

# Alias pour compatibilité
CustomUser = User


class UserProfile(models.Model):
    """Profil utilisateur étendu."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Utilisateur')
    )
    
    # Informations personnelles étendues
    bio = models.TextField(_('Biographie'), max_length=500, blank=True)
    avatar = models.ImageField(
        _('Avatar'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    
    # Vérifications
    is_verified = models.BooleanField(_('Profil vérifié'), default=False)
    verification_level = models.CharField(
        _('Niveau de vérification'),
        max_length=20,
        default='basic'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateur')
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    @property
    def age(self):
        """Âge de l'utilisateur."""
        return self.user.calculate_age()


# apps/accounts/models.py
# Remplacez votre classe UserPreferences par celle-ci

class UserPreferences(models.Model):
    """Préférences utilisateur."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('Utilisateur')
    )
    
    # Préférences d'interface
    language = models.CharField(
        _('Langue'),
        max_length=10,
        choices=User.LANGUAGE_CHOICES,  # Maintenant ça marche !
        default='fr'
    )
    currency = models.CharField(
        _('Devise'),
        max_length=5,
        choices=User.CURRENCY_CHOICES,  # Et ça aussi !
        default='FCFA'
    )
    timezone = models.CharField(_('Fuseau horaire'), max_length=50, default='UTC')
    theme = models.CharField(
        _('Thème'),
        max_length=20,
        choices=[('light', _('Clair')), ('dark', _('Sombre'))],
        default='light'
    )
    
    # Préférences de notification
    email_notifications = models.BooleanField(_('Notifications email'), default=True)
    push_notifications = models.BooleanField(_('Notifications push'), default=True)
    sms_notifications = models.BooleanField(_('Notifications SMS'), default=False)
    marketing_emails = models.BooleanField(_('Emails marketing'), default=False)
    
    # Préférences de jeu
    game_sounds = models.BooleanField(_('Sons du jeu'), default=True)
    auto_play = models.BooleanField(_('Jeu automatique'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = _('Préférences utilisateur')
        verbose_name_plural = _('Préférences utilisateur')
    
    def __str__(self):
        return f"Préférences de {self.user.username}"


class LoginHistory(models.Model):
    """Historique des connexions."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history',
        verbose_name=_('Utilisateur')
    )
    
    # Informations de connexion
    ip_address = models.GenericIPAddressField(_('Adresse IP'))
    user_agent = models.TextField(_('User Agent'), blank=True)
    device_type = models.CharField(_('Type d\'appareil'), max_length=50, blank=True)
    location = models.CharField(_('Localisation'), max_length=100, blank=True)
    success = models.BooleanField(_('Connexion réussie'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de connexion'), auto_now_add=True)
    
    class Meta:
        db_table = 'login_history'
        verbose_name = _('Historique de connexion')
        verbose_name_plural = _('Historiques de connexion')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class KYCDocument(models.Model):
    """Documents KYC uploadés par les utilisateurs."""
    
    DOCUMENT_TYPES = [
        ('id_card', _('Carte d\'identité')),
        ('passport', _('Passeport')),
        ('driving_license', _('Permis de conduire')),
        ('proof_of_address', _('Justificatif de domicile')),
        ('selfie', _('Selfie avec pièce d\'identité')),
        ('bank_statement', _('Relevé bancaire')),
        ('utility_bill', _('Facture de services publics')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('expired', _('Expiré')),
    ]
    
    def document_upload_path(instance, filename):
        """Chemin d'upload personnalisé pour les documents."""
        ext = filename.split('.')[-1]
        filename = f"{instance.user.id}_{instance.document_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        return f"kyc_documents/{timezone.now().year}/{timezone.now().month:02d}/{filename}"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='kyc_documents',
        verbose_name=_('Utilisateur')
    )
    document_type = models.CharField(
        _('Type de document'),
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    file = models.FileField(
        _('Fichier'),
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'],
                message=_('Seuls les fichiers JPG, PNG et PDF sont acceptés')
            )
        ],
        help_text=_('Formats acceptés: JPG, PNG, PDF (max 5MB)')
    )
    original_filename = models.CharField(_('Nom du fichier original'), max_length=255, blank=True)
    file_size = models.PositiveIntegerField(_('Taille du fichier (bytes)'), null=True, blank=True)
    
    # Vérification
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_kyc_documents',
        verbose_name=_('Vérifié par')
    )
    reviewed_at = models.DateTimeField(_('Vérifié le'), null=True, blank=True)
    rejection_reason = models.TextField(_('Raison du rejet'), blank=True)
    notes = models.TextField(_('Notes internes'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Uploadé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    expires_at = models.DateTimeField(_('Expire le'), null=True, blank=True)
    
    class Meta:
        db_table = 'kyc_documents'
        verbose_name = _('Document KYC')
        verbose_name_plural = _('Documents KYC')
        unique_together = ['user', 'document_type']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['document_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save pour capturer les métadonnées du fichier."""
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        
        # Définir une date d'expiration (2 ans)
        if not self.expires_at and self.status == 'approved':
            self.expires_at = timezone.now() + timedelta(days=730)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validation personnalisée."""
        if self.file and self.file.size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError(_('Le fichier ne peut pas dépasser 5MB'))
    
    @property
    def file_size_mb(self):
        """Taille du fichier en MB."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def is_expired(self):
        """Vérifier si le document est expiré."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class UserActivity(models.Model):
    """Historique des activités utilisateur."""
    
    ACTIVITY_TYPES = [
        ('login', _('Connexion')),
        ('logout', _('Déconnexion')),
        ('signup', _('Inscription')),
        ('email_verified', _('Email vérifié')),
        ('password_changed', _('Mot de passe changé')),
        ('profile_updated', _('Profil mis à jour')),
        ('kyc_submitted', _('KYC soumis')),
        ('kyc_status_changed', _('Statut KYC changé')),
        ('balance_updated', _('Solde mis à jour')),
        ('account_locked', _('Compte verrouillé')),
        ('account_unlocked', _('Compte déverrouillé')),
        ('game_created', _('Partie créée')),
        ('game_joined', _('Partie rejointe')),
        ('game_won', _('Partie gagnée')),
        ('game_lost', _('Partie perdue')),
        ('deposit_requested', _('Dépôt demandé')),
        ('deposit_completed', _('Dépôt complété')),
        ('withdrawal_requested', _('Retrait demandé')),
        ('withdrawal_completed', _('Retrait complété')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('Utilisateur')
    )
    activity_type = models.CharField(
        _('Type d\'activité'),
        max_length=30,
        choices=ACTIVITY_TYPES
    )
    description = models.CharField(_('Description'), max_length=500)
    
    # Contexte technique
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    session_id = models.CharField(_('ID de session'), max_length=255, blank=True)
    
    # Données supplémentaires
    metadata = models.JSONField(_('Métadonnées'), default=dict, blank=True)
    
    # Horodatage
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = _('Activité utilisateur')
        verbose_name_plural = _('Activités utilisateur')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


class UserSettings(models.Model):
    """Paramètres personnalisés de l'utilisateur."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name=_('Utilisateur')
    )
    
    # Préférences de notification
    email_notifications = models.BooleanField(
        _('Notifications par email'), 
        default=True,
        help_text=_('Recevoir des notifications par email')
    )
    sms_notifications = models.BooleanField(
        _('Notifications par SMS'), 
        default=False,
        help_text=_('Recevoir des notifications par SMS')
    )
    push_notifications = models.BooleanField(
        _('Notifications push'), 
        default=True,
        help_text=_('Recevoir des notifications push sur le navigateur')
    )
    marketing_emails = models.BooleanField(
        _('Emails marketing'), 
        default=False,
        help_text=_('Recevoir des offres promotionnelles')
    )
    login_notifications = models.BooleanField(
        _('Notifications de connexion'), 
        default=True,
        help_text=_('Être notifié des nouvelles connexions')
    )
    
    # Préférences de jeu
    auto_accept_games = models.BooleanField(
        _('Accepter automatiquement les parties'), 
        default=False,
        help_text=_('Accepter automatiquement les invitations de parties')
    )
    show_game_tips = models.BooleanField(
        _('Afficher les conseils de jeu'), 
        default=True,
        help_text=_('Afficher des conseils pendant le jeu')
    )
    sound_effects = models.BooleanField(
        _('Effets sonores'), 
        default=True,
        help_text=_('Activer les sons du jeu')
    )
    
    # Sécurité
    two_factor_enabled = models.BooleanField(
        _('Authentification à deux facteurs'), 
        default=False,
        help_text=_('Activer l\'authentification à deux facteurs')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    # Bannière KYC: moment où l'utilisateur a choisi de la masquer
    kyc_banner_dismissed_at = models.DateTimeField(_('KYC banner dismissed at'), null=True, blank=True)
    
    class Meta:
        db_table = 'user_settings'
        verbose_name = _('Paramètres utilisateur')
        verbose_name_plural = _('Paramètres utilisateur')
    
    def __str__(self):
        return f"Paramètres de {self.user.username}"
