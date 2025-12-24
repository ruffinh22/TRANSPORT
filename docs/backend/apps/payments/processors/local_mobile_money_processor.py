# apps/payments/processors/local_mobile_money_processor.py
# ========================================================

"""
Processeur Mobile Money local pour tests réels.
Simule les API des opérateurs mais avec gestion des erreurs réaliste.
"""

import random
import string
import time
from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from . import (
    BasePaymentProcessor, PaymentProcessorError,
    PaymentProcessorConfigurationError, PaymentProcessingError,
    PaymentResponse, WebhookResponse, handle_processor_errors
)


class LocalMobileMoneyProcessor(BasePaymentProcessor):
    """
    Processeur Mobile Money local pour tests réels.
    
    Simule le comportement des vrais opérateurs :
    - Orange Money
    - MTN Mobile Money  
    - Moov Money
    
    En mode développement, simule les réponses des API.
    En mode production, utiliserait les vraies API.
    """
    
    OPERATOR_CONFIGS = {
        'orange': {
            'name': 'Orange Money',
            'prefixes': ['07', '67', '+22507', '+22567'],
            'countries': ['CI', 'SN', 'ML', 'BF'],
            'currency': 'XOF',
            'min_amount': 500,
            'max_amount': 500000,
            'fees': {'percentage': 1.5, 'fixed': 0}
        },
        'mtn': {
            'name': 'MTN Mobile Money',
            'prefixes': ['05', '65', '+22505', '+22565'],
            'countries': ['CI', 'GH', 'UG', 'ZM'],
            'currency': 'XOF',
            'min_amount': 500,
            'max_amount': 500000,
            'fees': {'percentage': 1.5, 'fixed': 0}
        },
        'moov': {
            'name': 'Moov Money',
            'prefixes': ['01', '61', '+22501', '+22561'],
            'countries': ['CI', 'BF', 'TG', 'BJ'],
            'currency': 'XOF',
            'min_amount': 500,
            'max_amount': 500000,
            'fees': {'percentage': 1.5, 'fixed': 0}
        }
    }
    
    def __init__(self):
        """Initialiser le processeur."""
        super().__init__()
        self.test_mode = getattr(settings, 'DEBUG', True)
        
    def validate_configuration(self):
        """Valider la configuration (toujours OK en mode local)."""
        return True
    
    def _detect_operator_from_phone(self, phone_number):
        """Détecter l'opérateur depuis le numéro de téléphone."""
        if not phone_number:
            return None
            
        # Nettoyer le numéro
        clean_phone = phone_number.replace(' ', '').replace('-', '')
        
        for operator, config in self.OPERATOR_CONFIGS.items():
            for prefix in config['prefixes']:
                if clean_phone.startswith(prefix):
                    return operator
                    
        return None
    
    def _detect_operator_from_method(self, payment_method_name):
        """Détecter l'opérateur depuis le nom de la méthode."""
        method_lower = payment_method_name.lower()
        
        if 'orange' in method_lower:
            return 'orange'
        elif 'mtn' in method_lower:
            return 'mtn' 
        elif 'moov' in method_lower:
            return 'moov'
            
        return None
    
    def _generate_transaction_id(self, operator):
        """Générer un ID de transaction réaliste."""
        prefix = {
            'orange': 'OM',
            'mtn': 'MTN',
            'moov': 'MV'
        }.get(operator, 'MM')
        
        # Générer un ID aléatoire de 12 caractères
        random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        return f"{prefix}_{random_id}_{int(time.time())}"
    
    @handle_processor_errors
    def create_payment(self, payment_data):
        """Créer un paiement Mobile Money."""
        try:
            # Détecter l'opérateur
            operator = self._detect_operator_from_method(
                payment_data.get('payment_method_name', '')
            )
            
            if not operator:
                operator = self._detect_operator_from_phone(
                    payment_data.get('phone_number', '')
                )
                
            if not operator:
                operator = 'orange'  # Fallback
            
            # Validation du montant
            amount = payment_data['amount']
            operator_config = self.OPERATOR_CONFIGS[operator]
            
            if amount < operator_config['min_amount']:
                raise PaymentProcessingError(
                    f"Montant minimum pour {operator_config['name']}: "
                    f"{operator_config['min_amount']} {payment_data['currency']}"
                )
                
            if amount > operator_config['max_amount']:
                raise PaymentProcessingError(
                    f"Montant maximum pour {operator_config['name']}: "
                    f"{operator_config['max_amount']} {payment_data['currency']}"
                )
            
            # Valider le numéro de téléphone
            phone = payment_data.get('phone_number', '')
            if not phone:
                raise PaymentProcessingError("Numéro de téléphone requis")
                
            # Générer la transaction
            transaction_id = self._generate_transaction_id(operator)
            
            # En mode test, simuler différents scénarios
            if self.test_mode:
                return self._simulate_payment_response(
                    operator, transaction_id, payment_data
                )
            else:
                return self._create_real_payment(
                    operator, transaction_id, payment_data
                )
                
        except PaymentProcessingError:
            raise
        except Exception as e:
            raise PaymentProcessingError(f"Erreur inattendue: {str(e)}")
    
    def _simulate_payment_response(self, operator, transaction_id, payment_data):
        """Simuler une réponse de paiement réaliste."""
        operator_config = self.OPERATOR_CONFIGS[operator]
        
        # 90% de succès en simulation
        success_rate = 0.9
        is_success = random.random() < success_rate
        
        if is_success:
            status = 'pending'  # En attente de confirmation utilisateur
            message = f"Demande de paiement envoyée à {payment_data.get('phone_number')}. Confirmez sur votre téléphone."
        else:
            status = 'failed'
            message = f"Échec de l'initiation du paiement {operator_config['name']}"
        
        return PaymentResponse.success_response(
            message,
            {
                'payment_id': transaction_id,
                'external_reference': transaction_id,
                'status': status,
                'operator': operator,
                'operator_name': operator_config['name'],
                'amount': payment_data['amount'],
                'currency': payment_data['currency'],
                'phone_number': payment_data.get('phone_number'),
                'created_at': timezone.now(),
                'instructions': self._get_user_instructions(operator, payment_data),
                'estimated_processing_time': '2-5 minutes'
            }
        ).to_dict()
    
    def _create_real_payment(self, operator, transaction_id, payment_data):
        """Créer un vrai paiement (TODO: implémenter les vraies API)."""
        # TODO: Implémenter les vraies API des opérateurs
        # Pour l'instant, on simule
        return self._simulate_payment_response(operator, transaction_id, payment_data)
    
    def _get_user_instructions(self, operator, payment_data):
        """Obtenir les instructions pour l'utilisateur."""
        operator_config = self.OPERATOR_CONFIGS[operator]
        phone = payment_data.get('phone_number', '')
        amount = payment_data['amount']
        currency = payment_data['currency']
        
        instructions = {
            'orange': f"1. Vous recevrez un SMS de Orange Money\n2. Composez le code USSD affiché\n3. Confirmez le paiement de {amount} {currency}\n4. Entrez votre code PIN Orange Money",
            'mtn': f"1. Vous recevrez une notification MTN MoMo\n2. Ouvrez l'application MTN MoMo ou composez *133#\n3. Confirmez le paiement de {amount} {currency}\n4. Entrez votre code PIN MTN",
            'moov': f"1. Vous recevrez un SMS de Moov Money\n2. Composez *155# ou utilisez l'app Moov Money\n3. Confirmez le paiement de {amount} {currency}\n4. Entrez votre code PIN Moov"
        }
        
        return instructions.get(operator, "Suivez les instructions de votre opérateur mobile.")
    
    @handle_processor_errors
    def verify_payment(self, payment_reference):
        """Vérifier le statut d'un paiement."""
        # En mode test, simuler une progression réaliste
        if self.test_mode:
            # 70% de chance que le paiement soit confirmé
            if random.random() < 0.7:
                status = 'completed'
                message = "Paiement confirmé avec succès"
            else:
                status = 'pending'
                message = "En attente de confirmation utilisateur"
        else:
            # TODO: Appeler la vraie API de vérification
            status = 'pending'
            message = "Vérification du statut..."
        
        return PaymentResponse.success_response(
            message,
            {
                'payment_reference': payment_reference,
                'status': status,
                'verified_at': timezone.now()
            }
        ).to_dict()
    
    @handle_processor_errors
    def process_payment(self, payment_data):
        """Traiter/confirmer un paiement."""
        # Mobile Money ne nécessite pas de confirmation manuelle
        raise PaymentProcessingError("Traitement automatique via Mobile Money")
    
    @handle_processor_errors
    def cancel_payment(self, payment_reference):
        """Annuler un paiement."""
        # La plupart des opérateurs ne permettent pas l'annulation
        raise PaymentProcessingError("Annulation non supportée par Mobile Money")
    
    def process_webhook(self, webhook_data, signature=None):
        """Traiter un webhook de l'opérateur."""
        # TODO: Implémenter le traitement des webhooks des opérateurs
        return WebhookResponse.success_response(
            "Webhook traité",
            {'processed_at': timezone.now()}
        ).to_dict()