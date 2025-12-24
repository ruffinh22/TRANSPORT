# rumo_rush/asgi.py
# ===================

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')

django.setup()

from apps.games.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})


# rumo_rush/wsgi.py
# ===================

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.production')

application = get_wsgi_application()


# rumo_rush/celery.py
# ====================

import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.production')

app = Celery('rumo_rush')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'update-leaderboards': {
        'task': 'apps.analytics.tasks.update_leaderboards',
        'schedule': 3600.0,  # Toutes les heures
    },
    'process-referral-commissions': {
        'task': 'apps.referrals.tasks.process_pending_commissions',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
    'check-expired-games': {
        'task': 'apps.games.tasks.check_expired_games',
        'schedule': 600.0,  # Toutes les 10 minutes
    },
    'update-exchange-rates': {
        'task': 'apps.payments.tasks.update_exchange_rates',
        'schedule': 3600.0,  # Toutes les heures
    },
    'process-pending-withdrawals': {
        'task': 'apps.payments.tasks.process_pending_withdrawals',
        'schedule': 1800.0,  # Toutes les 30 minutes
    },
}

app.conf.timezone = 'UTC'


# rumo_rush/urls.py
# ===================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="RUMO RUSH API",
        default_version='v1',
        description="API pour la plateforme de jeux stratégiques RUMO RUSH",
        terms_of_service="https://www.rumorush.com/terms/",
        contact=openapi.Contact(email="dev@rumorush.com"),
        license=openapi.License(name="Propriétaire"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

def health_check(request):
    """Endpoint de vérification de santé."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'RUMO RUSH Backend',
        'version': '1.0.0'
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API v1
    path('api/v1/', include([
        path('', include('apps.accounts.urls')),
        path('', include('apps.games.urls')),
        path('', include('apps.payments.urls')),
        path('', include('apps.referrals.urls')),
        path('', include('apps.analytics.urls')),
    ])),
    
    # Health checks détaillés
    path('health/', include('health_check.urls')),
]

# Servir les fichiers media et static en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Configuration des erreurs
handler400 = 'apps.core.views.error_400'
handler403 = 'apps.core.views.error_403'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'


# apps/games/routing.py
# ========================

from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # WebSocket pour les parties en temps réel
    path('ws/game/<str:room_name>/', consumers.GameConsumer.as_asgi()),
    
    # WebSocket pour le matchmaking
    path('ws/matchmaking/', consumers.MatchmakingConsumer.as_asgi()),
    
    # WebSocket pour les spectateurs
    path('ws/spectate/<str:room_name>/', consumers.SpectatorConsumer.as_asgi()),
]


# apps/games/urls.py
# ===================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GameTypeListView, GameListCreateView, GameDetailView,
    JoinGameView, GameMoveView, GameSurrenderView,
    GameHistoryView, LeaderboardView, TournamentViewSet
)

router = DefaultRouter()
router.register('tournaments', TournamentViewSet)

urlpatterns = [
    # Types de jeux
    path('games/types/', GameTypeListView.as_view(), name='game_types'),
    
    # Gestion des parties
    path('games/', GameListCreateView.as_view(), name='games_list_create'),
    path('games/<uuid:pk>/', GameDetailView.as_view(), name='game_detail'),
    path('games/<uuid:pk>/join/', JoinGameView.as_view(), name='join_game'),
    path('games/<uuid:pk>/move/', GameMoveView.as_view(), name='game_move'),
    path('games/<uuid:pk>/surrender/', GameSurrenderView.as_view(), name='game_surrender'),
    
    # Historique et statistiques
    path('games/history/', GameHistoryView.as_view(), name='game_history'),
    path('games/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    
    # Tournois
    path('', include(router.urls)),
]


# apps/payments/urls.py
# ======================

from django.urls import path
from .views import (
    PaymentMethodListView, TransactionListView, DepositView,
    WithdrawalRequestView, WithdrawalStatusView, WebhookView,
    ExchangeRateView, TransactionDetailView
)

urlpatterns = [
    # Méthodes de paiement
    path('payments/methods/', PaymentMethodListView.as_view(), name='payment_methods'),
    
    # Transactions
    path('payments/transactions/', TransactionListView.as_view(), name='transactions'),
    path('payments/transactions/<uuid:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    
    # Dépôts et retraits
    path('payments/deposit/', DepositView.as_view(), name='deposit'),
    path('payments/withdraw/', WithdrawalRequestView.as_view(), name='withdraw'),
    path('payments/withdraw/status/', WithdrawalStatusView.as_view(), name='withdrawal_status'),
    
    # Webhooks
    path('payments/webhook/<str:provider>/', WebhookView.as_view(), name='payment_webhook'),
    
    # Taux de change
    path('payments/rates/', ExchangeRateView.as_view(), name='exchange_rates'),
]


# apps/referrals/urls.py
# ========================

from django.urls import path
from .views import (
    ReferralCodeView, ReferralStatisticsView, ReferralEar
