#!/usr/bin/env python
"""
Test de confirmation FeexPay avec authentification complète
"""

import requests
import json
import os
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Configuration
BASE_URL = "http://localhost:8000"
TRANSACTION_ID = "252b9473-e206-4931-aedd-90d7c4f99daa"

# Données FeexPay pour le test
feexpay_data = {
    "transaction_id": TRANSACTION_ID,
    "feexpay_reference": TRANSACTION_ID,
    "amount": 100,
    "status": "completed"
}

def get_or_create_token(username="hounsounon07@gmail.com"):
    """Obtenir l'utilisateur et faire une connexion directe"""
    try:
        user = User.objects.get(username=username)
        print(f"👤 Utilisateur trouvé: {user.username} ({user.email})")
        print(f"🔐 Tentative de connexion avec les credentials...")
        
        # Essayer avec le mot de passe par défaut
        return login_with_credentials(username, "password123"), user
        
    except User.DoesNotExist:
        print(f"❌ Utilisateur {username} non trouvé")
        return None, None

def login_with_credentials(username="hounsounon07@gmail.com", password="password123"):
    """Alternative: se connecter avec credentials"""
    print(f"🔐 Tentative de connexion avec: {username}")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login/",
            json=login_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access') or data.get('token') or data.get('access_token')
            print(f"✅ Connexion réussie, token: {token[:10]}..." if token else "❌ Pas de token dans la réponse")
            return token
        else:
            print(f"❌ Échec connexion: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"🚨 Erreur connexion: {e}")
        return None

def test_deposit_confirmation():
    """Tester la confirmation de dépôt FeexPay avec authentification"""
    print("🧪 TEST DE CONFIRMATION FEEXPAY AVEC AUTHENTIFICATION")
    print("="*80)
    
    # 1. Obtenir un token
    print("🔑 ÉTAPE 1: Authentification")
    print("-"*50)
    
    token, user = get_or_create_token()
    
    if not token:
        print("❌ ÉCHEC: Impossible d'obtenir un token d'authentification")
        return
    
    # 2. Tester la confirmation
    print("\n📡 ÉTAPE 2: Test de confirmation")
    print("-"*50)
    
    url = f"{BASE_URL}/api/v1/payments/deposits/confirm/"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    
    print(f"📡 URL: {url}")
    print(f"🔑 Token: {token[:20]}...")
    print(f"📋 Données: {json.dumps(feexpay_data, indent=2)}")
    print("-"*60)
    
    try:
        response = requests.post(
            url,
            json=feexpay_data,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️ Response Time: {response.elapsed.total_seconds():.3f}s")
        print("-"*60)
        
        try:
            response_data = response.json()
            print(f"✅ Response JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(f"📄 Response Text:")
            print(response.text)
        
        print("-"*60)
        
        if response.status_code == 200:
            print("🎉 SUCCESS! Confirmation FeexPay réussie!")
        elif response.status_code == 401:
            print("🔐 ERROR: Problème d'authentification")
        elif response.status_code == 400:
            print("📋 ERROR: Données invalides")
        elif response.status_code == 404:
            print("🔍 ERROR: Transaction non trouvée")
        else:
            print(f"❌ ERROR! Code {response.status_code}")
            
    except requests.RequestException as e:
        print(f"🚨 ERREUR RÉSEAU: {e}")
    
    except Exception as e:
        print(f"🚨 ERREUR INATTENDUE: {e}")

def test_transaction_ownership():
    """Vérifier que la transaction appartient bien à l'utilisateur connecté"""
    print("\n🔍 ÉTAPE 3: Vérification de la transaction")
    print("-"*50)
    
    from apps.payments.models import Transaction
    
    try:
        transaction = Transaction.objects.get(id=TRANSACTION_ID)
        print(f"✅ Transaction trouvée:")
        print(f"   ID: {transaction.id}")
        print(f"   Propriétaire: {transaction.user.username} ({transaction.user.email})")
        print(f"   Status actuel: {transaction.status}")
        print(f"   Amount: {transaction.amount} {transaction.currency}")
        print(f"   Created: {transaction.created_at}")
        
        return transaction
        
    except Transaction.DoesNotExist:
        print(f"❌ Transaction {TRANSACTION_ID} non trouvée dans la DB")
        return None

if __name__ == "__main__":
    test_deposit_confirmation()
    test_transaction_ownership()