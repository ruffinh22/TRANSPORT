# apps/core/urls.py
# ======================

from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from . import views

app_name = 'core'

# URLs principales de l'API core
urlpatterns = [
    
    # ===== ENDPOINTS DE SANTÉ ET MONITORING =====
    path('health/', views.health_check, name='health_check'),
    path('status/', views.status_check, name='status_check'),
    path('ping/', views.status_check, name='ping'),  # Alias pour ping
    
    # ===== CONFIGURATION ET MÉTADONNÉES =====
    path('config/', views.ConfigurationView.as_view(), name='configuration'),
    path('info/', views.ConfigurationView.as_view(), name='app_info'),  # Alias
    
    # ===== CONVERSION DE DEVISES =====
    path('currency/convert/', views.CurrencyConversionView.as_view(), name='currency_convert'),
    path('currency/rates/', views.ExchangeRatesView.as_view(), name='exchange_rates'),
    path('exchange-rates/', views.ExchangeRatesView.as_view(), name='exchange_rates_alias'),
    
    # ===== STATISTIQUES PUBLIQUES =====
    path('stats/', views.PublicStatsView.as_view(), name='public_stats'),
    path('statistics/', views.PublicStatsView.as_view(), name='statistics'),  # Alias
    
    # ===== MAINTENANCE ET ADMINISTRATION =====
    path('maintenance/', views.MaintenanceView.as_view(), name='maintenance'),
    path('system/info/', views.SystemInfoView.as_view(), name='system_info'),
    
    # ===== UTILITAIRES DE DÉVELOPPEMENT =====
]

# URLs de développement (uniquement en mode DEBUG)
if settings.DEBUG:
    urlpatterns += [
        path('test/', views.test_endpoint, name='test_endpoint'),
        path('clear-cache/', views.clear_cache, name='clear_cache'),
        path('debug/system/', views.SystemInfoView.as_view(), name='debug_system_info'),
    ]

# URLs pour les webhooks et callbacks (si nécessaire)
webhook_patterns = [
    # path('webhooks/payment/', views.PaymentWebhookView.as_view(), name='payment_webhook'),
    # path('webhooks/sms/', views.SMSWebhookView.as_view(), name='sms_webhook'),
]

# URLs pour l'API interne (communication entre microservices)
internal_api_patterns = [
    # path('internal/validate-user/', views.InternalUserValidationView.as_view(), name='internal_user_validation'),
    # path('internal/currency-rate/', views.InternalCurrencyRateView.as_view(), name='internal_currency_rate'),
]

# URLs versionnées de l'API
v1_patterns = [
    path('health/', views.health_check, name='v1_health_check'),
    path('config/', views.ConfigurationView.as_view(), name='v1_configuration'),
    path('currency/', include([
        path('convert/', views.CurrencyConversionView.as_view(), name='v1_currency_convert'),
        path('rates/', views.ExchangeRatesView.as_view(), name='v1_exchange_rates'),
    ])),
    path('stats/', views.PublicStatsView.as_view(), name='v1_public_stats'),
    path('maintenance/', views.MaintenanceView.as_view(), name='v1_maintenance'),
]

# URLs pour différentes versions de l'API
api_patterns = [
    path('v1/', include(v1_patterns)),
    # path('v2/', include(v2_patterns)),  # Pour les futures versions
]

# Ajouter les patterns de webhooks et API interne
urlpatterns += [
    path('webhooks/', include(webhook_patterns)),
    path('internal/', include(internal_api_patterns)),
    path('api/', include(api_patterns)),
]

# URLs de redirection pour compatibilité
legacy_patterns = [
    # Redirections pour d'anciennes URLs si nécessaire
    # path('old-endpoint/', RedirectView.as_view(url='/api/v1/new-endpoint/', permanent=True)),
]

urlpatterns += legacy_patterns 
