# ==================================================
# RUMO RUSH - Fichiers de Configuration Manquants
# ==================================================

# 1. rumo_rush/settings/testing.py - Configuration Tests Optimisée
# ================================================================

from .base import *
import tempfile
import os

# Configuration pour environnement de test
DEBUG = False
SECRET_KEY = 'test-secret-key-do-not-use-in-production'

# Base de données PostgreSQL pour tests (cohérence avec production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('TEST_DB_NAME', default='test_rumo_rush'),
        'USER': env('TEST_DB_USER', default='postgres'),
        'PASSWORD': env('TEST_DB_PASSWORD', default='password'),
        'HOST': env('TEST_DB_HOST', default='localhost'),
        'PORT': env('TEST_DB_PORT', default='5432'),
        'OPTIONS': {
            'charset': 'utf8',
        },
        'TEST': {
            'NAME': 'test_rumo_rush_temp',
            'CHARSET': 'utf8',
            'CREATE_DB': True,
        }
    }
}

# Alternative SQLite pour tests ultra-rapides si nécessaire
if env('USE_SQLITE_TESTS', default=False):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'OPTIONS': {
                'timeout': 20,
            },
            'TEST': {
                'NAME': ':memory:',
            }
        }
    }

# Cache Redis pour tests (cohérence avec production)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('TEST_REDIS_URL', default='redis://localhost:6379/15'),  # DB 15 pour tests
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Continue même si Redis n'est pas disponible
        },
        'KEY_PREFIX': 'rumo_test',
    }
}

# Fallback vers cache mémoire si Redis n'est pas disponible pour les tests
if env('USE_MEMORY_CACHE_TESTS', default=False):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }

# Channel layers en mémoire
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    },
}

# Celery en mode synchrone pour tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Email backend pour tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Désactiver les migrations pour accélérer les tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Password hashers rapides pour tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Media temporaire pour tests
MEDIA_ROOT = tempfile.mkdtemp()

# Désactiver la limitation de taux pour tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# JWT configuration pour tests (tokens plus longs)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
})

# Désactiver la sécurité pour tests
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS permissif pour tests
CORS_ALLOW_ALL_ORIGINS = True

# Logging minimal pour tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
        },
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'rumo_rush': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Configuration de test pour Stripe (mode test)
STRIPE_PUBLISHABLE_KEY = 'pk_test_fake_key_for_testing'
STRIPE_SECRET_KEY = 'sk_test_fake_key_for_testing'
STRIPE_WEBHOOK_SECRET = 'whsec_test_fake_secret_for_testing'

# Configuration de jeu pour tests (timeouts courts)
GAME_SETTINGS.update({
    'TURN_TIMEOUT': 10,  # 10 secondes pour tests
    'ALERT_TIME': 2,     # 2 secondes d'alerte
    'COMMISSION_RATE': 0.1,  # 10% pour tests
})

# Configuration de parrainage pour tests
REFERRAL_SETTINGS.update({
    'COMMISSION_RATE': 0.05,  # 5% pour tests
    'FREE_GAMES_LIMIT': 1,    # 1 partie gratuite pour tests
})

# Désactiver les services externes pour tests
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
SENTRY_DSN = None

# Configuration spéciale pour tests parallèles
if env('PARALLEL_TESTS', default=False):
    DATABASES['default']['TEST'] = {
        'NAME': f'test_rumo_rush_{os.environ.get("PYTEST_XDIST_WORKER", "master")}',
    }

print("🧪 RUMO RUSH - Mode TEST activé (optimisé pour vitesse)")


# ==================================================
# 2. rumo_rush/urls.py - URLs Principales
# ==================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration du schema OpenAPI/Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="RUMO RUSH API",
        default_version='v1',
        description="API complète pour la plateforme de jeux RUMO RUSH",
        terms_of_service="https://rumorush.com/terms/",
        contact=openapi.Contact(email="api@rumorush.com"),
        license=openapi.License(name="Propriétaire"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Configuration du router API principal
api_router = DefaultRouter()

urlpatterns = [
    # Redirection racine vers l'application frontend
    path('', RedirectView.as_view(url='https://rumorush.com', permanent=False)),
    
    # Administration Django
    path(f'{settings.ADMIN_URL}', admin.site.urls),
    
    # Health Check et Status
    path('health/', include('health_check.urls')),
    path('api/v1/status/', include('apps.core.urls')),
    
    # Documentation API
    path('api/v1/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/v1/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Authentication & Comptes Utilisateurs
    path('api/v1/auth/', include('apps.accounts.urls')),
    
    # API Jeux et Gaming
    path('api/v1/games/', include('apps.games.urls')),
    
    # API Paiements et Transactions
    path('api/v1/payments/', include('apps.payments.urls')),
    
    # API Parrainage et Commissions
    path('api/v1/referrals/', include('apps.referrals.urls')),
    
    # API Analytics et Statistiques
    path('api/v1/analytics/', include('apps.analytics.urls')),
    
    # Webhooks externes (Stripe, etc.)
    path('webhooks/', include('apps.payments.webhooks_urls')),
    
    # API Router (si des ViewSets globaux sont définis)
    path('api/v1/', include(api_router.urls)),
]

# Configuration pour fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar (si activée)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Configuration pour environnement de test
if settings.DEBUG and hasattr(settings, 'TESTING') and settings.TESTING:
    # URLs spéciales pour les tests
    urlpatterns += [
        path('test-auth/', include('apps.accounts.test_urls')),
        path('test-games/', include('apps.games.test_urls')),
    ]

# Gestion des erreurs personnalisées
handler400 = 'apps.core.views.error_400'
handler403 = 'apps.core.views.error_403'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'

# Configuration de l'interface d'administration
admin.site.site_header = "RUMO RUSH - Administration"
admin.site.site_title = "RUMO RUSH Admin"
admin.site.index_title = "Tableau de bord principal"
admin.site.site_url = "https://rumorush.com"


# ==================================================
# 3. rumo_rush/wsgi.py - Configuration WSGI Production
# ==================================================

import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Ajout du chemin du projet au Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.production')

# Initialisation de l'application WSGI
application = get_wsgi_application()

# Middleware personnalisé pour production (optionnel)
class WSGIMiddleware:
    """Middleware WSGI personnalisé pour monitoring et logs."""
    
    def __init__(self, application):
        self.application = application
    
    def __call__(self, environ, start_response):
        # Logging des requêtes (si nécessaire)
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', '')
        
        # Vous pouvez ajouter ici du monitoring personnalisé
        
        return self.application(environ, start_response)

# Application finale avec middleware personnalisé
# application = WSGIMiddleware(application)

# Configuration pour serveurs de production spécifiques
def get_wsgi_application_with_config():
    """
    Configuration WSGI adaptée selon l'environnement de déploiement.
    """
    import django
    django.setup()
    
    from django.conf import settings
    
    # Configuration spécifique selon le serveur
    if hasattr(settings, 'WSGI_CONFIG'):
        # Configurations personnalisées si nécessaires
        pass
    
    return get_wsgi_application()

# Export de l'application configurée
# application = get_wsgi_application_with_config()


# ==================================================
# 4. rumo_rush/asgi.py - Configuration ASGI WebSocket
# ==================================================

import os
import sys
from pathlib import Path
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Configuration du chemin
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configuration environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.production')

# Initialisation Django (OBLIGATOIRE avant les imports d'applications)
django.setup()

# Imports après setup Django
from apps.games.routing import websocket_urlpatterns
from apps.games.middleware import WebSocketAuthMiddleware
from apps.core.consumers import SystemConsumer

# Application HTTP traditionnelle
django_asgi_app = get_asgi_application()

# Configuration du routage WebSocket
websocket_routing = URLRouter([
    # Routes des jeux en temps réel
    path('ws/games/', include('apps.games.routing')),
    
    # Routes système (notifications, statuts)
    path('ws/system/', SystemConsumer.as_asgi()),
    
    # Routes des notifications utilisateur
    path('ws/notifications/', include('apps.accounts.routing')),
] + websocket_urlpatterns)

# Application ASGI complète avec support multi-protocole
application = ProtocolTypeRouter({
    # HTTP traditionnel (REST API, Admin, etc.)
    'http': django_asgi_app,
    
    # WebSocket avec authentification et validation
    'websocket': AllowedHostsOriginValidator(
        WebSocketAuthMiddleware(
            AuthMiddlewareStack(
                websocket_routing
            )
        )
    ),
})

# Configuration pour développement avec auto-reload
if os.environ.get('DJANGO_SETTINGS_MODULE') == 'rumo_rush.settings.development':
    # En développement, on peut ajouter des middlewares de debug
    class ASGIDebugMiddleware:
        def __init__(self, app):
            self.app = app
        
        async def __call__(self, scope, receive, send):
            # Log des connexions WebSocket en développement
            if scope['type'] == 'websocket':
                print(f"WebSocket connexion: {scope.get('path', 'Unknown')}")
            
            return await self.app(scope, receive, send)
    
    application = ASGIDebugMiddleware(application)


# ==================================================
# 5. rumo_rush/celery.py - Configuration Celery Complète
# ==================================================

import os
from celery import Celery
from django.conf import settings
from kombu import Queue, Exchange

# Configuration environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.production')

# Création de l'instance Celery
app = Celery('rumo_rush')

# Configuration depuis les settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuration avancée des queues
app.conf.task_routes = {
    # Queue haute priorité pour les actions de jeu
    'apps.games.tasks.process_move': {'queue': 'high_priority'},
    'apps.games.tasks.check_timeout': {'queue': 'high_priority'},
    'apps.games.tasks.end_game': {'queue': 'high_priority'},
    
    # Queue paiements
    'apps.payments.tasks.*': {'queue': 'payments'},
    'apps.payments.tasks.process_payment': {'queue': 'payments'},
    'apps.payments.tasks.verify_payment': {'queue': 'payments'},
    
    # Queue analytics (moins prioritaire)
    'apps.analytics.tasks.*': {'queue': 'analytics'},
    'apps.referrals.tasks.*': {'queue': 'analytics'},
    
    # Queue maintenance (tâches lourdes)
    'apps.core.tasks.*': {'queue': 'maintenance'},
    'apps.games.tasks.cleanup_*': {'queue': 'maintenance'},
}

# Définition des queues avec priorités
app.conf.task_queues = (
    Queue('high_priority', 
          Exchange('high_priority'), 
          routing_key='high_priority',
          queue_arguments={'x-max-priority': 10}),
    
    Queue('games', 
          Exchange('games'), 
          routing_key='games',
          queue_arguments={'x-max-priority': 5}),
    
    Queue('payments', 
          Exchange('payments'), 
          routing_key='payments',
          queue_arguments={'x-max-priority': 8}),
    
    Queue('analytics', 
          Exchange('analytics'), 
          routing_key='analytics',
          queue_arguments={'x-max-priority': 2}),
    
    Queue('maintenance', 
          Exchange('maintenance'), 
          routing_key='maintenance',
          queue_arguments={'x-max-priority': 1}),
)

# Configuration des tâches périodiques (Celery Beat)
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ============ TÂCHES HAUTE FRÉQUENCE ============
    
    # Vérification des timeouts de jeu toutes les 15 secondes
    'check-game-timeouts': {
        'task': 'apps.games.tasks.check_all_game_timeouts',
        'schedule': 15.0,
        'options': {'queue': 'high_priority'},
    },
    
    # Nettoyage des connexions WebSocket toutes les 30 secondes
    'cleanup-websocket-connections': {
        'task': 'apps.games.tasks.cleanup_disconnected_users',
        'schedule': 30.0,
        'options': {'queue': 'high_priority'},
    },
    
    # ============ TÂCHES MOYENNES FRÉQUENCE ============
    
    # Vérification des paiements en attente toutes les 2 minutes
    'check-pending-payments': {
        'task': 'apps.payments.tasks.check_pending_payments',
        'schedule': crontab(minute='*/2'),
        'options': {'queue': 'payments'},
    },
    
    # Mise à jour des classements toutes les 5 minutes
    'update-leaderboards': {
        'task': 'apps.games.tasks.update_live_leaderboards',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'games'},
    },
    
    # Nettoyage des invitations expirées toutes les 10 minutes
    'cleanup-expired-invitations': {
        'task': 'apps.games.tasks.cleanup_expired_invitations',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'maintenance'},
    },
    
    # Calcul des métriques temps réel toutes les 15 minutes
    'update-realtime-metrics': {
        'task': 'apps.analytics.tasks.update_realtime_metrics',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'analytics'},
    },
    
    # ============ TÂCHES QUOTIDIENNES ============
    
    # Calcul des commissions quotidiennes à 1h du matin
    'calculate-daily-commissions': {
        'task': 'apps.referrals.tasks.calculate_daily_commissions',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'payments'},
    },
    
    # Nettoyage des parties abandonnées à 2h du matin
    'cleanup-abandoned-games': {
        'task': 'apps.games.tasks.cleanup_abandoned_games',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'maintenance'},
    },
    
    # Sauvegarde des statistiques quotidiennes à 3h du matin
    'backup-daily-stats': {
        'task': 'apps.analytics.tasks.backup_daily_statistics',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'maintenance'},
    },
    
    # Envoi du rapport quotidien à 8h du matin
    'send-daily-report': {
        'task': 'apps.core.tasks.send_daily_admin_report',
        'schedule': crontab(hour=8, minute=0),
        'options': {'queue': 'analytics'},
    },
    
    # Nettoyage des logs anciens à 23h
    'cleanup-old-logs': {
        'task': 'apps.core.tasks.cleanup_old_logs',
        'schedule': crontab(hour=23, minute=0),
        'options': {'queue': 'maintenance'},
    },
    
    # ============ TÂCHES HEBDOMADAIRES ============
    
    # Sauvegarde complète le dimanche à 2h du matin
    'weekly-full-backup': {
        'task': 'apps.core.tasks.create_full_backup',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
        'options': {'queue': 'maintenance'},
    },
    
    # Calcul des classements hebdomadaires le lundi à 6h
    'calculate-weekly-rankings': {
        'task': 'apps.games.tasks.calculate_weekly_rankings',
        'schedule': crontab(hour=6, minute=0, day_of_week=1),
        'options': {'queue': 'analytics'},
    },
    
    # Nettoyage approfondi de la base le samedi à 3h
    'deep-database-cleanup': {
        'task': 'apps.core.tasks.deep_database_cleanup',
        'schedule': crontab(hour=3, minute=0, day_of_week=6),
        'options': {'queue': 'maintenance'},
    },
    
    # ============ TÂCHES MENSUELLES ============
    
    # Archivage des données anciennes le 1er de chaque mois à 1h
    'monthly-data-archiving': {
        'task': 'apps.core.tasks.archive_old_data',
        'schedule': crontab(hour=1, minute=0, day_of_month=1),
        'options': {'queue': 'maintenance'},
    },
    
    # Rapport mensuel complet le 1er à 9h
    'monthly-admin-report': {
        'task': 'apps.analytics.tasks.generate_monthly_report',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),
        'options': {'queue': 'analytics'},
    },
}

# Configuration du timezone pour les tâches
app.conf.timezone = 'UTC'

# Auto-découverte des tâches dans les applications Django
app.autodiscover_tasks()

# Configuration pour le monitoring et debugging
@app.task(bind=True)
def debug_task(self):
    """Tâche de debug pour vérifier le bon fonctionnement de Celery."""
    print(f'Request: {self.request!r}')
    return 'Debug task completed successfully'

# Configuration des signaux pour monitoring
from celery.signals import task_prerun, task_postrun, task_failure

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwargs_extra):
    """Signal exécuté avant chaque tâche."""
    print(f"Début tâche: {task.name} (ID: {task_id})")

@task_postrun.connect  
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwargs_extra):
    """Signal exécuté après chaque tâche."""
    print(f"Fin tâche: {task.name} (ID: {task_id}) - État: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Signal exécuté en cas d'échec de tâche."""
    print(f"ÉCHEC tâche: {sender.name} (ID: {task_id}) - Erreur: {exception}")
    # Ici vous pourriez envoyer une alerte (Slack, Discord, Email)

# Configuration pour les workers en production
app.conf.update(
    # Optimisations de performance
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Sérialisation optimisée
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Compression pour économiser la bande passante
    task_compression='gzip',
    result_compression='gzip',
    
    # Configuration des résultats
    result_expires=3600,  # Les résultats expirent après 1 heure
    
    # Configuration avancée
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

print("⚡ Celery configuré avec succès pour RUMO RUSH")
print(f"📋 {len(app.conf.beat_schedule)} tâches périodiques programmées")
print(f"🔄 {len(app.conf.task_queues)} queues de priorités configurées")
