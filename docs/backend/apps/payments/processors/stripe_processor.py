# apps/payments/processors/stripe_processor.py
# ============================================

import stripe
from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from . import (
    BasePaymentProcessor, PaymentProcessorError,
    PaymentProcessorConfigurationError, PaymentProcessingError,
    PaymentResponse, WebhookResponse, handle_processor_errors
)


class StripeProcessor(BasePaymentProcessor):
    """Processeur de paiement Stripe pour cartes bancaires."""
    
    def __init__(self):
        """Initialiser le processeur Stripe."""
        super().__init__()
        
        # Configuration Stripe
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.publishable_key = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    def validate_configuration(self):
        """Valider la configuration Stripe."""
        required_settings = [
            'STRIPE_SECRET_KEY',
            'STRIPE_PUBLISHABLE_KEY'
        ]
        
        for setting in required_settings:
            if not getattr(settings, setting, ''):
                raise PaymentProcessorConfigurationError(
                    f"Configuration Stripe manquante: {setting}"
                )
        
        # Tester la connexion à l'API Stripe
        try:
            stripe.Account.retrieve()
        except stripe.error.AuthenticationError:
            raise PaymentProcessorConfigurationError(
                "Clés API Stripe invalides"
            )
        except Exception as e:
            raise PaymentProcessorConfigurationError(
                f"Erreur de connexion Stripe: {str(e)}"
            )
    
    @handle_processor_errors
    def create_payment(self, payment_data):
        """Créer un Payment Intent Stripe."""
        try:
            # Convertir le montant en centimes (requis par Stripe)
            amount_cents = int(payment_data['amount'] * 100)
            
            # Paramètres du Payment Intent
            intent_params = {
                'amount': amount_cents,
                'currency': payment_data['currency'].lower(),
                'metadata': {
                    'transaction_id': payment_data['transaction_id'],
                    'user_email': payment_data.get('user_email', ''),
                    **payment_data.get('metadata', {})
                },
                'automatic_payment_methods': {'enabled': True},
            }
            
            # URL de retour si fournie
            if payment_data.get('return_url'):
                intent_params['return_url'] = payment_data['return_url']
            
            # Créer le Payment Intent
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            return PaymentResponse.success_response(
                "Payment Intent créé avec succès",
                {
                    'payment_intent_id': payment_intent.id,
                    'client_secret': payment_intent.client_secret,
                    'publishable_key': self.publishable_key,
                    'status': payment_intent.status,
                    'payment_url': None,  # Stripe utilise des éléments intégrés
                    'external_reference': payment_intent.id
                }
            ).to_dict()
            
        except stripe.error.CardError as e:
            # Erreur de carte
            raise PaymentProcessingError(f"Erreur de carte: {e.user_message}")
            
        except stripe.error.RateLimitError:
            raise PaymentProcessingError("Trop de requêtes vers Stripe")
            
        except stripe.error.InvalidRequestError as e:
            raise PaymentProcessingError(f"Requête invalide: {str(e)}")
            
        except stripe.error.AuthenticationError:
            raise PaymentProcessorConfigurationError("Authentification Stripe échouée")
            
        except stripe.error.APIConnectionError:
            raise PaymentProcessingError("Impossible de se connecter à Stripe")
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur Stripe: {str(e)}")
    
    @handle_processor_errors
    def process_payment(self, payment_data):
        """Confirmer un Payment Intent Stripe."""
        try:
            payment_intent_id = payment_data.get('payment_intent_id')
            payment_method_id = payment_data.get('payment_method_id')
            
            if not payment_intent_id:
                raise PaymentProcessingError("ID Payment Intent requis")
            
            # Récupérer le Payment Intent
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Si un payment method est fourni, l'attacher
            if payment_method_id:
                payment_intent = stripe.PaymentIntent.modify(
                    payment_intent_id,
                    payment_method=payment_method_id
                )
            
            # Confirmer le paiement
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            return PaymentResponse.success_response(
                "Paiement traité avec succès",
                {
                    'payment_intent_id': payment_intent.id,
                    'status': payment_intent.status,
                    'amount_received': payment_intent.amount_received / 100,
                    'currency': payment_intent.currency.upper()
                }
            ).to_dict()
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur Stripe: {str(e)}")
    
    @handle_processor_errors
    def verify_payment(self, payment_reference):
        """Vérifier le statut d'un Payment Intent."""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_reference)
            
            return PaymentResponse.success_response(
                "Statut du paiement récupéré",
                {
                    'payment_reference': payment_reference,
                    'status': payment_intent.status,
                    'amount': payment_intent.amount / 100,
                    'currency': payment_intent.currency.upper(),
                    'created': payment_intent.created,
                    'metadata': payment_intent.metadata
                }
            ).to_dict()
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur Stripe: {str(e)}")
    
    @handle_processor_errors
    def create_withdrawal(self, withdrawal_data):
        """Créer un transfert Stripe (payout)."""
        try:
            # Pour les retraits, Stripe utilise des transferts vers des comptes connectés
            # ou des payouts vers des cartes de débit
            
            # Convertir le montant en centimes
            amount_cents = int(withdrawal_data['amount'] * 100)
            
            # Créer un transfert
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency=withdrawal_data['currency'].lower(),
                destination=withdrawal_data.get('destination_account'),
                metadata={
                    'transaction_id': withdrawal_data['transaction_id'],
                    'withdrawal_type': 'card_payout'
                }
            )
            
            return PaymentResponse.success_response(
                "Transfert créé avec succès",
                {
                    'transfer_id': transfer.id,
                    'status': 'processing',
                    'amount': transfer.amount / 100,
                    'estimated_arrival': None  # Dépend du type de destination
                }
            ).to_dict()
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur Stripe transfer: {str(e)}")
    
    @handle_processor_errors
    def process_webhook(self, webhook_data):
        """Traiter un webhook Stripe."""
        try:
            # Vérifier la signature du webhook si configurée
            if self.webhook_secret:
                sig_header = webhook_data.get('stripe_signature')
                if not sig_header:
                    raise PaymentProcessingError("Signature webhook manquante")
                
                try:
                    event = stripe.Webhook.construct_event(
                        webhook_data['payload'],
                        sig_header,
                        self.webhook_secret
                    )
                except ValueError:
                    raise PaymentProcessingError("Payload webhook invalide")
                except stripe.error.SignatureVerificationError:
                    raise PaymentProcessingError("Signature webhook invalide")
            else:
                # Si pas de secret configuré, parser directement
                import json
                event = json.loads(webhook_data['payload'])
            
            # Traiter selon le type d'événement
            event_type = event['type']
            event_data = event['data']['object']
            
            transaction_id = None
            
            if event_type == 'payment_intent.succeeded':
                # Paiement réussi
                transaction_id = self._handle_payment_succeeded(event_data)
                
            elif event_type == 'payment_intent.payment_failed':
                # Paiement échoué
                transaction_id = self._handle_payment_failed(event_data)
                
            elif event_type == 'payment_intent.canceled':
                # Paiement annulé
                transaction_id = self._handle_payment_canceled(event_data)
                
            elif event_type == 'transfer.created':
                # Transfert créé
                transaction_id = self._handle_transfer_created(event_data)
                
            elif event_type == 'transfer.updated':
                # Transfert mis à jour
                transaction_id = self._handle_transfer_updated(event_data)
            
            return WebhookResponse(
                processed=True,
                transaction_id=transaction_id
            ).to_dict()
            
        except Exception as e:
            return WebhookResponse(
                processed=False,
                error=str(e)
            ).to_dict()
    
    def _handle_payment_succeeded(self, payment_intent):
        """Gérer un paiement réussi."""
        from ..models import Transaction
        
        try:
            # Trouver la transaction correspondante
            transaction = Transaction.objects.get(
                external_reference=payment_intent['id'],
                status__in=['pending', 'processing']
            )
            
            # Mettre à jour le statut
            transaction.status = 'completed'
            transaction.completed_at = timezone.now()
            transaction.save()
            
            # Traiter la transaction (créditer le compte, etc.)
            transaction.process()
            
            return str(transaction.id)
            
        except Transaction.DoesNotExist:
            raise PaymentProcessingError(
                f"Transaction introuvable pour Payment Intent: {payment_intent['id']}"
            )
    
    def _handle_payment_failed(self, payment_intent):
        """Gérer un paiement échoué."""
        from ..models import Transaction
        
        try:
            transaction = Transaction.objects.get(
                external_reference=payment_intent['id'],
                status__in=['pending', 'processing']
            )
            
            # Récupérer la raison de l'échec
            last_payment_error = payment_intent.get('last_payment_error', {})
            failure_reason = last_payment_error.get('message', 'Paiement échoué')
            
            transaction.status = 'failed'
            transaction.failure_reason = failure_reason
            transaction.processed_at = timezone.now()
            transaction.save()
            
            return str(transaction.id)
            
        except Transaction.DoesNotExist:
            raise PaymentProcessingError(
                f"Transaction introuvable pour Payment Intent: {payment_intent['id']}"
            )
    
    def _handle_payment_canceled(self, payment_intent):
        """Gérer un paiement annulé."""
        from ..models import Transaction
        
        try:
            transaction = Transaction.objects.get(
                external_reference=payment_intent['id'],
                status__in=['pending', 'processing']
            )
            
            transaction.cancel('Annulé côté Stripe')
            
            return str(transaction.id)
            
        except Transaction.DoesNotExist:
            raise PaymentProcessingError(
                f"Transaction introuvable pour Payment Intent: {payment_intent['id']}"
            )
    
    def _handle_transfer_created(self, transfer):
        """Gérer la création d'un transfert."""
        # Logique pour les retraits/transferts
        pass
    
    def _handle_transfer_updated(self, transfer):
        """Gérer la mise à jour d'un transfert."""
        # Logique pour les mises à jour de retraits
        pass
    
    def get_supported_currencies(self):
        """Obtenir les devises supportées par Stripe."""
        # Liste des principales devises supportées par Stripe
        return [
            'EUR', 'USD', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF',
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'BGN',
            'RON', 'HRK', 'LTL', 'LVL', 'EEK'
            # Note: FCFA n'est pas directement supporté par Stripe
        ]
    
    def calculate_fees(self, amount, currency, transaction_type='deposit'):
        """Calculer les frais Stripe."""
        # Frais Stripe standards (variables selon la région)
        if currency.upper() == 'EUR':
            # Frais européens
            percentage_fee = Decimal('1.4')  # 1.4%
            fixed_fee = Decimal('0.25')      # 0.25€
        elif currency.upper() == 'USD':
            # Frais US
            percentage_fee = Decimal('2.9')  # 2.9%
            fixed_fee = Decimal('0.30')      # $0.30
        else:
            # Frais internationaux
            percentage_fee = Decimal('3.4')  # 3.4%
            fixed_fee = Decimal('0.50')      # Equivalent
        
        # Calculer les frais
        processing_fee = (amount * percentage_fee / 100) + fixed_fee
        
        return {
            'processing_fee': processing_fee,
            'service_fee': Decimal('0'),  # Pas de frais supplémentaires
            'total_fees': processing_fee,
            'net_amount': amount - processing_fee if transaction_type == 'withdrawal' else amount,
            'breakdown': {
                'stripe_percentage': f"{percentage_fee}%",
                'stripe_fixed': f"{fixed_fee} {currency}",
                'stripe_total': processing_fee
            }
        }
    
    def create_customer(self, customer_data):
        """Créer un customer Stripe."""
        try:
            customer = stripe.Customer.create(
                email=customer_data.get('email'),
                name=customer_data.get('name'),
                phone=customer_data.get('phone'),
                metadata=customer_data.get('metadata', {})
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'customer': customer
            }
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur création customer: {str(e)}")
    
    def create_setup_intent(self, customer_id):
        """Créer un Setup Intent pour sauvegarder une méthode de paiement."""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session'
            )
            
            return {
                'setup_intent_id': setup_intent.id,
                'client_secret': setup_intent.client_secret,
                'status': setup_intent.status
            }
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur Setup Intent: {str(e)}")
    
    def get_payment_methods(self, customer_id):
        """Récupérer les méthodes de paiement sauvegardées."""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            return {
                'success': True,
                'payment_methods': payment_methods.data
            }
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur récupération payment methods: {str(e)}")
    
    def delete_payment_method(self, payment_method_id):
        """Supprimer une méthode de paiement."""
        try:
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            
            return {
                'success': True,
                'payment_method': payment_method
            }
            
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Erreur suppression payment method: {str(e)}")
