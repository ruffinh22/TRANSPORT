# FEEXPAY_INTEGRATION.md

# 🚀 Intégration FeexPay - Guide Complet

## 📋 Table des Matières

1. [Configuration](#configuration)
2. [Architecture](#architecture)
3. [Endpoints API](#endpoints-api)
4. [Modèles de Données](#modèles-de-données)
5. [Client HTTP](#client-http)
6. [Webhooks](#webhooks)
7. [Gestion des Erreurs](#gestion-des-erreurs)
8. [Tests](#tests)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## 🔧 Configuration

### Prérequis
- Django 4.2+
- Django REST Framework
- Compte FeexPay avec API key et Shop ID

### Variables d'Environnement

```bash
# .env.production
FEEXPAY_API_KEY=your_api_key_here
FEEXPAY_SHOP_ID=your_shop_id_here
FEEXPAY_WEBHOOK_SECRET=your_webhook_secret
FEEXPAY_TEST_MODE=False
```

### Settings Django

```python
# rumo_rush/settings/base.py

INSTALLED_APPS = [
    # ...
    'apps.payments',
]

# Configuration FeexPay
FEEXPAY_API_KEY = os.environ.get('FEEXPAY_API_KEY')
FEEXPAY_SHOP_ID = os.environ.get('FEEXPAY_SHOP_ID')
FEEXPAY_WEBHOOK_SECRET = os.environ.get('FEEXPAY_WEBHOOK_SECRET')
FEEXPAY_TEST_MODE = os.environ.get('FEEXPAY_TEST_MODE', 'False') == 'True'

# Logging FeexPay
LOGGING = {
    # ...
    'loggers': {
        'feexpay': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## 🏗️ Architecture

### Structure des Modèles

```
┌─────────────────────────────────────────┐
│         Transaction (existant)          │
│  - ID de transaction interne            │
│  - Montant, devise, type                │
│  - Statut, timestamps, métadonnées      │
└────────────────┬────────────────────────┘
                 │
                 │ 1:1 relation
                 ▼
┌─────────────────────────────────────────┐
│      FeexPayTransaction (nouveau)       │
│  - ID FeexPay                           │
│  - Provider, méthode paiement           │
│  - Détails destinataire                 │
│  - Frais, réponse API                   │
│  - Retry count, timestamps              │
└────────────────┬────────────────────────┘
                 │
                 │ FK
                 ▼
┌─────────────────────────────────────────┐
│      FeexPayProvider (16 options)       │
│  - Code (mtn, orange, wave, etc.)       │
│  - Pays, devises                        │
│  - Limites montant, frais               │
│  - Taux de réussite                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│   FeexPayWebhookSignature (nouveau)     │
│  - Webhook ID unique                    │
│  - Payload, signature HMAC              │
│  - Validation, processing               │
│  - Retry logic avec backoff exponentiel │
└─────────────────────────────────────────┘
```

### Flux de Paiement

```
1. Client initie paiement
   │
   ├─→ POST /api/v1/payments/feexpay/initiate/
   │   ├─→ Créer Transaction (interne)
   │   ├─→ Créer FeexPayTransaction
   │   ├─→ Appeler API FeexPay
   │   └─→ Retourner détails paiement
   │
2. Client vérifie statut (polling)
   │
   ├─→ GET /api/v1/payments/feexpay/{tx_id}/status/
   │   ├─→ Récupérer FeexPayTransaction
   │   ├─→ Vérifier auprès de FeexPay si non-final
   │   └─→ Retourner statut actuel
   │
3. FeexPay envoie webhook
   │
   ├─→ POST /api/v1/payments/feexpay/webhook/
   │   ├─→ Valider signature HMAC
   │   ├─→ Parser payload
   │   ├─→ Mettre à jour transaction
   │   └─→ Retourner confirmation (200 OK)
   │
4. Client met à jour UI
   └─→ Afficher succès/erreur
```

---

## 📡 Endpoints API

### 1. Liste des Providers

```http
GET /api/v1/payments/feexpay/providers/
```

**Paramètres:**
- `country` (optionnel): Code pays (SN, CI, TG, etc.)
- `provider` (optionnel): Code provider (mtn, orange, wave, etc.)
- `page` (optionnel): Numéro de page

**Réponse:**
```json
{
  "count": 16,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-1",
      "provider_code": "mtn",
      "provider_display": "MTN",
      "provider_name": "MTN Senegal",
      "country_code": "SN",
      "country_display": "Sénégal",
      "is_active": true,
      "is_test_mode": false,
      "min_amount": 100.00,
      "max_amount": 1000000.00,
      "supported_currencies": ["XOF", "EUR", "USD"],
      "processing_time_seconds": 300,
      "description": "Mobile Money MTN",
      "icon_url": "https://...",
      "success_rate": 99.5,
      "fees_info": {
        "percentage": 1.50,
        "fixed": 0.00,
        "description": "Frais appliqués sur le montant brut"
      },
      "limits_info": {
        "minimum": 100.00,
        "maximum": 1000000.00,
        "currencies": ["XOF", "EUR", "USD"]
      }
    }
  ]
}
```

### 2. Initier un Paiement

```http
POST /api/v1/payments/feexpay/initiate/
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "provider_code": "mtn",
  "amount": "50000",
  "currency": "XOF",
  "recipient_phone": "+221771234567",
  "recipient_email": "user@example.com",
  "recipient_account": "account_number",
  "description": "Dépôt pour jouer",
  "metadata": {
    "game_id": "game-123",
    "source": "mobile"
  },
  "callback_url": "https://app.com/payments/callback"
}
```

**Réponse (201 Created):**
```json
{
  "id": "tx-uuid",
  "internal_transaction_id": "DEP20240115ABC123",
  "feexpay_transaction_id": "",
  "user": "user-id",
  "user_username": "johndoe",
  "provider": "provider-uuid",
  "provider_display": "MTN",
  "amount": "50000.00",
  "currency": "XOF",
  "payment_method": "mobile_money",
  "recipient_phone": "+221771234567",
  "recipient_email": "user@example.com",
  "recipient_account": "account_number",
  "status": "processing",
  "status_display": "En cours de traitement",
  "status_message": "Paiement initié avec FeexPay",
  "fee_amount": "750.00",
  "gross_amount": "50750.00",
  "payment_reference": "ref_12345",
  "callback_status": "",
  "error_code": "",
  "error_message": "",
  "created_at": "2024-01-15T10:30:00Z",
  "initiated_at": "2024-01-15T10:30:05Z",
  "processed_at": null,
  "completed_at": null,
  "expires_at": "2024-01-15T11:00:00Z",
  "retry_count": 0,
  "notes": "",
  "fees_breakdown": {
    "fee_amount": 750.00,
    "gross_amount": 50750.00,
    "percentage_fee": 750.00
  },
  "can_retry": false
}
```

**Codes d'erreur:**
- `400 Bad Request`: Données invalides
- `404 Not Found`: Fournisseur non trouvé
- `402 INVALID_REQUEST`: Montant invalide
- `422 VALIDATION_ERROR`: Validation FeexPay échouée

### 3. Vérifier Statut de Paiement

```http
GET /api/v1/payments/feexpay/{transaction_id}/status/
Authorization: Bearer <token>
```

**Réponse (200 OK):**
```json
{
  "id": "tx-uuid",
  "internal_transaction_id": "DEP20240115ABC123",
  "feexpay_transaction_id": "tx_12345",
  "status": "successful",
  "status_display": "Réussi",
  "completed_at": "2024-01-15T10:35:00Z",
  "amount": "50000.00",
  "currency": "XOF",
  "fees_breakdown": {
    "fee_amount": 750.00,
    "gross_amount": 50750.00
  }
}
```

### 4. Historique des Transactions

```http
GET /api/v1/payments/feexpay/history/
Authorization: Bearer <token>
```

**Paramètres:**
- `status`: Filtrer par statut (pending, processing, successful, failed)
- `provider`: Filtrer par provider
- `page`: Numéro de page

**Réponse:**
```json
{
  "count": 42,
  "next": "https://api.../history/?page=2",
  "previous": null,
  "results": [
    {
      "id": "tx-uuid-1",
      "amount": "50000.00",
      "status": "successful",
      "provider_display": "MTN",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 5. Relancer une Transaction

```http
POST /api/v1/payments/feexpay/retry/
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "transaction_id": "DEP20240115ABC123",
  "reason": "Utilisateur a redemandé"
}
```

**Réponse (200 OK):**
```json
{
  "id": "tx-uuid",
  "internal_transaction_id": "DEP20240115ABC123",
  "status": "pending",
  "retry_count": 1,
  "last_retry_at": "2024-01-15T10:40:00Z"
}
```

---

## 💾 Modèles de Données

### FeexPayProvider

Représente un fournisseur de paiement (16 au total).

```python
class FeexPayProvider(models.Model):
    provider_code: CharField  # mtn, orange, wave, etc.
    provider_name: CharField  # MTN Senegal
    country_code: CharField   # SN, CI, TG, etc.
    is_active: Boolean        # Actif?
    is_test_mode: Boolean     # Mode test?
    min_amount: Decimal       # Minimum 100
    max_amount: Decimal       # Maximum 1M
    fee_percentage: Decimal   # 0-5%
    fee_fixed: Decimal        # Frais fixes
    supported_currencies: JSON # [XOF, EUR, USD]
    success_rate: Decimal     # 0-100%
    created_at: DateTime
    updated_at: DateTime
```

### FeexPayTransaction

Représente une transaction FeexPay spécifique.

```python
class FeexPayTransaction(models.Model):
    user: ForeignKey(User)
    transaction: OneToOneField(Transaction)
    provider: ForeignKey(FeexPayProvider)
    
    # IDs
    feexpay_transaction_id: CharField  # ID FeexPay
    internal_transaction_id: CharField # ID interne
    
    # Montants
    amount: Decimal
    currency: CharField
    fee_amount: Decimal
    gross_amount: Decimal
    
    # Destinataire
    recipient_phone: CharField
    recipient_email: EmailField
    recipient_account: CharField
    
    # Statut
    status: CharField  # pending, processing, successful, failed, cancelled
    status_message: TextField
    
    # Erreurs
    error_code: CharField
    error_message: TextField
    
    # Timing
    created_at: DateTime
    initiated_at: DateTime
    processed_at: DateTime
    completed_at: DateTime
    expires_at: DateTime
    
    # Retry
    retry_count: Integer
    last_retry_at: DateTime
    
    # Métadonnées
    feexpay_response: JSON
    notes: TextField
    ip_address: GenericIPAddressField
    user_agent: TextField
```

### FeexPayWebhookSignature

Suivi des webhooks reçus de FeexPay.

```python
class FeexPayWebhookSignature(models.Model):
    webhook_id: CharField  # Unique
    event_type: CharField
    payload: JSONField     # Données brutes
    signature: CharField   # HMAC SHA256
    headers: JSONField     # Headers HTTP
    
    # Validation
    is_valid: Boolean
    validation_error: TextField
    
    # Traitement
    is_processed: Boolean
    processed_at: DateTime
    processing_error: TextField
    
    # Retry
    retry_count: Integer
    next_retry_at: DateTime
    
    # Métadonnées
    ip_address: GenericIPAddressField
    user_agent: TextField
    received_at: DateTime
    
    # Relation
    transaction: ForeignKey(FeexPayTransaction, null=True)
```

---

## 🌐 Client HTTP

### Utilisation Basique

```python
from apps.payments.feexpay_client import FeexPayClient

# Créer un client
client = FeexPayClient()

# Vérifier santé
is_healthy = client.health_check()

# Récupérer providers
providers = client.get_providers(country_code='SN', active_only=True)

# Initier paiement
response = client.initiate_payment(
    provider_code='mtn',
    amount=Decimal('50000'),
    currency='XOF',
    recipient_phone='+221771234567',
    description='Dépôt pour jouer'
)

# Vérifier statut
status = client.get_payment_status('tx_12345')

# Valider webhook
is_valid = client.validate_webhook_signature(payload, signature)

# Utiliser avec context manager
with FeexPayClient() as client:
    providers = client.get_providers()
    # ...
```

### Gestion des Erreurs

```python
from apps.payments.feexpay_client import (
    FeexPayException, 
    FeexPayValidationError, 
    FeexPayAPIError
)

try:
    client.initiate_payment(...)
except FeexPayValidationError as e:
    print(f"Validation error: {e}")
except FeexPayAPIError as e:
    print(f"API error: {e.error_code} - {e.message}")
except FeexPayException as e:
    print(f"Error: {e}")
```

---

## 🔔 Webhooks

### Configuration

1. **URL Webhook:** `https://api.app.com/api/v1/payments/feexpay/webhook/`

2. **Événements Supportés:**
   - `payment.success` - Paiement réussi
   - `payment.failed` - Paiement échoué
   - `payment.pending` - En attente
   - `payment.expired` - Expiré
   - `payment.cancelled` - Annulé

### Payload Webhook

```json
{
  "webhook_id": "wh_12345",
  "event": "payment.success",
  "transaction_id": "tx_12345",
  "status": "successful",
  "timestamp": "2024-01-15T10:35:00Z",
  "amount": "50000",
  "currency": "XOF",
  "metadata": {
    "internal_tx_id": "DEP20240115ABC123"
  },
  "error_code": null,
  "error_message": null
}
```

### Signature Validation

```http
POST /api/v1/payments/feexpay/webhook/
Content-Type: application/json
X-Webhook-Signature: 8f6e81cc2c5ca77172f3860c254f67e1a6c5c467e3893bcc9c6e6b46af7f1234

{
  "webhook_id": "wh_12345",
  ...
}
```

**Validation:**
```python
import hmac
import hashlib

payload = json.dumps(webhook_data)
secret = 'FEEXPAY_WEBHOOK_SECRET'

# Créer la signature attendue
expected_signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

# Comparer (timing-safe)
if hmac.compare_digest(expected_signature, received_signature):
    # Webhook valide
    pass
else:
    # Webhook invalide - rejeter
    pass
```

### Retry Logic

Les webhooks non-traités sont automatiquement relancés avec backoff exponentiel:

```
Tentative 1: immédiate
Tentative 2: +1 minute
Tentative 3: +2 minutes
Tentative 4: +4 minutes
Tentative 5: +8 minutes
```

Max 5 tentatives, puis manuel.

---

## ⚠️ Gestion des Erreurs

### Codes d'Erreur FeexPay

| Code | Signification |
|------|---------------|
| 401 | Non authentifié - Vérifier API key |
| 402 | Requête invalide - Données manquantes/invalides |
| 404 | Ressource non trouvée |
| 405 | Méthode non autorisée |
| 422 | Erreur validation - Montant/devise invalide |
| 500 | Erreur serveur FeexPay |
| 503 | Service indisponible - Réessayer |

### Handling de Timeout

```python
try:
    response = client.initiate_payment(...)
except FeexPayAPIError as e:
    if e.status_code == 408:
        # Timeout - marquer comme "pending_validation"
        # Polling manuel nécessaire
        pass
```

### Network Resilience

```python
# Avec retries automatiques
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
```

---

## 🧪 Tests

### Tests Unitaires

```bash
# Exécuter tous les tests FeexPay
pytest apps/payments/test_feexpay.py -v

# Tests spécifiques
pytest apps/payments/test_feexpay.py::TestFeexPayClient -v
pytest apps/payments/test_feexpay.py::TestFeexPayAPI::test_feexpay_initiate_payment_success -v

# Avec coverage
pytest apps/payments/test_feexpay.py --cov=apps.payments
```

### Tests d'Intégration

```python
# test_feexpay_integration.py
def test_full_payment_flow(client):
    """Tester flux complet."""
    # 1. Initier paiement
    # 2. Vérifier statut
    # 3. Simuler webhook
    # 4. Vérifier mise à jour
```

### Mocking

```python
from unittest.mock import patch, MagicMock

with patch('apps.payments.feexpay_views.FeexPayClient') as mock_client:
    mock_instance = mock_client.return_value
    mock_instance.initiate_payment.return_value = {
        'transaction_id': 'tx_12345'
    }
    
    # Test avec mock
```

---

## 🚀 Deployment

### Pre-Deployment Checklist

- [ ] Variables d'environnement configurées
- [ ] FEEXPAY_API_KEY et FEEXPAY_SHOP_ID valides
- [ ] FEEXPAY_WEBHOOK_SECRET configuré
- [ ] URL webhook configurée dans FeexPay
- [ ] Tests passent (pytest)
- [ ] Coverage ≥80%
- [ ] Logs configurés (fichier + JSON)
- [ ] Database migrations appliquées

### Commandes de Déploiement

```bash
# Préparer
python manage.py migrate apps.payments

# Seed providers (optionnel)
python manage.py loaddata feexpay_providers

# Collecte des statics
python manage.py collectstatic

# Tests
pytest apps/payments/test_feexpay.py --cov=apps.payments -v

# Health check
curl -H "Authorization: Bearer <token>" \
  https://api.app.com/api/v1/payments/feexpay/health/
```

### Monitoring

```python
# Ajouter monitoring
# - Nombre de paiements/jour
# - Taux de réussite
# - Temps de traitement moyen
# - Erreurs par type
# - Latence API FeexPay

from django.core.mail import send_mail

if success_rate < 95:
    send_mail(
        'FeexPay Success Rate Alert',
        f'Rate: {success_rate}%',
        'alerts@app.com',
        ['admin@app.com']
    )
```

---

## 🔧 Troubleshooting

### Problème: "Unauthorized - Invalid API key"

```
Solution:
1. Vérifier FEEXPAY_API_KEY en .env
2. S'assurer pas d'espaces avant/après
3. Regénérer clé dans dashboard FeexPay
4. Redémarrer service
```

### Problème: "Webhook signature invalide"

```
Solution:
1. Vérifier FEEXPAY_WEBHOOK_SECRET
2. S'assurer payload n'est pas modifié
3. Vérifier algorith HMAC (SHA256)
4. Vérifier endianness (hex encoding)
```

### Problème: "Provider not found"

```
Solution:
1. Vérifier code provider valide (mtn, orange, wave, etc.)
2. Vérifier provider actif dans dashboard
3. Vérifier pays correspond
4. Recharger providers: curl /api/v1/payments/feexpay/providers/
```

### Problème: "Montant invalide"

```
Solution:
1. Vérifier montant ≥ min_amount (100 généralement)
2. Vérifier montant ≤ max_amount (1M généralement)
3. Vérifier devise supportée (XOF, EUR, USD)
4. Vérifier montant ≠ 0
```

### Problème: "Webhook not arriving"

```
Solution:
1. Vérifier URL webhook correcte
2. Vérifier firewall/VPN n'y bloque pas
3. Vérifier logs: tail -f logs/feexpay.log
4. Tester manual webhook: POST /api/v1/payments/feexpay/webhook/
5. Vérifier retry_count dans DB
```

---

## 📚 Resources

- [FeexPay API Docs](https://docs.feexpay.io)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [HMAC Validation](https://en.wikipedia.org/wiki/HMAC)
- [Payment Processing Best Practices](https://stripe.com/docs/payments)

---

## 📞 Support

- **Email:** support@rhumorush.com
- **Slack:** #payments-integration
- **GitHub Issues:** github.com/rhumorush/backend/issues

---

**Dernière mise à jour:** 2024-01-15  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
