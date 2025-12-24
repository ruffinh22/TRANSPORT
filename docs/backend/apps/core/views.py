# apps/core/views.py
# ======================

import time
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model

from rest_framework import status, generics, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .decorators import (
    log_performance, audit_action, rate_limit, 
    api_endpoint, check_maintenance_mode
)
from .permissions import IsVerifiedUser, MaintenanceModePermission
from .pagination import StandardResultsSetPagination
from .utils import (
    get_exchange_rate, convert_currency, format_currency,
    get_client_ip, extract_client_info
)
from .exceptions import (
    RumoRushException, MaintenanceModeException,
    InvalidCurrencyException
)
from . import (
    SUPPORTED_CURRENCIES, DEFAULT_EXCHANGE_RATES, 
    BUSINESS_LIMITS, APP_VERSION, APP_NAME
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ===== VUES DE SANTÉ ET MONITORING =====

@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(30)  # Cache pendant 30 secondes
def health_check(request):
    """
    Endpoint de santé pour le monitoring de l'application.
    Utilisé par les load balancers et outils de surveillance.
    """
    start_time = time.time()
    
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': APP_VERSION,
        'app_name': APP_NAME,
        'checks': {}
    }
    
    try:
        # 1. Vérifier la base de données
        try:
            from django.db import connections
            db_conn = connections['default']
            db_conn.ensure_connection()
            
            # Test simple de requête
            user_count = User.objects.count()
            health_status['checks']['database'] = {
                'status': 'ok',
                'users_count': user_count
            }
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 2. Vérifier Redis/Cache
        try:
            cache.set('health_check_key', 'ok', 10)
            if cache.get('health_check_key') == 'ok':
                health_status['checks']['cache'] = {'status': 'ok'}
                cache.delete('health_check_key')
            else:
                raise Exception("Cache read/write failed")
        except Exception as e:
            health_status['checks']['cache'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 3. Vérifier les services externes (optionnel)
        health_status['checks']['external_services'] = _check_external_services()
        
        # 4. Métriques système
        try:
            import psutil
            health_status['metrics'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
            }
        except ImportError:
            health_status['metrics'] = {
                'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
            }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


def _check_external_services() -> Dict[str, Any]:
    """Vérifier les services externes critiques."""
    services_status = {}
    
    # Payment providers
    services_status['payment_providers'] = {
        'orange_money': 'unknown',  # À implémenter
        'mtn_money': 'unknown',     # À implémenter
        'moov_money': 'unknown'     # À implémenter
    }
    
    return services_status


@api_view(['GET'])
@permission_classes([AllowAny])
def status_check(request):
    """
    Endpoint de statut simple pour les health checks légers.
    """
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'version': APP_VERSION
    })


# ===== VUES DE CONFIGURATION ET MÉTADONNÉES =====

class ConfigurationView(APIView):
    """
    Vue pour obtenir la configuration client de l'application.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(cache_page(300))  # Cache 5 minutes
    def get(self, request):
        """Retourner la configuration pour le client."""
        
        config = {
            'app': {
                'name': APP_NAME,
                'version': APP_VERSION,
                'environment': getattr(settings, 'ENVIRONMENT', 'production')
            },
            'currencies': self._get_currencies_config(),
            'limits': self._get_business_limits(),
            'features': self._get_feature_flags(request),
            'regions': self._get_supported_regions(),
            'payment_methods': self._get_payment_methods(),
            'game_types': self._get_available_game_types(),
            'maintenance_mode': cache.get('maintenance_mode', False)
        }
        
        return Response(config)
    
    def _get_currencies_config(self) -> Dict[str, Any]:
        """Configuration des devises supportées."""
        return {
            code: {
                'symbol': info['symbol'],
                'decimal_places': info['decimal_places'],
                'min_amount': info['min_amount'],
                'max_amount': info['max_amount'],
                'region': info['region']
            }
            for code, info in SUPPORTED_CURRENCIES.items()
        }
    
    def _get_business_limits(self) -> Dict[str, Any]:
        """Limites métier publiques."""
        return {
            'min_bet_amount': BUSINESS_LIMITS['MIN_BET_AMOUNT'],
            'max_bet_amount': BUSINESS_LIMITS['MAX_BET_AMOUNT'],
            'max_concurrent_games': BUSINESS_LIMITS['MAX_CONCURRENT_GAMES'],
            'game_timeout_seconds': BUSINESS_LIMITS['GAME_TIMEOUT_SECONDS']
        }
    
    def _get_feature_flags(self, request) -> Dict[str, bool]:
        """Feature flags selon l'utilisateur."""
        flags = {
            'tournaments': cache.get('feature_flag:tournaments', True),
            'crypto_payments': cache.get('feature_flag:crypto_payments', False),
            'live_chat': cache.get('feature_flag:live_chat', True),
            'social_features': cache.get('feature_flag:social_features', True)
        }
        
        # Flags spécifiques aux utilisateurs connectés
        if request.user.is_authenticated:
            flags.update({
                'premium_features': self._is_premium_user(request.user),
                'beta_features': request.user.is_staff
            })
        
        return flags
    
    def _is_premium_user(self, user) -> bool:
        """Vérifier si l'utilisateur est premium."""
        try:
            from apps.referrals.models import PremiumSubscription
            return PremiumSubscription.objects.filter(
                user=user, status='active'
            ).exists()
        except:
            return False
    
    def _get_supported_regions(self) -> list:
        """Régions supportées."""
        return ['CI', 'SN', 'ML', 'BF', 'NE', 'TG', 'BJ', 'GN', 'FR', 'US', 'CA']
    
    def _get_payment_methods(self) -> Dict[str, Any]:
        """Méthodes de paiement disponibles."""
        return {
            'mobile_money': {
                'providers': ['orange_money', 'mtn_money', 'moov_money'],
                'min_amount': {'FCFA': 500},
                'max_amount': {'FCFA': 1000000}
            },
            'bank_transfer': {
                'min_amount': {'FCFA': 5000, 'EUR': 10, 'USD': 10},
                'max_amount': {'FCFA': 5000000, 'EUR': 5000, 'USD': 6000}
            }
        }
    
    def _get_available_game_types(self) -> list:
        """Types de jeux disponibles."""
        return [
            {
                'id': 'chess',
                'name': 'Échecs',
                'description': 'Jeu d\'échecs classique',
                'min_players': 2,
                'max_players': 2,
                'average_duration': '20 minutes'
            },
            {
                'id': 'checkers',
                'name': 'Dames',
                'description': 'Jeu de dames traditionnel',
                'min_players': 2,
                'max_players': 2,
                'average_duration': '15 minutes'
            },
            {
                'id': 'ludo',
                'name': 'Ludo',
                'description': 'Jeu de plateau populaire',
                'min_players': 2,
                'max_players': 4,
                'average_duration': '25 minutes'
            }
        ]


# ===== VUES DE CONVERSION ET DEVISES =====

class CurrencyConversionView(APIView):
    """
    Vue pour la conversion de devises en temps réel.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(rate_limit(max_requests=100, window=60))
    def get(self, request):
        """Convertir un montant d'une devise à une autre."""
        
        try:
            amount = Decimal(request.query_params.get('amount', '0'))
            from_currency = request.query_params.get('from', 'FCFA').upper()
            to_currency = request.query_params.get('to', 'EUR').upper()
            
            # Validation
            if amount <= 0:
                return Response({
                    'error': 'Le montant doit être positif'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if from_currency not in SUPPORTED_CURRENCIES:
                raise InvalidCurrencyException(f"Devise source non supportée: {from_currency}")
            
            if to_currency not in SUPPORTED_CURRENCIES:
                raise InvalidCurrencyException(f"Devise cible non supportée: {to_currency}")
            
            # Conversion
            converted_amount = convert_currency(amount, from_currency, to_currency)
            exchange_rate = get_exchange_rate(from_currency, to_currency)
            
            return Response({
                'original_amount': float(amount),
                'converted_amount': float(converted_amount),
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate,
                'formatted_original': format_currency(amount, from_currency),
                'formatted_converted': format_currency(converted_amount, to_currency),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return Response({
                'error': 'Erreur lors de la conversion',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExchangeRatesView(APIView):
    """
    Vue pour obtenir tous les taux de change.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(cache_page(300))  # Cache 5 minutes
    def get(self, request):
        """Retourner tous les taux de change."""
        
        rates = {}
        timestamp = timezone.now()
        
        for from_currency in SUPPORTED_CURRENCIES.keys():
            rates[from_currency] = {}
            for to_currency in SUPPORTED_CURRENCIES.keys():
                if from_currency != to_currency:
                    rate = get_exchange_rate(from_currency, to_currency)
                    rates[from_currency][to_currency] = rate
        
        return Response({
            'rates': rates,
            'base_rates': DEFAULT_EXCHANGE_RATES,
            'timestamp': timestamp.isoformat(),
            'valid_for_minutes': 5
        })


# ===== VUES DE STATISTIQUES PUBLIQUES =====

class PublicStatsView(APIView):
    """
    Vue pour les statistiques publiques de la plateforme.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(cache_page(900))  # Cache 15 minutes
    @method_decorator(log_performance(threshold=1.0))
    def get(self, request):
        """Retourner les statistiques publiques."""
        
        try:
            stats = self._calculate_public_stats()
            
            return Response({
                'platform_stats': stats,
                'last_updated': timezone.now().isoformat(),
                'cache_duration': '15 minutes'
            })
            
        except Exception as e:
            logger.error(f"Public stats calculation error: {e}")
            return Response({
                'error': 'Erreur lors du calcul des statistiques'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_public_stats(self) -> Dict[str, Any]:
        """Calculer les statistiques publiques."""
        
        # Stats basiques (mockées pour l'instant)
        stats = {
            'total_users': self._get_total_users(),
            'active_users_today': self._get_active_users_today(),
            'total_games_played': self._get_total_games(),
            'games_in_progress': self._get_active_games(),
            'total_prize_pool': self._get_total_prize_pool(),
            'top_countries': self._get_top_countries(),
            'popular_games': self._get_popular_games()
        }
        
        return stats
    
    def _get_total_users(self) -> int:
        """Nombre total d'utilisateurs."""
        return User.objects.filter(is_active=True).count()
    
    def _get_active_users_today(self) -> int:
        """Utilisateurs actifs aujourd'hui."""
        today = timezone.now().date()
        return User.objects.filter(last_login__date=today).count()
    
    def _get_total_games(self) -> int:
        """Total des parties jouées."""
        try:
            from apps.games.models import Game
            return Game.objects.filter(status='completed').count()
        except:
            return 0
    
    def _get_active_games(self) -> int:
        """Parties en cours."""
        try:
            from apps.games.models import Game
            return Game.objects.filter(status__in=['waiting', 'playing']).count()
        except:
            return 0
    
    def _get_total_prize_pool(self) -> Dict[str, float]:
        """Cagnotte totale par devise."""
        try:
            from apps.payments.models import Transaction
            
            prize_pools = {}
            for currency in SUPPORTED_CURRENCIES.keys():
                total = Transaction.objects.filter(
                    transaction_type='bet',
                    status='completed',
                    currency=currency
                ).aggregate(Sum('amount'))['amount__sum'] or 0
                
                prize_pools[currency] = float(total)
            
            return prize_pools
        except:
            return {currency: 0.0 for currency in SUPPORTED_CURRENCIES.keys()}
    
    def _get_top_countries(self) -> list:
        """Top 5 des pays par nombre d'utilisateurs."""
        try:
            countries = User.objects.values('country').annotate(
                user_count=Count('id')
            ).order_by('-user_count')[:5]
            
            return list(countries)
        except:
            return []
    
    def _get_popular_games(self) -> list:
        """Jeux les plus populaires."""
        try:
            from apps.games.models import Game
            
            games = Game.objects.values('game_type').annotate(
                game_count=Count('id')
            ).order_by('-game_count')[:5]
            
            return list(games)
        except:
            return []


# ===== VUES DE MAINTENANCE ET ADMINISTRATION =====

class MaintenanceView(APIView):
    """
    Vue pour gérer le mode maintenance.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtenir le statut de maintenance."""
        if not request.user.is_staff:
            return Response({
                'error': 'Accès refusé'
            }, status=status.HTTP_403_FORBIDDEN)
        
        maintenance_mode = cache.get('maintenance_mode', False)
        maintenance_message = cache.get('maintenance_message', '')
        maintenance_duration = cache.get('maintenance_duration', '')
        
        return Response({
            'maintenance_mode': maintenance_mode,
            'message': maintenance_message,
            'estimated_duration': maintenance_duration,
            'timestamp': timezone.now().isoformat()
        })
    
    @audit_action('MAINTENANCE_MODE_TOGGLE', sensitive=True)
    def post(self, request):
        """Activer/désactiver le mode maintenance."""
        if not request.user.is_staff:
            return Response({
                'error': 'Accès refusé'
            }, status=status.HTTP_403_FORBIDDEN)
        
        enabled = request.data.get('enabled', False)
        message = request.data.get('message', 'Maintenance en cours')
        duration = request.data.get('duration', 'inconnue')
        
        # Mettre à jour le cache
        cache.set('maintenance_mode', enabled, None)  # Pas d'expiration
        cache.set('maintenance_message', message, None)
        cache.set('maintenance_duration', duration, None)
        
        logger.warning(
            f"Maintenance mode {'enabled' if enabled else 'disabled'} by {request.user.username}"
        )
        
        return Response({
            'maintenance_mode': enabled,
            'message': message,
            'duration': duration,
            'changed_by': request.user.username,
            'timestamp': timezone.now().isoformat()
        })


# ===== VUES UTILITAIRES =====

class SystemInfoView(APIView):
    """
    Vue pour obtenir des informations système (debug).
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Informations système pour le debug."""
        if not request.user.is_staff:
            return Response({
                'error': 'Accès refusé'
            }, status=status.HTTP_403_FORBIDDEN)
        
        info = {
            'django_version': self._get_django_version(),
            'python_version': self._get_python_version(),
            'database_info': self._get_database_info(),
            'cache_info': self._get_cache_info(),
            'server_time': timezone.now().isoformat(),
            'uptime': self._get_uptime(),
            'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
            'debug_mode': settings.DEBUG
        }
        
        return Response(info)
    
    def _get_django_version(self) -> str:
        """Version de Django."""
        import django
        return django.get_version()
    
    def _get_python_version(self) -> str:
        """Version de Python."""
        import sys
        return sys.version
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Informations de base de données."""
        try:
            from django.db import connection
            return {
                'vendor': connection.vendor,
                'version': connection.get_server_version()
            }
        except:
            return {'error': 'Information non disponible'}
    
    def _get_cache_info(self) -> Dict[str, Any]:
        """Informations de cache."""
        try:
            from django.core.cache import cache
            return {
                'backend': cache.__class__.__name__,
                'location': getattr(cache, '_cache', {}).get('_host', 'unknown')
            }
        except:
            return {'error': 'Information non disponible'}
    
    def _get_uptime(self) -> str:
        """Uptime du serveur."""
        app_start_time = cache.get('health_metric:app_start_time')
        if app_start_time:
            try:
                start = datetime.fromisoformat(app_start_time.replace('Z', '+00:00'))
                uptime = timezone.now() - start
                return str(uptime)
            except:
                pass
        return 'unknown'


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def clear_cache(request):
    """
    Endpoint pour vider le cache (développement uniquement).
    """
    if not settings.DEBUG:
        return JsonResponse({
            'error': 'Non disponible en production'
        }, status=403)
    
    try:
        cache.clear()
        return JsonResponse({
            'message': 'Cache vidé avec succès',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors du vidage du cache: {e}'
        }, status=500)


# ===== VUES D'ERREUR PERSONNALISÉES =====

def custom_404_view(request, exception=None):
    """Vue d'erreur 404 personnalisée."""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Endpoint non trouvé',
            'code': 'not_found',
            'path': request.path,
            'method': request.method,
            'timestamp': timezone.now().isoformat()
        }, status=404)
    
    # Pour les autres requêtes, retourner une page HTML
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page non trouvée - RUMO RUSH</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .error { color: #e74c3c; }
            .logo { font-size: 3em; margin: 20px; }
        </style>
    </head>
    <body>
        <div class="logo">🎮</div>
        <h1>RUMO RUSH</h1>
        <h2 class="error">Page non trouvée (404)</h2>
        <p>La page que vous cherchez n'existe pas.</p>
        <a href="/">Retour à l'accueil</a>
    </body>
    </html>
    """, status=404, content_type='text/html')


def custom_500_view(request):
    """Vue d'erreur 500 personnalisée."""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Erreur serveur interne',
            'code': 'server_error',
            'message': 'Une erreur inattendue s\'est produite',
            'timestamp': timezone.now().isoformat()
        }, status=500)
    
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Erreur serveur - RUMO RUSH</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .error { color: #e74c3c; }
            .logo { font-size: 3em; margin: 20px; }
        </style>
    </head>
    <body>
        <div class="logo">🎮</div>
        <h1>RUMO RUSH</h1>
        <h2 class="error">Erreur serveur (500)</h2>
        <p>Nous rencontrons un problème technique temporaire.</p>
        <p>Veuillez réessayer dans quelques instants.</p>
        <a href="/">Retour à l'accueil</a>
    </body>
    </html>
    """, status=500, content_type='text/html')


# ===== VUE DE TEST (DÉVELOPPEMENT) =====

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_endpoint(request):
    """
    Endpoint de test pour le développement.
    """
    if not settings.DEBUG:
        return Response({
            'error': 'Non disponible en production'
        }, status=403)
    
    client_info = extract_client_info(request)
    
    response_data = {
        'message': 'Endpoint de test RUMO RUSH',
        'method': request.method,
        'timestamp': timezone.now().isoformat(),
        'user': {
            'is_authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None,
            'is_staff': request.user.is_staff if request.user.is_authenticated else False
        },
        'client_info': client_info,
        'headers': dict(request.headers),
        'query_params': dict(request.query_params),
        'data': request.data if request.method == 'POST' else None
    }
    
    return Response(response_data)
