"""
FeexPay Payout Service - Système de retrait vers Mobile Money
Permet d'effectuer des retraits/virements depuis RUMO RUSH vers les comptes Mobile Money
"""
import requests
import logging
import json
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class FeexPayPayout:
    """
    Service de retrait FeexPay pour envoyer de l'argent vers Mobile Money
    """
    
    def __init__(self):
        """Initialiser avec les clés API de retrait FeexPay"""
        self.shop_id = os.getenv('FEEXPAY_SHOP_ID', '67d68239474b2509dcde6d10')
        self.api_key = os.getenv('FEEXPAY_API_KEY', 'fp_live_aGlCTGNJWE85QUFOeC0xNzMxNTExODkwLTE3MzE1MTgzNzg=')
        self.base_url = "https://api.feexpay.me"
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"💸 FeexPay Payout Service initialisé - Shop: {self.shop_id}")
    
    def send_money(self, amount: Decimal, phone_number: str, network: str, 
                   recipient_name: str, description: str = "Retrait RUMO RUSH", 
                   custom_id: str = None, force_production: bool = False) -> Dict[str, Any]:
        """
        Envoyer de l'argent vers un compte Mobile Money
        
        Args:
            amount: Montant à envoyer (FCFA)
            phone_number: Numéro du destinataire
            network: Réseau (MTN, ORANGE, MOOV, etc.)
            recipient_name: Nom du destinataire
            description: Description du transfert
            custom_id: ID personnalisé pour le suivi
        
        Returns:
            Dict contenant la réponse FeexPay
        """
        try:
            # Données du transfert
            transfer_data = {
                "shop_id": self.shop_id,
                "amount": str(int(amount)),  # Convertir en entier
                "phone_number": phone_number,
                "network": network.upper(),
                "recipient_name": recipient_name,
                "description": description,
                "custom_id": custom_id or f"payout_{phone_number}_{int(amount)}",
                "currency": "XOF"  # Franc CFA
            }
            
            logger.info(f"💸 Tentative retrait FeexPay: {json.dumps(transfer_data, indent=2)}")
            
            # Vérifier si on force le mode production
            if force_production:
                logger.warning(f"🚀 MODE PRODUCTION FORCÉ - Transfert réel FeexPay")
            elif settings.DEBUG:
                # En mode debug, simuler le transfert
                logger.info(f"🧪 Mode DEBUG - Simulation du retrait")
                return self.simulate_payout(amount, phone_number, network, recipient_name, description, custom_id)
            
            # Endpoint officiel FeexPay Payout selon documentation
            # https://api.feexpay.me/api/payouts/public/transfer/global
            endpoint = "/api/payouts/public/transfer/global"
            
            # Format exact selon la documentation FeexPay Payout API
            payout_data = {
                "phoneNumber": phone_number,  # 10 chiffres avec préfixe 01
                "amount": int(amount),  # Montant en entier (minimum 50)
                "shop": self.shop_id,  # ID boutique depuis menu Développeur
                "network": network.upper(),  # MTN ou MOOV
                "motif": description  # Description sans caractères spéciaux
            }
            
            logger.info(f"💸 Appel API FeexPay Payout: {json.dumps(payout_data, indent=2)}")
            logger.info(f"🔑 Headers: Authorization: Bearer {self.api_key[:20]}...")
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payout_data,
                timeout=30
            )
            
            logger.info(f"📤 Réponse FeexPay Payout: Status {response.status_code}")
            logger.info(f"📤 Body: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                # Réponse contient: phoneNumber, amount, reference, status
                return {
                    'success': True,
                    'data': result,
                    'transfer_id': result.get('reference'),  # Référence transaction FeexPay
                    'status': result.get('status', 'pending').lower(),  # SUCCESSFUL/FAILED/PENDING
                    'message': 'Transfert initié avec succès',
                    'phone_number': result.get('phoneNumber'),
                    'amount': result.get('amount')
                }
            else:
                error_message = response.text
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', error_message)
                except:
                    pass
                
                return {
                    'success': False,
                    'error': f"Erreur HTTP {response.status_code}",
                    'message': error_message,
                    'data': None
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur requête FeexPay Payout: {e}")
            return {
                'success': False,
                'error': 'Erreur de connexion',
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"❌ Erreur FeexPay Payout: {e}")
            return {
                'success': False,
                'error': 'Erreur interne',
                'message': str(e),
                'data': None
            }
    
    def check_transfer_status(self, reference: str) -> Dict[str, Any]:
        """
        Vérifier le statut d'un transfert (payout)
        
        Selon la doc FeexPay: GET https://api.feexpay.me/api/payouts/status/public/{reference}
        
        Args:
            reference: Référence du payout FeexPay
        
        Returns:
            Dict contenant le statut du transfert
        """
        try:
            # Endpoint officiel pour vérifier le status d'un payout
            endpoint = f"/api/payouts/status/public/{reference}"
            
            logger.info(f"🔍 Vérification status payout: {reference}")
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=15
            )
            
            logger.info(f"📤 Status payout {reference}: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                # Réponse contient: reference, amount, phoneNumber, status
                return {
                    'success': True,
                    'status': result.get('status', '').lower(),  # SUCCESSFUL/FAILED/PENDING
                    'reference': result.get('reference'),
                    'amount': result.get('amount'),
                    'phone_number': result.get('phoneNumber'),
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur HTTP {response.status_code}",
                    'message': response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification statut: {e}")
            return {
                'success': False,
                'error': 'Erreur vérification',
                'message': str(e)
            }
    
    def get_supported_networks(self) -> list:
        """
        Retourner la liste des réseaux supportés pour les retraits
        
        Returns:
            List des réseaux supportés
        """
        return [
            {'code': 'MTN', 'name': 'MTN Mobile Money', 'country': 'multi'},
            {'code': 'ORANGE', 'name': 'Orange Money', 'country': 'multi'},
            {'code': 'MOOV', 'name': 'Moov Money', 'country': 'multi'},
            {'code': 'WAVE', 'name': 'Wave', 'country': 'multi'},
            {'code': 'CELTIIS', 'name': 'Celtiis', 'country': 'BJ'},
            {'code': 'TOGOCOM', 'name': 'Togocom', 'country': 'TG'},
            {'code': 'FREE', 'name': 'Free Money', 'country': 'SN'}
        ]
    
    def simulate_payout(self, amount: Decimal, phone_number: str, network: str, 
                       recipient_name: str, description: str = "Retrait RUMO RUSH", 
                       custom_id: str = None) -> Dict[str, Any]:
        """
        Simuler un retrait pour les tests (mode développement)
        
        Args:
            amount: Montant à envoyer
            phone_number: Numéro du destinataire  
            network: Réseau Mobile Money
            recipient_name: Nom du destinataire
            description: Description
            custom_id: ID personnalisé
        
        Returns:
            Dict simulant une réponse FeexPay réussie
        """
        import uuid
        import time
        
        # Simuler un délai
        time.sleep(2)
        
        # Générer une référence simulée
        fake_transfer_id = str(uuid.uuid4())
        
        return {
            'success': True,
            'data': {
                'id': fake_transfer_id,
                'transfer_id': fake_transfer_id,
                'status': 'completed',
                'amount': str(int(amount)),
                'phone_number': phone_number,
                'network': network,
                'recipient_name': recipient_name,
                'description': description,
                'created_at': '2025-11-18T10:00:00Z',
                'completed_at': '2025-11-18T10:02:00Z',
                'simulation': True
            },
            'transfer_id': fake_transfer_id,
            'status': 'completed',
            'message': f'Simulation: {amount} FCFA envoyés vers {phone_number} ({network})'
        }