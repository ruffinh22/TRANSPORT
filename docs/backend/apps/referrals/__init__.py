# apps/referrals/__init__.py
# ===========================

"""
Application Referrals - Système de Parrainage RUMO RUSH
=======================================================

Gestion complète du système de parrainage avec :
- Programmes de parrainage configurables avec différents types de commissions
- Calcul automatique des commissions sur les parties jouées
- Système d'abonnement premium pour augmenter les gains
- Gestion des bonus et récompenses de parrainage
- Statistiques détaillées par période (jour/semaine/mois/année)
- Limitations et contrôles anti-abus
- Conformité aux réglementations financières

Fonctionnalités principales :
- Commission en pourcentage, montant fixe ou par paliers
- Limites quotidiennes et mensuelles de gains
- Bonus d'inscription, de premier dépôt et de fidélité
- Tableau de bord complet pour les parrains
- Export des données fiscales
- Notifications en temps réel

Architecture technique :
- Modèles Django avec contraintes d'intégrité
- API REST complète avec pagination
- Tâches Celery pour calculs asynchrones
- Signaux Django pour automatisation
- Cache Redis pour performances
- Audit trail complet

Version: 1.0.0
Dernière mise à jour: 2024
License: Propriétaire RUMO RUSH
"""

# Configuration de l'application
default_app_config = 'apps.referrals.apps.ReferralsConfig'

# Constantes métier
DEFAULT_COMMISSION_RATE = 10.0  # 10% par défaut
FREE_GAMES_LIMIT = 3  # Limite gratuite pour non-premium
MIN_BET_FOR_COMMISSION = 100.0  # Mise minimum en FCFA

# Types de commissions supportés
COMMISSION_TYPES = {
    'percentage': 'Commission en pourcentage',
    'fixed': 'Commission fixe',
    'tiered': 'Commission par paliers'
}

# Types d'abonnement premium
PREMIUM_PLANS = {
    'monthly': {
        'duration_months': 1,
        'price_fcfa': 10000,
        'price_eur': 15,
        'price_usd': 18
    },
    'quarterly': {
        'duration_months': 3,
        'price_fcfa': 27000,
        'price_eur': 40,
        'price_usd': 50
    },
    'yearly': {
        'duration_months': 12,
        'price_fcfa': 96000,
        'price_eur': 145,
        'price_usd': 170
    },
    'lifetime': {
        'duration_months': None,  # Pas d'expiration
        'price_fcfa': 500000,
        'price_eur': 750,
        'price_usd': 900
    }
}

# Paliers de commission par défaut
DEFAULT_COMMISSION_TIERS = [
    (1000, 5.0),    # Jusqu'à 1000 FCFA: 5%
    (5000, 7.5),    # 1001-5000 FCFA: 7.5%
    (10000, 10.0),  # 5001-10000 FCFA: 10%
    (50000, 12.5),  # 10001-50000 FCFA: 12.5%
    (float('inf'), 15.0)  # 50000+ FCFA: 15%
]

# Bonus prédéfinis
BONUS_AMOUNTS = {
    'signup': {
        'fcfa': 500,
        'eur': 1,
        'usd': 1
    },
    'first_deposit': {
        'fcfa': 2000,
        'eur': 3,
        'usd': 4
    },
    'milestone_10_referrals': {
        'fcfa': 5000,
        'eur': 8,
        'usd': 10
    }
}

# Configuration des limites
DAILY_COMMISSION_LIMITS = {
    'free_user': {
        'fcfa': 10000,
        'eur': 15,
        'usd': 18
    },
    'premium_user': {
        'fcfa': 100000,
        'eur': 150,
        'usd': 180
    }
}

MONTHLY_COMMISSION_LIMITS = {
    'free_user': {
        'fcfa': 200000,
        'eur': 300,
        'usd': 350
    },
    'premium_user': {
        'fcfa': 2000000,
        'eur': 3000,
        'usd': 3500
    }
}

# Messages d'erreur standardisés
ERROR_MESSAGES = {
    'inactive_referral': "Ce parrainage n'est plus actif",
    'program_inactive': "Le programme de parrainage est suspendu",
    'bet_too_low': "La mise est trop faible pour générer une commission",
    'daily_limit_reached': "Limite quotidienne de commission atteinte",
    'monthly_limit_reached': "Limite mensuelle de commission atteinte",
    'free_games_exhausted': "Limite de parties gratuites atteinte",
    'self_referral': "Impossible de se parrainer soi-même",
    'already_referred': "Cet utilisateur a déjà un parrain",
    'subscription_required': "Abonnement premium requis pour cette fonctionnalité"
}

# Configuration des notifications
NOTIFICATION_SETTINGS = {
    'new_referral': True,
    'commission_earned': True,
    'bonus_available': True,
    'subscription_expiring': True,
    'milestone_reached': True
}

# Métriques importantes à tracker
TRACKED_METRICS = [
    'total_referrals',
    'active_referrals',
    'total_commission_earned',
    'conversion_rate',
    'average_game_frequency',
    'lifetime_value',
    'retention_rate'
]

# Export des constantes principales
__all__ = [
    'DEFAULT_COMMISSION_RATE',
    'FREE_GAMES_LIMIT',
    'MIN_BET_FOR_COMMISSION',
    'COMMISSION_TYPES',
    'PREMIUM_PLANS',
    'DEFAULT_COMMISSION_TIERS',
    'BONUS_AMOUNTS',
    'DAILY_COMMISSION_LIMITS',
    'MONTHLY_COMMISSION_LIMITS',
    'ERROR_MESSAGES',
    'NOTIFICATION_SETTINGS',
    'TRACKED_METRICS'
]
