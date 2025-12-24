# apps/accounts/permissions.py
# ============================

from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from decimal import Decimal


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission pour permettre seulement au propriétaire de modifier ses propres données."""
    
    message = _('Vous ne pouvez modifier que vos propres informations.')
    
    def has_permission(self, request, view):
        """Vérifier les permissions au niveau de la vue."""
        # Les permissions de lecture sont autorisées pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Les permissions d'écriture nécessitent une authentification
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Vérifier les permissions au niveau de l'objet."""
        # Permissions de lecture pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture seulement pour le propriétaire
        return obj == request.user or (hasattr(obj, 'user') and obj.user == request.user)


class IsVerifiedUser(permissions.BasePermission):
    """Permission pour les utilisateurs avec email vérifié uniquement."""
    
    message = _('Vous devez vérifier votre adresse email pour accéder à cette ressource.')
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur est connecté et vérifié."""
        # En mode DEBUG, bypasser la vérification pour faciliter les tests locaux
        if getattr(settings, 'DEBUG', False):
            return True

        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )


class IsKYCApproved(permissions.BasePermission):
    """Permission pour les utilisateurs avec KYC approuvé uniquement."""
    
    message = _('Votre vérification KYC doit être approuvée pour accéder à cette ressource.')
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur a un KYC approuvé."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.kyc_status == 'approved'
        )


class IsKYCPendingOrApproved(permissions.BasePermission):
    """Permission pour les utilisateurs avec KYC en cours ou approuvé."""
    
    message = _('Vous devez soumettre vos documents KYC pour accéder à cette ressource.')
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur a au moins soumis son KYC."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.kyc_status in ['under_review', 'approved']
        )


class CanWithdraw(permissions.BasePermission):
    """Permission complexe pour les retraits avec vérifications multiples."""
    
    def has_permission(self, request, view):
        """Vérifier toutes les conditions pour effectuer un retrait."""
        if not (request.user and request.user.is_authenticated):
            self.message = _('Authentification requise')
            return False
        
        user = request.user
        
        # Vérification de l'email
        if not user.is_verified:
            self.message = _('Vous devez vérifier votre adresse email')
            return False
        
        # Vérification KYC
        if user.kyc_status != 'approved':
            self.message = _('Votre vérification KYC doit être approuvée')
            return False
        
        # Vérification du verrouillage du compte
        if user.is_account_locked():
            remaining_time = user.account_locked_until - timezone.now()
            minutes = int(remaining_time.total_seconds() / 60)
            self.message = _('Compte temporairement verrouillé. Réessayez dans {} minutes.').format(minutes)
            return False
        
        # Vérification de l'âge du compte (minimum 24h)
        account_age = timezone.now() - user.created_at
        if account_age.total_seconds() < 24 * 3600:
            self.message = _('Votre compte doit exister depuis au moins 24 heures')
            return False
        
        return True


class CanDeposit(permissions.BasePermission):
    """Permission pour les dépôts avec vérifications de base."""
    
    def has_permission(self, request, view):
        """Vérifier les conditions pour effectuer un dépôt."""
        # En mode DEBUG, autoriser les dépôts pour faciliter les tests locaux
        if getattr(settings, 'DEBUG', False):
            return True

        if not (request.user and request.user.is_authenticated):
            self.message = _('Authentification requise')
            return False
        
        user = request.user
        
        # Vérification de l'email
        if not user.is_verified:
            self.message = _('Vous devez vérifier votre adresse email')
            return False
        
        # Vérification du verrouillage du compte
        if user.is_account_locked():
            self.message = _('Compte temporairement verrouillé')
            return False
        
        return True


class CanPlayGames(permissions.BasePermission):
    """Permission pour jouer aux jeux avec mises."""
    
    def has_permission(self, request, view):
        """Vérifier les conditions pour jouer."""
        if not (request.user and request.user.is_authenticated):
            self.message = _('Authentification requise')
            return False
        
        user = request.user
        
        # Vérification de l'email
        if not user.is_verified:
            self.message = _('Vous devez vérifier votre adresse email pour jouer')
            return False
        
        # Vérification du verrouillage du compte
        if user.is_account_locked():
            self.message = _('Compte temporairement verrouillé')
            return False
        
        # Vérification de l'âge (18+)
        if user.age and user.age < 18:
            self.message = _('Vous devez avoir au moins 18 ans')
            return False
        
        return True


class HasSufficientBalance(permissions.BasePermission):
    """Permission pour vérifier le solde suffisant."""
    
    def __init__(self, required_amount=None, currency='FCFA'):
        """Initialiser avec le montant requis."""
        self.required_amount = required_amount
        self.currency = currency
    
    def has_permission(self, request, view):
        """Vérifier le solde de l'utilisateur."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        if self.required_amount is None:
            # Si pas de montant spécifié, récupérer depuis la requête
            amount = request.data.get('amount') or request.query_params.get('amount')
            if not amount:
                return True  # Laisser la vue gérer la validation
            self.required_amount = Decimal(str(amount))
        
        user_balance = request.user.get_balance(self.currency)
        
        if user_balance < self.required_amount:
            self.message = _('Solde insuffisant. Solde actuel: {} {}').format(
                user_balance, self.currency
            )
            return False
        
        return True


class IsAccountNotLocked(permissions.BasePermission):
    """Permission pour vérifier que le compte n'est pas verrouillé."""
    
    def has_permission(self, request, view):
        """Vérifier que le compte n'est pas verrouillé."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_account_locked():
            remaining_time = request.user.account_locked_until - timezone.now()
            minutes = int(remaining_time.total_seconds() / 60)
            self.message = _('Compte verrouillé pendant {} minutes.').format(minutes)
            return False
        
        return True


class IsActiveUser(permissions.BasePermission):
    """Permission pour vérifier que l'utilisateur est actif."""
    
    message = _('Votre compte a été désactivé. Contactez le support.')
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur est actif."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class IsStaffOrOwner(permissions.BasePermission):
    """Permission pour le staff ou le propriétaire."""
    
    def has_permission(self, request, view):
        """Vérifier les permissions au niveau de la vue."""
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )
    
    def has_object_permission(self, request, view, obj):
        """Vérifier les permissions au niveau de l'objet."""
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Le propriétaire peut accéder à ses propres objets
        return obj == request.user or (hasattr(obj, 'user') and obj.user == request.user)


class IsOwnerOfKYCDocument(permissions.BasePermission):
    """Permission spécifique pour les documents KYC."""
    
    message = _('Vous ne pouvez accéder qu\'à vos propres documents KYC.')
    
    def has_object_permission(self, request, view, obj):
        """Vérifier que l'utilisateur est propriétaire du document."""
        return obj.user == request.user


class CanUploadKYCDocument(permissions.BasePermission):
    """Permission pour uploader des documents KYC."""
    
    def has_permission(self, request, view):
        """Vérifier les conditions pour uploader un document KYC."""
        if not (request.user and request.user.is_authenticated):
            self.message = _('Authentification requise')
            return False
        
        user = request.user
        
        # Vérifier que le KYC n'est pas déjà approuvé
        if user.kyc_status == 'approved':
            self.message = _('Votre KYC est déjà approuvé')
            return False
        
        # Limiter le nombre de tentatives après rejet
        if user.kyc_status == 'rejected':
            # Vérifier si assez de temps s'est écoulé (24h)
            if user.kyc_reviewed_at:
                time_since_rejection = timezone.now() - user.kyc_reviewed_at
                if time_since_rejection.total_seconds() < 24 * 3600:
                    hours_remaining = 24 - int(time_since_rejection.total_seconds() / 3600)
                    self.message = _('Vous devez attendre {} heures avant de soumettre de nouveaux documents').format(hours_remaining)
                    return False
        
        return True


class HasValidSession(permissions.BasePermission):
    """Permission pour vérifier la validité de la session."""
    
    def has_permission(self, request, view):
        """Vérifier que la session est valide."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Vérifier la dernière activité (session expirée après 24h d'inactivité)
        if request.user.last_activity:
            time_since_activity = timezone.now() - request.user.last_activity
            if time_since_activity.total_seconds() > 24 * 3600:
                self.message = _('Session expirée. Veuillez vous reconnecter.')
                return False
        
        return True


class IsWithinRateLimit(permissions.BasePermission):
    """Permission pour vérifier les limites de taux personnalisées."""
    
    def __init__(self, max_requests=10, time_window_minutes=60, action_type='general'):
        """Initialiser avec les paramètres de limite."""
        self.max_requests = max_requests
        self.time_window_minutes = time_window_minutes
        self.action_type = action_type
    
    def has_permission(self, request, view):
        """Vérifier les limites de taux."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Compter les activités récentes de ce type
        from .models import UserActivity
        
        cutoff_time = timezone.now() - timezone.timedelta(minutes=self.time_window_minutes)
        recent_activities = UserActivity.objects.filter(
            user=request.user,
            activity_type=self.action_type,
            created_at__gte=cutoff_time
        ).count()
        
        if recent_activities >= self.max_requests:
            self.message = _('Trop de tentatives. Réessayez dans {} minutes.').format(
                self.time_window_minutes
            )
            return False
        
        return True


# Classes de permissions combinées pour des cas d'usage courants
class StandardUserPermissions(permissions.BasePermission):
    """Permissions standard pour un utilisateur normal."""
    
    def has_permission(self, request, view):
        """Vérifications standard combinées."""
        if not (request.user and request.user.is_authenticated):
            self.message = _('Authentification requise')
            return False
        
        user = request.user
        
        # Compte actif
        if not user.is_active:
            self.message = _('Compte désactivé')
            return False
        
        # Compte non verrouillé
        if user.is_account_locked():
            self.message = _('Compte temporairement verrouillé')
            return False
        
        # Email vérifié
        if not user.is_verified:
            self.message = _('Email non vérifié')
            return False
        
        return True


class HighValueTransactionPermissions(permissions.BasePermission):
    """Permissions pour les transactions de grande valeur."""
    
    def __init__(self, threshold_fcfa=100000):
        """Initialiser avec le seuil de valeur élevée."""
        self.threshold_fcfa = threshold_fcfa
    
    def has_permission(self, request, view):
        """Vérifications pour les transactions importantes."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        user = request.user
        
        # Vérifications de base
        if not user.is_active or not user.is_verified:
            self.message = _('Compte non vérifié')
            return False
        
        # KYC obligatoire pour les gros montants
        if user.kyc_status != 'approved':
            self.message = _('Vérification KYC requise pour les transactions importantes')
            return False
        
        # Compte doit exister depuis au moins 7 jours
        account_age = timezone.now() - user.created_at
        if account_age.days < 7:
            self.message = _('Votre compte doit exister depuis au moins 7 jours')
            return False
        
        return True
