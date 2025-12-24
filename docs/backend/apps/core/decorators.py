# apps/core/decorators.py
# ===========================

import functools
import time
import logging
from typing import Any, Callable, Dict, Optional
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.response import Response

from .exceptions import RateLimitExceededException, KYCRequiredException, MaintenanceModeException
from .utils import get_client_ip, extract_client_info

logger = logging.getLogger(__name__)


# ===== DÉCORATEURS DE SÉCURITÉ =====

def require_verified_user(view_func: Callable) -> Callable:
    """Décorateur pour exiger un utilisateur vérifié (KYC)."""
    
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentification requise'}, status=401)
        
        if not getattr(request.user, 'is_verified', False):
            raise KYCRequiredException()
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_premium_user(view_func: Callable) -> Callable:
    """Décorateur pour exiger un utilisateur premium."""
    
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentification requise'}, status=401)
        
        # Vérifier le statut premium
        try:
            from apps.referrals.models import PremiumSubscription
            is_premium = PremiumSubscription.objects.filter(
                user=request.user,
                status='active'
            ).exists()
        except ImportError:
            is_premium = False
        
        if not is_premium:
            return JsonResponse({
                'error': 'Abonnement premium requis',
                'code': 'premium_required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def rate_limit(max_requests: int = 60, window: int = 60, key_func: Optional[Callable] = None):
    """
    Décorateur de limitation de taux personnalisable.
    
    Args:
        max_requests: Nombre max de requêtes
        window: Fenêtre de temps en secondes
        key_func: Fonction pour générer la clé de cache
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            
            # Générer la clé de limitation
            if key_func:
                cache_key = key_func(request)
            else:
                user_id = request.user.id if request.user.is_authenticated else 'anonymous'
                ip = get_client_ip(request)
                cache_key = f"rate_limit:{user_id}:{ip}:{view_func.__name__}"
            
            # Vérifier et incrémenter
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= max_requests:
                logger.warning(f"Rate limit exceeded for {cache_key}")
                raise RateLimitExceededException(retry_after=window)
            
            # Incrémenter le compteur
            cache.set(cache_key, current_requests + 1, window)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def check_maintenance_mode(view_func: Callable) -> Callable:
    """Décorateur pour vérifier le mode maintenance."""
    
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        
        # Vérifier le mode maintenance
        maintenance_mode = cache.get('maintenance_mode', False)
        
        if maintenance_mode:
            # Permettre aux admins de passer
            if not (request.user.is_authenticated and request.user.is_staff):
                raise MaintenanceModeException()
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ===== DÉCORATEURS DE PERFORMANCE =====

def log_performance(threshold: float = 1.0):
    """
    Décorateur pour logger les performances lentes.
    
    Args:
        threshold: Seuil en secondes pour considérer comme lent
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = view_func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                
                if execution_time > threshold:
                    logger.warning(
                        f"Slow execution: {view_func.__name__} took {execution_time:.3f}s"
                    )
                else:
                    logger.debug(
                        f"Performance: {view_func.__name__} executed in {execution_time:.3f}s"
                    )
        
        return wrapper
    
    return decorator


def cache_result(timeout: int = 300, key_prefix: str = None, vary_on_user: bool = False):
    """
    Décorateur pour mettre en cache les résultats de fonction.
    
    Args:
        timeout: Durée de cache en secondes
        key_prefix: Préfixe pour la clé de cache
        vary_on_user: Inclure l'ID utilisateur dans la clé
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs) -> Any:
            
            # Construire la clé de cache
            cache_key_parts = [key_prefix or view_func.__name__]
            
            # Ajouter l'ID utilisateur si demandé
            if vary_on_user and hasattr(args[0], 'user') and args[0].user.is_authenticated:
                cache_key_parts.append(f"user_{args[0].user.id}")
            
            # Ajouter les arguments
            if args:
                cache_key_parts.extend([str(arg) for arg in args[1:]])  # Skip 'self' ou 'request'
            
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                cache_key_parts.extend([f"{k}_{v}" for k, v in sorted_kwargs])
            
            cache_key = ":".join(cache_key_parts)
            
            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Exécuter et mettre en cache
            result = view_func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set for {cache_key}")
            
            return result
        
        return wrapper
    
    return decorator


def debounce(wait_time: float):
    """
    Décorateur debounce - évite les exécutions trop rapprochées.
    
    Args:
        wait_time: Temps d'attente en secondes
    """
    
    def decorator(view_func: Callable) -> Callable:
        last_called = {}
        
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs) -> Any:
            key = f"{view_func.__name__}:{id(args)}:{id(kwargs)}"
            now = time.time()
            
            if key in last_called:
                time_since_last = now - last_called[key]
                if time_since_last < wait_time:
                    logger.debug(f"Debounced call to {view_func.__name__}")
                    return None
            
            last_called[key] = now
            return view_func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ===== DÉCORATEURS MÉTIER =====

def game_action_required(view_func: Callable) -> Callable:
    """Décorateur pour les actions de jeu nécessitant des vérifications."""
    
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        
        # Vérifications de base
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentification requise'}, status=401)
        
        # Vérifier les jeux actifs de l'utilisateur
        game_id = kwargs.get('game_id') or kwargs.get('pk')
        if game_id:
            try:
                from apps.games.models import Game
                game = Game.objects.get(id=game_id)
                
                # Vérifier que l'utilisateur participe au jeu
                if request.user not in [game.player1, game.player2]:
                    return JsonResponse({
                        'error': 'Vous ne participez pas à ce jeu'
                    }, status=403)
                
                # Vérifier que le jeu est actif
                if game.status not in ['waiting', 'playing']:
                    return JsonResponse({
                        'error': 'Jeu non actif'
                    }, status=400)
                
                # Ajouter le jeu à la requête pour éviter de le re-récupérer
                request.game = game
                
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du jeu: {e}")
                return JsonResponse({
                    'error': 'Jeu introuvable'
                }, status=404)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def transaction_required(transaction_type: str = None):
    """
    Décorateur pour les actions nécessitant des vérifications de transaction.
    
    Args:
        transaction_type: Type de transaction requis
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentification requise'}, status=401)
            
            # Vérifications spécifiques selon le type de transaction
            if transaction_type == 'withdrawal':
                if not getattr(request.user, 'is_verified', False):
                    return JsonResponse({
                        'error': 'Vérification d\'identité requise pour les retraits'
                    }, status=403)
            
            elif transaction_type == 'bet':
                # Vérifier les limites de jeux simultanés
                from apps.games.models import Game
                active_games = Game.objects.filter(
                    models.Q(player1=request.user) | models.Q(player2=request.user),
                    status__in=['waiting', 'playing']
                ).count()
                
                max_concurrent = getattr(settings, 'MAX_CONCURRENT_GAMES', 5)
                if active_games >= max_concurrent:
                    return JsonResponse({
                        'error': f'Limite de {max_concurrent} jeux simultanés atteinte'
                    }, status=400)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# ===== DÉCORATEURS D'AUDIT =====

def audit_action(action_type: str, sensitive: bool = False):
    """
    Décorateur pour auditer les actions utilisateur.
    
    Args:
        action_type: Type d'action pour l'audit
        sensitive: Si True, log des informations sensibles
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            
            # Informations de base
            user_id = request.user.id if request.user.is_authenticated else None
            client_info = extract_client_info(request)
            
            # Timestamp de début
            start_time = timezone.now()
            
            try:
                result = view_func(request, *args, **kwargs)
                
                # Log de succès
                logger.info(
                    f"AUDIT: {action_type} successful",
                    extra={
                        'user_id': user_id,
                        'action_type': action_type,
                        'ip_address': client_info['ip_address'],
                        'user_agent': client_info['user_agent'],
                        'timestamp': start_time.isoformat(),
                        'status': 'success',
                        'response_code': getattr(result, 'status_code', 200)
                    }
                )
                
                return result
                
            except Exception as e:
                # Log d'erreur
                logger.error(
                    f"AUDIT: {action_type} failed - {str(e)}",
                    extra={
                        'user_id': user_id,
                        'action_type': action_type,
                        'ip_address': client_info['ip_address'],
                        'timestamp': start_time.isoformat(),
                        'status': 'error',
                        'error': str(e)
                    }
                )
                raise
        
        return wrapper
    
    return decorator


def log_api_usage(view_func: Callable) -> Callable:
    """Décorateur pour logger l'usage de l'API."""
    
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        
        start_time = time.time()
        
        # Informations de la requête
        endpoint = request.path
        method = request.method
        user_id = request.user.id if request.user.is_authenticated else None
        client_info = extract_client_info(request)
        
        try:
            result = view_func(request, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Logger l'usage
            logger.info(
                f"API: {method} {endpoint}",
                extra={
                    'endpoint': endpoint,
                    'method': method,
                    'user_id': user_id,
                    'ip_address': client_info['ip_address'],
                    'execution_time': execution_time,
                    'status_code': getattr(result, 'status_code', 200),
                    'user_agent': client_info['user_agent'],
                    'device_type': client_info['device_type']
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"API ERROR: {method} {endpoint} - {str(e)}",
                extra={
                    'endpoint': endpoint,
                    'method': method,
                    'user_id': user_id,
                    'ip_address': client_info['ip_address'],
                    'execution_time': execution_time,
                    'error': str(e)
                }
            )
            raise
    
    return wrapper


# ===== DÉCORATEURS DE VALIDATION =====

def validate_json_content_type(view_func: Callable) -> Callable:
    """Décorateur pour valider le Content-Type JSON."""
    
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            
            if not content_type.startswith('application/json'):
                return JsonResponse({
                    'error': 'Content-Type doit être application/json'
                }, status=400)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validate_request_size(max_size: int = 1048576):  # 1MB par défaut
    """
    Décorateur pour valider la taille de la requête.
    
    Args:
        max_size: Taille maximale en octets
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            
            content_length = int(request.META.get('CONTENT_LENGTH', 0))
            
            if content_length > max_size:
                return JsonResponse({
                    'error': f'Requête trop volumineuse (max: {max_size} octets)'
                }, status=413)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# ===== DÉCORATEURS UTILITAIRES =====

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Décorateur pour retry automatique en cas d'échec.
    
    Args:
        max_retries: Nombre maximum de tentatives
        delay: Délai initial entre tentatives
        backoff: Facteur de backoff exponentiel
    """
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                        raise
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    
    return decorator


def handle_exceptions(*exception_types, default_response=None):
    """
    Décorateur pour gérer des types d'exceptions spécifiques.
    
    Args:
        exception_types: Types d'exceptions à capturer
        default_response: Réponse par défaut en cas d'exception
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs) -> Any:
            
            try:
                return view_func(*args, **kwargs)
                
            except exception_types as e:
                logger.error(f"Handled exception in {view_func.__name__}: {e}")
                
                if default_response:
                    return default_response
                else:
                    return JsonResponse({
                        'error': 'Une erreur est survenue',
                        'code': e.__class__.__name__.lower()
                    }, status=500)
        
        return wrapper
    
    return decorator


def feature_flag(flag_name: str, default: bool = False):
    """
    Décorateur pour activer/désactiver des fonctionnalités via feature flags.
    
    Args:
        flag_name: Nom du feature flag
        default: Valeur par défaut si le flag n'existe pas
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs) -> Any:
            
            # Vérifier le feature flag (cache ou BDD)
            flag_value = cache.get(f"feature_flag:{flag_name}", default)
            
            if not flag_value:
                return JsonResponse({
                    'error': 'Fonctionnalité temporairement indisponible',
                    'code': 'feature_disabled'
                }, status=503)
            
            return view_func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ===== COMPOSITIONS DE DÉCORATEURS =====

def api_endpoint(
    rate_limit_requests: int = 60,
    cache_timeout: int = 0,
    require_auth: bool = True,
    require_verified: bool = False,
    audit_action_type: str = None
):
    """
    Décorateur composite pour endpoints API standard.
    
    Args:
        rate_limit_requests: Limite de requêtes par minute
        cache_timeout: Timeout de cache (0 = pas de cache)
        require_auth: Authentification requise
        require_verified: Utilisateur vérifié requis
        audit_action_type: Type d'action pour audit
    """
    
    def decorator(view_func: Callable) -> Callable:
        
        # Appliquer les décorateurs en ordre inverse
        decorated_func = view_func
        
        # Audit (en premier pour capturer tout)
        if audit_action_type:
            decorated_func = audit_action(audit_action_type)(decorated_func)
        
        # Logging API
        decorated_func = log_api_usage(decorated_func)
        
        # Vérifications utilisateur
        if require_verified:
            decorated_func = require_verified_user(decorated_func)
        elif require_auth:
            # Authentification de base avec Django
            from django.contrib.auth.decorators import login_required
            decorated_func = login_required(decorated_func)
        
        # Rate limiting
        if rate_limit_requests > 0:
            decorated_func = rate_limit(
                max_requests=rate_limit_requests,
                window=60
            )(decorated_func)
        
        # Cache (en dernier pour cacher le résultat final)
        if cache_timeout > 0:
            decorated_func = cache_result(
                timeout=cache_timeout,
                vary_on_user=require_auth
            )(decorated_func)
        
        # Performance logging
        decorated_func = log_performance(threshold=2.0)(decorated_func)
        
        return decorated_func
    
    return decorator
