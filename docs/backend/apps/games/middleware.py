# apps/games/middleware.py
# ========================

import json
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone

User = get_user_model()


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    Middleware d'authentification pour WebSocket.
    Gère l'authentification via session ou token JWT.
    """
    
    def __init__(self, inner):
        super().__init__(inner)
    
    async def __call__(self, scope, receive, send):
        """Traiter la connexion WebSocket avec authentification."""
        
        # Vérifier si c'est une connexion WebSocket
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)
        
        # Extraire les informations d'authentification
        user = await self.get_user_from_scope(scope)
        
        # Ajouter l'utilisateur au scope
        scope['user'] = user
        
        # Ajouter des métadonnées de connexion
        scope['websocket_metadata'] = {
            'connected_at': timezone.now(),
            'path': scope.get('path', ''),
            'user_id': user.id if user.is_authenticated else None,
            'is_authenticated': user.is_authenticated
        }
        
        return await self.inner(scope, receive, send)
    
    async def get_user_from_scope(self, scope):
        """Extraire l'utilisateur authentifié depuis le scope."""
        try:
            # Méthode 1: Authentification par session (cookies)
            session_user = await self.get_user_from_session(scope)
            if session_user and session_user.is_authenticated:
                return session_user
            
            # Méthode 2: Authentification par token JWT
            jwt_user = await self.get_user_from_jwt(scope)
            if jwt_user and jwt_user.is_authenticated:
                return jwt_user
            
            # Méthode 3: Authentification par query params (développement uniquement)
            if scope.get('query_string'):
                query_user = await self.get_user_from_query(scope)
                if query_user and query_user.is_authenticated:
                    return query_user
            
        except Exception as e:
            print(f"Erreur authentification WebSocket: {e}")
        
        # Retourner utilisateur anonyme par défaut
        return AnonymousUser()
    
    async def get_user_from_session(self, scope):
        """Authentification via session Django."""
        try:
            # Extraire les cookies de la requête
            cookies = {}
            for header_name, header_value in scope.get('headers', []):
                if header_name == b'cookie':
                    cookie_header = header_value.decode('latin1')
                    for cookie in cookie_header.split(';'):
                        if '=' in cookie:
                            name, value = cookie.strip().split('=', 1)
                            cookies[name] = value
            
            # Récupérer l'ID de session
            session_key = cookies.get('sessionid')
            if not session_key:
                return AnonymousUser()
            
            # Charger la session
            session = await database_sync_to_async(Session.objects.get)(
                session_key=session_key,
                expire_date__gte=timezone.now()
            )
            
            # Décoder les données de session
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            
            if user_id:
                user = await database_sync_to_async(User.objects.get)(id=user_id)
                return user
                
        except (Session.DoesNotExist, User.DoesNotExist):
            pass
        except Exception as e:
            print(f"Erreur session auth: {e}")
        
        return AnonymousUser()
    
    async def get_user_from_jwt(self, scope):
        """Authentification via token JWT."""
        try:
            # Extraire le token depuis les headers ou query params
            token = None
            
            # Vérifier dans les headers Authorization
            for header_name, header_value in scope.get('headers', []):
                if header_name == b'authorization':
                    auth_header = header_value.decode('utf-8')
                    if auth_header.startswith('Bearer '):
                        token = auth_header[7:]  # Enlever "Bearer "
                        break
            
            # Si pas trouvé dans les headers, vérifier query params
            if not token and scope.get('query_string'):
                query_params = parse_qs(scope['query_string'].decode('utf-8'))
                token = query_params.get('token', [None])[0]
            
            if not token:
                return AnonymousUser()
            
            # Décoder et valider le JWT
            user = await self.validate_jwt_token(token)
            return user if user else AnonymousUser()
            
        except Exception as e:
            print(f"Erreur JWT auth: {e}")
        
        return AnonymousUser()
    
    async def get_user_from_query(self, scope):
        """Authentification via query parameters (développement seulement)."""
        try:
            query_params = parse_qs(scope['query_string'].decode('utf-8'))
            user_id = query_params.get('user_id', [None])[0]
            
            if user_id:
                user = await database_sync_to_async(User.objects.get)(id=user_id)
                return user
                
        except User.DoesNotExist:
            pass
        except Exception as e:
            print(f"Erreur query auth: {e}")
        
        return AnonymousUser()
    
    @database_sync_to_async
    def validate_jwt_token(self, token):
        """Valider un token JWT et retourner l'utilisateur."""
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.authentication import JWTAuthentication
            
            # Valider le token
            UntypedToken(token)
            
            # Extraire l'utilisateur
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            return user
            
        except Exception as e:
            print(f"Erreur validation JWT: {e}")
            return None


class WebSocketRateLimitMiddleware(BaseMiddleware):
    """
    Middleware de limitation du taux pour WebSocket.
    Prévient les abus et spam de connexions.
    """
    
    def __init__(self, inner, max_connections_per_user=10, max_messages_per_minute=60):
        super().__init__(inner)
        self.max_connections_per_user = max_connections_per_user
        self.max_messages_per_minute = max_messages_per_minute
        self.connections = {}  # user_id -> count
        self.message_counts = {}  # user_id -> {minute: count}
    
    async def __call__(self, scope, receive, send):
        """Appliquer la limitation du taux."""
        
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)
        
        user = scope.get('user')
        if not user or not user.is_authenticated:
            # Permettre les connexions anonymes mais avec limite globale
            return await self.inner(scope, receive, send)
        
        user_id = str(user.id)
        
        # Vérifier le nombre de connexions
        current_connections = self.connections.get(user_id, 0)
        if current_connections >= self.max_connections_per_user:
            await send({
                'type': 'websocket.close',
                'code': 4008  # Policy violation
            })
            return
        
        # Incrémenter le compteur de connexions
        self.connections[user_id] = current_connections + 1
        
        try:
            # Wrapper pour surveiller les messages
            async def rate_limited_receive():
                message = await receive()
                
                # Compter les messages reçus
                if message['type'] == 'websocket.receive':
                    await self.track_message(user_id)
                
                return message
            
            return await self.inner(scope, rate_limited_receive, send)
            
        finally:
            # Décrémenter le compteur à la déconnexion
            if user_id in self.connections:
                self.connections[user_id] = max(0, self.connections[user_id] - 1)
                if self.connections[user_id] == 0:
                    del self.connections[user_id]
    
    async def track_message(self, user_id):
        """Suivre les messages par minute."""
        current_minute = int(timezone.now().timestamp() // 60)
        
        if user_id not in self.message_counts:
            self.message_counts[user_id] = {}
        
        # Nettoyer les anciens compteurs (plus de 2 minutes)
        old_minutes = [
            minute for minute in self.message_counts[user_id].keys()
            if minute < current_minute - 2
        ]
        for old_minute in old_minutes:
            del self.message_counts[user_id][old_minute]
        
        # Incrémenter le compteur pour la minute actuelle
        self.message_counts[user_id][current_minute] = \
            self.message_counts[user_id].get(current_minute, 0) + 1
        
        # Vérifier la limite
        if self.message_counts[user_id][current_minute] > self.max_messages_per_minute:
            raise Exception(f"Limite de messages dépassée pour l'utilisateur {user_id}")


class WebSocketLoggingMiddleware(BaseMiddleware):
    """
    Middleware de logging pour WebSocket.
    Enregistre les connexions et événements pour le monitoring.
    """
    
    def __init__(self, inner):
        super().__init__(inner)
    
    async def __call__(self, scope, receive, send):
        """Logger les événements WebSocket."""
        
        if scope['type'] != 'websocket':
            return await self.inner(scope, receive, send)
        
        user = scope.get('user')
        path = scope.get('path', '')
        metadata = scope.get('websocket_metadata', {})
        
        # Logger la connexion
        print(f"[WebSocket] Connexion: {path} | User: {user.username if user.is_authenticated else 'Anonymous'}")
        
        # Wrapper pour logger les événements
        async def logged_receive():
            message = await receive()
            
            if message['type'] == 'websocket.connect':
                print(f"[WebSocket] CONNECT: {path}")
            elif message['type'] == 'websocket.disconnect':
                print(f"[WebSocket] DISCONNECT: {path}")
            elif message['type'] == 'websocket.receive':
                # Logger les messages (attention à la confidentialité)
                text = message.get('text', '')
                if len(text) > 100:
                    text = text[:100] + '...'
                print(f"[WebSocket] RECEIVE: {path} | Data: {text}")
            
            return message
        
        async def logged_send(message):
            if message['type'] == 'websocket.send':
                # Logger les messages envoyés (avec limitation)
                text = message.get('text', '')
                if len(text) > 100:
                    text = text[:100] + '...'
                print(f"[WebSocket] SEND: {path} | Data: {text}")
            
            return await send(message)
        
        return await self.inner(scope, logged_receive, logged_send)


# Stack de middlewares recommandé pour production
def get_websocket_application():
    """Retourner l'application WebSocket avec tous les middlewares."""
    from apps.games.routing import websocket_urlpatterns
    
    return WebSocketLoggingMiddleware(
        WebSocketRateLimitMiddleware(
            WebSocketAuthMiddleware(
                AuthMiddlewareStack(
                    URLRouter(websocket_urlpatterns)
                )
            )
        )
    )