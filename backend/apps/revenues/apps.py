"""Configuration app Revenus"""
from django.apps import AppConfig


class RevenuesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.revenues'
    verbose_name = 'Gestion Revenus'
