# rumo_rush/__init__.py
# ======================

"""
RUMO RUSH - Plateforme de Jeux en Ligne
=======================================

Package principal de configuration Django pour RUMO RUSH.
Plateforme de gaming multi-jeux avec système de paris et de commissions.

Architecture:
- Django 4.2+ avec Django REST Framework
- PostgreSQL pour la persistance des données
- Redis pour le cache et les sessions WebSocket
- Celery pour les tâches asynchrones
- Channels pour les WebSockets temps réel

Version: 1.0.0
Auteur: Équipe RUMO RUSH
License: Propriétaire
"""

# Informations sur la version
__version__ = '1.0.0'
__author__ = 'Équipe RUMO RUSH'
__email__ = 'dev@rumorush.com'
__license__ = 'Propriétaire'

# Configuration par défaut de Celery
# Ceci garantit que l'app Celery est chargée quand Django démarre
from .celery import app as celery_app

__all__ = ('celery_app',)

# Vérification de la version Python
import sys
import django

# Version Python minimale requise
PYTHON_VERSION_REQUIRED = (3, 8)
if sys.version_info < PYTHON_VERSION_REQUIRED:
    raise RuntimeError(
        f'Python {PYTHON_VERSION_REQUIRED[0]}.{PYTHON_VERSION_REQUIRED[1]}+ requis. '
        f'Version actuelle: {sys.version_info[0]}.{sys.version_info[1]}'
    )

# Version Django minimale requise
DJANGO_VERSION_REQUIRED = (4, 2)
django_version = tuple(map(int, django.VERSION[:2]))
if django_version < DJANGO_VERSION_REQUIRED:
    raise RuntimeError(
        f'Django {DJANGO_VERSION_REQUIRED[0]}.{DJANGO_VERSION_REQUIRED[1]}+ requis. '
        f'Version actuelle: {django_version[0]}.{django_version[1]}'
    )

# Configuration globale de l'application
APP_CONFIG = {
    'name': 'RUMO RUSH',
    'description': 'Plateforme de gaming multi-jeux avec système de paris',
    'website': 'https://rumorush.com',
    'api_version': 'v1',
    'supported_languages': ['fr', 'en', 'es'],
    'default_language': 'fr',
    'supported_currencies': ['FCFA', 'EUR', 'USD'],
    'default_currency': 'FCFA',
}

# Jeux supportés
SUPPORTED_GAMES = {
    'chess': {
        'name': 'Échecs',
        'min_players': 2,
        'max_players': 2,
        'estimated_duration': 1800,  # 30 minutes
        'skill_based': True,
    },
    'checkers': {
        'name': 'Dames',
        'min_players': 2,
        'max_players': 2,
        'estimated_duration': 1200,  # 20 minutes
        'skill_based': True,
    },
    'ludo': {
        'name': 'Ludo',
        'min_players': 2,
        'max_players': 4,
        'estimated_duration': 900,   # 15 minutes
        'skill_based': False,
    },
    'cards': {
        'name': 'Jeux de Cartes',
        'min_players': 2,
        'max_players': 6,
        'estimated_duration': 600,   # 10 minutes
        'skill_based': True,
    },
}

# Configuration des environnements
ENVIRONMENTS = {
    'development': {
        'debug': True,
        'database': 'postgresql',
        'cache': 'redis',
        'email_backend': 'console',
    },
    'testing': {
        'debug': False,
        'database': 'postgresql',
        'cache': 'redis',
        'email_backend': 'locmem',
    },
    'production': {
        'debug': False,
        'database': 'postgresql',
        'cache': 'redis',
        'email_backend': 'smtp',
    },
}

# Configuration des features flags
FEATURE_FLAGS = {
    'ai_matchmaking': True,
    'tournament_mode': True,
    'crypto_payments': False,  # À venir
    'live_streaming': False,   # À venir
    'social_features': True,
    'referral_system': True,
    'mobile_app': True,
}

# Messages de démarrage selon l'environnement
import os
django_settings_module = os.getenv('DJANGO_SETTINGS_MODULE', '')
environment = django_settings_module.split('.')[-1] if django_settings_module else 'production'

if environment == 'development':
    print("🚀 RUMO RUSH - Mode Développement")
    print(f"Version: {__version__}")
    print("Base de données: PostgreSQL")
    print("Cache: Redis")
    
elif environment == 'production':
    print("🏆 RUMO RUSH - Mode Production")
    print(f"Version: {__version__}")
    
elif environment == 'testing':
    print("🧪 RUMO RUSH - Mode Test")
else:
    print(f"🔧 RUMO RUSH - Environment: {environment}")
    print(f"Version: {__version__}")

# Validation de la configuration
def validate_configuration():
    """Valide la configuration globale de l'application."""
    required_env_vars = [
        'SECRET_KEY',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars and environment == 'production':
        raise RuntimeError(
            f"Variables d'environnement manquantes: {', '.join(missing_vars)}"
        )
    
    return True

# Auto-validation lors de l'import
try:
    validate_configuration()
except RuntimeError as e:
    # Debug information
    print(f"Environment détecté: {environment}")
    print(f"DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE', 'Non défini')}")
    
    if environment == 'production':
        print(f"Erreur en production: {e}")
        raise e
    else:
        print(f"Attention en développement: {e}")
        # En développement, on continue même avec des variables manquantes

# Export des constantes principales
__all__ += (
    '__version__',
    '__author__',
    '__email__',
    'APP_CONFIG',
    'SUPPORTED_GAMES',
    'ENVIRONMENTS',
    'FEATURE_FLAGS',
    'validate_configuration',
)
