"""
Context processors pour l'application core
"""

def debug_context(request):
    """
    Ajoute des variables de debug au contexte des templates
    """
    from django.conf import settings
    
    return {
        'DEBUG': settings.DEBUG,
        'ENVIRONMENT': getattr(settings, 'DJANGO_ENVIRONMENT', 'production'),
    }
