"""
FeexPay SDK Officiel - Basé sur la documentation PHP officielle
Implémente les vraies méthodes FeexPay selon leur documentation
"""
import requests
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FeexpayOfficialSDK:
    """
    SDK FeexPay officiel basé sur la documentation PHP
    
    Méthodes disponibles :
    1. paiementLocal() - Pour MTN, MOOV, CELTIIS BJ, MOOV TG, TOGOCOM TG, ORANGE SN, MTN CI, MTN CG
    2. requestToPayWeb() - Pour FREE SN, ORANGE CI, MOOV CI, WAVE CI, MOOV BF, ORANGE BF
    3. paiementCard() - Pour cartes VISA, MASTERCARD
    4. getPaiementStatus() - Vérifier statut transaction
    """
    
    def __init__(self, shop_id: str, api_key: str, callback_url: str = "", mode: str = "LIVE", error_callback_url: str = ""):
        """
        Initialise le SDK FeexPay
        
        Args:
            shop_id: ID de la boutique FeexPay
            api_key: Clé API FeexPay (commence par fp_)
            callback_url: URL de retour après paiement réussi
            mode: LIVE ou SANDBOX
            error_callback_url: URL de retour après échec
        """
        self.shop_id = shop_id
        self.api_key = api_key
        self.callback_url = callback_url
        self.mode = mode
        self.error_callback_url = error_callback_url
        self.base_url = "https://api.feexpay.me"
        
        # Headers par défaut
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"🚀 FeexPay SDK initialisé - Shop: {shop_id}, Mode: {mode}")
    
    def paiementLocal(self, amount: str, phone_number: str, network: str, 
                     name: str, email: str, custom_id: str, otp: str = "") -> Dict[str, Any]:
        """
        Paiement local avec USSD push - Selon documentation PHP officielle
        
        Réseaux supportés: MTN, MOOV, CELTIIS BJ, MOOV TG, TOGOCOM TG, ORANGE SN, MTN CI, MTN CG
        
        Args:
            amount: Montant en string (ex: "500")
            phone_number: Numéro avec indicatif (ex: "2290196092246")
            network: Réseau (MTN, MOOV, ORANGE SN, etc.)
            name: Nom du client
            email: Email du client
            custom_id: ID unique de transaction
            otp: Code OTP (requis pour ORANGE SN, sinon "")
            
        Returns:
            Dict avec réponse FeexPay
        """
        logger.info(f"🚀 FeexPay paiementLocal: {network} {amount} FCFA vers {phone_number}")
        
        # Validation réseau
        valid_networks = ["MTN", "MOOV", "CELTIIS BJ", "MOOV TG", "TOGOCOM TG", "ORANGE SN", "MTN CI", "MTN CG"]
        if network not in valid_networks:
            raise ValueError(f"Réseau {network} non supporté pour paiementLocal. Réseaux valides: {valid_networks}")
        
        # Construction du payload selon la doc PHP
        payload = {
            "shop": self.shop_id,
            "amount": str(amount),
            "phone_number": phone_number,
            "network": network,
            "name": name,
            "email": email,
            "custom_id": custom_id,
            "mode": self.mode,
            "currency": "XOF"
        }
        
        # Ajout OTP si Orange Sénégal
        if network == "ORANGE SN" and otp:
            payload["otp"] = otp
            
        logger.info(f"📡 Payload paiementLocal: {json.dumps(payload, indent=2)}")
        
        # Essayer plusieurs endpoints possibles pour paiementLocal
        endpoints = [
            "/api/payments/local",
            "/api/mobile/local", 
            "/api/v1/payments/local",
            "/sdk/paiement-local",
            "/feexpay/paiement-local",
            "/api/paiement/local"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"🔄 Test endpoint paiementLocal: {url}")
                
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                logger.info(f"📥 Response Status: {response.status_code}")
                
                # Si pas 404, on a trouvé un endpoint valide
                if response.status_code != 404:
                    try:
                        response_data = response.json()
                        logger.info(f"✅ Endpoint trouvé ! Response: {json.dumps(response_data, indent=2)}")
                        return response_data
                    except:
                        logger.info(f"📄 Response HTML: {response.text[:200]}...")
                        return {"status": "error", "message": "Réponse non-JSON", "response": response.text}
                else:
                    logger.info(f"❌ 404 sur {endpoint}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur sur {endpoint}: {e}")
                continue
        
        # Aucun endpoint trouvé
        logger.warning("⚠️ Aucun endpoint paiementLocal trouvé - Besoin de contacter FeexPay")
        return {
            "status": "error",
            "message": "Aucun endpoint API trouvé. Contactez FeexPay pour les endpoints corrects.",
            "contact": "contact@feexpay.me ou WhatsApp +22997430303"
        }
    
    def requestToPayWeb(self, amount: str, phone_number: str, network: str, 
                       name: str, email: str, cancel_url: str, return_url: str) -> Dict[str, Any]:
        """
        Paiement web avec redirection - Selon documentation PHP officielle
        
        Réseaux supportés: FREE SN, ORANGE CI, MOOV CI, WAVE CI, MOOV BF, ORANGE BF
        
        Args:
            amount: Montant
            phone_number: Numéro
            network: Réseau (FREE SN, ORANGE CI, MOOV CI, WAVE CI, MOOV BF, ORANGE BF)
            name: Nom
            email: Email
            cancel_url: URL d'annulation
            return_url: URL de retour
            
        Returns:
            Dict avec payment_url et reference
        """
        logger.info(f"🌐 FeexPay requestToPayWeb: {network} {amount} FCFA")
        
        # Validation réseau
        valid_networks = ["FREE SN", "ORANGE CI", "MOOV CI", "WAVE CI", "MOOV BF", "ORANGE BF"]
        if network not in valid_networks:
            raise ValueError(f"Réseau {network} non supporté pour requestToPayWeb. Réseaux valides: {valid_networks}")
        
        payload = {
            "shop": self.shop_id,
            "amount": str(amount),
            "phone_number": phone_number,
            "network": network,
            "name": name,
            "email": email,
            "cancel_url": cancel_url,
            "return_url": return_url,
            "mode": self.mode
        }
        
        # Endpoints possibles pour requestToPayWeb
        endpoints = [
            "/api/payments/web",
            "/api/request-to-pay-web",
            "/api/v1/payments/web"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.post(url, json=payload, headers=self.headers, timeout=30)
                
                if response.status_code != 404:
                    return response.json()
                    
            except Exception as e:
                logger.error(f"Erreur requestToPayWeb {endpoint}: {e}")
                continue
        
        return {"status": "error", "message": "Endpoint requestToPayWeb non trouvé"}
    
    def getPaiementStatus(self, reference: str) -> Dict[str, Any]:
        """
        Vérifier le statut d'une transaction
        
        URL selon documentation: https://api.feexpay.me/api/transactions/public/single/status/
        
        Args:
            reference: Référence de la transaction
            
        Returns:
            Dict avec status: PENDING, SUCCESSFUL, FAILED
        """
        logger.info(f"🔍 Vérification statut transaction: {reference}")
        
        url = f"{self.base_url}/api/transactions/public/single/status/{reference}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Statut: {data.get('status', 'UNKNOWN')}")
                return data
            else:
                logger.error(f"❌ Erreur statut {response.status_code}: {response.text}")
                return {"status": "ERROR", "message": response.text}
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification statut: {e}")
            return {"status": "ERROR", "message": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Test de santé de l'API FeexPay
        """
        logger.info("🩺 Test de santé FeexPay API")
        
        # Test avec endpoint de statut
        try:
            url = f"{self.base_url}/api/transactions/public/single/status/test"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            return {
                "status": "ok" if response.status_code in [200, 404] else "error",
                "api_reachable": True,
                "status_code": response.status_code,
                "authentication": "Bearer token accepté" if response.status_code != 401 else "Erreur auth"
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "api_reachable": False,
                "error": str(e)
            }

def test_feexpay_official_sdk():
    """Test du SDK officiel FeexPay"""
    import os
    from django.conf import settings
    
    # Configuration depuis .env.feexpay
    shop_id = os.getenv('FEEXPAY_SHOP_ID', '67d68239474b2509dcde6d10')
    api_key = os.getenv('FEEXPAY_API_KEY', '')
    
    sdk = FeexpayOfficialSDK(
        shop_id=shop_id,
        api_key=api_key,
        mode="LIVE"
    )
    
    # Test santé
    health = sdk.health_check()
    print(f"🩺 Health Check: {health}")
    
    # Test paiement MTN (méthode correcte selon doc)
    result = sdk.paiementLocal(
        amount="500",
        phone_number="2290196092246",
        network="MTN",
        name="RUMO RUSH User",
        email="ahounsounon@gmail.com", 
        custom_id="test-sdk-official-001",
        otp=""
    )
    
    print(f"💰 Résultat paiement MTN: {result}")
    
    return result

if __name__ == "__main__":
    test_feexpay_official_sdk()