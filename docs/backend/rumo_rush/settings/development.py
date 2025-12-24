# rumo_rush/settings/development.py
# ==================================

from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # ✅ DÉSACTIVÉ POUR TESTS DE RETRAIT RÉEL

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'rumorush.com',
    'www.rumorush.com',
    'api.rumorush.com',
    '*.ngrok.io',  # Pour les tests avec tunneling
]

# CSP détendue pour le développement avec FeexPay
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://api.feexpay.me", "https://pagead2.googlesyndication.com"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_CONNECT_SRC = ["'self'", "wss:", "ws:", "https://api.feexpay.me"]
CSP_IMG_SRC = ["'self'", "data:", "https:", "blob:"]
CSP_FONT_SRC = ["'self'", "https://fonts.gstatic.com"]
CSP_OBJECT_SRC = ["'none'"]

# Database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DEV_DB_NAME', default='rhumo'),
        'USER': env('DEV_DB_USER', default='admin'),
        'PASSWORD': env('DEV_DB_PASSWORD', default='ThankGod!'),
        'HOST': env('DEV_DB_HOST', default='localhost'),
        'PORT': env('DEV_DB_PORT', default='5432'),
        
        'TEST': {
            'NAME': 'test_rumo_rush_dev',
        }
    }
}

# Cache pour développement (Redis local ou dummy)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Ignore les erreurs Redis en dev
        },
        'KEY_PREFIX': 'rumo_dev',
    }
}

# Channel Layers pour développement
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
            'capacity': 100,
            'expiry': 60,
        },
    },
}

# Celery pour développement
CELERY_BROKER_URL = 'redis://localhost:6379/2'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/3'
CELERY_TASK_ALWAYS_EAGER = env('CELERY_ALWAYS_EAGER', default=False)  # Pour les tests
CELERY_TASK_EAGER_PROPAGATES = True

# Email backend pour développement
# Configuration SMTP RumoRush - Emails réels avec optimisations anti-spam
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.rumorush.com'
EMAIL_PORT = 8587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'support@rumorush.com'
EMAIL_HOST_PASSWORD = '7VHSQNzKj4T3Xy'
DEFAULT_FROM_EMAIL = 'RumoRush <support@rumorush.com>'  # Format propre sans "Support"
EMAIL_TIMEOUT = 30

# Optimisations anti-spam
EMAIL_USE_LOCALTIME = True
EMAIL_SUBJECT_PREFIX = ''  # Pas de préfixe [Django]
SERVER_EMAIL = 'noreply@rumorush.com'  # Pour les erreurs système

# Pour revenir au mode console (tests uniquement) :
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS plus permissif en développement
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS += [
    'http://localhost:5173',   # Vite dev server
    'http://127.0.0.1:5173',
    'http://localhost:3000',   # React/Next.js
    'http://localhost:3001',
    'http://localhost:8080',   # Vue dev server
    'http://localhost:8081',
]

# Headers CORS additionnels pour les WebSockets et APIs
CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'x-csrftoken',
    'accept',
    'accept-encoding',
    'authorization',
    'cache-control',
    'connection',
    'cookie',
    'host',
    'origin',
    'pragma',
    'referer',
    'sec-websocket-extensions',
    'sec-websocket-key',
    'sec-websocket-protocol',
    'sec-websocket-version',
    'upgrade',
    'user-agent',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Rate limiting configuration for reverse proxy
RATELIMIT_IP_META_KEY = 'HTTP_X_FORWARDED_FOR'
RATELIMIT_USE_CACHE = 'default'

# Proxy and security settings for development behind nginx
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Désactiver la vérification HTTPS en développement
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Logging plus verbeux en développement
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
        'colored': {
            'format': '\033[1;32m[{levelname}]\033[0m {asctime} \033[1;36m{name}\033[0m {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',  # Changer à DEBUG pour voir les requêtes SQL
            'propagate': False,
        },
        'rumo_rush': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Extensions de développement - DISABLE DEBUG TOOLBAR TO FIX PROFILING CONFLICT
INSTALLED_APPS += [
    'django_extensions',
    # 'debug_toolbar',  # DISABLED - Causing profiling tool conflict
]

# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',  # DISABLED
# ]

# Configuration Django Debug Toolbar - DISABLED
# DEBUG_TOOLBAR_CONFIG = {
#     'DISABLE_PANELS': [
#         'debug_toolbar.panels.redirects.RedirectsPanel',
#         'debug_toolbar.panels.profiling.ProfilingPanel',  # Disable profiling panel
#     ],
#     'SHOW_TEMPLATE_CONTEXT': True,
#     'SHOW_TOOLBAR_CALLBACK': lambda request: False,  # Completely disable
# }

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# JWT plus permissif en développement (tokens plus longs)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # 24h au lieu de 1h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # 30 jours
    'ROTATE_REFRESH_TOKENS': False,  # Pas de rotation en dev
})

# Settings de jeu pour développement (timeouts plus longs)
GAME_SETTINGS.update({
    'TURN_TIMEOUT': 300,  # 5 minutes par tour en dev
    'ALERT_TIME': 60,     # Alerte à 1 minute
})

# Stripe Test Keys
STRIPE_PUBLISHABLE_KEY = env('STRIPE_TEST_PUBLISHABLE_KEY', default='pk_test_...')
STRIPE_SECRET_KEY = env('STRIPE_TEST_SECRET_KEY', default='sk_test_...')

# Désactiver la vérification des webhooks Stripe en dev
STRIPE_WEBHOOK_SECRET = ''

# File uploads pour développement
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB

# Créer les dossiers nécessaires en développement
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'media', exist_ok=True)
os.makedirs(BASE_DIR / 'staticfiles', exist_ok=True)

# Configuration pour les tests de performance
if env('PERFORMANCE_TESTING', default=False):
    DATABASES['default']['OPTIONS'].update({
        'MAX_CONNS': 1,
        'OPTIONS': {
            'MAX_CONNS': 1,
        }
    })

# Configuration de développement pour l'authentification
AUTH_PASSWORD_VALIDATORS = []  # Désactiver la validation des mots de passe

# Configuration pour hot-reload des templates
TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'apps.core.context_processors.debug_context',
]

# Timezone pour développement
USE_TZ = True
TIME_ZONE = 'Europe/Paris'  # Timezone locale en développement

# Configuration des langues pour développement
LANGUAGE_CODE = 'fr'

# Désactiver le cache des templates en développement
if DEBUG:
    TEMPLATES[0]['OPTIONS']['debug'] = True
    TEMPLATES[0]['OPTIONS']['context_processors'] += [
        'django.template.context_processors.debug',
    ]

# Configuration des médias pour développement
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration des fichiers statiques pour développement
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'frontend' / 'dist',  # Pour les assets frontend
]

# Collecte des fichiers statiques plus rapide en dev
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Configuration pour les tests d'API
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',  # Plus permissif en dev
    'user': '10000/hour',
    'login': '100/minute',
    'register': '50/minute',
}

# Désactiver les permissions strictes en développement
if env('DISABLE_PERMISSIONS', default=False):
    REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
        'rest_framework.permissions.AllowAny',
    ]

# Configuration pour les WebSockets en développement
ASGI_APPLICATION = 'rumo_rush.asgi.application'

# Configuration pour le développement mobile (CORS)
if env('MOBILE_DEV', default=False):
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS += [
        "http://10.0.2.2:3000",    # Android emulator
        "http://localhost:19000",   # Expo
        "http://localhost:19006",   # Expo web
    ]

# Configuration des commandes de gestion personnalisées
MANAGEMENT_COMMANDS_CONFIG = {
    'create_sample_data': True,
    'reset_game_data': True,
    'simulate_games': True,
}

# Configuration pour les fixtures de développement
FIXTURE_DIRS = [
    BASE_DIR / 'fixtures',
    BASE_DIR / 'apps' / 'accounts' / 'fixtures',
    BASE_DIR / 'apps' / 'games' / 'fixtures',
]



print(f"🚀 RUMO RUSH - Mode DÉVELOPPEMENT activé")
print(f"📡 WebSocket: ws://localhost:8000/ws/")
print(f"🗄️  Base de données: {DATABASES['default']['NAME']}")
print(f"📧 Email: Console backend")
print(f"🔄 Cache: Redis localhost:6379")
print(f"⚡ Celery: {'Eager mode' if CELERY_TASK_ALWAYS_EAGER else 'Async mode'}")
print(f"🔧 Debug Toolbar: DISABLED (to prevent profiling conflicts)")

# Variables d'environnement recommandées pour le développement
RECOMMENDED_ENV_VARS = {
    'DEBUG': 'True',
    'DJANGO_ENVIRONMENT': 'development',
    'SECRET_KEY': 'dev-secret-key-change-in-production',
    'DB_NAME': 'rhumo',
    'DB_USER': 'admin',
    'DB_PASSWORD': 'ThankGod!',
    'REDIS_URL': 'redis://localhost:6379',
}

# Afficher les variables d'environnement manquantes
missing_vars = []
for var, default in RECOMMENDED_ENV_VARS.items():
    if not env(var, default=None):
        missing_vars.append(f"{var}={default}")

if missing_vars and env('SHOW_ENV_WARNINGS', default=True):
    print("⚠️  Variables d'environnement recommandées :")
    for var in missing_vars:
        print(f"   export {var}")
        
