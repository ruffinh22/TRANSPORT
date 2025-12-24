# apps/core/mixins.py
from django.core.cache import cache
from django.utils.cache import get_cache_key
from rest_framework.response import Response
from django.conf import settings
import hashlib


class CacheResponseMixin:
    """
    Mixin pour mettre en cache les réponses des API.
    """
    cache_timeout = getattr(settings, 'CACHE_TIMEOUT', 300)  # 5 minutes par défaut
    cache_key_prefix = 'api_cache'
    
    def get_cache_key(self, request, view_name, *args, **kwargs):
        """Générer une clé de cache unique."""
        # Créer une clé basée sur l'URL, les paramètres et l'utilisateur
        key_data = f"{request.build_absolute_uri()}_{request.user.id if request.user.is_authenticated else 'anonymous'}"
        
        # Ajouter les paramètres de requête
        if request.GET:
            key_data += f"_{request.GET.urlencode()}"
        
        # Hash pour éviter les clés trop longues
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"{self.cache_key_prefix}_{view_name}_{key_hash}"
    
    def get_cached_response(self, request, *args, **kwargs):
        """Récupérer la réponse depuis le cache."""
        if not getattr(settings, 'USE_CACHE', False):
            return None
            
        cache_key = self.get_cache_key(
            request, 
            self.__class__.__name__, 
            *args, 
            **kwargs
        )
        
        return cache.get(cache_key)
    
    def cache_response(self, request, response, *args, **kwargs):
        """Mettre la réponse en cache."""
        if not getattr(settings, 'USE_CACHE', False):
            return response
            
        # Ne mettre en cache que les réponses réussies
        if response.status_code == 200:
            cache_key = self.get_cache_key(
                request, 
                self.__class__.__name__, 
                *args, 
                **kwargs
            )
            
            cache.set(cache_key, response.data, self.cache_timeout)
        
        return response
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch pour intégrer le cache."""
        # Vérifier le cache pour les requêtes GET
        if request.method == 'GET':
            cached_response = self.get_cached_response(request, *args, **kwargs)
            if cached_response is not None:
                return Response(cached_response)
        
        # Traitement normal
        response = super().dispatch(request, *args, **kwargs)
        
        # Mettre en cache la réponse si applicable
        if hasattr(response, 'data') and request.method == 'GET':
            response = self.cache_response(request, response, *args, **kwargs)
        
        return response
