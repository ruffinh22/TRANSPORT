#!/usr/bin/env python
"""
Script pour créer un utilisateur de test et vérifier l'authentification
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

def list_users():
    """Lister tous les utilisateurs"""
    print("👥 UTILISATEURS EXISTANTS:")
    print("-" * 50)
    
    users = User.objects.all()
    for user in users:
        print(f"🙍 ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Is Staff: {user.is_staff}")
        print(f"   Date Joined: {user.date_joined}")
        print(f"   Last Login: {user.last_login}")
        print()

def create_test_user():
    """Créer un utilisateur de test"""
    print("🧪 CRÉATION UTILISATEUR DE TEST:")
    print("-" * 40)
    
    username = "testuser"
    email = "test@example.com"
    password = "testpass123"
    
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=username).exists():
        print(f"⚠️ Utilisateur {username} existe déjà")
        user = User.objects.get(username=username)
    elif User.objects.filter(email=email).exists():
        print(f"⚠️ Email {email} existe déjà")
        user = User.objects.get(email=email)
    else:
        # Créer nouvel utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=True,
            is_verified=True
        )
        print(f"✅ Utilisateur créé: {username}")
    
    print(f"👤 User: {user.username} ({user.email})")
    print(f"🔑 Password: {password}")
    print(f"✅ Active: {user.is_active}")
    
    return user, password

def reset_user_password(username, new_password="testpass123"):
    """Réinitialiser le mot de passe d'un utilisateur"""
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.is_active = True
        user.save()
        print(f"✅ Mot de passe réinitialisé pour {username}")
        print(f"🔑 Nouveau mot de passe: {new_password}")
        return user, new_password
    except User.DoesNotExist:
        print(f"❌ Utilisateur {username} non trouvé")
        return None, None

def main():
    print("="*60)
    print("👤 GESTION UTILISATEURS DE TEST")
    print("="*60)
    
    # 1. Lister les utilisateurs existants
    list_users()
    
    # 2. Vérifier l'utilisateur hounsounon07@gmail.com
    try:
        user = User.objects.get(email="hounsounon07@gmail.com")
        print(f"✅ Utilisateur trouvé: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Active: {user.is_active}")
        print(f"   Staff: {user.is_staff}")
        
        # Réinitialiser le mot de passe
        new_password = "password123"
        user.set_password(new_password)
        user.is_active = True
        user.save()
        print(f"🔑 Mot de passe réinitialisé: {new_password}")
        
        return user, new_password
        
    except User.DoesNotExist:
        print(f"❌ Utilisateur hounsounon07@gmail.com non trouvé")
        
        # Créer un utilisateur de test
        return create_test_user()

if __name__ == "__main__":
    user, password = main()
    
    print("\n" + "="*60)
    print("🧪 DONNÉES POUR TEST:")
    print("="*60)
    print(f"Username: {user.username}")
    print(f"Password: {password}")
    print(f"Email: {user.email}")
    print()
    
    # Afficher les données JSON pour le test
    import json
    test_data = {
        "username": user.username,
        "password": password
    }
    print(f"📋 Données de connexion:")
    print(json.dumps(test_data, indent=2))