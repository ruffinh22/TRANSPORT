from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from typing import Optional, Dict, Any

User = get_user_model()


class UserVerifier:
    """Utilitaire pour créer et vérifier des utilisateurs de test."""
    
    ROLES = {
        'admin': {'permissions': ['add_user', 'change_user', 'delete_user']},
        'moderator': {'permissions': ['change_user', 'view_user']},
        'user': {'permissions': ['view_user']},
    }
    
    @staticmethod
    def create_test_user(
        username: str = 'testuser',
        email: str = 'test@example.com',
        password: str = 'testpass123',
        role: str = 'user',
        is_active: bool = True,
        **kwargs
    ) -> User:
        """Crée un utilisateur de test avec un rôle spécifique."""
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=is_active,
            **kwargs
        )
        
        if role in UserVerifier.ROLES:
            UserVerifier._assign_role(user, role)
        
        return user
    
    @staticmethod
    def _assign_role(user: User, role: str) -> None:
        """Assigne un rôle et ses permissions à l'utilisateur."""
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
    
    @staticmethod
    def verify_user_exists(username: str) -> bool:
        """Vérifie qu'un utilisateur existe."""
        return User.objects.filter(username=username).exists()
    
    @staticmethod
    def verify_user_role(user: User, role: str) -> bool:
        """Vérifie que l'utilisateur a un rôle spécifique."""
        return user.groups.filter(name=role).exists()
    
    @staticmethod
    def verify_user_active(user: User) -> bool:
        """Vérifie que l'utilisateur est actif."""
        return user.is_active
    
    @staticmethod
    def get_user_info(user: User) -> Dict[str, Any]:
        """Retourne les informations complètes d'un utilisateur."""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'roles': list(user.groups.values_list('name', flat=True)),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
    
    @staticmethod
    def delete_test_user(username: str) -> None:
        """Supprime un utilisateur de test."""
        User.objects.filter(username=username).delete()
