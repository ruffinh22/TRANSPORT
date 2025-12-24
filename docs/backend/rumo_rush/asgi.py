
# ==================================================
# 4. rumo_rush/asgi.py - Configuration ASGI complète avec WebSocket
# ==================================================

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Configuration environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')

# Initialisation Django
django.setup()

# Import du middleware WebSocket (maintenant que Django est initialisé)
from apps.games.middleware import WebSocketAuthMiddleware

# Application HTTP traditionnelle
django_asgi_app = get_asgi_application()

# Import du routing WebSocket
from apps.games.routing import websocket_urlpatterns

# Configuration complète avec WebSocket
application = ProtocolTypeRouter({
    # HTTP traditionnel (REST API, Admin, etc.)
    'http': django_asgi_app,
    
    # WebSocket avec authentification
    'websocket': WebSocketAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})


