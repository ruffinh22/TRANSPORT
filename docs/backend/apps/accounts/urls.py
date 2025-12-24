# apps/accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import oauth_views

app_name = 'accounts'

# URLs principales
urlpatterns = [
    # Authentification
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # Gestion du mot de passe
    path('auth/password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('auth/password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Vérification email
    path('auth/email/verify/', views.EmailVerificationView.as_view(), name='email_verify'),
    path('auth/email/resend/', views.ResendVerificationEmailView.as_view(), name='email_resend'),
    
    # Profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/balance/', views.UserBalanceView.as_view(), name='balance'),
    path('profile/statistics/', views.UserStatisticsView.as_view(), name='statistics'),
    path('profile/activities/', views.UserActivityListView.as_view(), name='activities'),
    path('profile/settings/', views.UserSettingsView.as_view(), name='settings'),
    
    # KYC
    path('kyc/upload/', views.KYCDocumentUploadView.as_view(), name='kyc_upload'),
    path('kyc/documents/', views.KYCDocumentListView.as_view(), name='kyc_documents'),
    path('kyc/status/', views.KYCStatusView.as_view(), name='kyc_status'),
    
    # Gestion du compte
    path('account/deactivate/', views.AccountDeactivationView.as_view(), name='account_deactivate'),
    
    # OAuth URLs
    path('oauth/providers/', oauth_views.oauth_providers, name='oauth_providers'),
    path('oauth/google/url/', oauth_views.google_oauth_url, name='google_oauth_url'),
    path('oauth/google/callback/', oauth_views.google_oauth_callback, name='google_oauth_callback'),
    path('oauth/google/disconnect/', oauth_views.google_oauth_disconnect, name='google_oauth_disconnect'),
    
    # Test OAuth (développement uniquement)
    path('oauth/test/', oauth_views.oauth_config_test, name='oauth_test'),
]

# URLs de debug (développement uniquement)
if hasattr(views, 'DebugUserInfoView'):
    urlpatterns += [
        path('debug/user-info/', views.DebugUserInfoView.as_view(), name='debug_user_info'),
        path('debug/clear-activities/', views.DebugClearUserActivitiesView.as_view(), name='debug_clear_activities'),
    ]  

# ==========================================
# DOCUMENTATION DES ENDPOINTS
# ==========================================
"""
Documentation complète des endpoints de l'API accounts:

AUTHENTIFICATION (/api/accounts/auth/):
├── POST /login/                    - Connexion utilisateur
├── POST /token/refresh/            - Renouvellement token JWT
├── POST /logout/                   - Déconnexion utilisateur
├── POST /register/                 - Inscription nouvel utilisateur
├── POST /verify-email/             - Vérification adresse email
├── POST /resend-verification/      - Renvoyer email de vérification
├── POST /change-password/          - Changer mot de passe
├── POST /forgot-password/          - Demande réinitialisation mot de passe
└── POST /reset-password/           - Confirmer réinitialisation mot de passe

PROFIL UTILISATEUR (/api/accounts/):
├── GET /profile/                   - Consulter profil utilisateur
├── PUT /profile/                   - Modifier profil utilisateur
├── PATCH /profile/                 - Modification partielle profil
├── GET /balance/                   - Consulter soldes multi-devises
├── GET /statistics/                - Statistiques détaillées utilisateur
├── GET /activities/                - Historique activités (paginé)
├── GET /settings/                  - Consulter paramètres utilisateur
└── PUT /settings/                  - Modifier paramètres utilisateur

SYSTÈME KYC (/api/accounts/kyc/):
├── POST /upload/                   - Upload document KYC
├── GET /documents/                 - Liste documents KYC utilisateur
└── GET /status/                    - Statut KYC complet et détaillé

GESTION COMPTE (/api/accounts/account/):
└── POST /deactivate/               - Désactivation temporaire compte

DEBUG (développement seulement - /api/accounts/debug/):
├── GET /info/                      - Informations debug utilisateur
└── DELETE /clear-activities/       - Nettoyer anciennes activités

CODES DE RÉPONSE STANDARDS:
├── 200 OK                         - Succès
├── 201 Created                    - Création réussie
├── 400 Bad Request                - Données invalides
├── 401 Unauthorized               - Non authentifié
├── 403 Forbidden                  - Permissions insuffisantes
├── 404 Not Found                  - Ressource introuvable
├── 429 Too Many Requests          - Limite de taux dépassée
└── 500 Internal Server Error      - Erreur serveur

EXEMPLES D'UTILISATION:

1. INSCRIPTION:
   POST /api/accounts/auth/register/
   {
     "username": "johndoe",
     "email": "john@example.com",
     "password": "SecurePass123",
     "password_confirm": "SecurePass123",
     "first_name": "John",
     "last_name": "Doe",
     "phone_number": "+33612345678",
     "date_of_birth": "1990-01-15",
     "country": "France",
     "terms_accepted": true
   }

2. CONNEXION:
   POST /api/accounts/auth/login/
   {
     "username": "johndoe",
     "password": "SecurePass123"
   }

3. UPLOAD DOCUMENT KYC:
   POST /api/accounts/kyc/upload/
   Content-Type: multipart/form-data
   {
     "document_type": "id_card",
     "file": [fichier binaire]
   }

4. CONSULTER PROFIL:
   GET /api/accounts/profile/
   Authorization: Bearer [access_token]

5. MODIFIER PARAMÈTRES:
   PUT /api/accounts/settings/
   {
     "email_notifications": true,
     "sound_effects": false,
     "auto_accept_games": false
   }

SÉCURITÉ ET LIMITATIONS:
├── Rate limiting sur endpoints sensibles
├── Validation stricte des données d'entrée
├── Chiffrement des mots de passe (bcrypt)
├── Tokens JWT avec expiration
├── Logging complet des activités utilisateur
├── Validation KYC pour gros montants
├── Verrouillage compte après tentatives échouées
└── CORS configuré pour domaines autorisés uniquement

PERMISSIONS REQUISES:
├── Endpoints publics: register, login, verify-email, reset-password
├── Authentification requise: profil, balance, settings, activities
├── KYC approuvé requis: retraits importants (géré dans payments)
└── Staff requis: endpoints d'administration (admin interface)
"""
