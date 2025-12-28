"""Serializers pour l'authentification et les utilisateurs"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserSession
import logging

logger = logging.getLogger(__name__)


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour un utilisateur"""
    
    roles = serializers.SerializerMethodField()
    is_fully_verified = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    
    def get_roles(self, obj):
        """Retourner les codes des rôles au lieu des noms"""
        return list(obj.roles.values_list('code', flat=True))
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'gender', 'avatar',
            'document_type', 'document_number', 'document_verified',
            'country', 'city', 'address', 'postal_code',
            'email_verified', 'phone_verified', 'is_fully_verified',
            'language', 'timezone',
            'notify_email', 'notify_sms', 'notify_push',
            'is_active', 'is_blocked', 'roles',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_fully_verified',
            'email_verified', 'phone_verified', 'document_verified'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes"""
    
    full_name = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name', 'avatar',
            'is_active', 'is_blocked', 'roles', 'created_at'
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_roles(self, obj):
        """Retourner les codes des rôles"""
        return list(obj.roles.values_list('code', flat=True))


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text=_('Au moins 8 caractères')
    )
    password2 = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text=_('Confirmation du mot de passe')
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name',
            'password', 'password2', 'language', 'timezone'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        """Valider les données d'inscription"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'password2': _('Les mots de passe ne correspondent pas')
            })
        
        # Vérifier que l'email n'existe pas
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': _('Cet email est déjà utilisé')
            })
        
        # Vérifier que le téléphone n'existe pas
        if User.objects.filter(phone=data['phone']).exists():
            raise serializers.ValidationError({
                'phone': _('Ce numéro de téléphone est déjà utilisé')
            })
        
        return data
    
    def create(self, validated_data):
        """Créer l'utilisateur"""
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(password=password, **validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour obtenir les tokens JWT"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    username = None  # Override parent's username field
    
    class Meta:
        model = User
        fields = ['email', 'password']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field from parent
        if 'username' in self.fields:
            del self.fields['username']
    
    def validate(self, attrs):
        """Valider les credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Authentifier l'utilisateur - lookup par email et vérifier le mot de passe
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                user = None
        except User.DoesNotExist:
            user = None
        
        if not user:
            raise serializers.ValidationError(
                _('Email ou mot de passe invalide')
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                _('Ce compte est désactivé')
            )
        
        if user.is_blocked:
            raise serializers.ValidationError(
                _('Ce compte a été bloqué')
            )
        
        if user.locked_until:
            from django.utils import timezone
            if timezone.now() < user.locked_until:
                raise serializers.ValidationError(
                    _('Trop de tentatives échouées. Réessayez plus tard.')
                )
            else:
                user.unlock_login()
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        # Réinitialiser les tentatives échouées
        if user.failed_login_attempts > 0:
            user.unlock_login()
        
        # Logger la connexion
        logger.info(f"User {user.email} logged in")
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserDetailSerializer(user).data
        }


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer pour rafraîchir les tokens"""
    
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        """Valider le refresh token"""
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken(attrs['refresh'])
            
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        except Exception as e:
            raise serializers.ValidationError(
                _('Token invalide ou expiré')
            )


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour un utilisateur"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'country', 'city', 'address', 'postal_code',
            'language', 'timezone', 'avatar',
            'notify_email', 'notify_sms', 'notify_push'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    
    old_password = serializers.CharField(write_only=True, min_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, attrs):
        """Valider le changement de mot de passe"""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                'new_password2': _('Les mots de passe ne correspondent pas')
            })
        
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({
                'old_password': _('Mot de passe actuel incorrect')
            })
        
        return attrs
    
    def save(self):
        """Sauvegarder le nouveau mot de passe"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        
        logger.info(f"User {user.email} changed password")
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer pour demander la réinitialisation du mot de passe"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Vérifier que l'utilisateur existe"""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _('Aucun utilisateur avec cet email')
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer pour confirmer la réinitialisation du mot de passe"""
    
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, attrs):
        """Valider la réinitialisation"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password2': _('Les mots de passe ne correspondent pas')
            })
        
        return attrs


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer pour les sessions utilisateurs"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user_email', 'device_name', 'ip_address',
            'is_active', 'expires_at', 'created_at'
        ]
        read_only_fields = fields
