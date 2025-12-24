# apps/payments/processors/__init__.py
# =======================================

from .base import (
    BasePaymentProcessor,
    PaymentProcessorError,
    PaymentProcessorConfigurationError,
    PaymentProcessingError,
    PaymentResponse,
    WebhookResponse,
    handle_processor_errors,
)


def get_payment_processor(method_type):
    """Factory pour obtenir le bon processeur de paiement."""
    # Import local pour éviter l'import circulaire
    from .stripe_processor import StripeProcessor
    from .feexpay_processor import FeexPayProcessor
    from .crypto_processor import CryptoProcessor
    
    # Utiliser FeexPay pour Mobile Money (avec URL corrigée)
    processors = {
        'card': StripeProcessor,
        'stripe': StripeProcessor, 
        'mobile_money': FeexPayProcessor,  # Utiliser FeexPay pour Mobile Money
        'crypto': CryptoProcessor,
        'bank_transfer': FeexPayProcessor,  # FeexPay supporte aussi les virements
    }
    
    processor_class = processors.get(method_type)
    if not processor_class:
        raise ValueError(f"Processeur non supporté: {method_type}")

    return processor_class()


# Exporter les utilitaires et la factory pour import depuis le package
__all__ = [
    'BasePaymentProcessor',
    'PaymentProcessorError',
    'PaymentProcessorConfigurationError',
    'PaymentProcessingError',
    'PaymentResponse',
    'WebhookResponse',
    'handle_processor_errors',
    'get_payment_processor'
]
