# apps/payments/feexpay_client.py
# ================================

"""
Client HTTP pour FeexPay API.

Supporte 16 fournisseurs de paiement :
- Mobile Money: MTN, Moov, Orange, Celtiis, Coris, Wave, Free
- Virements bancaires
- Cartes: Visa, Mastercard, Amex, UnionPay
- Portefeuilles régionaux: Orange CI, Moov Togo, MTN Sénégal, Wave Sénégal
"""

import requests
import hmac
import hashlib
import json
import logging
from decimal import Decimal
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from urllib.parse import urljoin

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError

logger = logging.getLogger('feexpay')


class FeexPayException(Exception):
    """Exception de base pour les erreurs FeexPay."""
    pass


class FeexPayAuthenticationError(FeexPayException):
    """Erreur d'authentification FeexPay."""
    pass


class FeexPayValidationError(FeexPayException):
    """Erreur de validation FeexPay."""
    pass


class FeexPayAPIError(FeexPayException):
    """Erreur API FeexPay."""
    
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class FeexPayClient:
    """
    Client pour l'API FeexPay.
    
    Authentification par Bearer token.
    Supporte les 16 fournisseurs de paiement.
    """
    
    # Endpoints FeexPay
    BASE_URL = "https://api.feexpay.me"
    INITIATE_ENDPOINT = "/api/v1/payments/initiate"
    STATUS_ENDPOINT = "/api/v1/payments/{transaction_id}/status"
    PROVIDERS_ENDPOINT = "/api/v1/providers"
    EXCHANGE_RATE_ENDPOINT = "/api/v1/exchange-rates"
    
    # Timeout par défaut
    DEFAULT_TIMEOUT = 30
    
    # Codes d'erreur FeexPay mappés
    ERROR_CODES = {
        '401': 'UNAUTHORIZED',
        '402': 'INVALID_REQUEST',
        '404': 'NOT_FOUND',
        '405': 'METHOD_NOT_ALLOWED',
        '422': 'VALIDATION_ERROR',
        '500': 'SERVER_ERROR',
        '503': 'SERVICE_UNAVAILABLE',
    }
    
    def __init__(self, api_key: str = None, shop_id: str = None, test_mode: bool = False):
        """
        Initialiser le client FeexPay.
        
        Args:
            api_key: Clé API Bearer (de settings par défaut)
            shop_id: ID du magasin (de settings par défaut)
            test_mode: Utiliser l'environnement de test
        """
        self.api_key = api_key or getattr(settings, 'FEEXPAY_API_KEY', None)
        self.shop_id = shop_id or getattr(settings, 'FEEXPAY_SHOP_ID', None)
        self.webhook_secret = getattr(settings, 'FEEXPAY_WEBHOOK_SECRET', None)
        self.test_mode = test_mode or getattr(settings, 'FEEXPAY_TEST_MODE', False)
        
        if not self.api_key or not self.shop_id:
            raise FeexPayAuthenticationError(
                'FEEXPAY_API_KEY et FEEXPAY_SHOP_ID doivent être configurés'
            )
        
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configurer la session HTTP avec les headers par défaut."""
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'RumoRush/1.0 (FeexPay Client)',
            'X-Shop-ID': self.shop_id,
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        timeout: int = None
    ) -> Dict:
        """
        Effectuer une requête HTTP.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint API
            data: Données à envoyer
            params: Paramètres de query
            timeout: Timeout en secondes
        
        Returns:
            Réponse JSON parsée
        
        Raises:
            FeexPayAPIError: Erreur API
        """
        url = urljoin(self.BASE_URL, endpoint)
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        try:
            logger.debug(f"Requête FeexPay: {method} {endpoint}")
            
            if method.upper() == 'GET':
                response = self.session.get(
                    url,
                    params=params,
                    timeout=timeout
                )
            elif method.upper() == 'POST':
                response = self.session.post(
                    url,
                    json=data,
                    params=params,
                    timeout=timeout
                )
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url,
                    json=data,
                    timeout=timeout
                )
            else:
                raise FeexPayException(f"Méthode HTTP non supportée: {method}")
            
            # Traiter la réponse
            response.raise_for_status()
            
            try:
                result = response.json()
                logger.debug(f"Réponse FeexPay: {result}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Réponse non JSON: {response.text}")
                raise FeexPayAPIError("Réponse invalide du serveur FeexPay")
        
        except requests.Timeout:
            logger.error(f"Timeout FeexPay: {endpoint}")
            raise FeexPayAPIError("Timeout - FeexPay ne répond pas", status_code=408)
        
        except requests.HTTPError as e:
            status_code = e.response.status_code
            error_code = self.ERROR_CODES.get(str(status_code), 'UNKNOWN_ERROR')
            
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', str(e))
                error_details = error_data.get('details', {})
            except:
                error_msg = str(e)
                error_details = {}
            
            logger.error(f"Erreur FeexPay: {status_code} - {error_msg}")
            
            raise FeexPayAPIError(
                f"{error_code}: {error_msg}",
                status_code=status_code,
                error_code=error_code
            )
        
        except requests.RequestException as e:
            logger.error(f"Erreur requête FeexPay: {str(e)}")
            raise FeexPayException(f"Erreur de communication: {str(e)}")
    
    # ============= ENDPOINTS DE PAIEMENT =============
    
    def initiate_payment(
        self,
        provider_code: str,
        amount: Decimal,
        currency: str,
        recipient_phone: str = None,
        recipient_email: str = None,
        recipient_account: str = None,
        description: str = None,
        metadata: Dict = None,
        customer_id: str = None,
        order_id: str = None,
        callback_url: str = None
    ) -> Dict:
        """
        Initier un paiement FeexPay.
        
        Args:
            provider_code: Code du fournisseur (ex: 'mtn', 'orange', 'wave')
            amount: Montant à payer
            currency: Devise (XOF, EUR, USD)
            recipient_phone: Numéro de téléphone du destinataire
            recipient_email: Email du destinataire
            recipient_account: Compte bancaire du destinataire
            description: Description du paiement
            metadata: Métadonnées additionnelles
            customer_id: ID client
            order_id: ID de commande
            callback_url: URL de callback (webhook)
        
        Returns:
            Réponse d'initiation de paiement
        """
        payload = {
            'shop_id': self.shop_id,
            'provider': provider_code,
            'amount': str(amount),
            'currency': currency,
            'customer_id': customer_id or str(timezone.now().timestamp()),
            'order_id': order_id,
        }
        
        # Ajouter les détails du destinataire selon le fournisseur
        if recipient_phone:
            payload['recipient_phone'] = recipient_phone
        if recipient_email:
            payload['recipient_email'] = recipient_email
        if recipient_account:
            payload['recipient_account'] = recipient_account
        if description:
            payload['description'] = description
        if metadata:
            payload['metadata'] = metadata
        if callback_url:
            payload['callback_url'] = callback_url
        
        return self._make_request('POST', self.INITIATE_ENDPOINT, data=payload)
    
    def get_payment_status(self, transaction_id: str) -> Dict:
        """
        Récupérer le statut d'un paiement.
        
        Args:
            transaction_id: ID de transaction FeexPay
        
        Returns:
            Détails du paiement et son statut
        """
        endpoint = self.STATUS_ENDPOINT.format(transaction_id=transaction_id)
        return self._make_request('GET', endpoint)
    
    def cancel_payment(self, transaction_id: str, reason: str = None) -> Dict:
        """
        Annuler un paiement.
        
        Args:
            transaction_id: ID de transaction FeexPay
            reason: Raison de l'annulation
        
        Returns:
            Réponse d'annulation
        """
        data = {'reason': reason} if reason else {}
        endpoint = f"/api/v1/payments/{transaction_id}/cancel"
        return self._make_request('POST', endpoint, data=data)
    
    def refund_payment(
        self,
        transaction_id: str,
        amount: Decimal = None,
        reason: str = None
    ) -> Dict:
        """
        Rembourser un paiement (partiellement ou totalement).
        
        Args:
            transaction_id: ID de transaction FeexPay
            amount: Montant à rembourser (montant total si non spécifié)
            reason: Raison du remboursement
        
        Returns:
            Réponse de remboursement
        """
        data = {}
        if amount:
            data['amount'] = str(amount)
        if reason:
            data['reason'] = reason
        
        endpoint = f"/api/v1/payments/{transaction_id}/refund"
        return self._make_request('POST', endpoint, data=data)
    
    # ============= PROVIDERS =============
    
    def get_providers(self, country_code: str = None, active_only: bool = True) -> List[Dict]:
        """
        Récupérer la liste des fournisseurs FeexPay disponibles.
        
        Args:
            country_code: Filtrer par code pays (SN, CI, TG, etc.)
            active_only: Retourner uniquement les fournisseurs actifs
        
        Returns:
            Liste des fournisseurs disponibles
        """
        params = {}
        if country_code:
            params['country'] = country_code
        if active_only:
            params['active'] = 'true'
        
        cache_key = f"feexpay_providers_{country_code}_{active_only}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        result = self._make_request('GET', self.PROVIDERS_ENDPOINT, params=params)
        providers = result.get('providers', [])
        
        # Cacher 1 heure
        cache.set(cache_key, providers, 3600)
        
        return providers
    
    def get_provider_details(self, provider_code: str) -> Dict:
        """
        Récupérer les détails d'un fournisseur spécifique.
        
        Args:
            provider_code: Code du fournisseur
        
        Returns:
            Détails du fournisseur
        """
        providers = self.get_providers()
        for provider in providers:
            if provider.get('code') == provider_code:
                return provider
        
        raise FeexPayValidationError(f"Fournisseur non trouvé: {provider_code}")
    
    def validate_provider_amount(
        self,
        provider_code: str,
        amount: Decimal,
        currency: str = 'XOF'
    ) -> bool:
        """
        Valider si le montant est acceptable pour un fournisseur.
        
        Args:
            provider_code: Code du fournisseur
            amount: Montant
            currency: Devise
        
        Returns:
            True si valide
        
        Raises:
            FeexPayValidationError: Si invalide
        """
        provider = self.get_provider_details(provider_code)
        
        min_amount = Decimal(str(provider.get('min_amount', 0)))
        max_amount = Decimal(str(provider.get('max_amount', float('inf'))))
        
        if amount < min_amount:
            raise FeexPayValidationError(
                f"Montant minimum pour {provider_code}: {min_amount}"
            )
        if amount > max_amount:
            raise FeexPayValidationError(
                f"Montant maximum pour {provider_code}: {max_amount}"
            )
        
        return True
    
    # ============= TAUX DE CHANGE =============
    
    def get_exchange_rates(self, base_currency: str = 'XOF') -> Dict[str, Decimal]:
        """
        Récupérer les taux de change.
        
        Args:
            base_currency: Devise de référence
        
        Returns:
            Dictionnaire des taux par devise
        """
        cache_key = f"feexpay_rates_{base_currency}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        params = {'base': base_currency}
        result = self._make_request('GET', self.EXCHANGE_RATE_ENDPOINT, params=params)
        
        rates = result.get('rates', {})
        # Convertir en Decimal
        rates = {k: Decimal(str(v)) for k, v in rates.items()}
        
        # Cacher 1 heure
        cache.set(cache_key, rates, 3600)
        
        return rates
    
    def convert_amount(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Convertir un montant d'une devise à une autre.
        
        Args:
            amount: Montant
            from_currency: Devise source
            to_currency: Devise cible
        
        Returns:
            Montant converti
        """
        if from_currency == to_currency:
            return amount
        
        rates = self.get_exchange_rates(base_currency=from_currency)
        
        if to_currency not in rates:
            raise FeexPayValidationError(
                f"Taux non disponible: {from_currency} → {to_currency}"
            )
        
        return amount * rates[to_currency]
    
    # ============= WEBHOOKS =============
    
    def validate_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str = None
    ) -> bool:
        """
        Valider la signature d'un webhook FeexPay.
        
        Args:
            payload: Données du webhook (JSON string)
            signature: Signature HMAC SHA256
            secret: Clé secrète (de settings par défaut)
        
        Returns:
            True si valide
        
        Raises:
            FeexPayException: Si invalid
        """
        secret = secret or self.webhook_secret
        
        if not secret:
            raise FeexPayException('FEEXPAY_WEBHOOK_SECRET non configurée')
        
        # Créer la signature attendue
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode() if isinstance(payload, str) else payload,
            hashlib.sha256
        ).hexdigest()
        
        # Comparer (timing-safe)
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(f"Signature webhook invalide: {signature}")
            raise FeexPayException("Signature de webhook invalide")
        
        return True
    
    def parse_webhook_payload(self, payload: Dict) -> Dict:
        """
        Parser et valider une charge utile de webhook.
        
        Args:
            payload: Données du webhook
        
        Returns:
            Payload validé
        """
        required_fields = ['event', 'transaction_id', 'status', 'timestamp']
        
        for field in required_fields:
            if field not in payload:
                raise FeexPayValidationError(f"Champ manquant: {field}")
        
        return {
            'event': payload.get('event'),
            'transaction_id': payload.get('transaction_id'),
            'status': payload.get('status'),
            'timestamp': payload.get('timestamp'),
            'amount': Decimal(str(payload.get('amount', 0))),
            'currency': payload.get('currency'),
            'metadata': payload.get('metadata', {}),
            'error_code': payload.get('error_code'),
            'error_message': payload.get('error_message'),
        }
    
    # ============= UTILITAIRES =============
    
    def health_check(self) -> bool:
        """
        Vérifier la santé de l'API FeexPay.
        
        Returns:
            True si l'API est accessible
        """
        try:
            # Essayer de récupérer les fournisseurs (requête simple)
            self.get_providers(active_only=False)
            logger.info("FeexPay API: OK")
            return True
        except Exception as e:
            logger.error(f"FeexPay API: ERREUR - {str(e)}")
            return False
    
    def get_supported_providers(self) -> List[str]:
        """
        Obtenir la liste des codes de fournisseurs supportés.
        
        Returns:
            Liste des codes de fournisseurs
        """
        return [
            'mtn', 'moov', 'orange', 'celtiis', 'coris', 'wave', 'free',
            'bank_transfer', 'mastercard', 'visa', 'amex', 'unionpay',
            'orange_ci', 'moov_togo', 'mtn_senegal', 'wave_senegal'
        ]
    
    def get_countries_for_provider(self, provider_code: str) -> List[str]:
        """
        Récupérer les pays supportés pour un fournisseur.
        
        Args:
            provider_code: Code du fournisseur
        
        Returns:
            Liste des codes pays
        """
        provider_countries = {
            'mtn': ['SN', 'CI', 'TG', 'BJ', 'CM'],
            'moov': ['SN', 'TG', 'BJ'],
            'orange': ['SN', 'CI'],
            'celtiis': ['SN'],
            'coris': ['BJ'],
            'wave': ['SN'],
            'free': ['SN'],
            'bank_transfer': ['SN', 'CI', 'TG', 'BJ', 'GW', 'CM', 'GA'],
            'mastercard': ['SN', 'CI', 'TG', 'BJ', 'GW', 'CM', 'GA'],
            'visa': ['SN', 'CI', 'TG', 'BJ', 'GW', 'CM', 'GA'],
            'amex': ['SN', 'CI'],
            'unionpay': ['CI', 'TG'],
            'orange_ci': ['CI'],
            'moov_togo': ['TG'],
            'mtn_senegal': ['SN'],
            'wave_senegal': ['SN'],
        }
        return provider_countries.get(provider_code, [])
    
    def close(self):
        """Fermer la session HTTP."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Singleton pour utilisation facile
_client = None


def get_feexpay_client() -> FeexPayClient:
    """
    Obtenir le client FeexPay singleton.
    
    Returns:
        Instance FeexPayClient
    """
    global _client
    if _client is None:
        _client = FeexPayClient()
    return _client
