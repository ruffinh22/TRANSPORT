# 🔧 Corrections des Tests Échoués - FeexPay Integration

Ce fichier fournit les corrections complètes pour les 6 tests échoués.

---

## 🔴 PRIORITE 1: Correction Test 5 (test_feexpay_webhook_valid)

### Le Problème
```
TypeError: Object of type FakePayload is not JSON serializable
when serializing dict item 'wsgi.input'
```

### La Correction

**Fichier**: `backend/apps/payments/feexpay_views.py`

**À appliquer aux lignes ~343-350**:

```python
import json
from io import IOBase

class WebhookView(APIView):
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def post(self, request):
        """Gérer les webhooks FeexPay."""
        try:
            raw_body = request.body
            payload = json.loads(raw_body)
            
            # ✅ CORRECTION: Nettoyer request.META
            clean_meta = {}
            for key, value in request.META.items():
                try:
                    # Vérifier que la valeur peut être sérialisée en JSON
                    json.dumps(value)
                    clean_meta[key] = value
                except (TypeError, ValueError):
                    # Ignorer les valeurs non-sérialisables (FakePayload, etc.)
                    pass
            
            # Créer la signature avec les données nettoyées
            webhook_sig = FeexPayWebhookSignature.objects.create(
                webhook_id=payload.get('webhook_id', ''),
                raw_request=clean_meta,  # ✅ Utiliser clean_meta
                payload=payload,
                raw_payload=raw_body.decode('utf-8') if isinstance(raw_body, bytes) else raw_body,
                is_valid=True
            )
            
            logger.info(f"Webhook FeexPay reçu: {webhook_sig.webhook_id}")
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur traitement webhook FeexPay: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

---

## 🟠 PRIORITE 2: Corrections Tests 3, 4, 6 (HTTP Mocking)

### Le Problème
```
HTTPSConnectionPool: Max retries exceeded
NameResolutionError: Failed to resolve 'api.feexpay.io'
```

### La Correction

**Fichier**: `backend/apps/payments/test_feexpay.py`

**Ajouter ces imports au début**:

```python
from unittest.mock import patch, MagicMock
import requests
```

**Test 3: test_feexpay_initiate_payment_success**

```python
@patch('requests.post')
def test_feexpay_initiate_payment_success(self, mock_post):
    """Test initiate payment success."""
    # Mock la réponse HTTP
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'success': True,
        'payment_url': 'https://checkout.feexpay.io/....',
        'transaction_id': 'tx_test_123'
    }
    mock_post.return_value = mock_response
    
    response = self.client.post(
        '/api/v1/payments/feexpay/initiate/',
        {
            'phone_number': '+225712345678',
            'amount': '50000',
            'provider': 'mtn',
            'currency': 'XOF'
        },
        format='json'
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert 'transaction_id' in response.data
```

**Test 4: test_feexpay_transaction_status**

```python
@patch('requests.get')
def test_feexpay_transaction_status(self, mock_get):
    """Test get transaction status."""
    # Créer une transaction de test
    transaction = FeexPayTransaction.objects.create(
        transaction_id='tx_test_123',
        status='pending',
        provider='mtn',
        amount=Decimal('50000'),
        currency='XOF'
    )
    
    # Mock la réponse HTTP
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': 'tx_test_123',
        'status': 'success',
        'amount': 50000,
        'currency': 'XOF'
    }
    mock_get.return_value = mock_response
    
    response = self.client.get(
        f'/api/v1/payments/feexpay/status/{transaction.id}/'
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
```

**Test 6: test_full_payment_flow**

```python
@patch('requests.post')
@patch('requests.get')
def test_full_payment_flow(self, mock_get, mock_post):
    """Test full payment flow from initiation to completion."""
    # Mock POST (initiate payment)
    initiate_response = MagicMock()
    initiate_response.status_code = 200
    initiate_response.json.return_value = {
        'success': True,
        'payment_url': 'https://checkout.feexpay.io/....',
        'transaction_id': 'tx_flow_123'
    }
    
    # Mock GET (check status)
    status_response = MagicMock()
    status_response.status_code = 200
    status_response.json.return_value = {
        'id': 'tx_flow_123',
        'status': 'success',
        'amount': 100000,
        'currency': 'XOF'
    }
    
    mock_post.return_value = initiate_response
    mock_get.return_value = status_response
    
    # Step 1: Initiate payment
    init_response = self.client.post(
        '/api/v1/payments/feexpay/initiate/',
        {
            'phone_number': '+225712345678',
            'amount': '100000',
            'provider': 'orange',
            'currency': 'XOF'
        },
        format='json'
    )
    assert init_response.status_code == status.HTTP_201_CREATED
    
    # Step 2: Check status
    tx_id = init_response.data['transaction_id']
    status_resp = self.client.get(
        f'/api/v1/payments/feexpay/status/{tx_id}/'
    )
    assert status_resp.status_code == status.HTTP_200_OK
    assert status_resp.data['status'] == 'success'
```

---

## 🟡 PRIORITE 3: Corrections Tests 1, 2 (Fixtures)

### Le Problème
```
Environment variables not available in pytest fixture
```

### La Correction

**Fichier**: `backend/apps/payments/test_feexpay.py`

```python
import os
import pytest
from unittest.mock import patch

class TestFeexPayClient:
    """Tests du client FeexPay."""
    
    @pytest.fixture
    def mock_env(self):
        """Fournir les variables d'environnement."""
        with patch.dict(os.environ, {
            'FEEXPAY_API_KEY': 'test_key_12345',
            'FEEXPAY_SHOP_ID': 'shop_12345',
            'FEEXPAY_WEBHOOK_SECRET': 'webhook_secret'
        }):
            yield
    
    def test_client_initialization(self, mock_env):
        """Tester l'initialisation du client."""
        from apps.payments.feexpay_client import FeexPayClient
        client = FeexPayClient()
        
        assert client.api_key == 'test_key_12345'
        assert client.shop_id == 'shop_12345'
        assert client.webhook_secret == 'webhook_secret'
    
    def test_client_missing_credentials(self):
        """Tester erreur sans credentials."""
        from apps.payments.feexpay_client import FeexPayClient, FeexPayException
        
        # Sans variable d'environnement
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(FeexPayException):
                FeexPayClient()
```

---

## 🚀 Guide d'Application des Corrections

### Étape 1: Corriger le Client (Priorité 1)

```bash
# Éditer feexpay_views.py
cd /home/lidruf/rhumo_rush/backend
nano apps/payments/feexpay_views.py
# Aller à la ligne ~343 et appliquer la correction
```

### Étape 2: Mettre à jour les Tests

```bash
# Éditer test_feexpay.py
nano apps/payments/test_feexpay.py
# Appliquer les corrections pour les tests 1-6
```

### Étape 3: Lancer les Tests

```bash
# Tester un par un
pytest apps/payments/test_feexpay.py::TestFeexPayClient::test_client_initialization -v
pytest apps/payments/test_feexpay.py::TestFeexPayAPI::test_feexpay_initiate_payment_success -v
pytest apps/payments/test_feexpay.py::TestFeexPayAPI::test_feexpay_webhook_valid -v

# Tous les tests
pytest apps/payments/test_feexpay.py -v
```

---

## ✅ Résultats Attendus Après Corrections

```
Résultats Avant:  ❌ 6 FAILED, ✅ 24 PASSED
Résultats Après:  ✅ 30 PASSED, ❌ 0 FAILED

Couverture:       36% → 50%+
Taux réussite:    80% → 100% ✅
```

---

## 📋 Checklist d'Implémentation

- [ ] **Test 5 (CRITIQUE)**: Nettoyer request.META dans feexpay_views.py
- [ ] **Test 3**: Ajouter @patch('requests.post') pour initiate payment
- [ ] **Test 4**: Ajouter @patch('requests.get') pour status check
- [ ] **Test 6**: Combiner mocks pour full flow
- [ ] **Test 1**: Fixer fixture avec mock_env yield
- [ ] **Test 2**: Utiliser patch.dict avec clear=True
- [ ] Lancer pytest pour valider
- [ ] Vérifier couverture de code
- [ ] Exécuter tous les tests à nouveau

---

**Généré**: 15 novembre 2025  
**Prêt pour implémentation**: OUI ✅
**Temps estimé**: 30-45 minutes
