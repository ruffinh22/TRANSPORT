# apps/core/middleware.py
# ==========================

import time
import json
import logging
from django.db import models  # Ajoutez cet import en haut du fichier
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.conf import settings
from django.utils.translation import get_language
from decimal import Decimal
import uuid

from .exceptions import RateLimitExceededException, MaintenanceModeException
from . import AUDIT_EVENT_TYPES, PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware pour ajouter les en-têtes de sécurité essentiels.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Ajouter les en-têtes de sécurité."""
        
        # Protection XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS pour HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP pour les ressources (avec support développement)
        if hasattr(settings, 'CSP_SCRIPT_SRC'):
            # Mode développement avec CSP configurée
            script_src = ' '.join(settings.CSP_SCRIPT_SRC)
            connect_src = ' '.join(settings.CSP_CONNECT_SRC)
            style_src = ' '.join(settings.CSP_STYLE_SRC)
            img_src = ' '.join(settings.CSP_IMG_SRC)
            font_src = ' '.join(settings.CSP_FONT_SRC)
            
            response['Content-Security-Policy'] = (
                f"default-src 'self'; "
                f"script-src {script_src}; "
                f"style-src {style_src}; "
                f"img-src {img_src}; "
                f"font-src {font_src}; "
                f"connect-src {connect_src}; "
                f"object-src 'none';"
            )
        else:
            # Mode production
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://pagead2.googlesyndication.com https://api.feexpay.me; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' wss: ws: https://api.feexpay.me; "
                "object-src 'none';"
            )
        
        # Référent Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (format corrigé)
        response['Permissions-Policy'] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=self"
        )
        
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware pour ajouter les en-têtes de sécurité et CORS.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Origines autorisées pour CORS
        self.allowed_origins = [
            'http://localhost:3000',
            'http://localhost:3001',
            'https://rumorush.com',
            'https://www.rumorush.com',
            'https://app.rumorush.com'
        ]
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Ajouter les en-têtes CORS et de sécurité."""
        
        # En-têtes CORS
        origin = request.META.get('HTTP_ORIGIN')
        if origin and self.is_origin_allowed(origin):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Authorization, Content-Type, X-Requested-With, '
                'X-Currency, X-Language, X-Request-ID, X-Device-ID'
            )
            response['Access-Control-Max-Age'] = '86400'
        
        # En-têtes de sécurité
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Vérifier si l'origine est autorisée."""
        return origin in self.allowed_origins
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Gérer les requêtes OPTIONS preflight."""
        if request.method == 'OPTIONS':
            response = HttpResponse()
            return self.process_response(request, response)
        return None


class DeviceDetectionMiddleware(MiddlewareMixin):
    """
    Middleware pour détecter le type d'appareil et optimiser la réponse.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Analyser le User-Agent et ajouter les infos d'appareil."""
        
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Détection mobile
        mobile_patterns = [
            'mobile', 'android', 'iphone', 'ipod', 'blackberry',
            'windows phone', 'palm', 'smartphone'
        ]
        request.is_mobile = any(pattern in user_agent for pattern in mobile_patterns)
        
        # Détection tablette
        tablet_patterns = ['ipad', 'tablet', 'kindle', 'playbook']
        request.is_tablet = any(pattern in user_agent for pattern in tablet_patterns)
        
        # Détection bot/crawler
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'googlebot', 'bingbot', 'facebookexternalhit'
        ]
        request.is_bot = any(pattern in user_agent for pattern in bot_patterns)
        
        # Type d'appareil
        if request.is_mobile:
            request.device_type = 'mobile'
        elif request.is_tablet:
            request.device_type = 'tablet'
        else:
            request.device_type = 'desktop'
        
        # Informations de navigateur
        if 'chrome' in user_agent:
            request.browser = 'chrome'
        elif 'firefox' in user_agent:
            request.browser = 'firefox'
        elif 'safari' in user_agent:
            request.browser = 'safari'
        elif 'edge' in user_agent:
            request.browser = 'edge'
        else:
            request.browser = 'unknown'


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les performances et ajouter des métriques.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Initialiser les métriques de performance."""
        request.perf_start = time.time()
        request.perf_queries_start = self.get_db_queries_count()
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Ajouter les métriques de performance."""
        
        if hasattr(request, 'perf_start'):
            # Temps de traitement total
            total_time = time.time() - request.perf_start
            response['X-Processing-Time'] = f"{total_time:.3f}s"
            
            # Nombre de requêtes DB
            if hasattr(request, 'perf_queries_start'):
                queries_count = self.get_db_queries_count() - request.perf_queries_start
                response['X-DB-Queries'] = str(queries_count)
            
            # Avertissement pour les requêtes lentes
            if total_time > 2.0:  # Plus de 2 secondes
                logger.warning(
                    f"Slow response: {request.method} {request.path} "
                    f"took {total_time:.2f}s"
                )
        
        # Compression pour les réponses JSON volumineuses
        if (response.get('Content-Type', '').startswith('application/json') and 
            len(response.content) > 1000):  # Plus de 1KB
            response['Vary'] = 'Accept-Encoding'
        
        return response
    
    def get_db_queries_count(self) -> int:
        """Obtenir le nombre de requêtes DB exécutées."""
        try:
            from django.db import connection
            return len(connection.queries)
        except:
            return 0


class LoadBalancingMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer la répartition de charge et la santé des serveurs.
    """
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Vérifier la santé du serveur."""
        
        # Endpoint de santé
        if request.path == '/health/':
            return self.health_check_response()
        
        # Vérifier la charge du serveur
        if self.is_server_overloaded():
            if not (hasattr(request, 'user') and request.user.is_staff):
                return JsonResponse({
                    'error': 'Server temporarily overloaded',
                    'message': 'Le serveur est temporairement surchargé',
                    'code': 'SERVER_OVERLOADED',
                    'retry_after': 30
                }, status=503)
        
        return None
    
    def health_check_response(self) -> JsonResponse:
        """Réponse du health check."""
        from django.db import connections
        
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'checks': {}
        }
        
        try:
            # Vérifier la base de données
            db_conn = connections['default']
            db_conn.ensure_connection()
            health_status['checks']['database'] = 'ok'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = f'error: {str(e)}'
        
        try:
            # Vérifier Redis/Cache
            cache.get('health_check')
            health_status['checks']['cache'] = 'ok'
        except Exception as e:
            health_status['checks']['cache'] = f'error: {str(e)}'
        
        # Métriques système
        try:
            import psutil
            health_status['metrics'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            pass
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JsonResponse(health_status, status=status_code)
    
    def is_server_overloaded(self) -> bool:
        """Vérifier si le serveur est surchargé."""
        try:
            import psutil
            
            # Vérifier CPU et mémoire
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Seuils de charge
            if cpu_percent > 90 or memory_percent > 90:
                return True
            
            # Vérifier les connexions actives
            active_connections = cache.get('active_connections', 0)
            if active_connections > 1000:  # Plus de 1000 connexions actives
                return True
            
            return False
        except ImportError:
            # psutil non disponible, ne pas bloquer
            return False


class GameSessionMiddleware(MiddlewareMixin):
    """
    Middleware spécialisé pour gérer les sessions de jeu.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Gérer les sessions de jeu actives."""
        
        # Seulement pour les endpoints de jeu
        if not request.path.startswith('/api/games/'):
            return
        
        # Vérifier si l'utilisateur a des jeux actifs
        if hasattr(request, 'user') and request.user.is_authenticated:
            active_games = self.get_active_games(request.user)
            request.active_games = active_games
            request.active_games_count = len(active_games)
            
            # Limiter le nombre de jeux simultanés
            if request.method == 'POST' and 'create' in request.path:
                max_games = getattr(settings, 'MAX_CONCURRENT_GAMES', 5)
                if request.active_games_count >= max_games:
                    logger.warning(
                        f"User {request.user.username} tried to exceed game limit "
                        f"({request.active_games_count}/{max_games})"
                    )
    
    def get_active_games(self, user) -> list:
        """Obtenir les jeux actifs de l'utilisateur."""
        try:
            from apps.games.models import Game
            return list(Game.objects.filter(
                models.Q(player1=user) | models.Q(player2=user),
                status__in=['waiting', 'playing']
            ).values_list('id', flat=True))
        except Exception:
            return []
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Ajouter les informations de session de jeu."""
        
        if hasattr(request, 'active_games_count'):
            response['X-Active-Games'] = str(request.active_games_count)
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware pour limiter le nombre de requêtes par utilisateur/IP.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Configuration des limites
        self.rate_limits = {
            'anonymous': {
                'requests': 30,
                'window': 60,  # 1 minute
                'burst': 10
            },
            'authenticated': {
                'requests': PERFORMANCE_CONFIG['API_RATE_LIMIT_PER_MINUTE'],
                'window': 60,
                'burst': 20
            },
            'premium': {
                'requests': 200,
                'window': 60,
                'burst': 50
            }
        }
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Vérifier les limites de taux."""
        
        # Identifier l'utilisateur
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_type = 'premium' if self.is_premium_user(request.user) else 'authenticated'
            identifier = f"user:{request.user.id}"
        else:
            user_type = 'anonymous'
            identifier = f"ip:{self.get_client_ip(request)}"
        
        # Vérifier les limites
        if self.is_rate_limited(identifier, user_type):
            logger.warning(f"Rate limit exceeded for {identifier}")
            return JsonResponse({
                'error': 'Limite de taux dépassée',
                'code': 'RATE_LIMIT_EXCEEDED',
                'retry_after': 60
            }, status=429)
        
        return None
    
    def is_rate_limited(self, identifier: str, user_type: str) -> bool:
        """Vérifier si l'utilisateur a dépassé les limites."""
        config = self.rate_limits[user_type]
        
        # Clés de cache pour sliding window
        current_window = int(time.time()) // config['window']
        prev_window = current_window - 1
        
        current_key = f"rate_limit:{identifier}:{current_window}"
        prev_key = f"rate_limit:{identifier}:{prev_window}"
        
        # Compter les requêtes
        current_count = cache.get(current_key, 0)
        prev_count = cache.get(prev_key, 0)
        
        # Calcul sliding window
        window_start = time.time() - config['window']
        weight = (time.time() - window_start) / config['window']
        estimated_count = prev_count * (1 - weight) + current_count
        
        if estimated_count >= config['requests']:
            return True
        
        # Incrémenter le compteur
        cache.set(current_key, current_count + 1, config['window'] * 2)
        
        return False
    
    def is_premium_user(self, user) -> bool:
        """Vérifier si l'utilisateur est premium."""
        try:
            from apps.referrals.models import PremiumSubscription
            return PremiumSubscription.objects.filter(
                user=user,
                status='active'
            ).exists()
        except:
            return False
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Obtenir l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware pour logger les requêtes importantes et détecter les anomalies.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Endpoints sensibles à logger
        self.sensitive_endpoints = [
            '/api/auth/',
            '/api/payments/',
            '/api/games/',
            '/api/users/profile',
            '/admin/'
        ]
    
    def process_request(self, request: HttpRequest) -> None:
        """Traitement avant la requête."""
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())[:8]
        
        # Logger les requêtes sensibles
        if any(request.path.startswith(endpoint) for endpoint in self.sensitive_endpoints):
            logger.info(
                f"[{request.request_id}] {request.method} {request.path} "
                f"from {self.get_client_ip(request)} "
                f"user: {getattr(request.user, 'username', 'anonymous') if hasattr(request, 'user') else 'unknown'}"
            )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Traitement après la requête."""
        
        # Calculer le temps de traitement
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Logger les requêtes lentes
            if duration > 1.0:  # Plus d'1 seconde
                logger.warning(
                    f"[{request_id}] Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s (status: {response.status_code})"
                )
            
            # Ajouter l'ID de requête dans les headers
            response['X-Request-ID'] = request_id
            response['X-Response-Time'] = f"{duration:.3f}"
        
        # Logger les erreurs
        if response.status_code >= 400:
            user_info = 'anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = request.user.username
            
            logger.error(
                f"[{getattr(request, 'request_id', 'unknown')}] "
                f"Error {response.status_code}: {request.method} {request.path} "
                f"user: {user_info}"
            )
        
        return response
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Middleware pour créer un audit trail des actions importantes.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Actions à auditer
        self.audit_patterns = {
            r'/api/auth/login': 'USER_LOGIN',
            r'/api/auth/logout': 'USER_LOGOUT',
            r'/api/auth/register': 'USER_REGISTER',
            r'/api/games/.*/join': 'GAME_JOIN',
            r'/api/games/create': 'GAME_CREATE',
            r'/api/payments/deposit': 'TRANSACTION_CREATE',
            r'/api/payments/withdraw': 'WITHDRAWAL_REQUEST',
            r'/api/users/kyc': 'KYC_SUBMIT'
        }
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Créer l'entrée d'audit si nécessaire."""
        
        # Seulement pour les requêtes réussies
        if response.status_code < 400:
            event_type = self.get_event_type(request.path, request.method)
            
            if event_type and hasattr(request, 'user') and request.user.is_authenticated:
                self.create_audit_entry(request, response, event_type)
        
        return response
    
    def get_event_type(self, path: str, method: str) -> Optional[str]:
        """Déterminer le type d'événement à auditer."""
        import re
        
        for pattern, event_type in self.audit_patterns.items():
            if re.search(pattern, path) and method in ['POST', 'PUT', 'DELETE']:
                return event_type
        
        return None
    
    def create_audit_entry(self, request: HttpRequest, response: HttpResponse, event_type: str) -> None:
        """Créer une entrée d'audit."""
        try:
            # Import tardif pour éviter les dépendances circulaires
            from apps.analytics.models import UserActivity
            
            UserActivity.objects.create(
                user=request.user,
                activity_type=event_type,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                request_id=getattr(request, 'request_id', ''),
                metadata={
                    'timestamp': timezone.now().isoformat(),
                    'session_key': request.session.session_key if hasattr(request, 'session') else None,
                    'language': get_language(),
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit entry: {e}")
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class CurrencyMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer les devises et conversions automatiques.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Détecter et configurer la devise de l'utilisateur."""
        
        # Devise par défaut
        default_currency = 'FCFA'
        
        # 1. Vérifier dans les headers
        currency_header = request.META.get('HTTP_X_CURRENCY')
        if currency_header and self.is_valid_currency(currency_header):
            request.user_currency = currency_header.upper()
            return
        
        # 2. Vérifier dans la session
        if hasattr(request, 'session'):
            session_currency = request.session.get('currency')
            if session_currency and self.is_valid_currency(session_currency):
                request.user_currency = session_currency
                return
        
        # 3. Vérifier le profil utilisateur
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Détecter la devise préférée par pays
                user_currency = self.detect_currency_by_country(request.user.country)
                if user_currency:
                    request.user_currency = user_currency
                    return
            except:
                pass
        
        # 4. Détecter par géolocalisation IP
        detected_currency = self.detect_currency_by_ip(request)
        request.user_currency = detected_currency or default_currency
    
    def is_valid_currency(self, currency: str) -> bool:
        """Vérifier si la devise est supportée."""
        from . import SUPPORTED_CURRENCIES
        return currency.upper() in SUPPORTED_CURRENCIES
    
    def detect_currency_by_country(self, country_code: str) -> Optional[str]:
        """Détecter la devise par code pays."""
        country_currency_map = {
            'CI': 'FCFA',  # Côte d'Ivoire
            'SN': 'FCFA',  # Sénégal
            'ML': 'FCFA',  # Mali
            'BF': 'FCFA',  # Burkina Faso
            'NE': 'FCFA',  # Niger
            'TG': 'FCFA',  # Togo
            'BJ': 'FCFA',  # Bénin
            'GN': 'FCFA',  # Guinée-Bissau
            'FR': 'EUR',   # France
            'DE': 'EUR',   # Allemagne
            'IT': 'EUR',   # Italie
            'ES': 'EUR',   # Espagne
            'US': 'USD',   # États-Unis
            'GB': 'USD',   # Royaume-Uni (pour simplifier)
            'CA': 'USD',   # Canada
        }
        
        return country_currency_map.get(country_code.upper())
    
    def detect_currency_by_ip(self, request: HttpRequest) -> Optional[str]:
        """Détecter la devise par géolocalisation IP."""
        # Cette fonctionnalité nécessiterait une API de géolocalisation
        # Pour l'instant, retourner None et utiliser la devise par défaut
        return None


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Middleware pour activer le mode maintenance.
    """
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Vérifier si le mode maintenance est activé."""
        
        # Vérifier le paramètre de maintenance
        maintenance_mode = cache.get('maintenance_mode', False)
        
        if maintenance_mode:
            # Permettre l'accès aux admins
            if hasattr(request, 'user') and request.user.is_staff:
                return None
            
            # Permettre l'accès aux endpoints de santé
            if request.path.startswith('/health/') or request.path.startswith('/status/'):
                return None
            
            # Mode maintenance activé
            logger.info(f"Maintenance mode: blocking request to {request.path}")
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Service temporarily unavailable',
                    'message': 'RUMO RUSH est en maintenance. Veuillez réessayer plus tard.',
                    'code': 'MAINTENANCE_MODE',
                    'estimated_duration': cache.get('maintenance_duration', 'inconnue')
                }, status=503)
            else:
                # Page de maintenance HTML
                return HttpResponse(
                    self.get_maintenance_page(),
                    status=503,
                    content_type='text/html'
                )
        
        return None
    
    def get_maintenance_page(self) -> str:
        """Générer la page de maintenance."""
        return """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RUMO RUSH - Maintenance</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
                h1 { font-size: 2.5em; margin-bottom: 20px; }
                p { font-size: 1.2em; margin-bottom: 15px; }
                .logo { font-size: 3em; margin-bottom: 30px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🎮</div>
                <h1>RUMO RUSH</h1>
                <h2>Maintenance en cours</h2>
                <p>Nous améliorons votre expérience de jeu.</p>
                <p>Merci de votre patience, nous revenons bientôt !</p>
                <p><small>Suivez-nous sur nos réseaux sociaux pour les mises à jour.</small></p>
            </div>
        </body>
        </html>
        """


# Correction pour la fin du fichier middleware.py

class CorsMiddleware(MiddlewareMixin):
    """
    Middleware CORS personnalisé pour la gestion des origines.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Origines autorisées
        self.allowed_origins = [
            'http://localhost:3000',
            'http://localhost:3001',
            'https://rumorush.com',
            'https://www.rumorush.com',
            'https://app.rumorush.com'
        ]
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Ajouter les en-têtes CORS appropriés."""
        
        origin = request.META.get('HTTP_ORIGIN')
        
        if origin and self.is_origin_allowed(origin):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Authorization, Content-Type, X-Requested-With, '
                'X-Currency, X-Language, X-Request-ID, X-Device-ID'
            )
            response['Access-Control-Max-Age'] = '86400'
        
        return response
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Vérifier si l'origine est autorisée."""
        return origin in self.allowed_origins
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Gérer les requêtes OPTIONS preflight."""
        if request.method == 'OPTIONS':
            response = HttpResponse()
            return self.process_response(request, response)
        return None

