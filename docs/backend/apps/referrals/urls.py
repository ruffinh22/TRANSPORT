# apps/referrals/urls.py
# ========================
# ✅ VERSION CORRIGÉE - Avec alias directs pour dashboard

from django.urls import path, include
from django.conf import settings
from rest_framework.routers import DefaultRouter
from .views import (
    ReferralProgramViewSet, ReferralViewSet, ReferralCommissionViewSet,
    PremiumSubscriptionViewSet, ReferralStatisticsViewSet, ReferralBonusViewSet,
    generate_qr_code, validate_referral_code
)

from .additional_views import (
    join_via_referral, export_commissions, premium_payment_webhook, 
    referral_analytics_view, bulk_bonus_creation, admin_dashboard_view
)

from .referral_code_views import (
    ReferralCodeViewSet, ReferralCodeClickTrackingView, ReferralLinkView
)

# Configuration du router principal
router = DefaultRouter()
router.register(r'programs', ReferralProgramViewSet, basename='referralprogram')
router.register(r'my-referrals', ReferralViewSet, basename='referral')
router.register(r'commissions', ReferralCommissionViewSet, basename='commission')
router.register(r'premium', PremiumSubscriptionViewSet, basename='subscription')
router.register(r'statistics', ReferralStatisticsViewSet, basename='statistics')
router.register(r'bonuses', ReferralBonusViewSet, basename='bonus')
router.register(r'codes', ReferralCodeViewSet, basename='referral-code')
router.register(r'click-tracking', ReferralCodeClickTrackingView, basename='click-tracking')
router.register(r'links', ReferralLinkView, basename='referral-link')

app_name = 'referrals'

urlpatterns = [
    # ===== ✅ ALIAS DIRECTS (CORRECTION MAJEURE) =====
    # Ces alias permettent d'accéder aux endpoints sans double "referrals/"
    
    # Dashboard principal - /api/v1/referrals/dashboard/
    path(
        'dashboard/',
        ReferralViewSet.as_view({'get': 'dashboard'}),
        name='dashboard'
    ),
    
    # Mon code de parrainage - /api/v1/referrals/my-code/
    path(
        'my-code/',
        ReferralViewSet.as_view({'get': 'my_code'}),
        name='my-code'
    ),
    
    # Créer un parrainage - /api/v1/referrals/create/
    path(
        'create/',
        ReferralViewSet.as_view({'post': 'create'}),
        name='create-referral'
    ),
    
    # Programme par défaut - /api/v1/referrals/programs/default/
    path(
        'programs/default/',
        ReferralProgramViewSet.as_view({'get': 'default'}),
        name='default-program'
    ),
    
    # ===== URLs DU ROUTER =====
    # Inclut tous les ViewSets avec leurs actions par défaut
    path('', include(router.urls)),
    
    # ===== URLs PERSONNALISÉES =====
    
    # Génération de QR code
    path(
        'qr-code/<str:referral_code>/',
        generate_qr_code,
        name='generate-qr-code'
    ),
    
    # Validation de code de parrainage
    path(
        'validate-code/<str:referral_code>/',
        validate_referral_code,
        name='validate-referral-code'
    ),
    
    # Lien de parrainage direct pour inscription
    path(
        'join/<str:referral_code>/',
        join_via_referral,
        name='join-via-referral'
    ),
    
    # Export des commissions
    path(
        'export/commissions/',
        export_commissions,
        name='export-commissions'
    ),
    
    # Webhook pour paiements premium
    path(
        'webhooks/premium-payment/',
        premium_payment_webhook,
        name='premium-payment-webhook'
    ),
    
    # Vue analytics globale
    path(
        'analytics/',
        referral_analytics_view,
        name='analytics'
    ),
    
    # Tableau de bord admin
    path(
        'admin/dashboard/',
        admin_dashboard_view,
        name='admin-dashboard'
    ),
    
    # Création de bonus en masse
    path(
        'admin/bulk-bonus/',
        bulk_bonus_creation,
        name='bulk-bonus-creation'
    ),
]

# ===== URLs DE DEBUG (développement uniquement) =====
if settings.DEBUG:
    from django.http import HttpResponse
    
    def placeholder_view(request, **kwargs):
        """Vue placeholder pour les endpoints non implémentés."""
        return HttpResponse(
            f"Endpoint placeholder - Paramètres: {kwargs}", 
            content_type='text/plain'
        )
    
    debug_patterns = [
        # Test de l'endpoint dashboard
        path(
            'debug/test-dashboard/',
            lambda request: HttpResponse("✅ Dashboard endpoint is working!"),
            name='test-dashboard'
        ),
    ]
    
    urlpatterns.extend(debug_patterns) 
