# rumo_rush/settings/__init__.py
# ==============================

"""
Configuration modulaire des settings Django pour RUMO RUSH.

Les settings sont organisés par environnement :
- base.py : Configuration de base commune à tous les environnements
- development.py : Configuration pour le développement local
- production.py : Configuration pour l'environnement de production
- testing.py : Configuration pour les tests

Usage:
- Développement : DJANGO_SETTINGS_MODULE=rumo_rush.settings.development
- Production : DJANGO_SETTINGS_MODULE=rumo_rush.settings.production
- Tests : DJANGO_SETTINGS_MODULE=rumo_rush.settings.testing
"""

import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name, default=None):
    """Obtenir une variable d'environnement ou lever une exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

# Détection automatique de l'environnement
environment = get_env_variable('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
elif environment == 'testing':
    from .testing import *
else:
    from .development import *
