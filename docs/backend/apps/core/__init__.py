# apps/core/__init__.py
# ======================

"""
Application Core - Utilitaires et composants partagés RUMO RUSH
==============================================================

Cette application centralise tous les utilitaires, middleware, permissions,
et composants partagés utilisés à travers l'ensemble de la plateforme RUMO RUSH.

Fonctionnalités principales :
- Middleware personnalisés pour sécurité et performance
- Système de permissions granulaire
- Pagination optimisée pour les API
- Gestionnaire d'exceptions centralisé
- Validateurs métier réutilisables
- Décorateurs pour la logique transversale
- Utilitaires pour les devises et calculs financiers

Architecture :
- Composants découplés et réutilisables
- Injection de dépendances pour les tests
- Configuration centralisée
- Logging unifié
- Gestion d'erreurs robuste

Version: 1.0.0
Dernière mise à jour: 2024
License: Propriétaire RUMO RUSH
"""

# Configuration par défaut de l'application
default_app_config = 'apps.core.apps.CoreConfig'

# Constantes globales de l'application
APP_VERSION = '1.0.0'
APP_NAME = 'RUMO RUSH'
APP_SLUG = 'rumo-rush'

# Devises supportées
SUPPORTED_CURRENCIES = {
    'FCFA': {
        'symbol': 'CFA',
        'code': 'XOF',
        'decimal_places': 0,
        'min_amount': 100,
        'max_amount': 10000000,
        'region': 'West Africa'
    },
    'EUR': {
        'symbol': '€',
        'code': 'EUR',
        'decimal_places': 2,
        'min_amount': 1,
        'max_amount': 10000,
        'region': 'Europe'
    },
    'USD': {
        'symbol': '$',
        'code': 'USD',
        'decimal_places': 2,
        'min_amount': 1,
        'max_amount': 12000,
        'region': 'International'
    }
}

# Taux de change par défaut (à mettre à jour via API externe)
DEFAULT_EXCHANGE_RATES = {
    'FCFA': {
        'EUR': 0.0015,
        'USD': 0.0017
    },
    'EUR': {
        'FCFA': 655.96,
        'USD': 1.08
    },
    'USD': {
        'FCFA': 590.00,
        'EUR': 0.93
    }
}

# Configuration des limites métier
BUSINESS_LIMITS = {
    'MIN_BET_AMOUNT': {
        'FCFA': 500,
        'EUR': 1,
        'USD': 1
    },
    'MAX_BET_AMOUNT': {
        'FCFA': 1000000,
        'EUR': 1500,
        'USD': 1700
    },
    'PLATFORM_COMMISSION_RATE': 0.14,  # 14%
    'REFERRAL_COMMISSION_RATE': 0.10,  # 10%
    'MAX_DAILY_TRANSACTIONS': 50,
    'MAX_CONCURRENT_GAMES': 5,
    'GAME_TIMEOUT_SECONDS': 120,  # 2 minutes par tour
    'SESSION_TIMEOUT_HOURS': 24
}

# Configuration de sécurité
SECURITY_CONFIG = {
    'PASSWORD_MIN_LENGTH': 8,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_NUMBERS': True,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOGIN_LOCKOUT_DURATION': 300,  # 5 minutes
    'JWT_EXPIRY_MINUTES': 60,
    'REFRESH_TOKEN_EXPIRY_DAYS': 7,
    'ENCRYPTION_ALGORITHM': 'AES-256',
    'HASH_ALGORITHM': 'bcrypt'
}

# Configuration de performance
PERFORMANCE_CONFIG = {
    'CACHE_TIMEOUT_SHORT': 300,     # 5 minutes
    'CACHE_TIMEOUT_MEDIUM': 3600,   # 1 heure
    'CACHE_TIMEOUT_LONG': 86400,    # 24 heures
    'PAGE_SIZE_DEFAULT': 20,
    'PAGE_SIZE_MAX': 100,
    'API_RATE_LIMIT_PER_MINUTE': 100,
    'WEBSOCKET_HEARTBEAT_INTERVAL': 30,
    'FILE_UPLOAD_MAX_SIZE': 10485760,  # 10MB
    'SESSION_COOKIE_AGE': 86400  # 24 heures
}

# Types d'événements pour audit
AUDIT_EVENT_TYPES = {
    'USER_LOGIN': 'Connexion utilisateur',
    'USER_LOGOUT': 'Déconnexion utilisateur',
    'USER_REGISTER': 'Inscription utilisateur',
    'GAME_CREATE': 'Création de partie',
    'GAME_JOIN': 'Participation à une partie',
    'GAME_FINISH': 'Fin de partie',
    'TRANSACTION_CREATE': 'Création de transaction',
    'TRANSACTION_COMPLETE': 'Transaction complétée',
    'WITHDRAWAL_REQUEST': 'Demande de retrait',
    'DEPOSIT_CONFIRM': 'Confirmation de dépôt',
    'KYC_SUBMIT': 'Soumission KYC',
    'KYC_APPROVE': 'Validation KYC',
    'REFERRAL_CREATE': 'Nouveau parrainage',
    'ADMIN_ACTION': 'Action administrateur'
}

# Messages d'erreur standardisés
ERROR_MESSAGES = {
    'INVALID_CREDENTIALS': "Identifiants invalides",
    'ACCOUNT_LOCKED': "Compte temporairement verrouillé",
    'INSUFFICIENT_FUNDS': "Solde insuffisant",
    'INVALID_AMOUNT': "Montant invalide",
    'CURRENCY_NOT_SUPPORTED': "Devise non supportée",
    'GAME_FULL': "La partie est complète",
    'GAME_NOT_FOUND': "Partie introuvable",
    'PERMISSION_DENIED': "Accès refusé",
    'RATE_LIMIT_EXCEEDED': "Limite de taux dépassée",
    'VALIDATION_ERROR': "Erreur de validation",
    'SERVER_ERROR': "Erreur serveur interne",
    'MAINTENANCE_MODE': "Maintenance en cours",
    'KYC_REQUIRED': "Vérification d'identité requise",
    'MIN_AGE_REQUIRED': "Vous devez avoir au moins 18 ans",
    'REGION_RESTRICTED': "Service non disponible dans votre région"
}

# Configuration des notifications
NOTIFICATION_TYPES = {
    'GAME_INVITATION': {
        'title': 'Nouvelle invitation de jeu',
        'icon': 'game-controller',
        'priority': 'high'
    },
    'GAME_RESULT': {
        'title': 'Résultat de partie',
        'icon': 'trophy',
        'priority': 'medium'
    },
    'TRANSACTION_SUCCESS': {
        'title': 'Transaction réussie',
        'icon': 'check-circle',
        'priority': 'medium'
    },
    'WITHDRAWAL_PROCESSED': {
        'title': 'Retrait traité',
        'icon': 'money',
        'priority': 'high'
    },
    'REFERRAL_EARNINGS': {
        'title': 'Gains de parrainage',
        'icon': 'users',
        'priority': 'low'
    },
    'SECURITY_ALERT': {
        'title': 'Alerte de sécurité',
        'icon': 'shield-alert',
        'priority': 'critical'
    }
}

# Configuration des langues
LANGUAGE_CONFIG = {
    'fr': {
        'name': 'Français',
        'flag': '🇫🇷',
        'rtl': False,
        'regions': ['CI', 'SN', 'ML', 'BF', 'FR', 'BE', 'CH']
    },
    'en': {
        'name': 'English',
        'flag': '🇬🇧',
        'rtl': False,
        'regions': ['US', 'GB', 'CA', 'AU', 'NZ', 'NG', 'GH']
    },
    'es': {
        'name': 'Español',
        'flag': '🇪🇸',
        'rtl': False,
        'regions': ['ES', 'MX', 'AR', 'CO', 'PE', 'CL', 'VE']
    },
    'zh': {
        'name': '中文',
        'flag': '🇨🇳',
        'rtl': False,
        'regions': ['CN', 'TW', 'HK', 'SG', 'MY']
    }
}

# Patterns regex utiles
REGEX_PATTERNS = {
    'USERNAME': r'^[a-zA-Z0-9_]{3,30}$',
    'PHONE_INTERNATIONAL': r'^\+[1-9]\d{1,14}$',
    'REFERRAL_CODE': r'^[A-Z0-9]{6,10}$',
    'TRANSACTION_ID': r'^[A-Z0-9\-]{10,50}$',
    'GAME_ID': r'^[a-f0-9\-]{36}$',
    'PASSWORD_STRONG': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
}

# Export des constantes principales
__all__ = [
    'SUPPORTED_CURRENCIES',
    'DEFAULT_EXCHANGE_RATES',
    'BUSINESS_LIMITS',
    'SECURITY_CONFIG',
    'PERFORMANCE_CONFIG',
    'AUDIT_EVENT_TYPES',
    'ERROR_MESSAGES',
    'NOTIFICATION_TYPES',
    'LANGUAGE_CONFIG',
    'REGEX_PATTERNS',
    'APP_VERSION',
    'APP_NAME',
    'APP_SLUG'
]
