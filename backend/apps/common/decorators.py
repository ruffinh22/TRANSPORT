"""
Décorateurs pour l'implémentation RBAC
Utilisés pour protéger les vues et endpoints
"""
from functools import wraps
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .permissions import get_user_permissions


def require_role(*roles):
    """
    Décorateur pour vérifier que l'utilisateur a un des rôles spécifiés.
    
    Usage:
        @require_role('ADMIN', 'MANAGER')
        @api_view(['GET', 'POST'])
        def my_view(request):
            return Response({'message': 'Success'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Vérifier l'authentification
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentification requise.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Obtenir les rôles de l'utilisateur
            user_roles = list(request.user.roles.values_list('code', flat=True))
            
            # Vérifier que l'utilisateur a au moins un des rôles requis
            if not any(role in user_roles for role in roles):
                return Response(
                    {
                        'detail': f'Rôles requis: {", ".join(roles)}. Vos rôles: {", ".join(user_roles) if user_roles else "Aucun"}.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(*permissions):
    """
    Décorateur pour vérifier que l'utilisateur a une des permissions spécifiées.
    
    Usage:
        @require_permission('trips.manage_trips')
        @api_view(['POST'])
        def create_trip(request):
            return Response({'message': 'Trip created'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Vérifier l'authentification
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentification requise.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Obtenir les permissions de l'utilisateur
            user_permissions = get_user_permissions(request.user)
            
            # Vérifier que l'utilisateur a au moins une des permissions requises
            if not any(perm in user_permissions for perm in permissions):
                return Response(
                    {
                        'detail': f'Permissions requises: {", ".join(permissions)}.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_any_role(*roles):
    """
    Alias pour require_role - vérifier qu'on a AU MOINS UN des rôles
    """
    return require_role(*roles)


def require_all_roles(*roles):
    """
    Décorateur pour vérifier que l'utilisateur a TOUS les rôles spécifiés.
    
    Usage:
        @require_all_roles('ADMIN', 'MANAGER')
        @api_view(['GET'])
        def my_view(request):
            return Response({'message': 'Success'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Vérifier l'authentification
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentification requise.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Obtenir les rôles de l'utilisateur
            user_roles = list(request.user.roles.values_list('code', flat=True))
            
            # Vérifier que l'utilisateur a TOUS les rôles requis
            if not all(role in user_roles for role in roles):
                return Response(
                    {
                        'detail': f'Tous les rôles suivants sont requis: {", ".join(roles)}.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def admin_required(func):
    """Alias pour @require_role('ADMIN', 'SUPER_ADMIN')"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentification requise.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_roles = list(request.user.roles.values_list('code', flat=True))
        
        if 'ADMIN' not in user_roles and 'SUPER_ADMIN' not in user_roles:
            return Response(
                {'detail': 'Seuls les administrateurs peuvent accéder à cette ressource.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return func(request, *args, **kwargs)
    
    return wrapper
