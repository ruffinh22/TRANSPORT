#!/usr/bin/env python
"""
Test détaillé FeexPay Payout API
Affiche toutes les informations de la requête et réponse
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
sys.path.append('/var/www/html/rhumo1/backend')
django.setup()

import requests
import json
from apps.payments.feexpay_payout import FeexPayPayout

def test_feexpay_detailed():
    print("🔍 TEST DÉTAILLÉ FEEXPAY PAYOUT API")
    print("=" * 50)
    
    # Initialiser FeexPay
    feexpay = FeexPayPayout()
    
    print(f"🏪 Shop ID: {feexpay.shop_id}")
    print(f"🔑 API Key: {feexpay.api_key[:20]}...")
    print(f"🌐 Base URL: {feexpay.base_url}")
    print()
    
    # Données de test avec format exactement comme la documentation
    test_data = {
        "shop": feexpay.shop_id,
        "amount": "200",
        "phoneNumber": "2290196092246",  # Format doc: 2290166000000
        "network": "MTN",
        "motif": "Test FeexPay RUMO RUSH"
    }
    
    print("📤 DONNÉES ENVOYÉES (format documentation):")
    print(json.dumps(test_data, indent=2))
    print()
    
    # Testons aussi le format minimal
    minimal_data = {
        "shop": feexpay.shop_id,
        "amount": "100", 
        "phoneNumber": "2290196092246",
        "network": "MTN",
        "motif": "Test"
    }
    
    print("📤 DONNÉES MINIMALES:")
    print(json.dumps(minimal_data, indent=2))
    print()
    
    print("📨 HEADERS:")
    print(json.dumps(feexpay.headers, indent=2))
    print()
    
    # Test de l'endpoint
    endpoint = "/api/payouts/public/transfer/global"
    url = f"{feexpay.base_url}{endpoint}"
    
    print(f"🎯 URL: {url}")
    print()
    
    try:
        print("🚀 ENVOI DE LA REQUÊTE...")
        
        # Test 1: Avec données complètes
        print("\n=== TEST 1: Données complètes ===")
        response = requests.post(
            url,
            headers=feexpay.headers,
            json=test_data,
            timeout=30
        )
        
        print(f"📊 STATUS CODE: {response.status_code}")
        print(f"📝 RESPONSE: {response.text}")
        
        # Test 2: Avec données minimales si le premier échoue
        if response.status_code != 200:
            print("\n=== TEST 2: Données minimales ===")
            response2 = requests.post(
                url,
                headers=feexpay.headers,
                json=minimal_data,
                timeout=30
            )
            print(f"📊 STATUS CODE 2: {response2.status_code}")
            print(f"📝 RESPONSE 2: {response2.text}")
        
        print(f"\n📄 RESPONSE HEADERS:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        
        # Analyser la réponse
        if response.status_code == 403:
            print("❌ ERREUR 403: IP non autorisée")
            print("💡 Solution: Ajouter 154.66.133.50 dans FeexPay Dashboard")
        elif response.status_code == 401:
            print("❌ ERREUR 401: Problème d'authentification")
            print("💡 Vérifier l'API Key dans FeexPay Dashboard")
        elif response.status_code == 400:
            print("❌ ERREUR 400: Données invalides")
            print("💡 Vérifier le format des données")
        elif response.status_code in [200, 201]:
            print("✅ SUCCÈS: Retrait initié avec succès !")
        else:
            print(f"❓ ERREUR {response.status_code}: Erreur inconnue")
            
    except requests.RequestException as e:
        print(f"💥 ERREUR RÉSEAU: {e}")

if __name__ == "__main__":
    test_feexpay_detailed()