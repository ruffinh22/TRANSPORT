"""Permissions personnalisées pour les modèles"""
from rest_framework.permissions import BasePermission, IsAuthenticated
from django.contrib.auth.models import Permission as DjangoPermission


class HasRolePermission(BasePermission):
    """Vérifier si l'utilisateur a un rôle spécifique"""
    
    message = 'Vous n\'avez pas les permissions nécessaires'
    required_role = None
    
    def has_permission(self, request, view):
        """Vérifier les permissions"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.required_role:
            return True
        
        return request.user.has_role(self.required_role)


class IsAdmin(BasePermission):
    """Vérifier si l'utilisateur est admin"""
    
    message = 'Seuls les administrateurs peuvent accéder à cette ressource'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_role('ADMIN')
        )


class IsManager(BasePermission):
    """Vérifier si l'utilisateur est manager"""
    
    message = 'Seuls les managers peuvent accéder à cette ressource'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.has_role('MANAGER') or request.user.has_role('ADMIN'))
        )


class IsOwnerOrReadOnly(BasePermission):
    """Permettre l'édition seulement au propriétaire de l'objet"""
    
    message = 'Vous ne pouvez éditer que vos propres données'
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tout le monde
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Écriture seulement pour le propriétaire
        return obj.user == request.user or request.user.is_staff


class IsVerified(BasePermission):
    """Vérifier si l'utilisateur est entièrement vérifié"""
    
    message = 'Vous devez vérifier votre email, téléphone et document'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_fully_verified
        )


class CanManageUser(BasePermission):
    """Vérifier si l'utilisateur peut gérer les utilisateurs"""
    
    message = 'Vous n\'avez pas les permissions pour gérer les utilisateurs'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_superuser or
            request.user.has_role('ADMIN') or
            request.user.has_permission('users.manage_users')
        )
    
    def has_object_permission(self, request, view, obj):
        # Chaque utilisateur peut modifier ses propres données
        if request.method in ['GET', 'PUT', 'PATCH'] and obj == request.user:
            return True
        
        # Les admins peuvent tout modifier
        return (
            request.user.is_superuser or
            request.user.has_role('ADMIN')
        )
