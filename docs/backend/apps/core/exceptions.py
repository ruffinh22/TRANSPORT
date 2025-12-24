# apps/core/exceptions.py
# ============================

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, APIException
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.http import Http404
from typing import Dict, Any, Optional
import logging

from . import ERROR_MESSAGES

logger = logging.getLogger(__name__)


# ===== EXCEPTIONS MÉTIER =====

class RumoRushException(APIException):
    """Exception de base pour toutes les erreurs métier RUMO RUSH."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Une erreur s'est produite"
    default_code = 'error'


class InsufficientFundsException(RumoRushException):
    """Exception pour solde insuffisant."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_MESSAGES['INSUFFICIENT_FUNDS']
    default_code = 'insufficient_funds'
    
    def __init__(self, required_amount: float = None, available_amount: float = None, currency: str = 'FCFA'):
        if required_amount and available_amount:
            detail = f"Solde insuffisant. Requis: {required_amount} {currency}, Disponible: {available_amount} {currency}"
        else:
            detail = self.default_detail
        super().__init__(detail)


class GameFullException(RumoRushException):
    """Exception quand une partie est complète."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_MESSAGES['GAME_FULL']
    default_code = 'game_full'


class GameNotFoundException(RumoRushException):
    """Exception quand une partie n'existe pas."""
    
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = ERROR_MESSAGES['GAME_NOT_FOUND']
    default_code = 'game_not_found'


class InvalidGameStateException(RumoRushException):
    """Exception pour état de jeu invalide."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Action non autorisée dans l'état actuel du jeu"
    default_code = 'invalid_game_state'


class RateLimitExceededException(RumoRushException):
    """Exception pour limite de taux dépassée."""
    
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = ERROR_MESSAGES['RATE_LIMIT_EXCEEDED']
    default_code = 'rate_limit_exceeded'
    
    def __init__(self, retry_after: int = 60):
        super().__init__()
        self.retry_after = retry_after


class KYCRequiredException(RumoRushException):
    """Exception pour KYC requis."""
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = ERROR_MESSAGES['KYC_REQUIRED']
    default_code = 'kyc_required'


class InvalidCurrencyException(RumoRushException):
    """Exception pour devise non supportée."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_MESSAGES['CURRENCY_NOT_SUPPORTED']
    default_code = 'invalid_currency'


class MaintenanceModeException(RumoRushException):
    """Exception pour mode maintenance."""
    
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = ERROR_MESSAGES['MAINTENANCE_MODE']
    default_code = 'maintenance_mode'


class RegionRestrictedException(RumoRushException):
    """Exception pour restriction géographique."""
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = ERROR_MESSAGES['REGION_RESTRICTED']
    default_code = 'region_restricted'


class MinAgeException(RumoRushException):
    """Exception pour âge minimum."""
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = ERROR_MESSAGES['MIN_AGE_REQUIRED']
    default_code = 'min_age_required'


class TransactionException(RumoRushException):
    """Exception pour erreurs de transaction."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Erreur lors du traitement de la transaction"
    default_code = 'transaction_error'
    
    def __init__(self, detail: str = None, transaction_id: str = None):
        super().__init__(detail)
        self.transaction_id = transaction_id


class PaymentProviderException(RumoRushException):
    """Exception pour erreurs du fournisseur de paiement."""
    
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Erreur du fournisseur de paiement"
    default_code = 'payment_provider_error'


class WithdrawalException(RumoRushException):
    """Exception pour erreurs de retrait."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Erreur lors du retrait"
    default_code = 'withdrawal_error'


class ReferralException(RumoRushException):
    """Exception pour erreurs de parrainage."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Erreur de parrainage"
    default_code = 'referral_error'


# ===== HANDLER D'EXCEPTIONS GLOBAL =====

def custom_exception_handler(exc, context):
    """
    Handler d'exceptions personnalisé pour l'API RUMO RUSH.
    Gère toutes les exceptions et renvoie des réponses uniformes.
    """
    
    # Obtenir la réponse standard de DRF
    response = exception_handler(exc, context)
    
    # Obtenir les informations de contexte
    view = context.get('view')
    request = context.get('request')
    
    # Log de l'exception
    logger.error(
        f"Exception in {view.__class__.__name__ if view else 'Unknown'}: {exc}",
        exc_info=True,
        extra={
            'user_id': getattr(request.user, 'id', None) if request and hasattr(request, 'user') else None,
            'path': request.path if request else None,
            'method': request.method if request else None,
            'request_id': getattr(request, 'request_id', None) if request else None,
        }
    )
    
    # Si DRF n'a pas géré l'exception, créer notre propre réponse
    if response is None:
        response = handle_unhandled_exception(exc, context)
    else:
        # Améliorer la réponse DRF
        response = enhance_drf_response(response, exc, context)
    
    return response


def handle_unhandled_exception(exc, context) -> Response:
    """Gérer les exceptions non traitées par DRF."""
    
    if isinstance(exc, ObjectDoesNotExist):
        return Response({
            'error': 'Ressource introuvable',
            'code': 'not_found',
            'detail': str(exc),
            'timestamp': get_current_timestamp()
        }, status=status.HTTP_404_NOT_FOUND)
    
    elif isinstance(exc, DjangoValidationError):
        return Response({
            'error': 'Erreur de validation',
            'code': 'validation_error',
            'detail': exc.messages if hasattr(exc, 'messages') else str(exc),
            'timestamp': get_current_timestamp()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, Http404):
        return Response({
            'error': 'Page non trouvée',
            'code': 'not_found',
            'detail': 'La ressource demandée n\'existe pas',
            'timestamp': get_current_timestamp()
        }, status=status.HTTP_404_NOT_FOUND)
    
    else:
        # Erreur serveur générique
        logger.critical(f"Unhandled exception: {exc}", exc_info=True)
        
        return Response({
            'error': ERROR_MESSAGES['SERVER_ERROR'],
            'code': 'server_error',
            'detail': 'Une erreur inattendue s\'est produite',
            'timestamp': get_current_timestamp()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def enhance_drf_response(response: Response, exc, context) -> Response:
    """Améliorer les réponses DRF avec des informations supplémentaires."""
    
    request = context.get('request')
    
    # Structure de réponse uniformisée
    custom_response_data = {
        'success': False,
        'error': get_error_message(exc),
        'code': get_error_code(exc),
        'timestamp': get_current_timestamp(),
    }
    
    # Ajouter les détails de l'erreur
    if hasattr(response, 'data') and response.data:
        if isinstance(response.data, dict):
            custom_response_data['details'] = response.data
        elif isinstance(response.data, list):
            custom_response_data['details'] = {'messages': response.data}
        else:
            custom_response_data['details'] = {'message': str(response.data)}
    
    # Ajouter des informations de debug en mode développement
    if hasattr(request, 'user') and request.user.is_staff and hasattr(exc, '__traceback__'):
        import traceback
        custom_response_data['debug'] = {
            'exception_type': exc.__class__.__name__,
            'traceback': traceback.format_exc()
        }
    
    # Ajouter le retry_after pour les erreurs 429
    if isinstance(exc, RateLimitExceededException):
        response['Retry-After'] = str(exc.retry_after)
        custom_response_data['retry_after'] = exc.retry_after
    
    # Ajouter l'ID de requête si disponible
    if request and hasattr(request, 'request_id'):
        custom_response_data['request_id'] = request.request_id
    
    response.data = custom_response_data
    return response


def get_error_message(exc) -> str:
    """Obtenir le message d'erreur approprié."""
    
    if isinstance(exc, RumoRushException):
        return str(exc.detail)
    elif hasattr(exc, 'detail'):
        return str(exc.detail)
    elif hasattr(exc, 'message'):
        return str(exc.message)
    else:
        return str(exc)


def get_error_code(exc) -> str:
    """Obtenir le code d'erreur approprié."""
    
    if isinstance(exc, RumoRushException):
        return exc.default_code
    elif hasattr(exc, 'default_code'):
        return exc.default_code
    else:
        return 'unknown_error'


def get_current_timestamp() -> str:
    """Obtenir le timestamp actuel au format ISO."""
    from django.utils import timezone
    return timezone.now().isoformat()


# ===== EXCEPTIONS POUR VALIDATION =====

class GameValidationException(ValidationError):
    """Exception pour validation de jeu."""
    
    def __init__(self, message: str, field: str = None):
        if field:
            super().__init__({field: [message]})
        else:
            super().__init__({'non_field_errors': [message]})


class PaymentValidationException(ValidationError):
    """Exception pour validation de paiement."""
    
    def __init__(self, message: str, field: str = None):
        if field:
            super().__init__({field: [message]})
        else:
            super().__init__({'non_field_errors': [message]})


# ===== UTILITAIRES POUR GESTION D'ERREURS =====

class ErrorCollector:
    """Collecteur d'erreurs pour validation en lot."""
    
    def __init__(self):
        self.errors = {}
    
    def add_error(self, field: str, message: str):
        """Ajouter une erreur."""
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)
    
    def has_errors(self) -> bool:
        """Vérifier s'il y a des erreurs."""
        return len(self.errors) > 0
    
    def raise_if_errors(self):
        """Lever une ValidationError s'il y a des erreurs."""
        if self.has_errors():
            raise ValidationError(self.errors)


def handle_database_error(func):
    """Décorateur pour gérer les erreurs de base de données."""
    
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from django.db import IntegrityError, OperationalError
            
            if isinstance(e, IntegrityError):
                raise ValidationError("Violation de contrainte de données")
            elif isinstance(e, OperationalError):
                raise RumoRushException("Erreur de base de données temporaire")
            else:
                raise
    
    return wrapper


def safe_api_call(func):
    """Décorateur pour sécuriser les appels API externes."""
    
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"External API call failed: {func.__name__}", exc_info=True)
            raise PaymentProviderException("Service de paiement temporairement indisponible")
    
    return wrapper


# ===== CONTEXTE D'ERREUR =====

class ErrorContext:
    """Contexte pour enrichir les messages d'erreur."""
    
    def __init__(self, user_id: str = None, game_id: str = None, transaction_id: str = None):
        self.user_id = user_id
        self.game_id = game_id
        self.transaction_id = transaction_id
        self.extra_data = {}
    
    def add_context(self, key: str, value: Any):
        """Ajouter du contexte supplémentaire."""
        self.extra_data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire."""
        context = {
            'user_id': self.user_id,
            'game_id': self.game_id,
            'transaction_id': self.transaction_id,
        }
        context.update(self.extra_data)
        return {k: v for k, v in context.items() if v is not None}
