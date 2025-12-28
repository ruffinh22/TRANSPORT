#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test avec leurs rôles respectifs
Chaque type d'utilisateur accédera au dashboard correspondant à ses permissions
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
django.setup()

from django.contrib.auth import get_user_model
from apps.common.models import Role
from datetime import datetime
import json

User = get_user_model()

# Définition des utilisateurs de test par rôle
TEST_USERS = {
    'ADMIN': {
        'username': 'admin_test',
        'email': 'admin@transport.local',
        'first_name': 'Admin',
        'last_name': 'System',
        'phone': '+237670000001',
        'password': 'AdminPass123!',
        'description': 'Gestion complète du système'
    },
    'COMPTABLE': {
        'username': 'comptable_test',
        'email': 'comptable@transport.local',
        'first_name': 'Jean',
        'last_name': 'Comptable',
        'phone': '+237670000002',
        'password': 'ComptablePass123!',
        'description': 'Gestion financière et rapports'
    },
    'GUICHETIER': {
        'username': 'guichetier_test',
        'email': 'guichetier@transport.local',
        'first_name': 'Marie',
        'last_name': 'Guichetier',
        'phone': '+237670000003',
        'password': 'GuichetierPass123!',
        'description': 'Gestion des colis et tickets'
    },
    'CHAUFFEUR': {
        'username': 'chauffeur_test',
        'email': 'chauffeur@transport.local',
        'first_name': 'Pierre',
        'last_name': 'Chauffeur',
        'phone': '+237670000004',
        'password': 'ChauffeurPass123!',
        'description': 'Gestion des trajets et véhicules'
    },
    'CLIENT': {
        'username': 'client_test',
        'email': 'client@transport.local',
        'first_name': 'Alice',
        'last_name': 'Client',
        'phone': '+237670000005',
        'password': 'ClientPass123!',
        'description': 'Suivi des colis'
    },
    'AGENT_SECURITE': {
        'username': 'securite_test',
        'email': 'securite@transport.local',
        'first_name': 'David',
        'last_name': 'Sécurité',
        'phone': '+237670000006',
        'password': 'SecuritePass123!',
        'description': 'Surveillance et sécurité'
    },
    'SUPERVISEUR': {
        'username': 'superviseur_test',
        'email': 'superviseur@transport.local',
        'first_name': 'Sophie',
        'last_name': 'Superviseur',
        'phone': '+237670000007',
        'password': 'SuperviseurPass123!',
        'description': 'Supervision et monitoring'
    },
    'DIRECTEUR': {
        'username': 'directeur_test',
        'email': 'directeur@transport.local',
        'first_name': 'Robert',
        'last_name': 'Directeur',
        'phone': '+237670000008',
        'password': 'DirecteurPass123!',
        'description': 'Direction générale'
    }
}


def create_test_users():
    """Créer les utilisateurs de test avec leurs rôles"""
    
    print("\n" + "=" * 80)
    print("🔧 CRÉATION DES UTILISATEURS DE TEST AVEC RÔLES")
    print("=" * 80)
    
    created_users = []
    
    for role_name, user_data in TEST_USERS.items():
        try:
            # Vérifier si l'utilisateur existe
            existing = User.objects.filter(
                username=user_data['username']
            ).first()
            
            if existing:
                print(f"\n⚠️  Utilisateur '{user_data['username']}' existe déjà")
                user = existing
                # Réinitialiser le mot de passe
                user.set_password(user_data['password'])
                user.is_active = True
                user.save()
                print(f"🔄 Mot de passe réinitialisé")
            else:
                # Créer le nouvel utilisateur
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone=user_data['phone'],
                    password=user_data['password'],
                    is_active=True,
                    email_verified=True,
                    phone_verified=True
                )
                print(f"\n✅ Utilisateur '{user_data['username']}' créé")
            
            # Assigner le rôle
            try:
                role = Role.objects.get(name=role_name)
                user.roles.clear()  # Supprimer les rôles existants
                user.roles.add(role)
                print(f"🎭 Rôle '{role_name}' assigné")
            except Role.DoesNotExist:
                print(f"⚠️  Rôle '{role_name}' non trouvé dans la base de données")
            
            created_users.append({
                'role': role_name,
                'username': user_data['username'],
                'email': user_data['email'],
                'password': user_data['password'],
                'phone': user_data['phone'],
                'description': user_data['description']
            })
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de '{user_data['username']}': {e}")
    
    return created_users


def display_credentials(users):
    """Afficher les coordonnées de connexion"""
    
    print("\n" + "=" * 80)
    print("📋 COORDONNÉES DE CONNEXION DES UTILISATEURS DE TEST")
    print("=" * 80)
    
    # Affichage formaté par rôle
    for user in users:
        print(f"\n{'─' * 80}")
        print(f"🎭 RÔLE: {user['role']}")
        print(f"{'─' * 80}")
        print(f"👤 Nom d'utilisateur (username): {user['username']}")
        print(f"📧 Email: {user['email']}")
        print(f"🔑 Mot de passe: {user['password']}")
        print(f"📱 Téléphone: {user['phone']}")
        print(f"📝 Description: {user['description']}")
        print(f"\n   🌐 URL de connexion: http://localhost:5173/login")
        print(f"   💼 Dashboard assigné: /{user['role'].lower()}_dashboard")
    
    print("\n" + "=" * 80)
    print("🧪 FLUX DE TEST COMPLET")
    print("=" * 80)
    print(f"""
Pour tester le flux d'authentification complet:

1. 🚀 Démarrer les serveurs:
   - Backend:  cd backend && python manage.py runserver
   - Frontend: cd frontend && npm start

2. 🔑 Connexion:
   - Aller à http://localhost:5173/login
   - Entrer les coordonnées d'un utilisateur de test
   - Cliquer sur "Connexion"

3. 📊 Dashboard:
   - Vérifier que le bon dashboard s'affiche selon le rôle
   - ADMIN: AdminDashboard (gestion des utilisateurs)
   - COMPTABLE: ComptableDashboard (rapports financiers)
   - GUICHETIER: GuichetierDashboard (colis et tickets)
   - CHAUFFEUR: ChauffeurDashboard (trajets et véhicules)
   - Autres: Accès refusé

4. 👤 Profil:
   - Cliquer sur le profil en haut à droite
   - Vérifier les informations utilisateur
   - Tester la modification du profil
   - Tester le changement de mot de passe

5. 🔐 Sécurité:
   - Tester la déconnexion
   - Vérifier que les tokens JWT sont gérés correctement
   - Tester le refresh token automatique
""")
    
    print("=" * 80)


def export_to_json(users, filename='test_users_credentials.json'):
    """Exporter les coordonnées en JSON"""
    
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'created_at': datetime.now().isoformat(),
            'total_users': len(users),
            'users': users
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Coordonnées exportées dans: {filename}")
    return filepath


def main():
    """Fonction principale"""
    
    try:
        # Créer les utilisateurs
        users = create_test_users()
        
        if not users:
            print("\n❌ Aucun utilisateur créé")
            return
        
        # Afficher les coordonnées
        display_credentials(users)
        
        # Exporter en JSON
        export_to_json(users)
        
        print("\n✅ Tous les utilisateurs de test ont été créés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
