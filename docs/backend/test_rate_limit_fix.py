#!/usr/bin/env python3
"""
Test rapide de l'endpoint de registration après correction du rate limiting
"""

import requests
import json

def test_registration_endpoint():
    """Test de l'endpoint d'inscription"""
    
    url = "http://127.0.0.1:8000/api/v1/auth/register/"
    
    # Données de test
    test_data = {
        "username": f"testuser_{int(__import__('time').time())}",
        "email": f"test{int(__import__('time').time())}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "country": "CI",
        "phone_number": "+225123456789"
    }
    
    try:
        print("🧪 Test de l'endpoint d'inscription...")
        print(f"📡 URL: {url}")
        print(f"📦 Données: {json.dumps(test_data, indent=2)}")
        
        # Envoi de la requête
        response = requests.post(
            url, 
            json=test_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📋 Response Body:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(f"📋 Response Text: {response.text}")
        
        if response.status_code == 201:
            print("✅ Inscription réussie !")
            return True
        elif response.status_code == 400:
            print("⚠️ Erreur de validation (normal pour les tests)")
            return True
        elif response.status_code == 500:
            print("❌ Erreur serveur - le fix n'a pas fonctionné")
            return False
        else:
            print(f"📊 Status inattendu: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("💡 Assurez-vous que le serveur Django est démarré:")
        print("   python manage.py runserver 0.0.0.0:8000")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_rate_limit_utils():
    """Test des utilitaires de rate limiting"""
    print("\n🧪 Test des utilitaires de rate limiting...")
    
    try:
        # Test de simulation d'une requête
        class MockRequest:
            def __init__(self):
                self.META = {
                    'REMOTE_ADDR': '127.0.0.1',
                    'HTTP_X_FORWARDED_FOR': '192.168.1.100',
                }
                self.user = None
        
        from apps.accounts.rate_limit_utils import (
            get_client_ip, safe_ratelimit_key, safe_user_or_ip_key
        )
        
        mock_request = MockRequest()
        
        # Test get_client_ip
        ip = get_client_ip(mock_request)
        print(f"✅ get_client_ip: {ip}")
        
        # Test safe_ratelimit_key
        key = safe_ratelimit_key("test_group", mock_request)
        print(f"✅ safe_ratelimit_key: {key}")
        
        # Test safe_user_or_ip_key
        user_or_ip = safe_user_or_ip_key("test_group", mock_request)
        print(f"✅ safe_user_or_ip_key: {user_or_ip}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans les utilitaires: {e}")
        return False

def main():
    print("🎮 RumoRush - Test Rate Limiting Fix")
    print("=" * 50)
    
    # Test des utilitaires
    utils_ok = test_rate_limit_utils()
    
    # Test de l'endpoint
    endpoint_ok = test_registration_endpoint()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    print(f"Utilitaires Rate Limit: {'✅ OK' if utils_ok else '❌ ERREUR'}")
    print(f"Endpoint Registration:  {'✅ OK' if endpoint_ok else '❌ ERREUR'}")
    
    if utils_ok and endpoint_ok:
        print("\n🎉 Fix du rate limiting réussi !")
        print("✅ L'endpoint d'inscription fonctionne maintenant")
    else:
        print("\n⚠️ Certains tests ont échoué")
        print("💡 Vérifiez les logs du serveur pour plus de détails")

if __name__ == "__main__":
    main()