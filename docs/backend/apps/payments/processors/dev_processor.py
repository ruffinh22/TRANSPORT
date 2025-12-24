"""Processor de développement pour tests locaux (DEBUG).
Retourne une réponse simulée et met la transaction en `processing` ou `completed`.
"""
from decimal import Decimal
from django.utils import timezone
from .base import BasePaymentProcessor, PaymentResponse, handle_processor_errors


class DevPaymentProcessor(BasePaymentProcessor):
    """Processeur factice utilisé en environnement de développement."""

    def __init__(self):
        super().__init__()

    def validate_configuration(self):
        # Toujours valide en dev
        return True

    @handle_processor_errors
    def create_payment(self, payment_data):
        # Simuler la création d'un paiement
        tx_id = payment_data.get('transaction_id')
        amount = payment_data.get('amount')
        currency = payment_data.get('currency')

        created_at = timezone.now()

        return PaymentResponse.success_response(
            "Paiement simulé (dev)",
            {
                'payment_id': f"dev_{tx_id}",
                'external_reference': f"dev_{tx_id}",
                'status': 'pending',
                'payment_url': None,
                'client_secret': None,
                'created_at': created_at,
                'amount': amount,
                'currency': currency
            }
        ).to_dict()

    @handle_processor_errors
    def verify_payment(self, payment_reference):
        return PaymentResponse.success_response(
            "Paiement simulé vérifié",
            {
                'payment_reference': payment_reference,
                'status': 'completed',
                'amount': Decimal('0'),
                'currency': 'FCFA'
            }
        ).to_dict()

    @handle_processor_errors
    def process_webhook(self, webhook_data):
        return PaymentResponse.success_response(
            "Webhook simulé traité",
            {'processed': True}
        ).to_dict()
