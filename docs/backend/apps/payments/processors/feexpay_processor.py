# apps/payments/processors/feexpay_processor.py
# ==============================================

"""
Processeur de paiement FeexPay pour Mobile Money et autres méthodes.
Utilise le FeexPayClient pour gérer les paiements via l'API FeexPay.
"""

from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from . import (
    BasePaymentProcessor, PaymentProcessorError,
    PaymentProcessorConfigurationError, PaymentProcessingError,
    PaymentResponse, WebhookResponse, handle_processor_errors
)
from ..feexpay_client_real import FeexPayClientReal as FeexPayClient, FeexPayAPIError
from ..feexpay_client import FeexPayValidationError
from ..models import FeexPayProvider, FeexPayTransaction, Transaction


class FeexPayProcessor(BasePaymentProcessor):
    """Processeur de paiement FeexPay pour Mobile Money et autres méthodes."""
    
    # Mapping des types de méthodes vers les codes FeexPay
    METHOD_TYPE_TO_FEEXPAY = {
        'mobile_money': {
            'Orange Money': 'orange',
            'MTN Mobile Money': 'mtn', 
            'Moov Money': 'moov'
        },
        'card': {
            'Carte Bancaire': 'visa'  # Par défaut Visa
        },
        'bank_transfer': {
            'Virement Bancaire': 'bank_transfer'
        }
    }
    
    def __init__(self):
        """Initialiser le processeur FeexPay."""
        super().__init__()
        self.client = None
        
    def validate_configuration(self):
        """Valider la configuration FeexPay."""
        try:
            self.client = FeexPayClient()
            # Tester la connectivité
            health_ok = self.client.health_check()
            if not health_ok:
                raise PaymentProcessorConfigurationError(
                    "Impossible de se connecter à l'API FeexPay"
                )
        except Exception as e:
            raise PaymentProcessorConfigurationError(
                f"Configuration FeexPay invalide: {str(e)}"
            )
    
    @handle_processor_errors
    def create_payment(self, payment_data):
        """Créer un paiement via FeexPay."""
        try:
            # Initialiser le client si pas encore fait
            if not self.client:
                self.client = FeexPayClient()
            
            # Déterminer le provider FeexPay
            provider_code = self._get_feexpay_provider_code(payment_data)
            
            # Préparer les données pour FeexPay
            feexpay_data = {
                'provider_code': provider_code,
                'amount': float(payment_data['amount']),
                'currency': payment_data['currency'],
                'recipient_phone': payment_data.get('phone_number', ''),
                'recipient_email': payment_data.get('user_email', ''),
                'metadata': {
                    'internal_tx_id': payment_data['transaction_id'],
                    'payment_method': payment_data.get('payment_method_name', ''),
                    'user_id': str(payment_data.get('user_id', '')),
                    'return_url': payment_data.get('return_url', ''),
                }
            }
            
            # Appeler l'API FeexPay
            response = self.client.initiate_payment(**feexpay_data)
            
            # Créer la transaction FeexPay
            self._create_feexpay_transaction(payment_data, response)
            
            return PaymentResponse.success_response(
                "Paiement FeexPay initié avec succès",
                {
                    'payment_id': response.get('transaction_id'),
                    'external_reference': response.get('transaction_id'),
                    'status': response.get('status', 'pending'),
                    'payment_url': response.get('payment_url'),
                    'feexpay_data': response,
                    'created_at': timezone.now(),
                    'amount': payment_data['amount'],
                    'currency': payment_data['currency'],
                    'provider': provider_code
                }
            ).to_dict()
            
        except FeexPayAPIError as e:
            raise PaymentProcessingError(f"Erreur FeexPay API: {e.message}")
        except FeexPayValidationError as e:
            raise PaymentProcessingError(f"Erreur validation FeexPay: {str(e)}")
        except Exception as e:
            raise PaymentProcessingError(f"Erreur inattendue FeexPay: {str(e)}")
    
    def _get_feexpay_provider_code(self, payment_data):
        """Déterminer le code provider FeexPay selon la méthode de paiement."""
        payment_method_name = payment_data.get('payment_method_name', '')
        method_type = payment_data.get('method_type', '')
        phone_number = payment_data.get('phone_number', '')
        
        # Pour Mobile Money, détecter l'opérateur depuis le nom ou le numéro
        if method_type == 'mobile_money':
            if 'Orange' in payment_method_name or 'orange' in payment_method_name.lower():
                return 'orange'
            elif 'MTN' in payment_method_name or 'mtn' in payment_method_name.lower():
                return 'mtn'
            elif 'Moov' in payment_method_name or 'moov' in payment_method_name.lower():
                return 'moov'
            
            # Détecter depuis le numéro de téléphone si pas de nom
            if phone_number:
                # Indicatifs Côte d'Ivoire (exemple)
                if phone_number.startswith(('07', '67', '+22507', '+22567')):  # Orange CI
                    return 'orange'
                elif phone_number.startswith(('05', '65', '+22505', '+22565')):  # MTN CI  
                    return 'mtn'
                elif phone_number.startswith(('01', '61', '+22501', '+22561')):  # Moov CI
                    return 'moov'
        
        # Pour les cartes
        elif method_type == 'card':
            return 'visa'  # Par défaut Visa, peut être étendu
            
        # Pour les virements
        elif method_type == 'bank_transfer':
            return 'bank_transfer'
        
        # Fallback : retourner le provider par défaut selon le type
        default_providers = {
            'mobile_money': 'orange',
            'card': 'visa',
            'bank_transfer': 'bank_transfer'
        }
        
        return default_providers.get(method_type, 'orange')
    
    def _create_feexpay_transaction(self, payment_data, feexpay_response):
        """Créer l'enregistrement FeexPayTransaction."""
        try:
            # Obtenir la transaction Django
            transaction_id = payment_data['transaction_id']
            transaction_obj = Transaction.objects.get(id=transaction_id)
            
            # Obtenir ou créer le provider FeexPay
            provider_code = feexpay_response.get('provider_code', 'orange')
            provider, _ = FeexPayProvider.objects.get_or_create(
                provider_code=provider_code,
                country_code='CI',  # Par défaut Côte d'Ivoire
                defaults={
                    'provider_name': provider_code.upper(),
                    'is_active': True,
                    'supported_currencies': ['XOF', 'FCFA'],
                    'min_amount': Decimal('100'),
                    'max_amount': Decimal('1000000'),
                }
            )
            
            # Créer la transaction FeexPay
            feexpay_tx = FeexPayTransaction.objects.create(
                transaction=transaction_obj,
                user=transaction_obj.user,
                provider=provider,
                feexpay_transaction_id=feexpay_response.get('transaction_id', ''),
                internal_transaction_id=str(transaction_id),
                amount=payment_data['amount'],
                currency=payment_data['currency'],
                payment_method=payment_data.get('method_type', 'mobile_money'),
                recipient_phone=payment_data.get('phone_number', ''),
                recipient_email=payment_data.get('user_email', ''),
                status='pending',
                feexpay_response=feexpay_response,
                initiated_at=timezone.now()
            )
            
            return feexpay_tx
            
        except Exception as e:
            # Log l'erreur mais ne pas faire échouer le paiement
            import logging
            logger = logging.getLogger('feexpay')
            logger.error(f"Erreur création FeexPayTransaction: {str(e)}")
            return None
    
    @handle_processor_errors  
    def verify_payment(self, payment_reference):
        """Vérifier le statut d'un paiement FeexPay."""
        try:
            if not self.client:
                self.client = FeexPayClient()
                
            status_response = self.client.get_payment_status(payment_reference)
            
            return PaymentResponse.success_response(
                "Statut FeexPay récupéré",
                {
                    'payment_reference': payment_reference,
                    'status': status_response.get('status'),
                    'amount': status_response.get('amount'),
                    'currency': status_response.get('currency'),
                    'feexpay_data': status_response
                }
            ).to_dict()
            
        except FeexPayAPIError as e:
            raise PaymentProcessingError(f"Erreur vérification FeexPay: {e.message}")
    
    @handle_processor_errors
    def process_payment(self, payment_data):
        """Traiter/confirmer un paiement (non applicable pour FeexPay)."""
        # FeexPay gère le processus automatiquement via webhooks
        raise PaymentProcessingError("Traitement manuel non supporté par FeexPay")
    
    @handle_processor_errors
    def cancel_payment(self, payment_reference):
        """Annuler un paiement FeexPay."""
        # FeexPay ne supporte pas l'annulation directe
        raise PaymentProcessingError("Annulation non supportée par FeexPay")
    
    def process_webhook(self, webhook_data, signature=None):
        """Traiter un webhook FeexPay."""
        try:
            if not self.client:
                self.client = FeexPayClient()
            
            # Valider la signature si fournie
            if signature and hasattr(self.client, 'verify_webhook_signature'):
                is_valid = self.client.verify_webhook_signature(webhook_data, signature)
                if not is_valid:
                    raise PaymentProcessingError("Signature webhook FeexPay invalide")
            
            # Traiter l'événement selon le type
            event_type = webhook_data.get('event_type', '')
            transaction_id = webhook_data.get('transaction_id', '')
            
            response_data = {
                'transaction_id': transaction_id,
                'event_type': event_type,
                'status': webhook_data.get('status'),
                'processed_at': timezone.now()
            }
            
            return WebhookResponse.success_response(
                f"Webhook FeexPay {event_type} traité",
                response_data
            ).to_dict()
            
        except Exception as e:
            raise PaymentProcessingError(f"Erreur traitement webhook FeexPay: {str(e)}")