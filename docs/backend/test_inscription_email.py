#!/usr/bin/env python3
"""
Test de l'inscription avec email automatique
"""

import requests
import json
import time

def test_registration_with_fresh_email():
    """Tester l'inscription avec un nouvel email"""
    
    # Générer un email unique
    timestamp = int(time.time())
    test_email = f"test.rumorush.{timestamp}@gmail.com"
    test_username = f"testuser_{timestamp}"
    
    url = "http://127.0.0.1:8000/api/v1/auth/register/"
    
    # Données d'inscription avec email frais
    registration_data = {
        "username": test_username,
        "email": test_email,
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!", 
        "first_name": "Test",
        "last_name": "RumoRush",
        "country": "CI",
        "phone_number": f"+22512345{timestamp % 10000}"
    }
    
    try:
        print("🧪 Test d'Inscription avec Email Automatique")
        print("="*60)
        print(f"📧 Email de test : {test_email}")
        print(f"👤 Username : {test_username}")
        print(f"🌐 URL : {url}")
        print("="*60)
        
        print("\n📤 Envoi de la requête d'inscription...")
        response = requests.post(
            url,
            json=registration_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"\n📊 Réponse HTTP : {response.status_code}")
        
        try:
            response_data = response.json()
            print("📋 Données de réponse :")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(f"📄 Réponse texte : {response.text}")
        
        if response.status_code == 201:
            print("\n✅ INSCRIPTION RÉUSSIE !")
            print(f"📧 Email de vérification envoyé vers : {test_email}")
            print("\n🔍 Vérifiez maintenant :")
            print("1. Votre boîte Gmail principale")
            print("2. Dossier Spam/Indésirables") 
            print("3. Onglets Promotions/Social")
            print(f"4. Recherchez 'RumoRush' ou '{test_email}'")
            print("\n⏱️ L'email devrait arriver dans 1-5 minutes")
            return True
        else:
            print(f"\n❌ Échec de l'inscription : {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur Django")
        print("💡 Assurez-vous que le serveur est démarré :")
        print("   python manage.py runserver 0.0.0.0:8000")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False

def test_with_ahounsounon_email():
    """Test avec l'email ahounsounon mais username unique"""
    
    timestamp = int(time.time())
    test_username = f"ahounsounon_{timestamp}"
    
    url = "http://127.0.0.1:8000/api/v1/auth/register/"
    
    # Utiliser l'email ahounsounon mais username différent
    registration_data = {
        "username": test_username,
        "email": "ahounsounon@gmail.com",  # Email réel
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!", 
        "first_name": "Ahounsounon",
        "last_name": "Test",
        "country": "CI",
        "phone_number": f"+22512345{timestamp % 10000}"
    }
    
    try:
        print("\n🎯 Test avec Email ahounsounon@gmail.com")
        print("="*60)
        print(f"📧 Email : ahounsounon@gmail.com")
        print(f"👤 Username unique : {test_username}")
        print("="*60)
        
        print("\n📤 Envoi de la requête d'inscription...")
        response = requests.post(
            url,
            json=registration_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"\n📊 Réponse HTTP : {response.status_code}")
        
        try:
            response_data = response.json()
            print("📋 Données de réponse :")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(f"📄 Réponse texte : {response.text}")
        
        if response.status_code == 201:
            print("\n✅ INSCRIPTION RÉUSSIE !")
            print("📧 Email de vérification envoyé vers : ahounsounon@gmail.com")
            print("\n🔍 Vérifiez votre boîte Gmail maintenant !")
            return True
        elif response.status_code == 400:
            print("\n⚠️ Erreur de validation (email peut-être déjà utilisé)")
            return False
        else:
            print(f"\n❌ Échec de l'inscription : {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False

def main():
    print("🎮 RumoRush - Test Email d'Inscription Automatique")
    print("="*70)
    
    # Test 1: Email complètement nouveau
    test1_success = test_registration_with_fresh_email()
    
    # Petit délai
    time.sleep(2)
    
    # Test 2: Email ahounsounon avec username unique
    test2_success = test_with_ahounsounon_email()
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"Email unique :        {'✅ OK' if test1_success else '❌ ERREUR'}")
    print(f"Email ahounsounon :   {'✅ OK' if test2_success else '❌ ERREUR'}")
    
    if test1_success or test2_success:
        print("\n🎉 AU MOINS UN TEST RÉUSSI !")
        print("📧 Vérifiez votre boîte Gmail dans les 5 prochaines minutes")
        print("🔍 N'oubliez pas de vérifier spams et onglets")
    else:
        print("\n⚠️ Les tests ont échoué")
        print("💡 Vérifiez que le serveur Django fonctionne")

if __name__ == "__main__":
    main()