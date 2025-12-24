# apps/accounts/serializers.py - VERSION COMPLÈTE ET CORRIGÉE

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import re
import secrets
from typing import Dict, Any

from .models import (
    User as CustomUser, 
    UserProfile, 
    UserPreferences, 
    LoginHistory,
    KYCDocument,
    UserActivity,
    UserSettings
)


# ===== FONCTIONS UTILITAIRES =====

def generate_referral_code():
    """Generate a unique referral code."""
    while True:
        code = secrets.token_urlsafe(6).upper()[:8]
        prohibited = ['FUCK', 'SHIT', '0O0O', 'IIII']
        if not any(p in code for p in prohibited):
            if not CustomUser.objects.filter(referral_code=code).exists():
                return code


def validate_password_strength(password):
    """Validate password strength."""
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    
    is_valid = (
        len(password) >= 8 and 
        has_upper and 
        has_lower and 
        has_digit
    )
    
    return {
        'is_valid': is_valid,
        'has_upper': has_upper,
        'has_lower': has_lower,
        'has_digit': has_digit,
        'length_ok': len(password) >= 8
    }


def get_client_ip(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def extract_client_info(request):
    """Extract client information from request."""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    device_type = 'desktop'
    if 'Mobile' in user_agent:
        device_type = 'mobile'
    elif 'Tablet' in user_agent:
        device_type = 'tablet'
    
    return {
        'ip_address': get_client_ip(request),
        'user_agent': user_agent,
        'device_type': device_type
    }


# ===== SERIALIZERS D'INSCRIPTION =====

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription des utilisateurs."""
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Minimum 8 caractères avec majuscules, minuscules et chiffres')
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Confirmez votre mot de passe')
    )
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Code de parrainage (optionnel)')
    )
    accept_terms = serializers.BooleanField(
        write_only=True,
        help_text=_('Acceptation des conditions d\'utilisation')
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'country', 'referral_code', 'accept_terms'
        ]
        extra_kwargs = {
            'username': {'help_text': _('Nom d\'utilisateur unique (3-30 caractères)')},
            'email': {'help_text': _('Adresse email valide')}
        }
    
    def validate_username(self, value):
        """Valider le nom d'utilisateur."""
        if len(value) < 3:
            raise serializers.ValidationError(
                _('Le nom d\'utilisateur doit contenir au moins 3 caractères.')
            )
        
        if len(value) > 30:
            raise serializers.ValidationError(
                _('Le nom d\'utilisateur ne peut pas dépasser 30 caractères.')
            )
        
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError(
                _('Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores.')
            )
        
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                _('Ce nom d\'utilisateur est déjà utilisé.')
            )
        
        return value
    
    def validate_email(self, value):
        """Valider l'email."""
        value = value.lower()
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _('Cette adresse email est déjà utilisée.')
            )
        
        return value
    
    def validate_password(self, value):
        """Valider le mot de passe."""
        try:
            validate_password(value)
        except ValidationError as e:
            # Inclure les messages du validateur Django
            raise serializers.ValidationError(list(e.messages))
        # Validation de la force du mot de passe avec message détaillé
        strength = validate_password_strength(value)
        if not strength['is_valid']:
            reasons = []
            if not strength['length_ok']:
                reasons.append(_('Au moins 8 caractères'))
            if not strength['has_upper']:
                reasons.append(_('Au moins une lettre majuscule'))
            if not strength['has_lower']:
                reasons.append(_('Au moins une lettre minuscule'))
            if not strength['has_digit']:
                reasons.append(_('Au moins un chiffre'))

            # Construire message lisible
            # ensure elements are strings (lazy gettext proxies may be returned)
            reasons_str = ', '.join([str(r) for r in reasons])
            message = _('Mot de passe trop faible : ') + reasons_str
            raise serializers.ValidationError(message)
        
        return value
    
    def validate_referral_code(self, value):
        """Valider le code de parrainage."""
        if value:
            try:
                referrer = CustomUser.objects.get(referral_code=value)
                if not referrer.is_active:
                    raise serializers.ValidationError(_('Code de parrainage invalide.'))
                return value
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(_('Code de parrainage introuvable.'))
        return value
    
    def validate_accept_terms(self, value):
        """Valider l'acceptation des conditions."""
        if not value:
            raise serializers.ValidationError(
                _('Vous devez accepter les conditions d\'utilisation.')
            )
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _('Les mots de passe ne correspondent pas.')
            })
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur avec profil."""
        validated_data.pop('password_confirm')
        referral_code = validated_data.pop('referral_code', None)
        validated_data.pop('accept_terms')
        
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            country=validated_data.get('country', '')
        )
        
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code)
                user.referred_by = referrer
                user.save()
            except CustomUser.DoesNotExist:
                pass
        
        # Créer les modèles liés avec gestion d'erreurs
        for model_class in [UserProfile, UserPreferences, UserSettings]:
            try:
                model_class.objects.create(user=user)
            except Exception:
                pass
        
        return user


class UserRegistrationResponseSerializer(serializers.ModelSerializer):
    """Serializer pour la réponse d'inscription."""
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'is_verified', 'referral_code', 'date_joined'
        ]
        read_only_fields = fields


# ===== SERIALIZERS D'AUTHENTIFICATION =====

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour l'obtention de tokens JWT."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre `username` optionnel au niveau du serializer pour
        # permettre aux clients d'envoyer `email` à la place.
        self.fields['username'] = serializers.CharField(
            label=_('Email ou nom d\'utilisateur'),
            required=False,
            help_text=_('Votre email ou nom d\'utilisateur')
        )
        self.fields['password'] = serializers.CharField(
            label=_('Mot de passe'),
            style={'input_type': 'password'},
            trim_whitespace=False
        )
        # Accepter explicitement un champ `email` (optionnel) pour l'API
        self.fields['email'] = serializers.EmailField(
            label=_('Email'),
            required=False,
            help_text=_('Adresse email (optionnel si vous enverrez username)')
        )
    
    @classmethod
    def get_token(cls, user):
        """Personnaliser les claims du token."""
        token = super().get_token(user)
        
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['username'] = user.username
        token['is_verified'] = getattr(user, 'is_verified', False)
        token['is_premium'] = getattr(user, 'is_premium', False)
        
        # Champs directement sur User
        token['first_name'] = user.first_name or ''
        token['last_name'] = user.last_name or ''
        
        # Avatar depuis le profil
        avatar_url = None
        if hasattr(user, 'profile') and user.profile and user.profile.avatar:
            avatar_url = user.profile.avatar.url
        token['avatar_url'] = avatar_url
        
        return token
    
    def validate(self, attrs):
        """Validation personnalisée avec support email/username et logging.

        Si l'utilisateur soumet son email dans le champ `username`, on
        tente de retrouver le `username` réel associé à cet email avant
        d'appeler la validation de `TokenObtainPairSerializer`.
        """

        # Supporter la connexion par email en remappant l'email vers le username
        # 1) Si un champ explicite `email` est fourni, tenter de résoudre le username
        email_val = attrs.get('email')
        if email_val and not attrs.get('username'):
            try:
                user_obj = CustomUser.objects.get(email=email_val.lower())
                attrs['username'] = user_obj.username
            except CustomUser.DoesNotExist:
                # laisser tel quel; l'auth échouera ensuite
                raise serializers.ValidationError(
                    _('Aucun compte actif n\'a été trouvé avec cet email.')
                )

        # 2) Si le champ `username` contient une adresse email, le mapper aussi
        username_val = attrs.get('username')
        if username_val and '@' in str(username_val):
            try:
                user_obj = CustomUser.objects.get(email=username_val.lower())
                attrs['username'] = user_obj.username
            except CustomUser.DoesNotExist:
                # on laisse attrs tel quel — l'authentification échouera ensuite
                raise serializers.ValidationError(
                    _('Aucun compte actif n\'a été trouvé avec cet identifiant.')
                )

        data = super().validate(attrs)

        request = self.context.get('request')
        if request and hasattr(self, 'user'):
            client_info = extract_client_info(request)

            try:
                LoginHistory.objects.create(
                    user=self.user,
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent'],
                    device_type=client_info['device_type'],
                    success=True
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur création LoginHistory: {e}")

        return data


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe."""
    
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Mot de passe actuel')
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Nouveau mot de passe')
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Confirmation du nouveau mot de passe')
    )
    
    def validate_old_password(self, value):
        """Valider l'ancien mot de passe."""
        user = self.context['request'].user
        
        if not user.check_password(value):
            raise serializers.ValidationError(_('Mot de passe actuel incorrect.'))
        
        return value
    
    def validate_new_password(self, value):
        """Valider le nouveau mot de passe."""
        try:
            validate_password(value, user=self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        strength = validate_password_strength(value)
        if not strength['is_valid']:
            raise serializers.ValidationError(
                _('Le mot de passe doit contenir au moins 8 caractères avec majuscules, minuscules et chiffres.')
            )
        
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _('Les mots de passe ne correspondent pas.')
            })
        
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': _('Le nouveau mot de passe doit être différent de l\'ancien.')
            })
        
        return attrs
    
    def save(self):
        """Sauvegarder le nouveau mot de passe."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer pour la demande de réinitialisation de mot de passe."""
    
    email = serializers.EmailField(
        help_text=_('Adresse email associée à votre compte')
    )
    
    def validate_email(self, value):
        """Valider que l'email existe."""
        value = value.lower()
        
        try:
            user = CustomUser.objects.get(email=value, is_active=True)
            self.user = user
            return value
        except CustomUser.DoesNotExist:
            # Ne pas révéler si l'email existe ou non pour la sécurité
            return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer pour la confirmation de réinitialisation de mot de passe."""
    
    uid = serializers.CharField(
        help_text=_('UID de l\'utilisateur (base64 encoded)')
    )
    token = serializers.CharField(
        help_text=_('Token de réinitialisation reçu par email')
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Nouveau mot de passe')
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Confirmation du nouveau mot de passe')
    )
    
    def validate_password(self, value):
        """Valider le nouveau mot de passe."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        strength = validate_password_strength(value)
        if not strength['is_valid']:
            raise serializers.ValidationError(
                _('Le mot de passe doit contenir au moins 8 caractères avec majuscules, minuscules et chiffres.')
            )
        
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _('Les mots de passe ne correspondent pas.')
            })
        
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification d'email."""
    # Nous utilisons l'UID encodé (base64) envoyé par email ainsi qu'un token
    uid = serializers.CharField(
        help_text=_('UID de l\'utilisateur encodé (base64)')
    )
    token = serializers.CharField(
        help_text=_('Token de vérification reçu par email')
    )


# ===== SERIALIZERS DE PROFIL =====

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur."""
    
    age = serializers.ReadOnlyField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'avatar_url',
            'is_verified', 'verification_level', 'age'
        ]
        read_only_fields = ['is_verified', 'verification_level']
    
    def get_avatar_url(self, obj):
        """Obtenir l'URL de l'avatar."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer pour les préférences utilisateur."""
    
    class Meta:
        model = UserPreferences
        fields = [
            'language', 'currency', 'timezone', 'theme',
            'email_notifications', 'push_notifications', 'sms_notifications',
            'marketing_emails', 'game_sounds', 'auto_play'
        ]


class UserBalanceSerializer(serializers.ModelSerializer):
    """Serializer pour les soldes utilisateur."""
    
    total_balance_fcfa = serializers.SerializerMethodField()
    balances = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'balance_fcfa', 'balance_eur', 'balance_usd', 
            'preferred_currency', 'total_balance_fcfa', 'balances'
        ]
        read_only_fields = ['balance_fcfa', 'balance_eur', 'balance_usd']
    
    def get_total_balance_fcfa(self, obj):
        """Calculer le solde total converti en FCFA."""
        exchange_rates = {
            'EUR': 655.957,
            'USD': 590.0,
        }
        
        total = (
            obj.balance_fcfa + 
            (obj.balance_eur * Decimal(str(exchange_rates['EUR']))) +
            (obj.balance_usd * Decimal(str(exchange_rates['USD'])))
        )
        
        return total
    
    def get_balances(self, obj):
        """Retourner tous les soldes avec formatage."""
        return {
            'fcfa': {
                'amount': obj.balance_fcfa,
                'formatted': f"{obj.balance_fcfa:,.2f} FCFA",
                'currency': 'FCFA'
            },
            'eur': {
                'amount': obj.balance_eur,
                'formatted': f"€{obj.balance_eur:,.2f}",
                'currency': 'EUR'
            },
            'usd': {
                'amount': obj.balance_usd,
                'formatted': f"${obj.balance_usd:,.2f}",
                'currency': 'USD'
            }
        }


class UserSerializer(serializers.ModelSerializer):
    """Serializer complet pour l'utilisateur."""
    
    profile = UserProfileSerializer(read_only=True)
    preferences = UserPreferencesSerializer(read_only=True)
    referral_stats = serializers.SerializerMethodField()
    account_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            # ✅ AJOUTER CES CHAMPS :
            'phone_number', 'date_of_birth', 'country', 'city',
            'is_active', 'is_verified', 'date_joined', 'last_login', 'referral_code', 
            'profile', 'preferences', 'referral_stats', 'account_stats',
            # Soldes
            'balance_fcfa', 'balance_eur', 'balance_usd', 'preferred_currency'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'referral_code',
            'balance_fcfa', 'balance_eur', 'balance_usd'
        ]
    
    def get_referral_stats(self, obj):
        """Obtenir les statistiques de parrainage."""
        return {
            'total_referrals': obj.referred_users.filter(is_active=True).count(),
            'active_referrals': obj.referred_users.filter(
                is_active=True,
                last_login__isnull=False
            ).count(),
            'referral_code': obj.referral_code
        }
    
    def get_account_stats(self, obj):
        """Obtenir les statistiques du compte."""
        return {
            'total_games': 0,
            'total_wins': 0,
            'total_losses': 0,
            'win_rate': 0.0,
            'total_earnings': Decimal('0.00'),
            'current_balance': obj.balance_fcfa
        }


# ===== SERIALIZERS DE STATISTIQUES =====

class UserStatisticsSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques utilisateur détaillées."""
    
    # Statistiques générales
    account_age_days = serializers.SerializerMethodField()
    total_logins = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    # Statistiques de vérification
    verification_status = serializers.SerializerMethodField()
    kyc_completion_percentage = serializers.SerializerMethodField()
    
    # Statistiques financières
    total_balance_fcfa = serializers.SerializerMethodField()
    balance_summary = serializers.SerializerMethodField()
    
    # Statistiques de jeu (placeholders)
    game_statistics = serializers.SerializerMethodField()
    
    # Statistiques de parrainage
    referral_statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'date_joined', 'last_login', 'is_active',
            'account_age_days', 'total_logins', 'last_activity',
            'verification_status', 'kyc_completion_percentage',
            'total_balance_fcfa', 'balance_summary',
            'game_statistics', 'referral_statistics'
        ]
        read_only_fields = fields
    
    def get_account_age_days(self, obj):
        """Calculer l'âge du compte en jours."""
        return (timezone.now().date() - obj.date_joined.date()).days
    
    def get_total_logins(self, obj):
        """Obtenir le nombre total de connexions."""
        return obj.login_history.filter(success=True).count()
    
    def get_last_activity(self, obj):
        """Obtenir la dernière activité."""
        last_login = obj.login_history.filter(success=True).order_by('-created_at').first()
        if last_login:
            return {
                'timestamp': last_login.created_at,
                'ip_address': last_login.ip_address,
                'device_type': last_login.device_type,
                'days_ago': (timezone.now().date() - last_login.created_at.date()).days
            }
        return None
    
    def get_verification_status(self, obj):
        """Obtenir le statut de vérification complet."""
        return {
            'email_verified': obj.is_verified,
            'phone_verified': hasattr(obj, 'profile') and obj.profile.is_verified,
            'kyc_status': obj.kyc_status,
            'kyc_submitted': obj.kyc_submitted_at is not None,
            'kyc_reviewed': obj.kyc_reviewed_at is not None
        }
    
    def get_kyc_completion_percentage(self, obj):
        """Calculer le pourcentage de completion KYC."""
        required_documents = ['id_card', 'proof_of_address', 'selfie']
        
        if not hasattr(obj, 'kyc_documents'):
            return 0
        
        approved_docs = obj.kyc_documents.filter(
            document_type__in=required_documents,
            status='approved'
        ).count()
        
        return int((approved_docs / len(required_documents)) * 100)
    
    def get_total_balance_fcfa(self, obj):
        """Calculer le solde total en FCFA."""
        exchange_rates = {
            'EUR': 655.957,
            'USD': 590.0,
        }
        
        total = (
            obj.balance_fcfa + 
            (obj.balance_eur * Decimal(str(exchange_rates['EUR']))) +
            (obj.balance_usd * Decimal(str(exchange_rates['USD'])))
        )
        
        return total
    
    def get_balance_summary(self, obj):
        """Résumé des soldes par devise."""
        return {
            'fcfa': obj.balance_fcfa,
            'eur': obj.balance_eur,
            'usd': obj.balance_usd,
            'preferred_currency': obj.preferred_currency,
        }
    
    def get_game_statistics(self, obj):
        """Statistiques de jeu (placeholder)."""
        return {
            'total_games': 0,
            'games_won': 0,
            'games_lost': 0,
            'win_rate': 0.0,
            'total_earnings': Decimal('0.00'),
            'favorite_game_mode': None,
            'longest_winning_streak': 0,
            'average_game_duration': 0,
            'total_time_played': 0
        }
    
    def get_referral_statistics(self, obj):
        """Statistiques de parrainage."""
        total_referrals = obj.referred_users.filter(is_active=True).count()
        active_referrals = obj.referred_users.filter(
            is_active=True,
            last_login__isnull=False
        ).count()
        
        referral_earnings = Decimal('0.00')
        
        return {
            'referral_code': obj.referral_code,
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'referral_earnings': referral_earnings,
            'referred_by': obj.referred_by.username if obj.referred_by else None
        }


# ===== SERIALIZERS KYC =====

class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents KYC."""
    
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = KYCDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'file', 'file_url',
            'original_filename', 'file_size', 'file_size_mb', 'status', 
            'status_display', 'reviewed_by', 'reviewed_at', 'rejection_reason',
            'created_at', 'updated_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_size', 'reviewed_by', 
            'reviewed_at', 'created_at', 'updated_at', 'expires_at'
        ]
    
    def get_file_url(self, obj):
        """Obtenir l'URL sécurisée du fichier."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def validate_file(self, value):
        """Valider le fichier uploadé."""
        if not value:
            raise serializers.ValidationError(_('Un fichier est requis.'))
        
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(_('Le fichier ne peut pas dépasser 5MB.'))
        
        allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']
        file_extension = value.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                _('Seuls les fichiers JPG, PNG et PDF sont acceptés.')
            )
        
        return value
    
    def create(self, validated_data):
        """Créer un nouveau document KYC."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class KYCStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut KYC global."""
    
    documents = KYCDocumentSerializer(source='kyc_documents', many=True, read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    next_steps = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'kyc_status', 'kyc_submitted_at', 'kyc_reviewed_at', 
            'kyc_rejection_reason', 'documents', 'completion_percentage', 
            'next_steps'
        ]
        read_only_fields = fields
    
    def get_completion_percentage(self, obj):
        """Calculer le pourcentage de completion du KYC."""
        required_documents = ['id_card', 'proof_of_address', 'selfie']
        approved_docs = obj.kyc_documents.filter(
            document_type__in=required_documents,
            status='approved'
        ).count()
        
        return int((approved_docs / len(required_documents)) * 100)
    
    def get_next_steps(self, obj):
        """Obtenir les prochaines étapes pour compléter le KYC."""
        required_documents = {
            'id_card': _('Pièce d\'identité'),
            'proof_of_address': _('Justificatif de domicile'),
            'selfie': _('Selfie avec pièce d\'identité')
        }
        
        submitted_types = set(
            obj.kyc_documents.filter(
                status__in=['pending', 'approved', 'under_review']
            ).values_list('document_type', flat=True)
        )
        
        rejected_types = set(
            obj.kyc_documents.filter(status='rejected').values_list('document_type', flat=True)
        )
        
        missing_documents = []
        
        # Ajouter les documents manquants
        for doc_type, doc_name in required_documents.items():
            if doc_type not in submitted_types:
                missing_documents.append({
                    'type': doc_type,
                    'name': doc_name,
                    'status': 'missing'
                })
        
        # Ajouter les documents rejetés
        for doc_type in rejected_types:
            if doc_type in required_documents:
                missing_documents.append({
                    'type': doc_type,
                    'name': required_documents[doc_type],
                    'status': 'rejected'
                })
        
        return missing_documents


# ===== SERIALIZERS DE SETTINGS =====

class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres utilisateur."""
    
    class Meta:
        model = UserSettings
        fields = [
            'email_notifications', 'sms_notifications', 'push_notifications',
            'marketing_emails', 'login_notifications', 'auto_accept_games',
            'show_game_tips', 'sound_effects', 'two_factor_enabled',
            # Server-side flag: moment où l'utilisateur a désactivé/masqué la bannière KYC
            'kyc_banner_dismissed_at'
        ]
    
    def update(self, instance, validated_data):
        """Mise à jour des paramètres avec logging."""
        old_settings = {field: getattr(instance, field) for field in self.Meta.fields}
        
        updated_instance = super().update(instance, validated_data)
        
        changes = {}
        for field, new_value in validated_data.items():
            old_value = old_settings.get(field)
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        
        if changes:
            UserActivity.objects.create(
                user=instance.user,
                activity_type='profile_updated',
                description=f"Paramètres mis à jour: {', '.join(changes.keys())}",
                metadata={'settings_changes': changes}
            )
        
        return updated_instance


class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer spécialisé pour les paramètres de notification."""
    
    class Meta:
        model = UserSettings
        fields = [
            'email_notifications', 'sms_notifications', 'push_notifications',
            'marketing_emails', 'login_notifications'
        ]
    
    def validate(self, attrs):
        """Validation des paramètres de notification."""
        notification_fields = [
            'email_notifications', 'sms_notifications', 'push_notifications'
        ]
        
        if self.instance:
            current_values = {
                field: getattr(self.instance, field) for field in notification_fields
            }
            for field, value in attrs.items():
                if field in notification_fields:
                    current_values[field] = value
        else:
            current_values = {
                field: attrs.get(field, False) for field in notification_fields
            }
        
        if not any(current_values.values()):
            raise serializers.ValidationError(
                _('Au moins un type de notification doit être activé.')
            )
        
        return attrs


class UserGameSettingsSerializer(serializers.ModelSerializer):
    """Serializer spécialisé pour les paramètres de jeu."""
    
    class Meta:
        model = UserSettings
        fields = [
            'auto_accept_games', 'show_game_tips', 'sound_effects'
        ]


class UserSecuritySettingsSerializer(serializers.ModelSerializer):
    """Serializer spécialisé pour les paramètres de sécurité."""
    
    two_factor_status = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSettings
        fields = [
            'two_factor_enabled', 'login_notifications', 'two_factor_status'
        ]
        read_only_fields = ['two_factor_status']
    
    def get_two_factor_status(self, obj):
        """Obtenir le statut détaillé de l'authentification à deux facteurs."""
        return {
            'enabled': obj.two_factor_enabled,
            'setup_completed': obj.two_factor_enabled,
            'backup_codes_generated': False,
            'last_used': None
        }


# ===== SERIALIZERS D'ACTIVITÉ =====

class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer pour les activités utilisateur."""
    
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'activity_type', 'activity_type_display', 'description',
            'ip_address', 'user_agent', 'session_id', 'metadata',
            'created_at', 'time_ago'
        ]
        read_only_fields = fields
    
    def get_time_ago(self, obj):
        """Calculer le temps écoulé."""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "à l'instant"


class CreateUserActivitySerializer(serializers.ModelSerializer):
    """Serializer pour créer de nouvelles activités utilisateur."""
    
    class Meta:
        model = UserActivity
        fields = [
            'activity_type', 'description', 'metadata'
        ]
    
    def create(self, validated_data):
        """Créer une nouvelle activité avec contexte automatique."""
        request = self.context.get('request')
        
        if request:
            client_info = extract_client_info(request)
            validated_data.update({
                'user': request.user,
                'ip_address': client_info.get('ip_address'),
                'user_agent': client_info.get('user_agent'),
                'session_id': request.session.session_key
            })
        
        return super().create(validated_data)


class UserActivityFilterSerializer(serializers.Serializer):
    """Serializer pour filtrer les activités utilisateur."""
    
    activity_types = serializers.MultipleChoiceField(
        choices=UserActivity.ACTIVITY_TYPES,
        required=False,
        help_text=_('Types d\'activité à inclure')
    )
    date_from = serializers.DateTimeField(
        required=False,
        help_text=_('Date de début')
    )
    date_to = serializers.DateTimeField(
        required=False,
        help_text=_('Date de fin')
    )
    ip_address = serializers.CharField(
        required=False,
        max_length=45,
        help_text=_('Filtrer par adresse IP')
    )
    limit = serializers.IntegerField(
        default=50,
        min_value=1,
        max_value=1000,
        help_text=_('Nombre maximum de résultats')
    )
    
    def validate_ip_address(self, value):
        """Valider l'adresse IP."""
        if value:
            import ipaddress
            try:
                ipaddress.ip_address(value)
            except ValueError:
                raise serializers.ValidationError(_('Adresse IP invalide.'))
        return value
    
    def validate(self, attrs):
        """Validation des filtres."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                'date_from': _('La date de début doit être antérieure à la date de fin.')
            })
        
        return attrs


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer pour l'historique de connexion."""
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'ip_address', 'user_agent', 'device_type',
            'location', 'success', 'created_at'
        ]
        read_only_fields = fields


# ===== SERIALIZERS PUBLICS =====

class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer public pour les utilisateurs."""
    
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'display_name', 'avatar_url', 'date_joined']
    
    def get_avatar_url(self, obj):
        """Obtenir l'URL de l'avatar."""
        if hasattr(obj, 'profile') and obj.profile and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
            return obj.profile.avatar.url
        return None
    
    def get_display_name(self, obj):
        """Obtenir le nom d'affichage."""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        return obj.username


# ===== SERIALIZERS ADMIN =====

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer pour l'administration des utilisateurs."""
    
    profile = UserProfileSerializer(read_only=True)
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'profile', 'last_activity'
        ]
    
    def get_last_activity(self, obj):
        """Obtenir la dernière activité."""
        last_login_history = obj.login_history.order_by('-created_at').first()
        if last_login_history:
            return {
                'timestamp': last_login_history.created_at,
                'ip_address': last_login_history.ip_address,
                'device_type': last_login_history.device_type
            }
        return None


# ===== SERIALIZERS DE BALANCE =====

class UserBalanceUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour des soldes (usage admin/interne)."""
    
    currency = serializers.ChoiceField(
        choices=['FCFA', 'EUR', 'USD'],
        help_text=_('Devise à modifier')
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_('Montant à ajouter/retirer')
    )
    operation = serializers.ChoiceField(
        choices=['add', 'subtract', 'set'],
        default='add',
        help_text=_('Type d\'opération: add (ajouter), subtract (retirer), set (définir)')
    )
    reason = serializers.CharField(
        max_length=255,
        help_text=_('Raison de la modification')
    )
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value < 0:
            raise serializers.ValidationError(_('Le montant ne peut pas être négatif.'))
        
        if value > Decimal('1000000'):
            raise serializers.ValidationError(_('Le montant ne peut pas dépasser 1,000,000.'))
        
        return value
    
    def update_balance(self, user, validated_data):
        """Mettre à jour le solde de l'utilisateur."""
        currency = validated_data['currency'].lower()
        amount = validated_data['amount']
        operation = validated_data['operation']
        
        balance_field = f'balance_{currency}'
        current_balance = getattr(user, balance_field)
        
        if operation == 'add':
            new_balance = current_balance + amount
        elif operation == 'subtract':
            new_balance = current_balance - amount
        elif operation == 'set':
            new_balance = amount
        
        if new_balance < 0:
            raise serializers.ValidationError(_('Le solde ne peut pas devenir négatif.'))
        
        setattr(user, balance_field, new_balance)
        user.save(update_fields=[balance_field])
        
        UserActivity.objects.create(
            user=user,
            activity_type='balance_updated',
            description=f"Solde {currency.upper()} modifié: {operation} {amount}",
            metadata={
                'currency': currency.upper(),
                'amount': str(amount),
                'operation': operation,
                'old_balance': str(current_balance),
                'new_balance': str(new_balance),
                'reason': validated_data['reason']
            }
        )
        
        return user
