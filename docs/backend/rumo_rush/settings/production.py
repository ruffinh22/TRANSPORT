# rumo_rush/settings/production.py
# ===================================

from .base import *
import logging
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Production hosts
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'rumorush.com',
    'www.rumorush.com',
    'api.rumorush.com',
    '*.rumorush.com'
])

# Database configuration for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 60,
        'ATOMIC_REQUESTS': True,
    }
}

# Redis configuration for production
REDIS_URL = env('REDIS_URL')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'ssl_cert_reqs': None,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'rumo_prod',
    }
}

# Channel Layers for production
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 1500,
            'expiry': 60,
        },
    },
}

# Celery configuration for production
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=REDIS_URL + '/3')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=REDIS_URL + '/4')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600       # 10 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# AWS S3 configuration for file storage
USE_S3 = env('USE_S3', default=True)

if USE_S3:
    # AWS Settings
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='eu-west-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    
    # Static and media files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session and CSRF security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# CORS settings for production
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'https://rumorush.com',
    'https://www.rumorush.com',
    'https://app.rumorush.com',
])
CORS_ALLOW_CREDENTIALS = True

# JWT settings for production (shorter tokens)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
})

# Sentry configuration for error tracking
SENTRY_DSN = env('SENTRY_DSN', default='')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style='url'),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=env('SENTRY_ENVIRONMENT', default='production'),
        release=env('GIT_COMMIT_SHA', default='unknown'),
    )

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} [{name}:{lineno}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'json': {
            'format': '{"level": "{levelname}", "time": "{asctime}", "name": "{name}", "message": "{message}"}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/rumorush/django.log',
            'maxBytes': 50 * 1024 * 1024,  # 50 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
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
        'django.security': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',  # Only log database errors
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Admin configuration
ADMINS = env.list('ADMINS', default=[
    ('Admin RUMO RUSH', 'admin@rumorush.com'),
])

MANAGERS = ADMINS

# Payment settings for production
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

# Mobile Money configuration
ORANGE_MONEY_API_KEY = env('ORANGE_MONEY_API_KEY', default='')
MTN_MOMO_API_KEY = env('MTN_MOMO_API_KEY', default='')
MOOV_MONEY_API_KEY = env('MOOV_MONEY_API_KEY', default='')

# Performance optimizations
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database optimizations
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 20,
    'CONN_MAX_AGE': 600,  # 10 minutes
})

# Cache sessions for better performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Compression middleware
MIDDLEWARE.insert(1, 'django.middleware.gzip.GZipMiddleware')

# Rate limiting more strict in production
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '20/minute',
    'register': '10/minute',
    'payment': '30/hour',
    'game_action': '300/minute',
}

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Health check configuration
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_URL = '/health/'

# Monitoring and metrics
MONITORING_ENABLED = True
METRICS_BACKEND = 'prometheus'

# Game settings for production
GAME_SETTINGS.update({
    'TURN_TIMEOUT_SECONDS': 120,  # 2 minutes
    'ALERT_TIME_SECONDS': 30,     # 30 seconds alert
    'MAX_CONCURRENT_GAMES': 3,    # Limit concurrent games per user
})

# Referral settings for production
REFERRAL_SETTINGS.update({
    'FREE_GAMES_LIMIT': 3,
    'COMMISSION_RATE': 0.10,
    'MAX_DAILY_COMMISSION': 100000,  # 100k FCFA per day
})

# KYC settings more strict in production
KYC_SETTINGS.update({
    'REQUIRED_FOR_WITHDRAWAL': True,
    'REQUIRED_FOR_HIGH_STAKES': True,
    'HIGH_STAKES_THRESHOLD': {
        'FCFA': 50000,
        'EUR': 75,
        'USD': 85,
    }
})

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 86400  # 1 day

# Internationalization for production
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Password validation more strict in production
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'apps.core.validators.StrongPasswordValidator',
    },
]

# Backup settings
BACKUP_ENABLED = env('BACKUP_ENABLED', default=True)
BACKUP_S3_BUCKET = env('BACKUP_S3_BUCKET', default='')
BACKUP_RETENTION_DAYS = env('BACKUP_RETENTION_DAYS', default=30)

# SSL Certificate settings
SSL_CERTIFICATE_PATH = env('SSL_CERTIFICATE_PATH', default='')
SSL_PRIVATE_KEY_PATH = env('SSL_PRIVATE_KEY_PATH', default='')

# CDN settings
USE_CDN = env('USE_CDN', default=True)
CDN_DOMAIN = env('CDN_DOMAIN', default='cdn.rumorush.com')

if USE_CDN:
    STATIC_URL = f'https://{CDN_DOMAIN}/static/'
    MEDIA_URL = f'https://{CDN_DOMAIN}/media/'

# API versioning
API_VERSION = env('API_VERSION', default='v1')
API_BASE_URL = f'/api/{API_VERSION}/'

# Google Analytics and AdSense
GOOGLE_ANALYTICS_ID = env('GOOGLE_ANALYTICS_ID', default='')
GOOGLE_ADSENSE_ID = env('GOOGLE_ADSENSE_ID', default='')

# Social authentication (if needed)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('GOOGLE_OAUTH2_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_KEY = env('FACEBOOK_KEY', default='')
SOCIAL_AUTH_FACEBOOK_SECRET = env('FACEBOOK_SECRET', default='')

# Create necessary directories
import os
os.makedirs('/var/log/rumorush', exist_ok=True)

# Final security check
if not env('SECRET_KEY'):
    raise ValueError("SECRET_KEY environment variable must be set in production")

if not env('DB_PASSWORD'):
    raise ValueError("DB_PASSWORD environment variable must be set in production")

# Production readiness checks
PRODUCTION_CHECKS = {
    'DEBUG': DEBUG is False,
    'SECRET_KEY': bool(env('SECRET_KEY')),
    'ALLOWED_HOSTS': len(ALLOWED_HOSTS) > 0,
    'DATABASE': bool(env('DB_NAME')) and bool(env('DB_PASSWORD')),
    'REDIS': bool(env('REDIS_URL')),
    'EMAIL': bool(env('EMAIL_HOST_USER')),
    'STRIPE': bool(env('STRIPE_SECRET_KEY')),
    'SSL': SECURE_SSL_REDIRECT,
}

failed_checks = [check for check, status in PRODUCTION_CHECKS.items() if not status]
if failed_checks:
    import warnings
    warnings.warn(f"Production readiness failed for: {', '.join(failed_checks)}")

print("🚀 RUMO RUSH - Mode PRODUCTION activé")
print(f"🌐 Domaine: {ALLOWED_HOSTS[0] if ALLOWED_HOSTS else 'Non configuré'}")
print(f"🔒 SSL: {'Activé' if SECURE_SSL_REDIRECT else 'Désactivé'}")
print(f"📊 Monitoring: {'Sentry activé' if SENTRY_DSN else 'Local uniquement'}")
print(f"☁️  Storage: {'AWS S3' if USE_S3 else 'Local'}")
print(f"📧 Email: {EMAIL_HOST if EMAIL_HOST else 'Non configuré'}")
print(f"🔄 Cache: Redis")
print(f"📱 Mobile Money: {'Configuré' if any([ORANGE_MONEY_API_KEY, MTN_MOMO_API_KEY]) else 'Non configuré'}")

# Environment variables required for production
REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DB_NAME',
    'DB_USER', 
    'DB_PASSWORD',
    'DB_HOST',
    'REDIS_URL',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'STRIPE_SECRET_KEY',
    'ALLOWED_HOSTS',
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not env(var, default=None)]
if missing_vars:
    raise EnvironmentError(
        f"Variables d'environnement manquantes pour la production: {', '.join(missing_vars)}"
    )
