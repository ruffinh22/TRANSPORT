# apps/core/permissions.py
# ============================

from rest_framework import permissions
from rest_framework.request import Request
from django.contrib.auth.models import AnonymousUser
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre seulement aux propriétaires d'un objet
    de le modifier. Les autres peuvent seulement lire.
    """
    
    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Vérifier les permissions au niveau de l'objet."""
        
        # Permissions de lecture pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture seulement pour le propriétaire
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'player1') and hasattr(obj, 'player2'):
            # Pour les jeux
            return request.user in [obj.player1, obj.player2]
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission permettant aux administrateurs de modifier,
    aux autres utilisateurs seulement de lire.
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier les permissions générales."""
        
        # Lecture autorisée pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Modification autorisée seulement pour les admins
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission pour les utilisateurs vérifiés (KYC validé).
    """
    
    message = "Votre compte doit être vérifié pour effectuer cette action."
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier que l'utilisateur est vérifié."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier le statut KYC
        return getattr(request.user, 'is_verified', False)


class HasMinimumBalance(permissions.BasePermission):
    """
    Permission pour vérifier que l'utilisateur a un solde minimum.
    """
    
    def __init__(self, min_amount: float = 0, currency: str = 'FCFA'):
        self.min_amount = min_amount
        self.currency = currency
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier le solde minimum."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Obtenir le solde dans la devise appropriée
        balance = self.get_user_balance(request.user, self.currency)
        
        if balance < self.min_amount:
            self.message = f"Solde insuffisant. Minimum requis: {self.min_amount} {self.currency}"
            return False
        
        return True
    
    def get_user_balance(self, user: Any, currency: str) -> float:
        """Obtenir le solde de l'utilisateur dans la devise spécifiée."""
        currency_field_map = {
            'FCFA': 'balance_fcfa',
            'EUR': 'balance_eur', 
            'USD': 'balance_usd'
        }
        
        field_name = currency_field_map.get(currency, 'balance_fcfa')
        return float(getattr(user, field_name, 0))


class IsGameParticipant(permissions.BasePermission):
    """
    Permission pour vérifier que l'utilisateur participe au jeu.
    """
    
    message = "Vous devez participer à ce jeu pour effectuer cette action."
    
    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Vérifier la participation au jeu."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur est l'un des joueurs
        if hasattr(obj, 'player1') and hasattr(obj, 'player2'):
            return request.user in [obj.player1, obj.player2]
        
        return False


class IsActiveGame(permissions.BasePermission):
    """
    Permission pour vérifier que le jeu est actif.
    """
    
    message = "Cette action n'est pas autorisée sur un jeu terminé."
    
    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Vérifier que le jeu est actif."""
        
        if hasattr(obj, 'status'):
            return obj.status in ['waiting', 'playing']
        
        return True


class CanWithdrawFunds(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur peut retirer des fonds.
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier les conditions de retrait."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier le KYC
        if not getattr(request.user, 'is_verified', False):
            self.message = "Vérification d'identité requise pour les retraits"
            return False
        
        # Vérifier s'il n'y a pas de retrait en cours
        if self.has_pending_withdrawal(request.user):
            self.message = "Vous avez déjà une demande de retrait en cours"
            return False
        
        # Vérifier les conditions de mise
        if not self.meets_wagering_requirements(request.user):
            self.message = "Conditions de mise non remplies"
            return False
        
        return True
    
    def has_pending_withdrawal(self, user: Any) -> bool:
        """Vérifier s'il y a un retrait en attente."""
        try:
            from apps.payments.models import Transaction
            return Transaction.objects.filter(
                user=user,
                transaction_type='withdrawal',
                status='pending'
            ).exists()
        except:
            return False
    
    def meets_wagering_requirements(self, user: Any) -> bool:
        """Vérifier les conditions de mise (60% du dépôt)."""
        try:
            from apps.payments.models import Transaction
            from django.db.models import Sum
            
            # Calculer les dépôts totaux
            deposits = Transaction.objects.filter(
                user=user,
                transaction_type='deposit',
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Calculer les mises totales
            bets = Transaction.objects.filter(
                user=user,
                transaction_type='bet',
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Vérifier que 60% des dépôts ont été misés
            required_wagering = deposits * 0.6
            return bets >= required_wagering
            
        except:
            return True  # En cas d'erreur, autoriser par défaut


class RateLimitPermission(permissions.BasePermission):
    """
    Permission pour vérifier les limites de taux d'API.
    """
    
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier les limites de taux."""
        
        if not request.user or not request.user.is_authenticated:
            return True  # Géré par le middleware
        
        from django.core.cache import cache
        import time
        
        # Clé de cache unique par utilisateur
        cache_key = f"rate_limit:{request.user.id}:{int(time.time() // self.window)}"
        
        # Compter les requêtes
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= self.max_requests:
            self.message = f"Limite de {self.max_requests} requêtes par minute dépassée"
            return False
        
        # Incrémenter le compteur
        cache.set(cache_key, current_requests + 1, self.window)
        
        return True


class IsCurrentPlayerTurn(permissions.BasePermission):
    """
    Permission pour vérifier que c'est le tour du joueur actuel.
    """
    
    message = "Ce n'est pas votre tour de jouer."
    
    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Vérifier le tour du joueur."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(obj, 'current_player'):
            return True  # Si pas de notion de tour, autoriser
        
        return obj.current_player == request.user


class IsPremiumUser(permissions.BasePermission):
    """
    Permission pour les utilisateurs premium.
    """
    
    message = "Cette fonctionnalité est réservée aux utilisateurs premium."
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier le statut premium."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        return self.is_premium_user(request.user)
    
    def is_premium_user(self, user: Any) -> bool:
        """Vérifier si l'utilisateur est premium."""
        try:
            from apps.referrals.models import PremiumSubscription
            return PremiumSubscription.objects.filter(
                user=user,
                status='active'
            ).exists()
        except:
            return False


class RegionRestrictedPermission(permissions.BasePermission):
    """
    Permission pour restreindre l'accès par région géographique.
    """
    
    def __init__(self, allowed_countries: list = None, blocked_countries: list = None):
        self.allowed_countries = allowed_countries or []
        self.blocked_countries = blocked_countries or []
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier les restrictions géographiques."""
        
        user_country = self.get_user_country(request)
        
        # Vérifier les pays bloqués
        if self.blocked_countries and user_country in self.blocked_countries:
            self.message = "Ce service n'est pas disponible dans votre région"
            return False
        
        # Vérifier les pays autorisés
        if self.allowed_countries and user_country not in self.allowed_countries:
            self.message = "Ce service n'est pas disponible dans votre région"
            return False
        
        return True
    
    def get_user_country(self, request: Request) -> str:
        """Obtenir le pays de l'utilisateur."""
        
        # 1. Depuis le profil utilisateur
        if request.user and request.user.is_authenticated:
            country = getattr(request.user, 'country', None)
            if country:
                return country.upper()
        
        # 2. Depuis l'IP (nécessiterait une API de géolocalisation)
        # Pour l'instant, retourner un pays par défaut
        return 'CI'  # Côte d'Ivoire par défaut


class MaintenanceModePermission(permissions.BasePermission):
    """
    Permission pour bloquer l'accès pendant la maintenance (sauf admins).
    """
    
    message = "Service temporairement indisponible pour maintenance."
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier le mode maintenance."""
        
        from django.core.cache import cache
        
        maintenance_mode = cache.get('maintenance_mode', False)
        
        if not maintenance_mode:
            return True
        
        # Autoriser les admins pendant la maintenance
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True
        
        return False


class AgeVerificationPermission(permissions.BasePermission):
    """
    Permission pour vérifier l'âge minimum (18 ans).
    """
    
    message = "Vous devez avoir au moins 18 ans pour utiliser ce service."
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Vérifier l'âge de l'utilisateur."""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        return self.is_adult(request.user)
    
    def is_adult(self, user: Any) -> bool:
        """Vérifier si l'utilisateur est majeur."""
        from datetime import date
        
        birth_date = getattr(user, 'date_of_birth', None)
        if not birth_date:
            return False
        
        today = date.today()
        age = today.year - birth_date.year
        
        # Ajuster si l'anniversaire n'est pas encore passé cette année
        if today < birth_date.replace(year=today.year):
            age -= 1
        
        return age >= 18


class CombinedPermission(permissions.BasePermission):
    """
    Permission pour combiner plusieurs permissions avec des opérateurs logiques.
    """
    
    def __init__(self, *permissions, operator='AND'):
        self.permissions = [perm() if isinstance(perm, type) else perm for perm in permissions]
        self.operator = operator.upper()
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """Évaluer les permissions combinées."""
        
        results = []
        messages = []
        
        for perm in self.permissions:
            result = perm.has_permission(request, view)
            results.append(result)
            
            if not result and hasattr(perm, 'message'):
                messages.append(perm.message)
        
        # Opérateur AND : toutes les permissions doivent être vraies
        if self.operator == 'AND':
            success = all(results)
        # Opérateur OR : au moins une permission doit être vraie
        elif self.operator == 'OR':
            success = any(results)
        else:
            success = all(results)  # Par défaut AND
        
        if not success and messages:
            self.message = ' | '.join(messages)
        
        return success
    
    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Évaluer les permissions d'objet combinées."""
        
        results = []
        
        for perm in self.permissions:
            if hasattr(perm, 'has_object_permission'):
                result = perm.has_object_permission(request, view, obj)
                results.append(result)
        
        if not results:
            return True
        
        if self.operator == 'AND':
            return all(results)
        elif self.operator == 'OR':
            return any(results)
        else:
            return all(results)


# ===== PERMISSIONS COMPOSÉES PRÉDÉFINIES =====

class GameActionPermission(CombinedPermission):
    """Permission pour les actions de jeu (combinaison de plusieurs vérifications)."""
    
    def __init__(self):
        super().__init__(
            permissions.IsAuthenticated,
            IsVerifiedUser,
            IsGameParticipant,
            IsActiveGame,
            IsCurrentPlayerTurn,
            operator='AND'
        )


class FinancialTransactionPermission(CombinedPermission):
    """Permission pour les transactions financières."""
    
    def __init__(self):
        super().__init__(
            permissions.IsAuthenticated,
            IsVerifiedUser,
            AgeVerificationPermission,
            operator='AND'
        )


class WithdrawalPermission(CombinedPermission):
    """Permission pour les retraits."""
    
    def __init__(self):
        super().__init__(
            FinancialTransactionPermission,
            CanWithdrawFunds,
            operator='AND'
        )
