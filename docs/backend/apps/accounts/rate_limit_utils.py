"""
Utilitaires pour le rate limiting RumoRush
Gestion des adresses IP avec fallback pour environnements locaux/proxy
"""

from django_ratelimit.core import _get_ip
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """
    Obtenir l'adresse IP du client avec fallback sécurisé
    
    Args:
        request: Objet request Django
    
    Returns:
        str: Adresse IP du client ou fallback par défaut
    """
    try:
        # Essayer d'abord la méthode standard de django-ratelimit
        return _get_ip(request)
    except ImproperlyConfigured as e:
        logger.warning(f"Impossible d'obtenir l'IP via django-ratelimit: {e}")
        
        # Fallback 1: HTTP_X_FORWARDED_FOR (proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Prendre la première IP (client original)
            ip = x_forwarded_for.split(',')[0].strip()
            logger.info(f"IP obtenue via X-Forwarded-For: {ip}")
            return ip
        
        # Fallback 2: HTTP_X_REAL_IP (Nginx)
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            logger.info(f"IP obtenue via X-Real-IP: {x_real_ip}")
            return x_real_ip
        
        # Fallback 3: REMOTE_ADDR (connexion directe)
        remote_addr = request.META.get('REMOTE_ADDR')
        if remote_addr:
            logger.info(f"IP obtenue via REMOTE_ADDR: {remote_addr}")
            return remote_addr
        
        # Fallback 4: IP par défaut pour développement local
        default_ip = '127.0.0.1'
        logger.warning(f"Utilisation de l'IP par défaut pour développement: {default_ip}")
        return default_ip

def get_user_or_ip(request):
    """
    Obtenir un identifiant unique pour rate limiting
    Utilise l'utilisateur authentifié ou l'IP comme fallback
    
    Args:
        request: Objet request Django
    
    Returns:
        str: Identifiant unique pour le rate limiting
    """
    # Si utilisateur authentifié, utiliser son ID
    if request.user and request.user.is_authenticated:
        return f"user_{request.user.id}"
    
    # Sinon, utiliser l'IP
    client_ip = get_client_ip(request)
    return f"ip_{client_ip}"

def safe_ratelimit_key(group, request):
    """
    Clé sécurisée pour rate limiting avec gestion d'erreur
    À utiliser avec django-ratelimit key=safe_ratelimit_key
    
    Args:
        group: Groupe de rate limiting (fourni automatiquement par django-ratelimit)
        request: Objet request Django
    
    Returns:
        str: Adresse IP sécurisée pour le rate limiting
    """
    return get_client_ip(request)

def safe_user_or_ip_key(group, request):
    """
    Clé hybride pour rate limiting : utilisateur authentifié ou IP
    À utiliser avec django-ratelimit key=safe_user_or_ip_key
    
    Args:
        group: Groupe de rate limiting (fourni automatiquement par django-ratelimit)
        request: Objet request Django
    
    Returns:
        str: ID utilisateur ou IP pour le rate limiting
    """
    return get_user_or_ip(request)