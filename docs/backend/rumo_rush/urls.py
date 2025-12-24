# ==================================================
# 2. rumo_rush/urls.py - URLs Principales
# ==================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration du schema OpenAPI/Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="RUMO RUSH API",
        default_version='v1',
        description="API complète pour la plateforme de jeux RUMO RUSH",
        terms_of_service="https://rumorush.com/terms/",
        contact=openapi.Contact(email="api@rumorush.com"),
        license=openapi.License(name="Propriétaire"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Configuration du router API principal
api_router = DefaultRouter()

urlpatterns = [
    # Redirection racine vers l'application frontend
    path('', RedirectView.as_view(url='https://rumorush.com', permanent=False)),
    
    # Page de test FeexPay
    path('test-feexpay/', TemplateView.as_view(template_name='payment_feexpay_test.html'), name='test-feexpay'),
    path('test-feexpay-js/', TemplateView.as_view(template_name='test_feexpay_javascript.html'), name='test_feexpay_js'),
    
    # Administration Django
    path(f'{settings.ADMIN_URL}', admin.site.urls),
    
    # Health Check et Status
    path('health/', include('health_check.urls')),
    path('api/v1/status/', include('apps.core.urls')),
    
    # Documentation API
    path('api/v1/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/v1/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Authentication & Comptes Utilisateurs
    path('api/v1/', include('apps.accounts.urls')),
    
    # API Jeux et Gaming
    path('api/v1/games/', include('apps.games.urls')),
    
    # API Paiements et Transactions
    path('api/v1/payments/', include('apps.payments.urls')),
    
    # API Parrainage et Commissions
    path('api/v1/referrals/', include('apps.referrals.urls')),
    
    # API Analytics et Statistiques
    path('api/v1/analytics/', include('apps.analytics.urls')),
    
    # Webhooks externes (Stripe, etc.)
    #path('webhooks/', include('apps.payments.webhooks_urls')),
    
    # API Router (si des ViewSets globaux sont définis)
    path('api/v1/', include(api_router.urls)),
]

# Configuration pour fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar (si activée)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Configuration pour environnement de test
if settings.DEBUG and hasattr(settings, 'TESTING') and settings.TESTING:
    # URLs spéciales pour les tests
    urlpatterns += [
        path('test-auth/', include('apps.accounts.test_urls')),
        path('test-games/', include('apps.games.test_urls')),
    ]
    

# Gestion des erreurs personnalisées
#handler400 = 'apps.core.views.error_400'
#handler403 = 'apps.core.views.error_403'
#handler404 = 'apps.core.views.error_404'
#handler500 = 'apps.core.views.error_500'


# Configuration de l'interface d'administration
admin.site.site_header = "RUMO RUSH - Administration"
admin.site.site_title = "RUMO RUSH Admin"
admin.site.index_title = "Tableau de bord principal"
admin.site.site_url = "https://rumorush.com"


