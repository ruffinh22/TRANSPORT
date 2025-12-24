"""
Base settings for RUMO RUSH project.
"""
import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'channels',
    'django_celery_beat',
    'django_celery_results',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.games',
    'apps.payments',
    'apps.referrals',
    'apps.analytics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.SecurityMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
]

ROOT_URLCONF = 'rumo_rush.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rumo_rush.wsgi.application'
ASGI_APPLICATION = 'rumo_rush.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='rhumo'),
        'USER': env('DB_USER', default='admin'),
        'PASSWORD': env('DB_PASSWORD', default='ThankGod!'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', default='redis://localhost:6379/2')],
        },
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',  # Vite dev server
    'http://127.0.0.1:5173',  # Vite dev server
    'http://localhost:8080',  # Vue/React dev servers
    'http://127.0.0.1:8080',
])

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Sera overridé en développement

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@rumorush.com')

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/3')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/3')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Payment settings
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')

# Game settings
GAME_SETTINGS = {
    'COMMISSION_RATE': 0.14,  # 14% commission
    'TURN_TIMEOUT_SECONDS': 120,  # 2 minutes per turn
    'ALERT_TIME_SECONDS': 30,  # Alert at 30 seconds remaining
    'MAX_GAME_DURATION_HOURS': 2,  # Maximum game duration
    'MIN_BET_AMOUNTS': {
        'FCFA': 500,
        'EUR': 2,
        'USD': 2,
    },
    'MAX_BET_AMOUNTS': {
        'FCFA': 1000000,
        'EUR': 1500,
        'USD': 1800,
    },
}

# Referral settings - CORRECTED
REFERRAL_SETTINGS = {
    'DEFAULT_COMMISSION_RATE': 0.10,  # 10% commission
    'COMMISSION_RATE': 0.10,  # Added missing key
    'FREE_GAMES_LIMIT': 3,  # 3 games for non-premium users
    'PREMIUM_SUBSCRIPTION_PRICE': {
        'FCFA': 10000,
        'EUR': 15,
        'USD': 18,
    },
    'PREMIUM_PRICE': {  # Added missing key
        'FCFA': 10000,
        'EUR': 15,
        'USD': 18,
    },
}

# KYC settings
KYC_SETTINGS = {
    'REQUIRED_AMOUNT_FCFA': 10000,
    'REQUIRED_AMOUNT_EUR': 15,
    'REQUIRED_AMOUNT_USD': 18,
    'DOCUMENT_MAX_SIZE_MB': 5,
    'ALLOWED_EXTENSIONS': ['jpg', 'jpeg', 'png', 'pdf'],
}

# Withdrawal limits
MIN_WITHDRAWAL = {
    'FCFA': 4000,
    'EUR': 6,
    'USD': 7,
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Rate limiting
ADMIN_URL = 'admin/'  # ou 'secure-admin/' pour plus de sécurité

RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ===================================================================
# FEEXPAY CONFIGURATION
# ===================================================================

# Charger la configuration FeexPay depuis .env.feexpay
feexpay_env = environ.Env()
feexpay_env_file = BASE_DIR / '.env.feexpay'

if feexpay_env_file.exists():
    feexpay_env.read_env(feexpay_env_file)
    
    FEEXPAY_API_KEY = feexpay_env('FEEXPAY_API_KEY', default='')
    FEEXPAY_SHOP_ID = feexpay_env('FEEXPAY_SHOP_ID', default='')
    FEEXPAY_WEBHOOK_SECRET = feexpay_env('FEEXPAY_WEBHOOK_SECRET', default='')
    FEEXPAY_TEST_MODE = feexpay_env('FEEXPAY_TEST_MODE', default=True)
else:
    # Valeurs par défaut si le fichier n'existe pas
    FEEXPAY_API_KEY = env('FEEXPAY_API_KEY', default='')
    FEEXPAY_SHOP_ID = env('FEEXPAY_SHOP_ID', default='')
    FEEXPAY_WEBHOOK_SECRET = env('FEEXPAY_WEBHOOK_SECRET', default='')
    FEEXPAY_TEST_MODE = env('FEEXPAY_TEST_MODE', default=True)

# URL API FeexPay (production uniquement, pas de sandbox pour payout)
FEEXPAY_BASE_URL = 'https://api.feexpay.me'

# Endpoints API FeexPay Payout
FEEXPAY_PAYOUT_URL = 'https://api.feexpay.me/api/payouts/public/transfer/global'
FEEXPAY_PAYOUT_STATUS_URL = 'https://api.feexpay.me/api/payouts/status/public'

# Limites de retrait (selon documentation FeexPay)
FEEXPAY_MIN_PAYOUT = 50  # 50 FCFA minimum
FEEXPAY_MAX_PAYOUT = 100000  # 100,000 FCFA maximum
