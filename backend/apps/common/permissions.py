"""
Permissions classes pour Django REST Framework
Implémente le contrôle d'accès basé sur les rôles (RBAC)
"""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class HasRolePermission(BasePermission):
    """
    Vérifie que l'utilisateur a un rôle spécifique.
    
    Usage:
        permission_classes = [HasRolePermission]
        required_role = 'ADMIN'
    """
    required_role = None
    message = "L'utilisateur n'a pas le rôle requis pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur a le rôle requis"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.required_role:
            return True
        
        # Obtenir les rôles de l'utilisateur
        user_roles = request.user.roles.values_list('code', flat=True)
        return self.required_role in user_roles


class HasPermission(BasePermission):
    """
    Vérifie que l'utilisateur a une permission spécifique.
    
    Usage:
        permission_classes = [HasPermission]
        required_permission = 'trips.manage_trips'
    """
    required_permission = None
    message = "L'utilisateur n'a pas les permissions requises pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur a la permission requise"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.required_permission:
            return True
        
        # Obtenir toutes les permissions de l'utilisateur à travers ses rôles
        user_permissions = []
        for role in request.user.roles.all():
            if isinstance(role.permissions, list):
                user_permissions.extend(role.permissions)
        
        return self.required_permission in user_permissions


class IsAdmin(BasePermission):
    """Vérifier si l'utilisateur est ADMIN ou SUPER_ADMIN"""
    message = "Seuls les administrateurs peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'ADMIN' in user_roles or 'SUPER_ADMIN' in user_roles


class IsSuperAdmin(BasePermission):
    """Vérifier si l'utilisateur est SUPER_ADMIN (réservé IT)"""
    message = "Seuls les super administrateurs peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'SUPER_ADMIN' in user_roles


class IsManager(BasePermission):
    """Vérifier si l'utilisateur est Manager"""
    message = "Seuls les managers peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'MANAGER' in user_roles


class IsComptable(BasePermission):
    """Vérifier si l'utilisateur est Comptable"""
    message = "Seuls les comptables peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'COMPTABLE' in user_roles


class IsGuichetier(BasePermission):
    """Vérifier si l'utilisateur est Guichetier"""
    message = "Seuls les guichetiers peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'GUICHETIER' in user_roles


class IsCharffeur(BasePermission):
    """Vérifier si l'utilisateur est Chauffeur"""
    message = "Seuls les chauffeurs peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'CHAUFFEUR' in user_roles


class IsControleur(BasePermission):
    """Vérifier si l'utilisateur est Contrôleur"""
    message = "Seuls les contrôleurs peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'CONTROLEUR' in user_roles


class IsGestionnaireCourrier(BasePermission):
    """Vérifier si l'utilisateur est Gestionnaire Courrier"""
    message = "Seuls les gestionnaires courrier peuvent accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'GESTIONNAIRE_COURRIER' in user_roles


def get_user_permissions(user):
    """
    Utilitaire pour obtenir toutes les permissions d'un utilisateur
    """
    permissions = []
    if user and user.is_authenticated:
        for role in user.roles.all():
            if isinstance(role.permissions, list):
                permissions.extend(role.permissions)
    return list(set(permissions))  # Remove duplicates


def user_has_permission(user, permission):
    """
    Vérifier si un utilisateur a une permission spécifique
    """
    user_perms = get_user_permissions(user)
    return permission in user_perms
