# apps/payments/processors/mobile_money.py
# ==========================================

import requests
import hashlib
import hmac
from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from . import (
    BasePaymentProcessor, PaymentProcessorError,
    PaymentProcessorConfigurationError, PaymentProcessingError,
    PaymentResponse, WebhookResponse, handle_processor_errors
)


class MobileMoneyProcessor(BasePaymentProcessor):
    """Processeur de paiement Mobile Money pour Orange Money, MTN Money, Moov Money."""
    
    # Configuration des opérateurs
    OPERATORS = {
        'orange': {
            'name': 'Orange Money',
            'api_base': 'https://api.orange.com/orange-money-webpay/dev/v1',
            'currency': 'XOF',  # FCFA
            'country_codes': ['CI', 'SN', 'ML', 'BF', 'NE', 'GN']
        },
        'mtn': {
            'name': 'MTN Mobile Money',
            'api_base': 'https://sandbox.momodeveloper.mtn.com',
            'currency': 'XOF',
            'country_codes': ['CI', 'GH', 'UG', 'ZM', 'CM']
        },
        'moov': {
            'name': 'Moov Money',
            'api_base': 'https://api.moovmoney.ci/v1',
            'currency': 'XOF',
            'country_codes': ['CI', 'BF', 'TG', 'BJ']
        }
    }
    
    def __init__(self):
        """Initialiser le processeur Mobile Money."""
        super().__init__()
        
        # Configuration depuis les settings
        self.orange_config = getattr(settings, 'ORANGE_MONEY_CONFIG', {})
        self.mtn_config = getattr(settings, 'MTN_MOMO_CONFIG', {})
        self.moov_config = getattr(settings, 'MOOV_MONEY_CONFIG', {})
    
    def validate_configuration(self):
        """Valider la configuration Mobile Money."""
        # Vérifier qu'au moins un opérateur est configuré
        configs = [self.orange_config, self.mtn_config, self.moov_config]
        if not any(configs):
            raise PaymentProcessorConfigurationError(
                "Aucune configuration Mobile Money trouvée"
            )
        
        # Valider chaque configuration active
        for operator, config in [
            ('orange', self.orange_config),
            ('mtn', self.mtn_config),
            ('moov', self.moov_config)
        ]:
            if config:
                self._validate_operator_config(operator, config)
    
    def _validate_operator_config(self, operator, config):
        """Valider la configuration d'un opérateur."""
        required_fields = {
            'orange': ['client_id', 'client_secret', 'merchant_key'],
            'mtn': ['user_id', 'api_key', 'subscription_key'],
            'moov': ['merchant_id', 'api_key', 'secret_key']
        }
        
        for field in required_fields.get(operator, []):
            if not config.get(field):
                raise PaymentProcessorConfigurationError(
                    f"Configuration {operator} manquante: {field}"
                )
    
    @handle_processor_errors
    def create_payment(self, payment_data):
        """Créer une demande de paiement Mobile Money."""
        operator = self._detect_operator(payment_data.get('phone_number', ''))
        
        if operator == 'orange':
            return self._create_orange_payment(payment_data)
        elif operator == 'mtn':
            return self._create_mtn_payment(payment_data)
        elif operator == 'moov':
            return self._create_moov_payment(payment_data)
        else:
            raise PaymentProcessingError("Opérateur Mobile Money non supporté")
    
    def _detect_operator(self, phone_number):
        """Détecter l'opérateur depuis le numéro de téléphone."""
        if not phone_number:
            return None
        
        # Nettoyer le numéro
        phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        
        # Préfixes pour la Côte d'Ivoire (exemple)
        orange_prefixes = ['07', '08', '09', '22507', '22508', '22509']
        mtn_prefixes = ['05', '06', '22505', '22506']
        moov_prefixes = ['01', '02', '03', '22501', '22502', '22503']
        
        for prefix in orange_prefixes:
            if phone.startswith(prefix) or phone.endswith(prefix):
                return 'orange'
        
        for prefix in mtn_prefixes:
            if phone.startswith(prefix) or phone.endswith(prefix):
                return 'mtn'
        
        for prefix in moov_prefixes:
            if phone.startswith(prefix) or phone.endswith(prefix):
                return 'moov'
        
        # Par défaut, essayer Orange
        return 'orange'
    
    def _create_orange_payment(self, payment_data):
        """Créer un paiement Orange Money."""
        if not self.orange_config:
            raise PaymentProcessorConfigurationError("Orange Money non configuré")
        
        # Obtenir le token d'accès
        access_token = self._get_orange_access_token()
        
        # Préparer les données de paiement
        payment_payload = {
            'merchant_key': self.orange_config['merchant_key'],
            'currency': 'OUV',  # Orange Unit Value
            'order_id': payment_data['transaction_id'],
            'amount': int(payment_data['amount']),
            'return_url': payment_data.get('return_url', ''),
            'cancel_url': payment_data.get('cancel_url', ''),
            'notif_url': f"{settings.BACKEND_URL}/api/payments/webhooks/orange/",
            'lang': 'fr',
            'reference': payment_data['transaction_id']
        }
        
        # Effectuer la requête
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.OPERATORS['orange']['api_base']}/webpayment",
                json=payment_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return PaymentResponse.success_response(
                    "Paiement Orange Money créé",
                    {
                        'payment_token': data.get('payment_token'),
                        'payment_url': data.get('payment_url'),
                        'external_reference': data.get('payment_token'),
                        'status': 'pending',
                        'expires_at': timezone.now() + timezone.timedelta(minutes=15)
                    }
                ).to_dict()
            else:
                error_msg = response.json().get('message', 'Erreur Orange Money')
                raise PaymentProcessingError(f"Orange Money: {error_msg}")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Orange Money: {str(e)}")
    
    def _get_orange_access_token(self):
        """Obtenir un token d'accès Orange Money."""
        auth_url = f"{self.OPERATORS['orange']['api_base']}/oauth/token"
        
        auth_data = {
            'grant_type': 'client_credentials'
        }
        
        auth_headers = {
            'Authorization': f"Basic {self._get_orange_basic_auth()}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                auth_url,
                data=auth_data,
                headers=auth_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                raise PaymentProcessorConfigurationError("Échec authentification Orange")
                
        except requests.RequestException as e:
            raise PaymentProcessorConfigurationError(f"Erreur auth Orange: {str(e)}")
    
    def _get_orange_basic_auth(self):
        """Générer l'authentification Basic pour Orange."""
        import base64
        
        client_id = self.orange_config['client_id']
        client_secret = self.orange_config['client_secret']
        
        credentials = f"{client_id}:{client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def _create_mtn_payment(self, payment_data):
        """Créer un paiement MTN Mobile Money."""
        if not self.mtn_config:
            raise PaymentProcessorConfigurationError("MTN Mobile Money non configuré")
        
        # MTN utilise un système différent avec requestToPay
        payment_payload = {
            'amount': str(int(payment_data['amount'])),
            'currency': 'XOF',
            'externalId': payment_data['transaction_id'],
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': payment_data.get('phone_number', '')
            },
            'payerMessage': f"Paiement RUMO RUSH - {payment_data['transaction_id']}",
            'payeeNote': f"Transaction {payment_data['transaction_id']}"
        }
        
        headers = {
            'Authorization': f"Bearer {self._get_mtn_access_token()}",
            'X-Reference-Id': payment_data['transaction_id'],
            'X-Target-Environment': getattr(settings, 'MTN_ENVIRONMENT', 'sandbox'),
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.mtn_config['subscription_key']
        }
        
        try:
            response = requests.post(
                f"{self.OPERATORS['mtn']['api_base']}/collection/v1_0/requesttopay",
                json=payment_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 202:
                return PaymentResponse.success_response(
                    "Paiement MTN Mobile Money créé",
                    {
                        'payment_id': payment_data['transaction_id'],
                        'external_reference': payment_data['transaction_id'],
                        'status': 'pending',
                        'message': 'Vérifiez votre téléphone pour confirmer le paiement'
                    }
                ).to_dict()
            else:
                error_msg = response.json().get('message', 'Erreur MTN')
                raise PaymentProcessingError(f"MTN: {error_msg}")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau MTN: {str(e)}")
    
    def _get_mtn_access_token(self):
        """Obtenir un token d'accès MTN."""
        # Logique d'authentification MTN
        # (simplifiée pour l'exemple)
        return "mtn_access_token_placeholder"
    
    def _create_moov_payment(self, payment_data):
        """Créer un paiement Moov Money."""
        if not self.moov_config:
            raise PaymentProcessorConfigurationError("Moov Money non configuré")
        
        # Signature pour Moov Money
        signature = self._generate_moov_signature(payment_data)
        
        payment_payload = {
            'merchant_id': self.moov_config['merchant_id'],
            'amount': int(payment_data['amount']),
            'currency': 'XOF',
            'transaction_id': payment_data['transaction_id'],
            'phone_number': payment_data.get('phone_number', ''),
            'callback_url': f"{settings.BACKEND_URL}/api/payments/webhooks/moov/",
            'signature': signature
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.moov_config['api_key']}"
        }
        
        try:
            response = requests.post(
                f"{self.OPERATORS['moov']['api_base']}/payments/request",
                json=payment_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse.success_response(
                    "Paiement Moov Money créé",
                    {
                        'payment_id': data.get('payment_id'),
                        'external_reference': data.get('payment_id'),
                        'status': 'pending',
                        'message': 'Composez le code USSD affiché sur votre téléphone'
                    }
                ).to_dict()
            else:
                error_msg = response.json().get('message', 'Erreur Moov')
                raise PaymentProcessingError(f"Moov: {error_msg}")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Moov: {str(e)}")
    
    def _generate_moov_signature(self, payment_data):
        """Générer une signature pour Moov Money."""
        # Données à signer
        data_to_sign = (
            f"{self.moov_config['merchant_id']}"
            f"{payment_data['amount']}"
            f"{payment_data['transaction_id']}"
            f"{self.moov_config['secret_key']}"
        )
        
        # Générer le hash SHA256
        return hashlib.sha256(data_to_sign.encode()).hexdigest()
    
    @handle_processor_errors
    def verify_payment(self, payment_reference):
        """Vérifier le statut d'un paiement Mobile Money."""
        # Déterminer l'opérateur depuis la référence ou les métadonnées
        operator = self._get_operator_from_reference(payment_reference)
        
        if operator == 'orange':
            return self._verify_orange_payment(payment_reference)
        elif operator == 'mtn':
            return self._verify_mtn_payment(payment_reference)
        elif operator == 'moov':
            return self._verify_moov_payment(payment_reference)
        else:
            raise PaymentProcessingError("Impossible de vérifier le paiement")
    
    def _verify_orange_payment(self, payment_token):
        """Vérifier un paiement Orange Money."""
        access_token = self._get_orange_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.OPERATORS['orange']['api_base']}/webpayment/{payment_token}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse.success_response(
                    "Statut Orange Money récupéré",
                    {
                        'payment_reference': payment_token,
                        'status': data.get('status', 'unknown'),
                        'amount': data.get('amount', 0),
                        'currency': 'XOF'
                    }
                ).to_dict()
            else:
                raise PaymentProcessingError("Erreur vérification Orange Money")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Orange: {str(e)}")
    
    def _verify_mtn_payment(self, reference_id):
        """Vérifier un paiement MTN."""
        headers = {
            'Authorization': f"Bearer {self._get_mtn_access_token()}",
            'X-Target-Environment': getattr(settings, 'MTN_ENVIRONMENT', 'sandbox'),
            'Ocp-Apim-Subscription-Key': self.mtn_config['subscription_key']
        }
        
        try:
            response = requests.get(
                f"{self.OPERATORS['mtn']['api_base']}/collection/v1_0/requesttopay/{reference_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse.success_response(
                    "Statut MTN récupéré",
                    {
                        'payment_reference': reference_id,
                        'status': data.get('status', 'PENDING').lower(),
                        'amount': data.get('amount', 0),
                        'currency': data.get('currency', 'XOF')
                    }
                ).to_dict()
            else:
                raise PaymentProcessingError("Erreur vérification MTN")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau MTN: {str(e)}")
    
    def _verify_moov_payment(self, payment_id):
        """Vérifier un paiement Moov Money."""
        headers = {
            'Authorization': f"Bearer {self.moov_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.OPERATORS['moov']['api_base']}/payments/status/{payment_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse.success_response(
                    "Statut Moov récupéré",
                    {
                        'payment_reference': payment_id,
                        'status': data.get('status', 'pending'),
                        'amount': data.get('amount', 0),
                        'currency': 'XOF'
                    }
                ).to_dict()
            else:
                raise PaymentProcessingError("Erreur vérification Moov")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Moov: {str(e)}")
    
    def _get_operator_from_reference(self, reference):
        """Déterminer l'opérateur depuis une référence."""
        # Logique pour déterminer l'opérateur
        # (peut être basée sur le format de la référence)
        if reference.startswith('orange_'):
            return 'orange'
        elif reference.startswith('mtn_'):
            return 'mtn'
        elif reference.startswith('moov_'):
            return 'moov'
        
        # Par défaut, essayer de deviner ou retourner une erreur
        return 'orange'
    
    @handle_processor_errors
    def create_withdrawal(self, withdrawal_data):
        """Créer un retrait Mobile Money."""
        operator = self._detect_operator(withdrawal_data.get('phone_number', ''))
        
        if operator == 'orange':
            return self._create_orange_withdrawal(withdrawal_data)
        elif operator == 'mtn':
            return self._create_mtn_withdrawal(withdrawal_data)
        elif operator == 'moov':
            return self._create_moov_withdrawal(withdrawal_data)
        else:
            raise PaymentProcessingError("Opérateur non supporté pour les retraits")
    
    def _create_orange_withdrawal(self, withdrawal_data):
        """Créer un retrait Orange Money."""
        # Orange Money Transfer API
        access_token = self._get_orange_access_token()
        
        transfer_payload = {
            'partner_id': self.orange_config.get('partner_id'),
            'transfer_type': 'cash_out',
            'amount': int(withdrawal_data['amount']),
            'currency': 'XOF',
            'recipient_phone': withdrawal_data['phone_number'],
            'reference': withdrawal_data['transaction_id'],
            'description': f"Retrait RUMO RUSH - {withdrawal_data['transaction_id']}"
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.OPERATORS['orange']['api_base']}/transfer",
                json=transfer_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return PaymentResponse.success_response(
                    "Retrait Orange Money créé",
                    {
                        'transfer_id': data.get('transfer_id'),
                        'status': 'processing',
                        'estimated_completion': '5-15 minutes'
                    }
                ).to_dict()
            else:
                error_msg = response.json().get('message', 'Erreur retrait Orange')
                raise PaymentProcessingError(f"Orange retrait: {error_msg}")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Orange retrait: {str(e)}")
    
    def _create_mtn_withdrawal(self, withdrawal_data):
        """Créer un retrait MTN Mobile Money."""
        # MTN Disbursement API
        return PaymentResponse.success_response(
            "Retrait MTN en cours",
            {'status': 'processing', 'message': 'Retrait MTN non implémenté'}
        ).to_dict()
    
    def _create_moov_withdrawal(self, withdrawal_data):
        """Créer un retrait Moov Money."""
        # Moov Money withdrawal API
        return PaymentResponse.success_response(
            "Retrait Moov en cours",
            {'status': 'processing', 'message': 'Retrait Moov non implémenté'}
        ).to_dict()
    
    @handle_processor_errors
    def process_webhook(self, webhook_data):
        """Traiter un webhook Mobile Money."""
        provider = webhook_data.get('provider', '').lower()
        
        if provider == 'orange':
            return self._process_orange_webhook(webhook_data)
        elif provider == 'mtn':
            return self._process_mtn_webhook(webhook_data)
        elif provider == 'moov':
            return self._process_moov_webhook(webhook_data)
        else:
            raise PaymentProcessingError(f"Webhook provider inconnu: {provider}")
    
    def _process_orange_webhook(self, webhook_data):
        """Traiter un webhook Orange Money."""
        payload = webhook_data.get('payload', {})
        
        # Vérifier la signature si configurée
        if self.orange_config.get('webhook_secret'):
            if not self._verify_orange_signature(webhook_data):
                raise PaymentProcessingError("Signature Orange invalide")
        
        # Extraire les informations
        order_id = payload.get('order_id')
        status = payload.get('status', '').lower()
        payment_token = payload.get('payment_token')
        
        if not order_id:
            raise PaymentProcessingError("Order ID manquant dans webhook Orange")
        
        # Mettre à jour la transaction
        transaction_id = self._update_transaction_from_webhook(
            order_id, status, payment_token
        )
        
        return WebhookResponse(
            processed=True,
            transaction_id=transaction_id
        ).to_dict()
    
    def _process_mtn_webhook(self, webhook_data):
        """Traiter un webhook MTN."""
        # Logique similaire pour MTN
        return WebhookResponse(processed=True).to_dict()
    
    def _process_moov_webhook(self, webhook_data):
        """Traiter un webhook Moov."""
        # Logique similaire pour Moov
        return WebhookResponse(processed=True).to_dict()
    
    def _verify_orange_signature(self, webhook_data):
        """Vérifier la signature Orange Money."""
        # Logique de vérification de signature
        return True  # Placeholder
    
    def _update_transaction_from_webhook(self, order_id, status, reference):
        """Mettre à jour une transaction depuis un webhook."""
        from ..models import Transaction
        
        try:
            transaction = Transaction.objects.get(
                transaction_id=order_id,
                status__in=['pending', 'processing']
            )
            
            # Mapper les statuts
            status_mapping = {
                'success': 'completed',
                'successful': 'completed',
                'failed': 'failed',
                'cancelled': 'cancelled',
                'expired': 'expired'
            }
            
            new_status = status_mapping.get(status, 'failed')
            
            if new_status == 'completed':
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.external_reference = reference
                transaction.save()
                
                # Traiter la transaction (créditer le compte)
                transaction._process_deposit()
                
            elif new_status in ['failed', 'cancelled', 'expired']:
                transaction.status = new_status
                transaction.failure_reason = f"Mobile Money: {status}"
                transaction.processed_at = timezone.now()
                transaction.save()
            
            return str(transaction.id)
            
        except Transaction.DoesNotExist:
            raise PaymentProcessingError(f"Transaction introuvable: {order_id}")
    
    def get_supported_currencies(self):
        """Devises supportées par Mobile Money."""
        return ['XOF']  # FCFA (Franc CFA Ouest Africain)
    
    def calculate_fees(self, amount, currency, transaction_type='deposit'):
        """Calculer les frais Mobile Money."""
        # Frais généralement appliqués par les opérateurs
        if transaction_type == 'deposit':
            # Frais de dépôt (variables selon le montant)
            if amount <= 5000:
                fee = Decimal('0')  # Gratuit
            elif amount <= 50000:
                fee = Decimal('100')  # 100 FCFA
            else:
                fee = amount * Decimal('0.01')  # 1%
        else:
            # Frais de retrait
            if amount <= 10000:
                fee = Decimal('200')  # 200 FCFA
            else:
                fee = amount * Decimal('0.015')  # 1.5%
        
        return {
            'processing_fee': fee,
            'service_fee': Decimal('0'),
            'total_fees': fee,
            'net_amount': amount - fee if transaction_type == 'withdrawal' else amount,
            'breakdown': {
                'operator_fee': fee,
                'description': f'Frais opérateur Mobile Money ({transaction_type})'
            }
        }
