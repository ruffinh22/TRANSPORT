#!/usr/bin/env python
"""
Test simple du nouveau système FeexPay
1. Créer un utilisateur de test
2. Envoyer des données FeexPay pour créer une transaction
3. Tester la synchronisation
"""

import requests
import json
import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

BASE_URL = "http://localhost:8000"

def create_test_user():
    """Créer un utilisateur de test"""
    username = "testfeexpay"
    email = "testfeexpay@example.com" 
    password = "testpass123"
    
    # Supprimer s'il existe
    User.objects.filter(username=username).delete()
    User.objects.filter(email=email).delete()
    
    # Créer nouvel utilisateur
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=True
    )
    
    print(f"✅ Utilisateur créé: {username} / {password}")
    return user, password

def get_jwt_token(username, password):
    """Obtenir un token JWT"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/login/", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access')
        if access_token:
            print(f"✅ Token JWT obtenu")
            return access_token
    
    print(f"❌ Échec login: {response.status_code} - {response.text}")
    return None

def test_feexpay_deposit(token):
    """Tester la création de dépôt FeexPay"""
    
    # Données simulant un retour FeexPay
    feexpay_data = {
        "feexpay_reference": "FEEX-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
        "amount": 1500,
        "status": "completed"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n📡 TEST CRÉATION DÉPÔT FEEXPAY:")
    print("-" * 40)
    print(f"Données: {json.dumps(feexpay_data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/payments/deposits/confirm/",
        json=feexpay_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Réponse:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print(f"🎉 SUCCÈS! Transaction créée")
            transaction_data = response_data.get('transaction', {})
            return transaction_data.get('id'), feexpay_data['feexpay_reference']
        else:
            print(f"❌ ERREUR: {response.status_code}")
            return None, None
            
    except json.JSONDecodeError:
        print(f"Réponse (texte): {response.text}")
        return None, None

def test_feexpay_sync(token, transaction_id, feexpay_reference):
    """Tester la synchronisation"""
    
    sync_data = {
        "transaction_id": transaction_id,
        "feexpay_reference": feexpay_reference
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n🔄 TEST SYNCHRONISATION:")
    print("-" * 30)
    print(f"Données: {json.dumps(sync_data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/payments/deposits/sync/",
        json=sync_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Réponse:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print(f"🎉 SYNC RÉUSSIE!")
        else:
            print(f"❌ ERREUR SYNC: {response.status_code}")
            
    except json.JSONDecodeError:
        print(f"Réponse (texte): {response.text}")

def main():
    print("🧪 TEST COMPLET NOUVEAU SYSTÈME FEEXPAY")
    print("=" * 60)
    
    # 1. Créer utilisateur de test
    user, password = create_test_user()
    
    # 2. Obtenir token JWT
    token = get_jwt_token(user.username, password)
    if not token:
        print("❌ Impossible d'obtenir un token")
        return
    
    # 3. Tester création dépôt FeexPay
    transaction_id, feexpay_reference = test_feexpay_deposit(token)
    if transaction_id:
        # 4. Tester synchronisation
        test_feexpay_sync(token, transaction_id, feexpay_reference)
    
    print(f"\n✅ Test terminé!")

if __name__ == "__main__":
    main()