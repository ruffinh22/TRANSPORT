# ==================================================
# 3. rumo_rush/wsgi.py - Configuration WSGI Production
# ==================================================

import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
# Charge le .env situé à la racine du projet
load_dotenv(dotenv_path=BASE_DIR / '.env')


import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv


load_dotenv()  
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


