# apps/payments/processors/crypto_processor.py
# =============================================

import requests
import hashlib
from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from . import (
    BasePaymentProcessor, PaymentProcessorError,
    PaymentProcessorConfigurationError, PaymentProcessingError,
    PaymentResponse, WebhookResponse, handle_processor_errors
)


class CryptoProcessor(BasePaymentProcessor):
    """Processeur de paiement crypto (Bitcoin, Ethereum, etc.)."""
    
    # Configuration des cryptomonnaies supportées
    SUPPORTED_CRYPTOS = {
        'BTC': {
            'name': 'Bitcoin',
            'decimals': 8,
            'min_confirmations': 1,
            'network': 'mainnet'
        },
        'ETH': {
            'name': 'Ethereum',
            'decimals': 18,
            'min_confirmations': 12,
            'network': 'mainnet'
        },
        'USDT': {
            'name': 'Tether USD',
            'decimals': 6,
            'min_confirmations': 12,
            'network': 'ethereum'
        },
        'USDC': {
            'name': 'USD Coin',
            'decimals': 6,
            'min_confirmations': 12,
            'network': 'ethereum'
        }
    }
    
    def __init__(self):
        """Initialiser le processeur crypto."""
        super().__init__()
        
        # Configuration depuis les settings
        self.coinbase_config = getattr(settings, 'COINBASE_CONFIG', {})
        self.blockchain_config = getattr(settings, 'BLOCKCHAIN_INFO_CONFIG', {})
        self.nowpayments_config = getattr(settings, 'NOWPAYMENTS_CONFIG', {})
        
        # Choisir le fournisseur principal
        self.primary_provider = getattr(settings, 'CRYPTO_PRIMARY_PROVIDER', 'nowpayments')
    
    def validate_configuration(self):
        """Valider la configuration crypto."""
        if self.primary_provider == 'coinbase' and not self.coinbase_config:
            raise PaymentProcessorConfigurationError(
                "Configuration Coinbase manquante"
            )
        elif self.primary_provider == 'nowpayments' and not self.nowpayments_config:
            raise PaymentProcessorConfigurationError(
                "Configuration NOWPayments manquante"
            )
        
        # Tester la connexion API
        try:
            self._test_api_connection()
        except Exception as e:
            raise PaymentProcessorConfigurationError(
                f"Erreur connexion API crypto: {str(e)}"
            )
    
    def _test_api_connection(self):
        """Tester la connexion à l'API crypto."""
        if self.primary_provider == 'nowpayments':
            response = requests.get(
                'https://api.nowpayments.io/v1/status',
                headers={'x-api-key': self.nowpayments_config.get('api_key', '')},
                timeout=10
            )
            if response.status_code != 200:
                raise Exception("Connexion NOWPayments échouée")
    
    @handle_processor_errors
    def create_payment(self, payment_data):
        """Créer un paiement crypto."""
        crypto_currency = payment_data.get('crypto_currency', 'BTC')
        
        if crypto_currency not in self.SUPPORTED_CRYPTOS:
            raise PaymentProcessingError(f"Cryptomonnaie non supportée: {crypto_currency}")
        
        if self.primary_provider == 'nowpayments':
            return self._create_nowpayments_payment(payment_data)
        elif self.primary_provider == 'coinbase':
            return self._create_coinbase_payment(payment_data)
        else:
            raise PaymentProcessorConfigurationError("Fournisseur crypto non supporté")
    
    def _create_nowpayments_payment(self, payment_data):
        """Créer un paiement via NOWPayments."""
    def _create_nowpayments_payment(self, payment_data):
        """Créer un paiement via NOWPayments."""
        if not self.nowpayments_config.get('api_key'):
            raise PaymentProcessorConfigurationError("Clé API NOWPayments manquante")
        
        # Convertir le montant FCFA en crypto si nécessaire
        crypto_currency = payment_data.get('crypto_currency', 'BTC')
        fiat_amount = payment_data['amount']
        
        # Obtenir le taux de change
        crypto_amount = self._convert_fiat_to_crypto(fiat_amount, 'XOF', crypto_currency)
        
        payment_payload = {
            'price_amount': float(fiat_amount),
            'price_currency': 'usd',  # NOWPayments utilise USD comme base
            'pay_currency': crypto_currency.lower(),
            'order_id': payment_data['transaction_id'],
            'order_description': f'RUMO RUSH Payment - {payment_data["transaction_id"]}',
            'ipn_callback_url': f"{settings.BACKEND_URL}/api/payments/webhooks/nowpayments/",
            'success_url': payment_data.get('return_url', ''),
            'cancel_url': payment_data.get('cancel_url', '')
        }
        
        headers = {
            'x-api-key': self.nowpayments_config['api_key'],
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://api.nowpayments.io/v1/payment',
                json=payment_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return PaymentResponse.success_response(
                    "Paiement crypto créé via NOWPayments",
                    {
                        'payment_id': data.get('payment_id'),
                        'payment_url': data.get('invoice_url'),
                        'crypto_amount': data.get('pay_amount'),
                        'crypto_currency': crypto_currency,
                        'payment_address': data.get('pay_address'),
                        'external_reference': data.get('payment_id'),
                        'status': 'pending',
                        'expires_at': timezone.now() + timezone.timedelta(hours=1)
                    }
                ).to_dict()
            else:
                error_msg = response.json().get('message', 'Erreur NOWPayments')
                raise PaymentProcessingError(f"NOWPayments: {error_msg}")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau NOWPayments: {str(e)}")
    
    def _create_coinbase_payment(self, payment_data):
        """Créer un paiement via Coinbase Commerce."""
        if not self.coinbase_config.get('api_key'):
            raise PaymentProcessorConfigurationError("Clé API Coinbase manquante")
        
        payment_payload = {
            'name': f'RUMO RUSH Payment',
            'description': f'Transaction {payment_data["transaction_id"]}',
            'local_price': {
                'amount': str(payment_data['amount']),
                'currency': 'USD'  # Coinbase utilise USD comme base
            },
            'pricing_type': 'fixed_price',
            'metadata': {
                'transaction_id': payment_data['transaction_id'],
                'user_email': payment_data.get('user_email', '')
            },
            'redirect_url': payment_data.get('return_url', ''),
            'cancel_url': payment_data.get('cancel_url', '')
        }
        
        headers = {
            'Authorization': f'Bearer {self.coinbase_config["api_key"]}',
            'Content-Type': 'application/json',
            'X-CC-Api-Version': '2018-03-22'
        }
        
        try:
            response = requests.post(
                'https://api.commerce.coinbase.com/charges',
                json=payment_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()['data']
                return PaymentResponse.success_response(
                    "Paiement crypto créé via Coinbase",
                    {
                        'charge_id': data.get('id'),
                        'payment_url': data.get('hosted_url'),
                        'external_reference': data.get('id'),
                        'status': 'pending',
                        'expires_at': data.get('expires_at')
                    }
                ).to_dict()
            else:
                error_msg = response.json().get('error', {}).get('message', 'Erreur Coinbase')
                raise PaymentProcessingError(f"Coinbase: {error_msg}")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Coinbase: {str(e)}")
    
    def _convert_fiat_to_crypto(self, fiat_amount, fiat_currency, crypto_currency):
        """Convertir un montant fiat en crypto."""
        try:
            # Utiliser l'API CoinGecko pour les taux de change
            response = requests.get(
                f'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': self._get_coingecko_id(crypto_currency),
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'false'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                crypto_id = self._get_coingecko_id(crypto_currency)
                usd_price = data[crypto_id]['usd']
                
                # Convertir FCFA en USD puis en crypto
                fiat_to_usd = fiat_amount / 560  # Taux approximatif FCFA/USD
                crypto_amount = fiat_to_usd / usd_price
                
                return Decimal(str(crypto_amount)).quantize(
                    Decimal('0.' + '0' * self.SUPPORTED_CRYPTOS[crypto_currency]['decimals'])
                )
            else:
                raise PaymentProcessingError("Impossible d'obtenir le taux de change crypto")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur API taux de change: {str(e)}")
    
    def _get_coingecko_id(self, crypto_currency):
        """Obtenir l'ID CoinGecko pour une crypto."""
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'USDC': 'usd-coin'
        }
        return mapping.get(crypto_currency, crypto_currency.lower())
    
    @handle_processor_errors
    def verify_payment(self, payment_reference):
        """Vérifier le statut d'un paiement crypto."""
        if self.primary_provider == 'nowpayments':
            return self._verify_nowpayments_payment(payment_reference)
        elif self.primary_provider == 'coinbase':
            return self._verify_coinbase_payment(payment_reference)
        else:
            raise PaymentProcessingError("Fournisseur non supporté")
    
    def _verify_nowpayments_payment(self, payment_id):
        """Vérifier un paiement NOWPayments."""
        headers = {
            'x-api-key': self.nowpayments_config['api_key']
        }
        
        try:
            response = requests.get(
                f'https://api.nowpayments.io/v1/payment/{payment_id}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse.success_response(
                    "Statut NOWPayments récupéré",
                    {
                        'payment_reference': payment_id,
                        'status': data.get('payment_status', 'waiting'),
                        'amount': data.get('price_amount', 0),
                        'currency': data.get('price_currency', '').upper(),
                        'crypto_amount': data.get('pay_amount', 0),
                        'crypto_currency': data.get('pay_currency', '').upper(),
                        'confirmations': data.get('network_confirmations', 0)
                    }
                ).to_dict()
            else:
                raise PaymentProcessingError("Erreur vérification NOWPayments")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau NOWPayments: {str(e)}")
    
    def _verify_coinbase_payment(self, charge_id):
        """Vérifier un paiement Coinbase."""
        headers = {
            'Authorization': f'Bearer {self.coinbase_config["api_key"]}',
            'X-CC-Api-Version': '2018-03-22'
        }
        
        try:
            response = requests.get(
                f'https://api.commerce.coinbase.com/charges/{charge_id}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                return PaymentResponse.success_response(
                    "Statut Coinbase récupéré",
                    {
                        'payment_reference': charge_id,
                        'status': data.get('status', 'NEW').lower(),
                        'amount': data.get('pricing', {}).get('local', {}).get('amount', 0),
                        'currency': data.get('pricing', {}).get('local', {}).get('currency', ''),
                        'confirmed_at': data.get('confirmed_at'),
                        'expires_at': data.get('expires_at')
                    }
                ).to_dict()
            else:
                raise PaymentProcessingError("Erreur vérification Coinbase")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur réseau Coinbase: {str(e)}")
    
    @handle_processor_errors
    def create_withdrawal(self, withdrawal_data):
        """Créer un retrait crypto."""
        crypto_currency = withdrawal_data.get('crypto_currency', 'BTC')
        wallet_address = withdrawal_data.get('wallet_address')
        
        if not wallet_address:
            raise PaymentProcessingError("Adresse de portefeuille requise")
        
        if not self._validate_crypto_address(wallet_address, crypto_currency):
            raise PaymentProcessingError("Adresse de portefeuille invalide")
        
        # Convertir le montant fiat en crypto
        crypto_amount = self._convert_fiat_to_crypto(
            withdrawal_data['amount'],
            'XOF',
            crypto_currency
        )
        
        return PaymentResponse.success_response(
            "Retrait crypto programmé",
            {
                'withdrawal_id': f"crypto_{withdrawal_data['transaction_id']}",
                'crypto_amount': float(crypto_amount),
                'crypto_currency': crypto_currency,
                'wallet_address': wallet_address,
                'status': 'processing',
                'estimated_completion': '10-60 minutes'
            }
        ).to_dict()
    
    def _validate_crypto_address(self, address, currency):
        """Valider une adresse crypto."""
        # Validation basique selon le format
        if currency == 'BTC':
            # Bitcoin: commence par 1, 3 ou bc1
            return (address.startswith(('1', '3', 'bc1')) and 
                    25 <= len(address) <= 62)
        elif currency == 'ETH':
            # Ethereum: commence par 0x et fait 42 caractères
            return (address.startswith('0x') and 
                    len(address) == 42)
        elif currency in ['USDT', 'USDC']:
            # Tokens ERC-20: même format qu'Ethereum
            return (address.startswith('0x') and 
                    len(address) == 42)
        
        return False
    
    @handle_processor_errors
    def process_webhook(self, webhook_data):
        """Traiter un webhook crypto."""
        provider = webhook_data.get('provider', '').lower()
        
        if provider == 'nowpayments':
            return self._process_nowpayments_webhook(webhook_data)
        elif provider == 'coinbase':
            return self._process_coinbase_webhook(webhook_data)
        else:
            raise PaymentProcessingError(f"Provider webhook inconnu: {provider}")
    
    def _process_nowpayments_webhook(self, webhook_data):
        """Traiter un webhook NOWPayments."""
        payload = webhook_data.get('payload', {})
        
        # Vérifier la signature HMAC si configurée
        if self.nowpayments_config.get('ipn_secret'):
            if not self._verify_nowpayments_signature(webhook_data):
                raise PaymentProcessingError("Signature NOWPayments invalide")
        
        payment_id = payload.get('payment_id')
        payment_status = payload.get('payment_status')
        order_id = payload.get('order_id')
        
        if not all([payment_id, payment_status, order_id]):
            raise PaymentProcessingError("Données webhook NOWPayments incomplètes")
        
        # Mettre à jour la transaction
        transaction_id = self._update_crypto_transaction(
            order_id, payment_status, payment_id
        )
        
        return WebhookResponse(
            processed=True,
            transaction_id=transaction_id
        ).to_dict()
    
    def _process_coinbase_webhook(self, webhook_data):
        """Traiter un webhook Coinbase."""
        payload = webhook_data.get('payload', {})
        
        # Vérifier la signature si configurée
        if self.coinbase_config.get('webhook_secret'):
            if not self._verify_coinbase_signature(webhook_data):
                raise PaymentProcessingError("Signature Coinbase invalide")
        
        event_type = payload.get('type')
        charge_data = payload.get('data', {})
        
        charge_id = charge_data.get('id')
        charge_status = charge_data.get('status', '').lower()
        order_id = charge_data.get('metadata', {}).get('transaction_id')
        
        if event_type == 'charge:confirmed' and charge_status == 'completed':
            transaction_id = self._update_crypto_transaction(
                order_id, 'confirmed', charge_id
            )
            
            return WebhookResponse(
                processed=True,
                transaction_id=transaction_id
            ).to_dict()
        elif event_type == 'charge:failed':
            transaction_id = self._update_crypto_transaction(
                order_id, 'failed', charge_id
            )
            
            return WebhookResponse(
                processed=True,
                transaction_id=transaction_id
            ).to_dict()
        
        return WebhookResponse(processed=False).to_dict()
    
    def _verify_nowpayments_signature(self, webhook_data):
        """Vérifier la signature HMAC NOWPayments."""
        import hmac
        import json
        
        signature = webhook_data.get('headers', {}).get('x-nowpayments-sig')
        payload = json.dumps(webhook_data.get('payload', {}), separators=(',', ':'))
        
        expected_signature = hmac.new(
            self.nowpayments_config['ipn_secret'].encode(),
            payload.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _verify_coinbase_signature(self, webhook_data):
        """Vérifier la signature HMAC Coinbase."""
        import hmac
        
        signature = webhook_data.get('headers', {}).get('x-cc-webhook-signature')
        payload = webhook_data.get('raw_payload', '')
        
        expected_signature = hmac.new(
            self.coinbase_config['webhook_secret'].encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _update_crypto_transaction(self, order_id, status, reference):
        """Mettre à jour une transaction crypto depuis un webhook."""
        from ..models import Transaction
        
        try:
            transaction = Transaction.objects.get(
                transaction_id=order_id,
                status__in=['pending', 'processing']
            )
            
            # Mapper les statuts crypto
            status_mapping = {
                'finished': 'completed',
                'confirmed': 'completed',
                'completed': 'completed',
                'partially_paid': 'processing',
                'confirming': 'processing',
                'sending': 'processing',
                'failed': 'failed',
                'refunded': 'refunded',
                'expired': 'expired'
            }
            
            new_status = status_mapping.get(status, status)
            
            if new_status == 'completed':
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.external_reference = reference
                transaction.save()
                
                # Traiter la transaction (créditer le compte)
                transaction._process_deposit()
                
            elif new_status in ['failed', 'expired', 'refunded']:
                transaction.status = new_status
                transaction.failure_reason = f"Crypto: {status}"
                transaction.processed_at = timezone.now()
                transaction.save()
            
            return str(transaction.id)
            
        except Transaction.DoesNotExist:
            raise PaymentProcessingError(f"Transaction crypto introuvable: {order_id}")
    
    def get_supported_currencies(self):
        """Obtenir les cryptomonnaies supportées."""
        return list(self.SUPPORTED_CRYPTOS.keys())
    
    def calculate_fees(self, amount, currency, transaction_type='deposit'):
        """Calculer les frais crypto."""
        crypto_currency = currency
        
        # Frais de réseau approximatifs (variables selon la congestion)
        network_fees = {
            'BTC': Decimal('0.0001'),  # ~5-50$ selon congestion
            'ETH': Decimal('0.005'),   # ~10-100$ selon congestion
            'USDT': Decimal('0.005'),  # Frais ETH pour ERC-20
            'USDC': Decimal('0.005')   # Frais ETH pour ERC-20
        }
        
        base_network_fee = network_fees.get(crypto_currency, Decimal('0.001'))
        
        # Frais de service (processeur)
        if self.primary_provider == 'nowpayments':
            service_fee = amount * Decimal('0.005')  # 0.5%
        elif self.primary_provider == 'coinbase':
            service_fee = amount * Decimal('0.01')   # 1%
        else:
            service_fee = Decimal('0')
        
        # Convertir les frais réseau en devise fiat si nécessaire
        if crypto_currency in ['BTC', 'ETH']:
            # Approximation: convertir en USD puis en devise locale
            network_fee_usd = base_network_fee * 30000  # Prix approximatif
            network_fee_local = network_fee_usd * 560   # USD to FCFA
        else:
            network_fee_local = base_network_fee
        
        total_fees = service_fee + network_fee_local
        
        return {
            'processing_fee': service_fee,
            'network_fee': network_fee_local,
            'service_fee': Decimal('0'),
            'total_fees': total_fees,
            'net_amount': amount - total_fees if transaction_type == 'withdrawal' else amount,
            'breakdown': {
                'provider_fee': f"{service_fee} ({self.primary_provider})",
                'network_fee': f"{base_network_fee} {crypto_currency}",
                'estimated_confirmation_time': f"{self.SUPPORTED_CRYPTOS[crypto_currency]['min_confirmations']} confirmations"
            }
        }
    
    def get_crypto_rates(self):
        """Obtenir les taux de change crypto en temps réel."""
        try:
            crypto_ids = [self._get_coingecko_id(crypto) for crypto in self.SUPPORTED_CRYPTOS.keys()]
            
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': ','.join(crypto_ids),
                    'vs_currencies': 'usd,eur',
                    'include_24hr_change': 'true'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = {}
                
                for crypto, crypto_id in zip(self.SUPPORTED_CRYPTOS.keys(), crypto_ids):
                    if crypto_id in data:
                        rates[crypto] = {
                            'usd': data[crypto_id]['usd'],
                            'eur': data[crypto_id]['eur'],
                            'change_24h': data[crypto_id].get('usd_24h_change', 0)
                        }
                
                return rates
            else:
                raise PaymentProcessingError("Impossible d'obtenir les taux crypto")
                
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Erreur API taux crypto: {str(e)}")
    
    def estimate_transaction_time(self, crypto_currency):
        """Estimer le temps de transaction pour une crypto."""
        times = {
            'BTC': '10-60 minutes',
            'ETH': '2-15 minutes',
            'USDT': '2-15 minutes',
            'USDC': '2-15 minutes'
        }
        
        return times.get(crypto_currency, '5-30 minutes')
