# Backend RBAC Implementation Guide

## Statut: 🔄 EN COURS - Structures créées, Middleware à implémenter

Ce document guide l'implémentation du middleware RBAC côté Django.

---

## 📋 Ce qui est fait

### ✅ Modèles Django
- `/backend/apps/common/models.py` - Role et Permission modèles
- `/backend/apps/users/models.py` - User.roles ManyToMany(Role)
- 8 rôles définis dans RoleType
- 8 permissions définies dans Permission

### ✅ Management Command
- `/backend/apps/common/management/commands/init_roles.py`
- Exécuter : `python manage.py init_roles`
- Crée les 8 rôles avec leurs permissions

### ✅ API Endpoints Existants
- POST `/users/login/` - Retourne user avec roles (à vérifier)
- GET `/users/me/` - Profil utilisateur (à augmenter avec roles)
- JWT Authentication avec access_token + refresh_token

---

## 🔧 À Implémenter - Middleware RBAC

### 1. Permission Checker Utility

**Fichier :** `/backend/apps/common/permissions.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class HasRolePermission(BasePermission):
    """
    Vérifie que l'utilisateur a un rôle spécifique
    """
    required_role = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.required_role:
            return True
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return self.required_role in user_roles


class HasPermission(BasePermission):
    """
    Vérifie que l'utilisateur a une permission spécifique
    """
    required_permission = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.required_permission:
            return True
        
        user_permissions = []
        for role in request.user.roles.all():
            user_permissions.extend(role.permissions)
        
        return self.required_permission in user_permissions


class IsAdminRole(BasePermission):
    """Vérifier si l'utilisateur est ADMIN ou SUPER_ADMIN"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_roles = request.user.roles.values_list('code', flat=True)
        return 'ADMIN' in user_roles or 'SUPER_ADMIN' in user_roles
```

---

### 2. Décorateurs pour les Vues

**Fichier :** `/backend/apps/common/decorators.py`

```python
from functools import wraps
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

def require_role(*roles):
    """
    Décorateur pour vérifier les rôles
    
    Usage:
    @require_role('ADMIN', 'MANAGER')
    @api_view(['GET'])
    def my_view(request):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Non authentifié'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_roles = list(request.user.roles.values_list('code', flat=True))
            
            if not any(role in user_roles for role in roles):
                return Response(
                    {'detail': f'Rôles requis: {", ".join(roles)}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(*permissions):
    """
    Décorateur pour vérifier les permissions
    
    Usage:
    @require_permission('trips.manage_trips')
    @api_view(['POST'])
    def create_trip(request):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Non authentifié'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_permissions = []
            for role in request.user.roles.all():
                user_permissions.extend(role.permissions)
            
            if not any(perm in user_permissions for perm in permissions):
                return Response(
                    {'detail': f'Permissions requises: {", ".join(permissions)}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator
```

---

### 3. Mixins pour ViewSets

**Fichier :** `/backend/apps/common/mixins.py`

```python
from rest_framework.permissions import IsAuthenticated
from .permissions import HasPermission

class RBACViewSetMixin:
    """
    Mixin pour ajouter le RBAC aux ViewSets
    """
    permission_classes = [IsAuthenticated]
    
    # Permissions par action
    action_permissions = {
        'list': 'view',
        'retrieve': 'view',
        'create': 'manage',
        'update': 'manage',
        'partial_update': 'manage',
        'destroy': 'manage',
    }
    
    def get_permission_required(self):
        """
        Obtenir la permission requise pour l'action actuelle
        """
        action = self.action
        operation = self.action_permissions.get(action, 'view')
        
        # Exemple: trips.view_trip ou trips.manage_trips
        module = self.basename.rstrip('s')  # trips -> trip
        return f'{module}.{operation}_{module}'
    
    def check_object_permissions(self, request, obj):
        """
        Vérifier les permissions sur l'objet
        """
        super().check_object_permissions(request, obj)
        # Peut être surchargé pour des vérifications custom
```

---

### 4. Exemple d'Intégration - TripsViewSet

**Fichier :** `/backend/apps/trips/views.py`

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.common.decorators import require_permission
from apps.common.mixins import RBACViewSetMixin
from .models import Trip
from .serializers import TripSerializer

class TripViewSet(RBACViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour les trajets avec RBAC
    """
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Obtenir les permissions selon l'action
        """
        permissions = super().get_permissions()
        
        # Vérifier les permissions RBAC
        required_perm = self.get_permission_required()
        
        # Cette vérification pourrait être faite dans un middleware
        # ou dans une permission class personnalisée
        
        return permissions
    
    def perform_create(self, serializer):
        """Créer un trajet - vérifie trips.manage_trips"""
        # La permission est vérifiée avant que cette méthode soit appelée
        serializer.save()
    
    def perform_update(self, serializer):
        """Mettre à jour un trajet"""
        serializer.save()
```

---

## 🚀 Étapes d'Implémentation

### Étape 1: Créer le fichier permissions.py
```bash
# /backend/apps/common/permissions.py
# Ajouter les classes BasePermission
```

### Étape 2: Créer le fichier decorators.py
```bash
# /backend/apps/common/decorators.py
# Ajouter les décorateurs @require_role et @require_permission
```

### Étape 3: Créer le fichier mixins.py
```bash
# /backend/apps/common/mixins.py
# Ajouter le RBACViewSetMixin
```

### Étape 4: Initialiser les rôles
```bash
cd /backend
python manage.py init_roles
```

### Étape 5: Augmenter les endpoints
- GET /users/me/ → Inclure roles dans la réponse
- POST /users/login/ → Inclure roles dans la réponse

### Étape 6: Protéger chaque ViewSet
- TripsViewSet - Ajouter `RBACViewSetMixin`
- TicketsViewSet - Ajouter `RBACViewSetMixin`
- ParcelsViewSet - Ajouter `RBACViewSetMixin`
- PaymentsViewSet - Ajouter `RBACViewSetMixin`
- VehiclesViewSet - Ajouter `RBACViewSetMixin`
- EmployeesViewSet - Ajouter `RBACViewSetMixin`

---

## 🔐 Sécurité - Reminders

- ✅ **Jamais** faire confiance aux rôles du frontend
- ✅ **Toujours** vérifier les permissions côté backend
- ✅ **Loguer** les accès refusés dans AuditTrail
- ✅ **Remonter** un 403 Forbidden si non autorisé
- ✅ **Remonter** un 401 Unauthorized si pas authentifié

---

## 📊 Exemple Complet - TripsViewSet

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from apps.common.decorators import require_permission
from .models import Trip
from .serializers import TripSerializer, TripListSerializer

class TripsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TripListSerializer
        return TripSerializer
    
    def get_queryset(self):
        # Un chauffeur ne voit que ses trajets
        user = self.request.user
        if user.roles.filter(code='CHAUFFEUR').exists():
            return Trip.objects.filter(driver=user.employee)
        
        # Les autres voir tous les trajets
        return Trip.objects.all()
    
    def list(self, request, *args, **kwargs):
        """Lister les trajets - trips.view_trip"""
        if not self.user_has_permission(request, 'trips.view_trip'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Créer un trajet - trips.manage_trips"""
        if not self.user_has_permission(request, 'trips.manage_trips'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Mettre à jour un trajet - trips.manage_trips"""
        if not self.user_has_permission(request, 'trips.manage_trips'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Supprimer un trajet - trips.manage_trips"""
        if not self.user_has_permission(request, 'trips.manage_trips'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    def user_has_permission(self, request, permission):
        """Vérifier si l'utilisateur a la permission"""
        user_permissions = []
        for role in request.user.roles.all():
            user_permissions.extend(role.permissions)
        return permission in user_permissions
```

---

## 📝 Checklist d'Implémentation

- [ ] Créer `/backend/apps/common/permissions.py`
- [ ] Créer `/backend/apps/common/decorators.py`
- [ ] Créer `/backend/apps/common/mixins.py`
- [ ] Exécuter `python manage.py init_roles`
- [ ] Augmenter `/users/me/` et `/users/login/` avec roles
- [ ] Protéger TripsViewSet
- [ ] Protéger TicketsViewSet
- [ ] Protéger ParcelsViewSet
- [ ] Protéger PaymentsViewSet
- [ ] Protéger VehiclesViewSet
- [ ] Protéger EmployeesViewSet
- [ ] Tester avec PostMan/Thunder Client
- [ ] Tester que roles apparaît dans les responses

---

**Version:** 1.0  
**Date:** 2024-12-27
