#!/usr/bin/env python
"""
Test de l'endpoint /profile/balance/ pour vérifier la synchronisation
"""
import os
import sys
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
sys.path.append('/var/www/html/rhumo1/backend')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_balance_endpoint():
    print("🔍 TEST DE L'ENDPOINT /profile/balance/")
    print("=" * 45)
    
    # Tester pour Ana et Ahounsounon
    usernames = ['ana', 'ahounsounon']
    
    for username in usernames:
        user = User.objects.filter(username=username).first()
        if user:
            print(f"\n👤 Test pour {username}:")
            print(f"   💰 DB Balance: {user.balance_fcfa} FCFA")
            
            # Créer JWT token pour tester l'API
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Tester l'endpoint
            try:
                response = requests.get(
                    'http://localhost:8000/api/v1/profile/balance/',
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=10
                )
                
                print(f"   📡 API Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   📊 API Response: {json.dumps(data, indent=4)}")
                else:
                    print(f"   ❌ API Error: {response.text}")
                    
            except Exception as e:
                print(f"   💥 Erreur: {e}")
        else:
            print(f"❌ Utilisateur {username} non trouvé")

if __name__ == "__main__":
    test_balance_endpoint()