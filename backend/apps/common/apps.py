"""Configuration app commune"""
from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
    verbose_name = 'Commun'
    
    def ready(self):
        """Initialiser les signaux et configurations"""
        import apps.common.signals  # noqa
