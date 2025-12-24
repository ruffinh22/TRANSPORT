# apps/accounts/oauth_views.py
# Vues pour l'authentification OAuth (Google, etc.)

import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import json
import secrets
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .models import User, UserProfile, UserPreferences, UserSettings
from .serializers import UserRegistrationResponseSerializer
from .email_service import send_welcome_email
from apps.core.utils import log_user_activity_with_ip, get_client_ip

logger = logging.getLogger(__name__)

class GoogleOAuthConfig:
    """Configuration pour Google OAuth"""
    
    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '')
        self.redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', 
                                  'http://localhost:5173/auth/google/callback')
        self.scope = 'openid email profile'
        
    @property
    def authorization_url(self):
        """URL d'autorisation Google"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

google_config = GoogleOAuthConfig()

@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_url(request):
    """Obtenir l'URL d'autorisation Google OAuth"""
    try:
        # Générer un state token pour la sécurité
        state_token = secrets.token_urlsafe(32)
        request.session['oauth_state'] = state_token
        
        # Construire l'URL avec le state token
        auth_url = f"{google_config.authorization_url}&state={state_token}"
        
        return Response({
            'success': True,
            'authorization_url': auth_url,
            'state': state_token
        })
        
    except Exception as e:
        logger.error(f"Erreur génération URL OAuth Google: {e}")
        return Response({
            'success': False,
            'error': 'Erreur de configuration OAuth'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_callback(request):
    """Callback pour l'authentification Google OAuth"""
    try:
        data = request.data
        authorization_code = data.get('code')
        state_token = data.get('state')
        
        # Vérifier le state token
        session_state = request.session.get('oauth_state')
        if not session_state or session_state != state_token:
            return Response({
                'success': False,
                'error': 'Token de sécurité invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Échanger le code contre un token d'accès
        token_data = exchange_code_for_token(authorization_code)
        if not token_data:
            return Response({
                'success': False,
                'error': 'Erreur lors de l\'échange du code d\'autorisation'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtenir les informations utilisateur
        user_info = get_google_user_info(token_data['id_token'])
        if not user_info:
            return Response({
                'success': False,
                'error': 'Impossible d\'obtenir les informations utilisateur'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer ou récupérer l'utilisateur
        user, created = get_or_create_user_from_google(user_info, request)
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Logger l'activité
        log_user_activity_with_ip(
            user=user,
            activity_type='login' if not created else 'signup',
            description=f'Connexion via Google OAuth {"(nouveau compte)" if created else ""}',
            ip_address=get_client_ip(request),
            metadata={
                'oauth_provider': 'google',
                'google_id': user_info.get('sub'),
                'new_account': created
            }
        )
        
        # Envoyer email de bienvenue pour les nouveaux utilisateurs
        if created:
            try:
                send_welcome_email(user)
            except Exception as e:
                logger.warning(f"Erreur envoi email bienvenue: {e}")
        
        return Response({
            'success': True,
            'message': 'Connexion réussie' if not created else 'Compte créé avec succès',
            'user': UserRegistrationResponseSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'new_account': created
        })
        
    except Exception as e:
        logger.error(f"Erreur callback OAuth Google: {e}")
        return Response({
            'success': False,
            'error': 'Erreur lors de l\'authentification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def exchange_code_for_token(authorization_code: str) -> Optional[Dict[str, Any]]:
    """Échanger le code d'autorisation contre un token d'accès"""
    try:
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': google_config.client_id,
            'client_secret': google_config.client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': google_config.redirect_uri,
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Erreur échange code pour token: {e}")
        return None

def get_google_user_info(id_token_str: str) -> Optional[Dict[str, Any]]:
    """Obtenir les informations utilisateur depuis le token ID Google"""
    try:
        # Vérifier et décoder le token ID
        id_info = id_token.verify_oauth2_token(
            id_token_str, 
            google_requests.Request(), 
            google_config.client_id
        )
        
        # Vérifier l'issuer
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Token ID invalide')
        
        return id_info
        
    except Exception as e:
        logger.error(f"Erreur vérification token ID Google: {e}")
        return None

def get_or_create_user_from_google(user_info: Dict[str, Any], request) -> tuple[User, bool]:
    """Créer ou récupérer un utilisateur depuis les infos Google"""
    
    email = user_info.get('email', '').lower()
    google_id = user_info.get('sub')
    
    if not email or not google_id:
        raise ValueError("Email ou ID Google manquant")
    
    # Chercher un utilisateur existant par email
    try:
        user = User.objects.get(email=email)
        
        # Mettre à jour les informations Google si nécessaire
        if not hasattr(user, 'google_id') or not user.google_id:
            user.google_id = google_id
            user.is_verified = True  # Les comptes Google sont pré-vérifiés
            user.save()
        
        return user, False
        
    except User.DoesNotExist:
        # Créer un nouveau utilisateur
        
        # Générer un username unique
        base_username = user_info.get('name', email.split('@')[0])
        username = generate_unique_username(base_username)
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            is_verified=True,  # Les comptes Google sont pré-vérifiés
        )
        
        # Ajouter l'ID Google
        user.google_id = google_id
        user.save()
        
        # Créer les modèles liés
        create_user_related_models(user, user_info)
        
        return user, True

def generate_unique_username(base_username: str) -> str:
    """Générer un nom d'utilisateur unique"""
    
    # Nettoyer le nom de base
    import re
    base_username = re.sub(r'[^a-zA-Z0-9_.-]', '', base_username.lower())
    base_username = base_username[:20]  # Limiter la longueur
    
    if not base_username:
        base_username = 'user'
    
    # Vérifier si le nom de base est disponible
    if not User.objects.filter(username=base_username).exists():
        return base_username
    
    # Ajouter un suffixe numérique
    counter = 1
    while True:
        username = f"{base_username}{counter}"
        if not User.objects.filter(username=username).exists():
            return username
        counter += 1
        
        # Éviter une boucle infinie
        if counter > 9999:
            username = f"{base_username}{secrets.token_hex(4)}"
            break
    
    return username

def create_user_related_models(user: User, user_info: Dict[str, Any]):
    """Créer les modèles liés pour un nouvel utilisateur"""
    
    try:
        # Créer le profil utilisateur
        profile = UserProfile.objects.create(
            user=user,
            bio=f"Utilisateur {user.first_name or user.username} inscrit via Google"
        )
        
        # Télécharger et sauvegarder l'avatar Google si disponible
        avatar_url = user_info.get('picture')
        if avatar_url:
            try:
                download_and_save_avatar(profile, avatar_url)
            except Exception as e:
                logger.warning(f"Erreur téléchargement avatar Google: {e}")
        
        # Créer les préférences utilisateur
        UserPreferences.objects.create(
            user=user,
            language='fr',  # Langue par défaut
            email_notifications=True,
            push_notifications=True
        )
        
        # Créer les paramètres utilisateur
        UserSettings.objects.create(
            user=user,
            email_notifications=True,
            login_notifications=True
        )
        
    except Exception as e:
        logger.error(f"Erreur création modèles liés pour {user.email}: {e}")

def download_and_save_avatar(profile: UserProfile, avatar_url: str):
    """Télécharger et sauvegarder l'avatar depuis Google"""
    
    try:
        import requests
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        import uuid
        
        response = requests.get(avatar_url, timeout=10)
        response.raise_for_status()
        
        # Générer un nom de fichier unique
        file_extension = 'jpg'  # Google utilise généralement JPG
        filename = f"avatars/google_{uuid.uuid4().hex}.{file_extension}"
        
        # Sauvegarder le fichier
        file_content = ContentFile(response.content)
        profile.avatar.save(filename, file_content, save=True)
        
        logger.info(f"Avatar Google sauvegardé pour {profile.user.email}")
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde avatar Google: {e}")
        raise

@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_disconnect(request):
    """Déconnecter le compte Google OAuth"""
    
    if not request.user.is_authenticated:
        return Response({
            'success': False,
            'error': 'Utilisateur non authentifié'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        user = request.user
        
        # Vérifier que l'utilisateur a un compte Google lié
        if not hasattr(user, 'google_id') or not user.google_id:
            return Response({
                'success': False,
                'error': 'Aucun compte Google lié'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supprimer l'ID Google
        user.google_id = None
        user.save()
        
        # Logger l'activité
        log_user_activity_with_ip(
            user=user,
            activity_type='oauth_disconnected',
            description='Compte Google déconnecté',
            ip_address=get_client_ip(request),
            metadata={'oauth_provider': 'google'}
        )
        
        return Response({
            'success': True,
            'message': 'Compte Google déconnecté avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur déconnexion Google OAuth: {e}")
        return Response({
            'success': False,
            'error': 'Erreur lors de la déconnexion'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_providers(request):
    """Obtenir la liste des providers OAuth disponibles"""
    
    providers = []
    
    # Google OAuth
    if google_config.client_id:
        providers.append({
            'name': 'google',
            'display_name': 'Google',
            'icon': 'google',
            'color': '#4285f4',
            'available': True
        })
    
    # Autres providers peuvent être ajoutés ici
    # Facebook, GitHub, etc.
    
    return Response({
        'success': True,
        'providers': providers
    })

# Vue de test pour vérifier la configuration OAuth
@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_config_test(request):
    """Tester la configuration OAuth (développement uniquement)"""
    
    if not settings.DEBUG:
        return Response({
            'success': False,
            'error': 'Disponible uniquement en mode développement'
        }, status=status.HTTP_403_FORBIDDEN)
    
    config_status = {
        'google': {
            'client_id_configured': bool(google_config.client_id),
            'client_secret_configured': bool(google_config.client_secret),
            'redirect_uri': google_config.redirect_uri,
            'authorization_url_available': bool(google_config.authorization_url)
        }
    }
    
    return Response({
        'success': True,
        'config_status': config_status
    })
