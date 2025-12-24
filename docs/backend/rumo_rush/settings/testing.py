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





