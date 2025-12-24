# apps/payments/urls.py
# =========================

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Vues génériques
    PaymentMethodListView,
    TransactionListView,
    TransactionDetailView,
    
    # Dépôts
    DepositCreateView,
    DepositConfirmView,
    FeexPaySyncView,
    
    # Retraits
    WithdrawalCreateView,
    WithdrawalListView,
    WithdrawalDetailView,
    WithdrawalCancelView,
    
    # Portefeuilles
    WalletListView,
    
    # Transactions
    TransactionCancelView,
    
    # Statistiques et utilitaires
    PaymentStatisticsView,
    FeeCalculatorView,
    CurrencyConversionView,
    ExchangeRateListView,
    
    # Webhooks
    PaymentWebhookView,
    
    # ViewSets
    PaymentMethodViewSet,
    TransactionViewSet,
    
    # Administration
    AdminWithdrawalApprovalView,
    AdminTransactionListView,
    PaymentAnalyticsView,
)
from .feexpay_views import (
    FeexPayHealthCheckView,
    FeexPayProvidersListView,
    FeexPayInitiatePaymentView,
    FeexPayTransactionStatusView,
    FeexPayWebhookView,
    FeexPayTransactionHistoryView,
    FeexPayRetryTransactionView
)
from .webhook_feexpay import FeexPayWebhookView as FeexPayWebhookNewView, test_feexpay_webhook
from . import views_withdrawal
from .views_sync import sync_status, force_sync, balance_audit, check_pending_transactions, auto_complete_pending, auto_complete_transactions, pending_transactions_status, feexpay_sync_all, feexpay_sync_by_reference, feexpay_check_status

# Configuration des ViewSets avec router
router = DefaultRouter()
router.register(r'methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'transactions-api', TransactionViewSet, basename='transaction-api')

app_name = 'payments'

# URLs principales
urlpatterns = [
    # ==========================================
    # API ROUTER (ViewSets)
    # ==========================================
    path('api/', include(router.urls)),
    
    # ==========================================
    # MÉTHODES DE PAIEMENT
    # ==========================================
    path('methods/', 
         PaymentMethodListView.as_view(), 
         name='payment_methods'),
    
    # ==========================================
    # DÉPÔTS
    # ==========================================
    path('deposits/', include([
        path('create/', 
             DepositCreateView.as_view(), 
             name='deposit_create'),
        path('confirm/', 
             DepositConfirmView.as_view(), 
             name='deposit_confirm'),
        path('sync/', 
             FeexPaySyncView.as_view(), 
             name='feexpay_sync'),
    ])),
    
    # ==========================================
    # RETRAITS
    # ==========================================
    path('withdrawals/', include([
        path('create/', 
             WithdrawalCreateView.as_view(), 
             name='withdrawal_create'),
        path('list/', 
             WithdrawalListView.as_view(), 
             name='withdrawal_list'),
        path('<uuid:pk>/', 
             WithdrawalDetailView.as_view(), 
             name='withdrawal_detail'),
        path('<uuid:pk>/cancel/', 
             WithdrawalCancelView.as_view(), 
             name='withdrawal_cancel'),
        
        # Nouveaux endpoints pour retraits FeexPay
        path('process/', 
             views_withdrawal.process_withdrawal, 
             name='process_withdrawal'),
        path('networks/', 
             views_withdrawal.withdrawal_networks, 
             name='withdrawal_networks'),
        path('history/', 
             views_withdrawal.withdrawal_history, 
             name='withdrawal_history'),
        path('fees/', 
             views_withdrawal.withdrawal_fees, 
             name='withdrawal_fees'),
    ])),
    
    # ==========================================
    # TRANSACTIONS
    # ==========================================
    path('transactions/', include([
        path('', 
             TransactionListView.as_view(), 
             name='transaction_list'),
        path('<uuid:pk>/', 
             TransactionDetailView.as_view(), 
             name='transaction_detail'),
        path('<uuid:pk>/cancel/', 
             TransactionCancelView.as_view(), 
             name='transaction_cancel'),
    ])),
    
    # ==========================================
    # PORTEFEUILLES
    # ==========================================
    path('wallets/', 
         WalletListView.as_view(), 
         name='wallet_list'),
    
    # ==========================================
    # STATISTIQUES ET UTILITAIRES
    # ==========================================
    path('statistics/', 
         PaymentStatisticsView.as_view(), 
         name='payment_statistics'),
    
    path('calculate-fees/', 
         FeeCalculatorView.as_view(), 
         name='calculate_fees'),
    
    path('convert-currency/', 
         CurrencyConversionView.as_view(), 
         name='convert_currency'),
    
    path('exchange-rates/', 
         ExchangeRateListView.as_view(), 
         name='exchange_rates'),
    
    # ==========================================
    # WEBHOOKS
    # ==========================================
    path('webhooks/<str:provider>/', 
         PaymentWebhookView.as_view(), 
         name='payment_webhook'),
    
    # Nouveau webhook FeexPay spécialisé
    path('webhooks/feexpay/', 
         FeexPayWebhookNewView.as_view(), 
         name='feexpay_webhook_new'),
    
    path('webhooks/feexpay/test/', 
         test_feexpay_webhook, 
         name='feexpay_webhook_test'),
    
    # ==========================================
    # ADMINISTRATION
    # ==========================================
    path('admin/', include([
        path('withdrawals/<uuid:pk>/approve/', 
             AdminWithdrawalApprovalView.as_view(), 
             name='admin_withdrawal_approval'),
        path('transactions/all/', 
             AdminTransactionListView.as_view(), 
             name='admin_transaction_list'),
        path('analytics/', 
             PaymentAnalyticsView.as_view(), 
             name='payment_analytics'),
    ])),
    
    # ==========================================
    # SYNCHRONISATION FEEXPAY
    # ==========================================
    path('sync/', include([
        path('status/', 
             sync_status, 
             name='sync_status'),
        path('force/', 
             force_sync, 
             name='force_sync'),
        path('audit/', 
             balance_audit, 
             name='balance_audit'),
        path('check-pending/', 
             check_pending_transactions, 
             name='check_pending'),
        path('auto-complete/', 
             auto_complete_pending, 
             name='auto_complete'),
        
        # ✅ Nouveaux endpoints FeexPay
        path('feexpay-all/', 
             feexpay_sync_all, 
             name='feexpay_sync_all'),
        path('feexpay-reference/', 
             feexpay_sync_by_reference, 
             name='feexpay_sync_reference'),
        path('feexpay-check/<str:feexpay_reference>/', 
             feexpay_check_status, 
             name='feexpay_check_status'),
    ])),
    
    # ==========================================
    # FEEXPAY INTEGRATION (Nouveaux endpoints)
    # ==========================================
    path('feexpay/', include([
        path('health/', 
             FeexPayHealthCheckView.as_view(), 
             name='feexpay_health'),
        
        path('providers/', 
             FeexPayProvidersListView.as_view(), 
             name='feexpay_providers'),
        
        path('initiate/', 
             FeexPayInitiatePaymentView.as_view(), 
             name='feexpay_initiate'),
        
        path('<uuid:transaction_id>/status/', 
             FeexPayTransactionStatusView.as_view(), 
             name='feexpay_status'),
        
        path('webhook/', 
             FeexPayWebhookView.as_view(), 
             name='feexpay_webhook'),
        
        path('history/', 
             FeexPayTransactionHistoryView.as_view(), 
             name='feexpay_history'),
        
        path('retry/', 
             FeexPayRetryTransactionView.as_view(), 
             name='feexpay_retry'),
    ])),
]

# Ajouter les URLs de test en mode développement
from django.conf import settings
if settings.DEBUG:
    from .views import TestPaymentView
    
    test_patterns = [
        path('test/', include([
            path('simulate/', 
                 TestPaymentView.as_view(), 
                 name='test_payment'),
        ])),
    ]
    urlpatterns += test_patterns

# ==========================================
# DOCUMENTATION DES ENDPOINTS
# ==========================================
"""
Documentation complète des endpoints de l'API payments:

MÉTHODES DE PAIEMENT (/api/payments/methods/):
├── GET /                           - Liste des méthodes disponibles
├── GET /api/{id}/                  - Détail d'une méthode
└── POST /api/{id}/calculate_fees/  - Calculer les frais

DÉPÔTS (/api/payments/deposits/):
└── POST /create/                   - Créer une demande de dépôt

RETRAITS (/api/payments/withdrawals/):
├── POST /create/                   - Créer une demande de retrait
├── GET /list/                      - Liste des retraits utilisateur
├── GET /{id}/                      - Détail d'un retrait
└── POST /{id}/cancel/              - Annuler un retrait

TRANSACTIONS (/api/payments/transactions/):
├── GET /                           - Liste des transactions utilisateur
├── GET /{id}/                      - Détail d'une transaction
├── POST /{id}/cancel/              - Annuler une transaction
├── GET /api/summary/               - Résumé des transactions (ViewSet)
└── POST /api/{id}/cancel/          - Annuler via ViewSet

PORTEFEUILLES (/api/payments/wallets/):
└── GET /                           - Liste des portefeuilles utilisateur

UTILITAIRES (/api/payments/):
├── GET /statistics/                - Statistiques de paiement utilisateur
├── POST /calculate-fees/           - Calculateur de frais
├── POST /convert-currency/         - Convertisseur de devises
└── GET /exchange-rates/            - Taux de change actuels

WEBHOOKS (/api/payments/webhooks/):
└── POST /{provider}/               - Recevoir webhook d'un fournisseur

ADMINISTRATION (/api/payments/admin/):
├── POST /withdrawals/{id}/approve/ - Approuver/rejeter un retrait
├── GET /transactions/all/          - Toutes les transactions (admin)
└── GET /analytics/                 - Analytics de paiement (admin)

TEST (développement - /api/payments/test/):
└── POST /simulate/                 - Simuler une transaction de test

EXEMPLES D'UTILISATION:

1. CRÉER UN DÉPÔT:
   POST /api/payments/deposits/create/
   {
     "amount": "10000",
     "currency": "FCFA",
     "payment_method_id": "uuid-here",
     "return_url": "https://app.com/success",
     "metadata": {"source": "mobile"}
   }

2. CRÉER UN RETRAIT:
   POST /api/payments/withdrawals/create/
   {
     "amount": "5000",
     "currency": "FCFA",
     "payment_method": "uuid-here",
     "recipient_details": {
       "phone_number": "+33612345678",
       "operator": "Orange"
     }
   }

3. CALCULER LES FRAIS:
   POST /api/payments/calculate-fees/
   {
     "amount": "10000",
     "currency": "FCFA",
     "payment_method_id": "uuid-here",
     "transaction_type": "withdrawal"
   }

4. CONVERTIR DEVISE:
   POST /api/payments/convert-currency/
   {
     "amount": "100",
     "from_currency": "EUR",
     "to_currency": "FCFA"
   }

5. CONSULTER STATISTIQUES:
   GET /api/payments/statistics/
   
   Retourne:
   {
     "deposits": {
       "total_amount": "50000.00",
       "count": 5,
       "average": "10000.00"
     },
     "withdrawals": {...},
     "gaming": {...},
     "summary": {...}
   }

CODES DE RÉPONSE:
├── 200 OK                         - Succès
├── 201 Created                    - Création réussie
├── 400 Bad Request                - Données invalides
├── 401 Unauthorized               - Non authentifié
├── 403 Forbidden                  - Permissions insuffisantes
├── 404 Not Found                  - Ressource introuvable
├── 429 Too Many Requests          - Limite de taux dépassée
└── 500 Internal Server Error      - Erreur serveur

PERMISSIONS REQUISES:
├── Public: exchange-rates, webhooks
├── Authentifié: methods, transactions, wallets
├── Email vérifié: deposits
├── KYC approuvé: withdrawals (gros montants)
└── Admin: administration, analytics

LIMITATIONS DE TAUX:
├── Dépôts: 10/h par utilisateur
├── Retraits: 5/h par utilisateur
└── Webhooks: illimité

SÉCURITÉ:
├── Validation stricte des montants et devises
├── Vérification des soldes avant transactions
├── Règle des 60% d'utilisation des dépôts
├── Logging complet de toutes les opérations
├── Auto-approbation pour petits montants
├── Blocage temporaire des fonds pendant traitement
└── Webhooks avec validation de signature (à implémenter)

NOTIFICATIONS:
├── Emails de confirmation pour dépôts/retraits
├── Notifications push pour changements de statut
├── Alertes admin pour nouvelles demandes
└── SMS pour transactions importantes (si activé)

INTÉGRATIONS:
├── Stripe: cartes bancaires internationales
├── Mobile Money: Orange, MTN, Moov
├── Crypto: Bitcoin, Ethereum
├── Banques locales: virements SEPA
└── PayPal: paiements internationaux
"""
