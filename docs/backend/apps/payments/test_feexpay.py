# apps/payments/test_feexpay.py
# ==============================

"""
Tests pour l'intégration FeexPay.

Tests unitaires et d'intégration pour les modèles, client, serializers et vues FeexPay.
"""

import os
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from apps.payments.models import FeexPayProvider, FeexPayTransaction, FeexPayWebhookSignature, Transaction
from apps.payments.feexpay_client import (
    FeexPayClient, FeexPayException, FeexPayValidationError, FeexPayAPIError,
    FeexPayAuthenticationError

)
from apps.accounts.models import User

pytestmark = pytest.mark.django_db


# ============= TESTS UNITAIRES - CLIENT FEEXPAY =============

class TestFeexPayClient:
    """Tests du client FeexPay."""
    
    @pytest.fixture
    def mock_settings(self):
        """Fournir les settings FeexPay moqués."""
        with patch('django.conf.settings.FEEXPAY_API_KEY', 'test_key_12345'):
            with patch('django.conf.settings.FEEXPAY_SHOP_ID', 'shop_12345'):
                with patch('django.conf.settings.FEEXPAY_WEBHOOK_SECRET', 'webhook_secret'):
                    yield
    
    @pytest.fixture
    def client(self, mock_settings):
        """Créer un client FeexPay pour les tests."""
        from apps.payments.feexpay_client import FeexPayClient
        return FeexPayClient()
    
    def test_client_initialization(self, client):
        """Tester l'initialisation du client."""
        assert client.api_key == 'test_key_12345'
        assert client.shop_id == 'shop_12345'
        assert client.webhook_secret == 'webhook_secret'
    
    def test_client_missing_credentials(self):
        """Tester erreur sans credentials."""
        from apps.payments.feexpay_client import FeexPayClient, FeexPayAuthenticationError
        with patch('django.conf.settings.FEEXPAY_API_KEY', None):
            with patch('django.conf.settings.FEEXPAY_SHOP_ID', None):
                with pytest.raises(FeexPayAuthenticationError):
                    FeexPayClient(api_key=None, shop_id=None)
    
    def test_health_check_success(self, client):
        """Tester health check succès."""
        with patch.object(client, 'get_providers', return_value=[]):
            assert client.health_check() is True
    
    def test_health_check_failure(self, client):
        """Tester health check échoue."""
        with patch.object(client, 'get_providers', side_effect=Exception("API down")):
            assert client.health_check() is False
    
    def test_get_supported_providers(self, client):
        """Tester récupération des providers supportés."""
        providers = client.get_supported_providers()
        assert 'mtn' in providers
        assert 'orange' in providers
        assert 'wave' in providers
        assert len(providers) == 16
    
    def test_get_countries_for_provider(self, client):
        """Tester pays pour un provider."""
        countries = client.get_countries_for_provider('mtn')
        assert 'SN' in countries  # Sénégal
        assert 'CI' in countries  # Côte d'Ivoire
        
        countries = client.get_countries_for_provider('wave')
        assert 'SN' in countries
        assert len(countries) == 1
    
    def test_validate_provider_amount_valid(self, client):
        """Tester validation montant valide."""
        with patch.object(client, 'get_provider_details', return_value={
            'min_amount': 100,
            'max_amount': 1000000
        }):
            assert client.validate_provider_amount('mtn', Decimal('50000')) is True
    
    def test_validate_provider_amount_too_small(self, client):
        """Tester montant minimum."""
        with patch.object(client, 'get_provider_details', return_value={
            'min_amount': 100,
            'max_amount': 1000000
        }):
            with pytest.raises(FeexPayValidationError):
                client.validate_provider_amount('mtn', Decimal('50'))
    
    def test_validate_provider_amount_too_large(self, client):
        """Tester montant maximum."""
        with patch.object(client, 'get_provider_details', return_value={
            'min_amount': 100,
            'max_amount': 1000000
        }):
            with pytest.raises(FeexPayValidationError):
                client.validate_provider_amount('mtn', Decimal('2000000'))
    
    def test_webhook_signature_validation_valid(self, client):
        """Tester validation signature valide."""
        import hmac
        import hashlib
        
        payload = '{"test": "data"}'
        secret = 'webhook_secret'
        
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert client.validate_webhook_signature(payload, signature, secret) is True
    
    def test_webhook_signature_validation_invalid(self, client):
        """Tester validation signature invalide."""
        with pytest.raises(FeexPayException):
            client.validate_webhook_signature(
                '{"test": "data"}',
                'invalid_signature_here',
                'webhook_secret'
            )
    
    def test_parse_webhook_payload_valid(self, client):
        """Tester parsing webhook valide."""
        payload = {
            'event': 'payment.success',
            'transaction_id': 'tx_12345',
            'status': 'successful',
            'timestamp': timezone.now().isoformat(),
            'amount': '50000',
            'currency': 'XOF'
        }
        
        result = client.parse_webhook_payload(payload)
        assert result['event'] == 'payment.success'
        assert result['transaction_id'] == 'tx_12345'
        assert result['status'] == 'successful'
    
    def test_parse_webhook_payload_missing_field(self, client):
        """Tester parsing webhook avec champ manquant."""
        payload = {
            'event': 'payment.success',
            'transaction_id': 'tx_12345'
            # Manque 'status' et 'timestamp'
        }
        
        with pytest.raises(FeexPayValidationError):
            client.parse_webhook_payload(payload)


# ============= TESTS MODELES =============

class TestFeexPayProvider(TestCase):
    """Tests du modèle FeexPayProvider."""
    
    def setUp(self):
        """Créer des données de test."""
        self.provider = FeexPayProvider.objects.create(
            provider_code='mtn',
            provider_name='MTN Senegal',
            country_code='SN',
            is_active=True,
            min_amount=Decimal('100.00'),
            max_amount=Decimal('1000000.00'),
            fee_percentage=Decimal('1.50'),
            fee_fixed=Decimal('0.00'),
            supported_currencies=['XOF', 'EUR', 'USD']
        )
    
    def test_provider_creation(self):
        """Tester création du provider."""
        assert self.provider.provider_code == 'mtn'
        assert self.provider.country_code == 'SN'
        assert self.provider.is_active is True
    
    def test_provider_calculate_fees(self):
        """Tester calcul des frais."""
        amount = Decimal('50000.00')
        fees = self.provider.calculate_fees(amount)
        
        assert fees['percentage_fee'] == Decimal('750.00')  # 1.5% de 50000
        assert fees['fixed_fee'] == Decimal('0.00')
        assert fees['total_fees'] == Decimal('750.00')
        assert fees['net_amount'] == Decimal('50750.00')
    
    def test_provider_validate_amount_valid(self):
        """Tester validation montant valide."""
        assert self.provider.validate_amount(Decimal('50000.00')) is True
    
    def test_provider_validate_amount_too_small(self):
        """Tester montant trop petit."""
        with pytest.raises(Exception):  # ValidationError
            self.provider.validate_amount(Decimal('50.00'))
    
    def test_provider_str(self):
        """Tester représentation string."""
        expected = "MTN - Sénégal"
        assert str(self.provider) == expected


class TestFeexPayTransaction(TestCase):
    """Tests du modèle FeexPayTransaction."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.provider = FeexPayProvider.objects.create(
            provider_code='mtn',
            provider_name='MTN Senegal',
            country_code='SN',
            is_active=True,
            min_amount=Decimal('100.00'),
            max_amount=Decimal('1000000.00'),
            fee_percentage=Decimal('1.50'),
            supported_currencies=['XOF']
        )
        
        self.transaction = Transaction.objects.create(
            user=self.user,
            transaction_type='deposit',
            amount=Decimal('50000.00'),
            currency='XOF',
            status='pending'
        )
    
    def test_feexpay_transaction_creation(self):
        """Tester création de transaction FeexPay."""
        feexpay_tx = FeexPayTransaction.objects.create(
            user=self.user,
            transaction=self.transaction,
            provider=self.provider,
            internal_transaction_id=self.transaction.transaction_id,
            amount=Decimal('50000.00'),
            currency='XOF',
            fee_amount=Decimal('750.00'),
            gross_amount=Decimal('50750.00')
        )
        
        assert feexpay_tx.user == self.user
        assert feexpay_tx.provider == self.provider
        assert feexpay_tx.status == 'pending'
        assert feexpay_tx.amount == Decimal('50000.00')
    
    def test_feexpay_transaction_mark_successful(self):
        """Tester marquer transaction comme réussie."""
        feexpay_tx = FeexPayTransaction.objects.create(
            user=self.user,
            transaction=self.transaction,
            provider=self.provider,
            internal_transaction_id=self.transaction.transaction_id,
            amount=Decimal('50000.00'),
            currency='XOF',
            fee_amount=Decimal('750.00'),
            gross_amount=Decimal('50750.00')
        )
        
        feexpay_tx.mark_as_successful('tx_12345', 'successful')
        
        assert feexpay_tx.status == 'successful'
        assert feexpay_tx.feexpay_transaction_id == 'tx_12345'
        assert feexpay_tx.completed_at is not None
    
    def test_feexpay_transaction_mark_failed(self):
        """Tester marquer transaction comme échouée."""
        feexpay_tx = FeexPayTransaction.objects.create(
            user=self.user,
            transaction=self.transaction,
            provider=self.provider,
            internal_transaction_id=self.transaction.transaction_id,
            amount=Decimal('50000.00'),
            currency='XOF'
        )
        
        feexpay_tx.mark_as_failed('INSUFFICIENT_FUNDS', 'Fonds insuffisants')
        
        assert feexpay_tx.status == 'failed'
        assert feexpay_tx.error_code == 'INSUFFICIENT_FUNDS'
        assert feexpay_tx.error_message == 'Fonds insuffisants'
    
    def test_feexpay_transaction_can_retry(self):
        """Tester vérifier si peut être relancé."""
        feexpay_tx = FeexPayTransaction.objects.create(
            user=self.user,
            transaction=self.transaction,
            provider=self.provider,
            internal_transaction_id=self.transaction.transaction_id,
            amount=Decimal('50000.00'),
            currency='XOF',
            status='failed',
            retry_count=0
        )
        
        assert feexpay_tx.can_retry() is True
        
        # Après 3 tentatives
        feexpay_tx.retry_count = 3
        assert feexpay_tx.can_retry() is False
    
    def test_feexpay_transaction_retry(self):
        """Tester relancer une transaction."""
        feexpay_tx = FeexPayTransaction.objects.create(
            user=self.user,
            transaction=self.transaction,
            provider=self.provider,
            internal_transaction_id=self.transaction.transaction_id,
            amount=Decimal('50000.00'),
            currency='XOF',
            status='failed',
            retry_count=1
        )
        
        feexpay_tx.retry()
        
        assert feexpay_tx.status == 'pending'
        assert feexpay_tx.retry_count == 2


# ============= TESTS API =============

class TestFeexPayAPI(APITestCase):
    """Tests des endpoints API FeexPay."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_verified=True
        )
        
        self.provider = FeexPayProvider.objects.create(
            provider_code='mtn',
            provider_name='MTN Senegal',
            country_code='SN',
            is_active=True,
            min_amount=Decimal('100.00'),
            max_amount=Decimal('1000000.00'),
            fee_percentage=Decimal('1.50'),
            supported_currencies=['XOF', 'EUR', 'USD']
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_feexpay_health_check_success(self):
        """Tester endpoint health check."""
        with patch('apps.payments.feexpay_views.FeexPayClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.health_check.return_value = True
            
            response = self.client.get('/api/v1/payments/feexpay/health/')
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'healthy'
    
    def test_feexpay_providers_list(self):
        """Tester listing des providers."""
        response = self.client.get('/api/v1/payments/feexpay/providers/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_feexpay_initiate_payment_success(self):
        """Tester initiation de paiement."""
        with patch('requests.Session.get') as mock_session_get, patch('requests.Session.post') as mock_session_post:
            # Mock la réponse GET pour get_providers
            get_response = Mock()
            get_response.status_code = 200
            get_response.json.return_value = {
                'providers': [{
                    'code': 'mtn',
                    'name': 'MTN',
                    'min_amount': 100,
                    'max_amount': 1000000
                }]
            }
            mock_session_get.return_value = get_response
            
            # Mock la réponse POST pour initiate_payment
            post_response = Mock()
            post_response.status_code = 200
            post_response.json.return_value = {
                'transaction_id': 'tx_12345',
                'reference': 'ref_12345',
                'status': 'pending'
            }
            mock_session_post.return_value = post_response
            
            payload = {
                'provider_code': 'mtn',
                'amount': '50000',
                'currency': 'XOF',
                'recipient_phone': '+221771234567'
            }
            
            response = self.client.post(
                '/api/v1/payments/feexpay/initiate/',
                data=payload,
                format='json'
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['status'] == 'processing'
    
    def test_feexpay_transaction_status(self):
        """Tester vérifier statut transaction."""
        with patch('requests.Session.get') as mock_session_get:
            # Mock la réponse GET pour get_payment_status
            status_response = Mock()
            status_response.status_code = 200
            status_response.json.return_value = {
                'transaction_id': 'tx_12345',
                'status': 'processing',
                'amount': 50000,
                'currency': 'XOF'
            }
            mock_session_get.return_value = status_response
            
            transaction = Transaction.objects.create(
                user=self.user,
                transaction_type='deposit',
                amount=Decimal('50000.00'),
                currency='XOF'
            )
            
            feexpay_tx = FeexPayTransaction.objects.create(
                user=self.user,
                transaction=transaction,
                provider=self.provider,
                internal_transaction_id=transaction.transaction_id,
                amount=Decimal('50000.00'),
                currency='XOF',
                status='processing',
                feexpay_transaction_id='tx_12345'
            )
            
            response = self.client.get(
                f'/api/v1/payments/feexpay/{transaction.transaction_id}/status/'
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'processing'
    
    def test_feexpay_transaction_history(self):
        """Tester historique transactions utilisateur."""
        transaction = Transaction.objects.create(
            user=self.user,
            transaction_type='deposit',
            amount=Decimal('50000.00'),
            currency='XOF'
        )
        
        FeexPayTransaction.objects.create(
            user=self.user,
            transaction=transaction,
            provider=self.provider,
            internal_transaction_id=transaction.transaction_id,
            amount=Decimal('50000.00'),
            currency='XOF'
        )
        
        response = self.client.get('/api/v1/payments/feexpay/history/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_feexpay_webhook_valid(self):
        """Tester webhook valide."""
        import hmac
        import hashlib
        import json
        
        transaction = Transaction.objects.create(
            user=self.user,
            transaction_type='deposit',
            amount=Decimal('50000.00'),
            currency='XOF'
        )
        
        feexpay_tx = FeexPayTransaction.objects.create(
            user=self.user,
            transaction=transaction,
            provider=self.provider,
            internal_transaction_id=transaction.transaction_id,
            feexpay_transaction_id='tx_12345',
            amount=Decimal('50000.00'),
            currency='XOF'
        )
        
        payload = {
            'webhook_id': 'wh_12345',
            'event': 'payment.success',
            'transaction_id': 'tx_12345',
            'status': 'successful',
            'timestamp': timezone.now().isoformat(),
            'amount': '50000',
            'currency': 'XOF'
        }
        
        payload_json = json.dumps(payload)
        signature = hmac.new(
            'webhook_secret'.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        with patch('apps.payments.feexpay_views.FeexPayClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.validate_webhook_signature.return_value = True
            mock_instance.parse_webhook_payload.return_value = {
                'event': 'payment.success',
                'transaction_id': 'tx_12345',
                'status': 'successful',
                'timestamp': timezone.now(),
                'amount': Decimal('50000'),
                'currency': 'XOF'
            }
            
            response = self.client.post(
                '/api/v1/payments/feexpay/webhook/',
                data=payload_json,
                content_type='application/json',
                HTTP_X_WEBHOOK_SIGNATURE=signature
            )
            
            assert response.status_code in [200, 201]


# ============= TESTS D'INTÉGRATION =============

class TestFeexPayIntegration(APITestCase):
    """Tests d'intégration complets du flux de paiement FeexPay."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_verified=True
        )
        
        # Créer plusieurs providers
        self.providers_data = [
            {'code': 'mtn', 'name': 'MTN Senegal', 'country': 'SN'},
            {'code': 'orange', 'name': 'Orange Senegal', 'country': 'SN'},
            {'code': 'wave', 'name': 'Wave Senegal', 'country': 'SN'},
        ]
        
        for data in self.providers_data:
            FeexPayProvider.objects.create(
                provider_code=data['code'],
                provider_name=data['name'],
                country_code=data['country'],
                is_active=True,
                min_amount=Decimal('100.00'),
                max_amount=Decimal('1000000.00'),
                fee_percentage=Decimal('1.50'),
                supported_currencies=['XOF', 'EUR', 'USD']
            )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_full_payment_flow(self):
        """Tester flux complet: initiate → status check → webhook."""
        # 1. Initier paiement
        with patch('apps.payments.feexpay_views.FeexPayClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.initiate_payment.return_value = {
                'transaction_id': 'tx_12345',
                'reference': 'ref_12345',
                'status': 'pending'
            }
            
            payload = {
                'provider_code': 'mtn',
                'amount': '50000',
                'currency': 'XOF',
                'recipient_phone': '+221771234567'
            }
            
            response = self.client.post(
                '/api/v1/payments/feexpay/initiate/',
                data=payload,
                format='json'
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            tx_id = response.data['internal_transaction_id']
            
            # 2. Vérifier statut
            response = self.client.get(
                f'/api/v1/payments/feexpay/{tx_id}/status/'
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'processing'
            
            # 3. Simuler webhook de succès
            import hmac
            import hashlib
            import json
            
            webhook_payload = {
                'webhook_id': 'wh_12345',
                'event': 'payment.success',
                'transaction_id': 'tx_12345',
                'status': 'successful',
                'timestamp': timezone.now().isoformat(),
                'amount': '50000',
                'currency': 'XOF'
            }
            
            payload_json = json.dumps(webhook_payload)
            signature = hmac.new(
                'webhook_secret'.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            with patch('apps.payments.feexpay_views.FeexPayClient') as mock_client2:
                mock_instance2 = mock_client2.return_value
                mock_instance2.validate_webhook_signature.return_value = True
                mock_instance2.parse_webhook_payload.return_value = {
                    'event': 'payment.success',
                    'transaction_id': 'tx_12345',
                    'status': 'successful',
                    'timestamp': timezone.now(),
                    'amount': Decimal('50000'),
                    'currency': 'XOF'
                }
                
                response = self.client.post(
                    '/api/v1/payments/feexpay/webhook/',
                    data=payload_json,
                    content_type='application/json',
                    HTTP_X_WEBHOOK_SIGNATURE=signature
                )
                
                assert response.status_code in [200, 201]
