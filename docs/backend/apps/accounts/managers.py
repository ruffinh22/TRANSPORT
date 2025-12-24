# apps/accounts/managers.py
# =========================

from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class UserManager(BaseUserManager):
    """Manager personnalisé pour les utilisateurs avec méthodes avancées."""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Créer un utilisateur standard avec validations."""
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        if not username:
            raise ValueError(_('Le nom d\'utilisateur est obligatoire'))
            
        # Normaliser l'email
        email = self.normalize_email(email)
        
        # Créer l'utilisateur
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Créer les paramètres par défaut
        from .models import UserSettings
        UserSettings.objects.get_or_create(user=user)
        
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Créer un superutilisateur avec tous les privilèges."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('kyc_status', 'approved')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Les superutilisateurs doivent avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Les superutilisateurs doivent avoir is_superuser=True.'))
        
        return self.create_user(username, email, password, **extra_fields)
    
    def get_by_referral_code(self, referral_code):
        """Obtenir un utilisateur par son code de parrainage."""
        try:
            return self.get(referral_code=referral_code)
        except self.model.DoesNotExist:
            return None
    
    def get_by_email_or_username(self, identifier):
        """Obtenir un utilisateur par email ou username."""
        if '@' in identifier:
            return self.filter(email=identifier.lower()).first()
        else:
            return self.filter(username=identifier).first()
    
    # Requêtes pour les utilisateurs par statut
    def active_users(self):
        """Utilisateurs actifs."""
        return self.filter(is_active=True)
    
    def verified_users(self):
        """Utilisateurs avec email vérifié."""
        return self.filter(is_verified=True)
    
    def kyc_approved_users(self):
        """Utilisateurs avec KYC approuvé."""
        return self.filter(kyc_status='approved')
    
    def unverified_users(self):
        """Utilisateurs non vérifiés."""
        return self.filter(is_verified=False)
    
    def pending_kyc_users(self):
        """Utilisateurs avec KYC en attente."""
        return self.filter(kyc_status__in=['pending', 'under_review'])
    
    # Requêtes pour les statistiques
    def new_users_today(self):
        """Nouveaux utilisateurs aujourd'hui."""
        today = timezone.now().date()
        return self.filter(created_at__date=today)
    
    def new_users_this_week(self):
        """Nouveaux utilisateurs cette semaine."""
        week_ago = timezone.now() - timedelta(days=7)
        return self.filter(created_at__gte=week_ago)
    
    def new_users_this_month(self):
        """Nouveaux utilisateurs ce mois."""
        month_ago = timezone.now() - timedelta(days=30)
        return self.filter(created_at__gte=month_ago)
    
    def active_users_last_30_days(self):
        """Utilisateurs actifs dans les 30 derniers jours."""
        cutoff = timezone.now() - timedelta(days=30)
        return self.filter(
            models.Q(last_activity__gte=cutoff) | 
            models.Q(last_login__gte=cutoff)
        )
    
    # Requêtes pour les soldes
    def users_with_balance(self, currency='FCFA', min_amount=0):
        """Utilisateurs avec un solde minimum dans une devise."""
        balance_field = f'balance_{currency.lower()}'
        filter_kwargs = {f'{balance_field}__gte': Decimal(str(min_amount))}
        return self.filter(**filter_kwargs)
    
    def top_balance_users(self, currency='FCFA', limit=10):
        """Top utilisateurs par solde."""
        balance_field = f'balance_{currency.lower()}'
        return self.order_by(f'-{balance_field}')[:limit]
    
    # Requêtes pour le parrainage
    def top_referrers(self, limit=10):
        """Top parrains par nombre de référés."""
        return self.annotate(
            referral_count=models.Count('referred_users')
        ).filter(
            referral_count__gt=0
        ).order_by('-referral_count')[:limit]
    
    def users_by_country(self):
        """Répartition des utilisateurs par pays."""
        return self.values('country').annotate(
            count=models.Count('id')
        ).order_by('-count')
    
    # Requêtes de sécurité
    def locked_accounts(self):
        """Comptes actuellement verrouillés."""
        return self.filter(
            account_locked_until__gt=timezone.now()
        )
    
    def suspicious_accounts(self):
        """Comptes potentiellement suspects."""
        return self.filter(
            failed_login_attempts__gte=3
        ).exclude(
            account_locked_until__gt=timezone.now()
        )


class KYCDocumentManager(models.Manager):
    """Manager pour les documents KYC avec requêtes spécialisées."""
    
    def pending_documents(self):
        """Documents en attente de validation."""
        return self.filter(status='pending')
    
    def approved_documents(self):
        """Documents approuvés."""
        return self.filter(status='approved')
    
    def rejected_documents(self):
        """Documents rejetés."""
        return self.filter(status='rejected')
    
    def expired_documents(self):
        """Documents expirés."""
        return self.filter(
            expires_at__lt=timezone.now(),
            status='approved'
        )
    
    def documents_expiring_soon(self, days=30):
        """Documents qui expirent bientôt."""
        cutoff_date = timezone.now() + timedelta(days=days)
        return self.filter(
            expires_at__lte=cutoff_date,
            expires_at__gt=timezone.now(),
            status='approved'
        )
    
    def documents_by_type(self, document_type):
        """Documents par type."""
        return self.filter(document_type=document_type)
    
    def user_documents(self, user):
        """Tous les documents d'un utilisateur."""
        return self.filter(user=user).order_by('-created_at')
    
    def complete_kyc_users(self):
        """Utilisateurs avec KYC complet (tous les documents requis)."""
        required_docs = ['id_card', 'proof_of_address', 'selfie']
        
        # Sous-requête pour trouver les utilisateurs avec tous les docs requis
        complete_users = []
        for user in self.values_list('user', flat=True).distinct():
            user_docs = self.filter(user=user, status='approved')
            user_doc_types = user_docs.values_list('document_type', flat=True)
            
            if all(doc_type in user_doc_types for doc_type in required_docs):
                complete_users.append(user)
        
        return self.filter(user__in=complete_users)
    
    def documents_needing_review(self):
        """Documents nécessitant une révision urgente."""
        # Documents en attente depuis plus de 48h
        cutoff = timezone.now() - timedelta(hours=48)
        return self.filter(
            status='pending',
            created_at__lt=cutoff
        )


class UserActivityManager(models.Manager):
    """Manager pour les activités utilisateur avec requêtes d'analyse."""
    
    def activities_today(self):
        """Activités d'aujourd'hui."""
        today = timezone.now().date()
        return self.filter(created_at__date=today)
    
    def activities_this_week(self):
        """Activités de cette semaine."""
        week_ago = timezone.now() - timedelta(days=7)
        return self.filter(created_at__gte=week_ago)
    
    def login_activities(self):
        """Activités de connexion."""
        return self.filter(activity_type='login')
    
    def recent_logins(self, hours=24):
        """Connexions récentes."""
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.filter(
            activity_type='login',
            created_at__gte=cutoff
        )
    
    def user_activities(self, user):
        """Activités d'un utilisateur spécifique."""
        return self.filter(user=user).order_by('-created_at')
    
    def activities_by_type(self, activity_type):
        """Activités par type."""
        return self.filter(activity_type=activity_type)
    
    def suspicious_activities(self):
        """Activités potentiellement suspectes."""
        return self.filter(
            activity_type__in=['login', 'password_changed', 'account_locked']
        ).order_by('-created_at')
    
    def activities_from_ip(self, ip_address):
        """Activités depuis une IP spécifique."""
        return self.filter(ip_address=ip_address)
    
    def failed_login_attempts(self, hours=24):
        """Tentatives de connexion échouées récentes."""
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.filter(
            activity_type='login_failed',
            created_at__gte=cutoff
        )
    
    def activities_summary(self):
        """Résumé des activités par type."""
        return self.values('activity_type').annotate(
            count=models.Count('id')
        ).order_by('-count')
    
    def cleanup_old_activities(self, days=90):
        """Nettoyer les anciennes activités."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = self.filter(created_at__lt=cutoff_date).delete()
        return deleted_count


class UserSettingsManager(models.Manager):
    """Manager pour les paramètres utilisateur."""
    
    def users_with_notifications_enabled(self):
        """Utilisateurs avec notifications activées."""
        return self.filter(email_notifications=True)
    
    def users_with_sms_enabled(self):
        """Utilisateurs avec SMS activés."""
        return self.filter(sms_notifications=True)
    
    def users_with_2fa_enabled(self):
        """Utilisateurs avec 2FA activé."""
        return self.filter(two_factor_enabled=True)
    
    def users_with_auto_accept(self):
        """Utilisateurs avec acceptation automatique activée."""
        return self.filter(auto_accept_games=True)
    
    def notification_preferences_stats(self):
        """Statistiques des préférences de notification."""
        return {
            'email_notifications': self.filter(email_notifications=True).count(),
            'sms_notifications': self.filter(sms_notifications=True).count(),
            'push_notifications': self.filter(push_notifications=True).count(),
            'marketing_emails': self.filter(marketing_emails=True).count(),
            'two_factor_enabled': self.filter(two_factor_enabled=True).count(),
            'total_users': self.count()
        }
    
    def create_default_settings(self, user):
        """Créer les paramètres par défaut pour un utilisateur."""
        return self.create(
            user=user,
            email_notifications=True,
            sms_notifications=False,
            push_notifications=True,
            marketing_emails=False,
            auto_accept_games=False,
            show_game_tips=True,
            sound_effects=True,
            two_factor_enabled=False,
            login_notifications=True
        )
