# apps/payments/processors/base.py
# ====================================

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional
from django.utils.translation import gettext_lazy as _
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class PaymentProcessorError(Exception):
    """Exception de base pour les processeurs de paiement."""
    pass


class PaymentProcessorConfigurationError(PaymentProcessorError):
    """Erreur de configuration du processeur."""
    pass


class PaymentProcessingError(PaymentProcessorError):
    """Erreur lors du traitement du paiement."""
    pass


class PaymentResponse:
    """Réponse standardisée des processeurs de paiement."""
    
    def __init__(self, success: bool, message: str, data: Dict[str, Any] = None, error: str = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.error = error
    
    @classmethod
    def success_response(cls, message: str, data: Dict[str, Any] = None):
        """Créer une réponse de succès."""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(cls, message: str, error: str = None, data: Dict[str, Any] = None):
        """Créer une réponse d'erreur."""
        return cls(success=False, message=message, error=error, data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire."""
        result = {
            'success': self.success,
            'message': self.message,
        }
        
        if self.success:
            result['data'] = self.data
        else:
            result['error'] = self.error or self.message
            if self.data:
                result['details'] = self.data
        
        return result


class WebhookResponse:
    """Réponse pour le traitement des webhooks."""
    
    def __init__(self, processed: bool, transaction_id: str = None, error: str = None):
        self.processed = processed
        self.transaction_id = transaction_id
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire."""
        result = {'processed': self.processed}
        
        if self.transaction_id:
            result['transaction_id'] = self.transaction_id
        
        if self.error:
            result['error'] = self.error
        
        return result


def handle_processor_errors(func):
    """Décorateur pour gérer les erreurs des processeurs de paiement."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except PaymentProcessorError:
            # Re-lever les erreurs spécifiques aux processeurs
            raise
        except Exception as e:
            # Logger l'erreur et la convertir en PaymentProcessingError
            logger.error(f"Erreur inattendue dans {func.__name__}: {str(e)}")
            raise PaymentProcessingError(f"Erreur interne du processeur: {str(e)}")
    return wrapper


class BasePaymentProcessor(ABC):
    """Classe de base abstraite pour tous les processeurs de paiement."""
    
    def __init__(self):
        """Initialiser le processeur de base."""
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"payments.{self.name.lower()}")
    
    @abstractmethod
    def validate_configuration(self):
        """Valider la configuration du processeur.
        
        Raises:
            PaymentProcessorConfigurationError: Si la configuration est invalide
        """
        pass
    
    @abstractmethod
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer une demande de paiement.
        
        Args:
            payment_data: Données du paiement contenant:
                - transaction_id: ID unique de la transaction
                - amount: Montant à payer (Decimal)
                - currency: Code devise (EUR, USD, FCFA, etc.)
                - user_email: Email de l'utilisateur (optionnel)
                - return_url: URL de retour après paiement (optionnel)
                - cancel_url: URL d'annulation (optionnel)
                - metadata: Métadonnées supplémentaires (optionnel)
        
        Returns:
            Dict contenant les informations du paiement créé
            
        Raises:
            PaymentProcessingError: En cas d'erreur lors de la création
        """
        pass
    
    @abstractmethod
    def verify_payment(self, payment_reference: str) -> Dict[str, Any]:
        """Vérifier le statut d'un paiement.
        
        Args:
            payment_reference: Référence du paiement à vérifier
        
        Returns:
            Dict contenant le statut du paiement
            
        Raises:
            PaymentProcessingError: En cas d'erreur lors de la vérification
        """
        pass
    
    @abstractmethod
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter un webhook reçu du processeur.
        
        Args:
            webhook_data: Données du webhook contenant:
                - payload: Corps du webhook
                - headers: En-têtes HTTP
                - provider: Nom du fournisseur
        
        Returns:
            WebhookResponse indiquant si le webhook a été traité
            
        Raises:
            PaymentProcessingError: En cas d'erreur lors du traitement
        """
        pass
    
    def create_withdrawal(self, withdrawal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer une demande de retrait.
        
        Méthode optionnelle - tous les processeurs ne supportent pas les retraits.
        
        Args:
            withdrawal_data: Données du retrait
        
        Returns:
            Dict contenant les informations du retrait
            
        Raises:
            PaymentProcessingError: Si les retraits ne sont pas supportés
        """
        raise PaymentProcessingError(
            f"Les retraits ne sont pas supportés par {self.name}"
        )
    
    def get_supported_currencies(self) -> list:
        """Obtenir la liste des devises supportées.
        
        Returns:
            Liste des codes devises supportés
        """
        return ['EUR', 'USD']  # Par défaut
    
    def calculate_fees(self, amount: Decimal, currency: str, transaction_type: str = 'deposit') -> Dict[str, Any]:
        """Calculer les frais pour une transaction.
        
        Args:
            amount: Montant de la transaction
            currency: Code devise
            transaction_type: Type de transaction ('deposit', 'withdrawal')
        
        Returns:
            Dict contenant le détail des frais:
                - processing_fee: Frais de traitement
                - service_fee: Frais de service
                - total_fees: Total des frais
                - net_amount: Montant net
                - breakdown: Détail des frais
        """
        # Implémentation par défaut - 0% de frais
        return {
            'processing_fee': Decimal('0'),
            'service_fee': Decimal('0'),
            'total_fees': Decimal('0'),
            'net_amount': amount,
            'breakdown': {'message': 'Aucun frais appliqué'}
        }
    
    def is_currency_supported(self, currency: str) -> bool:
        """Vérifier si une devise est supportée.
        
        Args:
            currency: Code devise à vérifier
        
        Returns:
            True si la devise est supportée
        """
        return currency.upper() in [c.upper() for c in self.get_supported_currencies()]
    
    def log_transaction(self, level: str, message: str, extra_data: Dict[str, Any] = None):
        """Logger une transaction.
        
        Args:
            level: Niveau de log ('info', 'warning', 'error')
            message: Message à logger
            extra_data: Données supplémentaires
        """
        log_data = {
            'processor': self.name,
            **(extra_data or {})
        }
        
        if level == 'info':
            self.logger.info(message, extra=log_data)
        elif level == 'warning':
            self.logger.warning(message, extra=log_data)
        elif level == 'error':
            self.logger.error(message, extra=log_data)
        else:
            self.logger.debug(message, extra=log_data)
    
    def validate_payment_data(self, payment_data: Dict[str, Any]) -> None:
        """Valider les données de paiement communes.
        
        Args:
            payment_data: Données à valider
            
        Raises:
            PaymentProcessingError: Si les données sont invalides
        """
        required_fields = ['transaction_id', 'amount', 'currency']
        
        for field in required_fields:
            if field not in payment_data:
                raise PaymentProcessingError(f"Champ requis manquant: {field}")
        
        # Valider le montant
        amount = payment_data['amount']
        if not isinstance(amount, (int, float, Decimal)) or amount <= 0:
            raise PaymentProcessingError("Le montant doit être positif")
        
        # Valider la devise
        currency = payment_data['currency']
        if not self.is_currency_supported(currency):
            raise PaymentProcessingError(
                f"Devise non supportée: {currency}. "
                f"Devises supportées: {', '.join(self.get_supported_currencies())}"
            )
    
    def format_amount_for_display(self, amount: Decimal, currency: str) -> str:
        """Formater un montant pour l'affichage.
        
        Args:
            amount: Montant à formater
            currency: Code devise
        
        Returns:
            Montant formaté
        """
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'FCFA': 'FCFA',
            'XOF': 'FCFA'
        }
        
        symbol = currency_symbols.get(currency.upper(), currency.upper())
        
        if currency.upper() in ['FCFA', 'XOF']:
            return f"{amount:,.0f} {symbol}"
        else:
            return f"{symbol}{amount:,.2f}"
    
    def __str__(self):
        """Représentation string du processeur."""
        return f"{self.name} Payment Processor"
    
    def __repr__(self):
        """Représentation debug du processeur."""
        return f"<{self.name}(currencies={self.get_supported_currencies()})>"
