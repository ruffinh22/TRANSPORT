#!/usr/bin/env python
"""
Test simple de l'authentification JWT et confirmation FeexPay
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TRANSACTION_ID = "252b9473-e206-4931-aedd-90d7c4f99daa"

def test_jwt_auth_and_feexpay():
    print("🧪 TEST JWT + FEEXPAY")
    print("=" * 50)
    
    # 1. Connexion JWT
    print("🔐 ÉTAPE 1: Connexion JWT")
    print("-" * 30)
    
    login_data = {
        "username": "hounsounon07@gmail.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login/",
            json=login_data,
            timeout=30
        )
        
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Connexion réussie!")
            print(f"Réponse: {json.dumps(token_data, indent=2)}")
            
            access_token = token_data.get('access')
            if access_token:
                print(f"🔑 Token obtenu: {access_token[:20]}...")
                
                # 2. Test confirmation FeexPay
                print(f"\n📡 ÉTAPE 2: Confirmation FeexPay")
                print("-" * 40)
                
                feexpay_data = {
                    "transaction_id": TRANSACTION_ID,
                    "feexpay_reference": TRANSACTION_ID,
                    "amount": 100,
                    "status": "completed"
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
                
                confirm_response = requests.post(
                    f"{BASE_URL}/api/v1/payments/deposits/confirm/",
                    json=feexpay_data,
                    headers=headers,
                    timeout=30
                )
                
                print(f"Confirm Status: {confirm_response.status_code}")
                
                try:
                    confirm_data = confirm_response.json()
                    print(f"📄 Réponse:")
                    print(json.dumps(confirm_data, indent=2, ensure_ascii=False))
                except:
                    print(f"📄 Réponse (texte): {confirm_response.text}")
                
                if confirm_response.status_code == 200:
                    print(f"🎉 SUCCÈS! Confirmation FeexPay réussie!")
                else:
                    print(f"❌ ERREUR Confirmation: {confirm_response.status_code}")
                    
            else:
                print(f"❌ Pas de token access dans la réponse")
                
        else:
            print(f"❌ Échec connexion: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erreur: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Erreur (texte): {response.text}")
                
    except Exception as e:
        print(f"🚨 Exception: {e}")

if __name__ == "__main__":
    test_jwt_auth_and_feexpay()