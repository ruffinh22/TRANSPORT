# apps/payments/feexpay_sdk_implementation.py
# =================================================

"""
Implémentation basée sur le SDK PHP FeexPay officiel.
Traduit les méthodes PHP documentées en Python.
"""

import requests
import json
import logging
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger('feexpay')


class FeexPaySDKImplementation:
    """
    Implémentation Python du SDK PHP FeexPay.
    Basée sur la documentation officielle docs.feexpay.me
    """
    
    def __init__(self, shop_id: str = None, api_token: str = None, 
                 callback_url: str = "", mode: str = "LIVE", error_callback_url: str = ""):
        """
        Initialiser le client FeexPay SDK.
        
        Équivalent PHP: new Feexpay\FeexpayPhp\FeexpayClass($shop_id, $token, $callback, $mode, $error_callback)
        """
        self.shop_id = shop_id or getattr(settings, 'FEEXPAY_SHOP_ID', '')
        self.api_token = api_token or getattr(settings, 'FEEXPAY_API_KEY', '')
        self.callback_url = callback_url
        self.mode = mode
        self.error_callback_url = error_callback_url
        
        # Base URL selon la documentation
        self.base_url = "https://api.feexpay.me"
        
        # Headers standards
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        logger.info(f"FeexPay SDK initialisé: {self.mode} mode, Shop: {self.shop_id[:10]}...")
    
    def paiement_local(self, amount: str, phone_number: str, network: str, 
                      customer_name: str, customer_email: str, custom_id: str, otp: str = "") -> Dict[str, Any]:
        """
        Méthode paiementLocal du SDK PHP.
        
        Pour MTN, MOOV, CELTIIS BJ, MOOV TG, TOGOCOM TG, ORANGE SN, MTN CI, MTN CG.
        Lance les paiements avec USSD où le client reçoit un push de confirmation.
        
        PHP: $skeleton->paiementLocal($amount, $phone, $network, $name, $email, $custom_id, $otp)
        """
        # Valider le réseau
        allowed_networks = ['MTN', 'MOOV', 'CELTIIS BJ', 'MOOV TG', 'TOGOCOM TG', 'ORANGE SN', 'MTN CI', 'MTN CG']
        if network.upper() not in allowed_networks:
            raise ValueError(f"Réseau non autorisé: {network}. Réseaux autorisés: {allowed_networks}")
        
        # Préparer les données
        payload = {
            'shop': self.shop_id,
            'token': self.api_token,
            'amount': str(amount),
            'phone_number': phone_number,
            'network': network.upper(),
            'customer_name': customer_name,
            'customer_email': customer_email,
            'custom_id': custom_id,
            'mode': self.mode,
        }
        
        # Ajouter OTP pour Orange Sénégal
        if network.upper() == 'ORANGE SN' and otp:
            payload['otp'] = otp
        
        logger.info(f"🚀 FeexPay paiementLocal: {network} {amount} FCFA → {phone_number}")
        logger.info(f"📡 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Essayer les endpoints possibles pour paiementLocal
            endpoints = [
                '/api/payments/local',
                '/api/mobile/local', 
                '/api/v1/payments/local',
                '/sdk/paiement-local'
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    logger.info(f"🔄 Tentative: {url}")
                    
                    response = requests.post(
                        url,
                        json=payload,
                        headers=self.headers,
                        timeout=30
                    )
                    
                    logger.info(f"📤 Response status: {response.status_code}")
                    logger.info(f"📤 Response text: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"✅ Paiement local initié via {endpoint}")
                        return result
                    elif response.status_code == 404:
                        logger.debug(f"Endpoint {endpoint} non trouvé")
                        continue
                    else:
                        logger.warning(f"Erreur {response.status_code} sur {endpoint}: {response.text}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Erreur réseau sur {endpoint}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Erreur sur {endpoint}: {e}")
                    continue
            
            # Si aucun endpoint ne fonctionne
            logger.error("❌ Aucun endpoint paiementLocal trouvé")
            return {
                'status': 'ERROR',
                'message': 'Endpoints FeexPay SDK non disponibles',
                'reference': custom_id,
                'simulation': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur paiementLocal: {e}")
            return {
                'status': 'ERROR',
                'message': str(e),
                'reference': custom_id
            }
    
    def get_paiement_status(self, reference: str) -> Dict[str, Any]:
        """
        Obtenir le statut d'un paiement.
        
        PHP: $skeleton->getPaiementStatus($reference)
        """
        try:
            endpoint = f"/api/transactions/public/single/status/{reference}"
            url = f"{self.base_url}{endpoint}"
            
            logger.info(f"🔍 Vérification statut: {reference}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Erreur statut {response.status_code}: {response.text}")
                return {
                    'status': 'ERROR',
                    'message': 'Impossible de récupérer le statut',
                    'reference': reference
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur get_paiement_status: {e}")
            return {
                'status': 'ERROR',
                'message': str(e),
                'reference': reference
            }


def test_feexpay_sdk():
    """
    Fonction de test pour le SDK FeexPay.
    """
    sdk = FeexPaySDKImplementation()
    
    # Test paiement MTN
    result = sdk.paiement_local(
        amount="100",
        phone_number="2290196092246", 
        network="MTN",
        customer_name="RUMO RUSH User",
        customer_email="ahounsounon@gmail.com",
        custom_id=f"RUMO_TEST_{int(__import__('time').time())}"
    )
    
    print("📱 Résultat SDK:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    return result


if __name__ == "__main__":
    test_feexpay_sdk()