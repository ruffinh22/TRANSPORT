"""Views pour l'authentification et les utilisateurs"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from .models import User, UserSession
from .serializers import (
    UserDetailSerializer, UserListSerializer,
    UserRegistrationSerializer, CustomTokenObtainPairSerializer,
    UserUpdateSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, UserSessionSerializer
)
from .permissions import IsVerified, CanManageUser, IsOwnerOrReadOnly
from apps.common.models import AuditTrail
import logging

logger = logging.getLogger(__name__)


class RegisterView(TokenObtainPairView):
    """Enregistrer un nouvel utilisateur"""
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Créer un nouvel utilisateur"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Générer les tokens JWT
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"New user registered: {user.email}")
        
        return Response({
            'user': UserDetailSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """Connecter un utilisateur"""
    
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class TokenRefreshCustomView(TokenRefreshView):
    """Rafraîchir le token JWT"""
    
    permission_classes = [permissions.AllowAny]


class LogoutView(viewsets.ViewSet):
    """Déconnecter un utilisateur"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Déconnecter l'utilisateur"""
        try:
            # Récupérer le refresh token
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                # Essayer de trouver et de terminer la session
                try:
                    session = UserSession.objects.get(
                        refresh_token=refresh_token,
                        user=request.user
                    )
                    session.logout()
                except UserSession.DoesNotExist:
                    pass
            
            logger.info(f"User {request.user.email} logged out")
            
            return Response(
                {'detail': _('Déconnexion réussie')},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'detail': _('Erreur lors de la déconnexion')},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet pour les utilisateurs"""
    
    queryset = User.objects.filter(deleted_at__isnull=True)
    permission_classes = [permissions.IsAuthenticated, CanManageUser]
    
    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        """Filtrer les utilisateurs"""
        user = self.request.user
        
        # Les admins voient tous les utilisateurs
        if user.has_role('ADMIN'):
            return self.queryset
        
        # Les utilisateurs normaux voient seulement leurs données
        return User.objects.filter(id=user.id, deleted_at__isnull=True)
    
    def list(self, request, *args, **kwargs):
        """Lister les utilisateurs"""
        if not request.user.has_role('ADMIN'):
            # Retourner seulement l'utilisateur courant
            return Response(
                UserDetailSerializer(request.user).data
            )
        
        return super().list(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete d'un utilisateur"""
        instance = self.get_object()
        
        if instance == request.user:
            return Response(
                {'detail': _('Vous ne pouvez pas supprimer votre propre compte')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.soft_delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retourner les infos de l'utilisateur actuel"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Mettre à jour le profil de l'utilisateur"""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Audit
        AuditTrail.objects.create(
            user=request.user,
            model_name='User',
            object_id=str(user.id),
            action='UPDATE',
            new_values=serializer.data
        )
        
        return Response(UserDetailSerializer(user).data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Changer le mot de passe"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Audit
        AuditTrail.objects.create(
            user=request.user,
            model_name='User',
            object_id=str(user.id),
            action='UPDATE',
            new_values={'password_changed': True}
        )
        
        logger.info(f"User {user.email} changed password")
        
        return Response(
            {'detail': _('Mot de passe changé avec succès')},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def block(self, request, pk=None):
        """Bloquer un utilisateur (Admin seulement)"""
        if not request.user.has_role('ADMIN'):
            return Response(
                {'detail': _('Vous n\'avez pas les permissions')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        reason = request.data.get('reason', '')
        
        user.block(reason)
        
        # Audit
        AuditTrail.objects.create(
            user=request.user,
            model_name='User',
            object_id=str(user.id),
            action='UPDATE',
            new_values={'is_blocked': True, 'block_reason': reason}
        )
        
        return Response(UserDetailSerializer(user).data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unblock(self, request, pk=None):
        """Débloquer un utilisateur (Admin seulement)"""
        if not request.user.has_role('ADMIN'):
            return Response(
                {'detail': _('Vous n\'avez pas les permissions')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.unblock()
        
        # Audit
        AuditTrail.objects.create(
            user=request.user,
            model_name='User',
            object_id=str(user.id),
            action='UPDATE',
            new_values={'is_blocked': False}
        )
        
        return Response(UserDetailSerializer(user).data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_email(self, request, pk=None):
        """Vérifier l'email d'un utilisateur"""
        if request.user.id != int(pk) and not request.user.has_role('ADMIN'):
            return Response(
                {'detail': _('Vous n\'avez pas les permissions')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.verify_email()
        
        return Response(
            {'detail': _('Email vérifié')},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_phone(self, request, pk=None):
        """Vérifier le téléphone d'un utilisateur"""
        if request.user.id != int(pk) and not request.user.has_role('ADMIN'):
            return Response(
                {'detail': _('Vous n\'avez pas les permissions')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.verify_phone()
        
        return Response(
            {'detail': _('Téléphone vérifié')},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """Lister les sessions de l'utilisateur"""
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        )
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def logout_all(self, request):
        """Terminer toutes les sessions sauf la courante"""
        current_session = request.auth
        
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(
            refresh_token=current_session if current_session else None
        ).update(is_active=False, logged_out_at=timezone.now())
        
        return Response(
            {'detail': _('Toutes les autres sessions ont été fermées')},
            status=status.HTTP_200_OK
        )
