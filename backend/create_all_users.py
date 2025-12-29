#!/usr/bin/env python
"""
Script pour créer tous les utilisateurs avec leurs rôles et permissions
Usage: python manage.py shell < create_all_users.py
ou: python create_all_users.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import Role, Permission

User = get_user_model()

# Définir les rôles et leurs permissions
ROLES_CONFIG = {
    'ADMIN': {
        'display_name': 'Administrateur',
        'permissions': [
            'view_trips', 'create_trips', 'edit_trips', 'delete_trips',
            'view_tickets', 'create_tickets', 'edit_tickets', 'delete_tickets',
            'view_parcels', 'create_parcels', 'edit_parcels', 'delete_parcels',
            'view_payments', 'create_payments', 'edit_payments', 'delete_payments',
            'view_revenue', 'view_reports', 'create_reports', 'edit_reports',
            'view_employees', 'create_employees', 'edit_employees', 'delete_employees',
            'view_cities', 'create_cities', 'edit_cities', 'delete_cities',
            'manage_users', 'create_users', 'edit_users', 'delete_users',
            'view_settings', 'edit_settings',
        ]
    },
    'COMPTABLE': {
        'display_name': 'Comptable',
        'permissions': [
            'view_payments', 'create_payments', 'edit_payments',
            'view_revenue', 'view_reports', 'create_reports', 'edit_reports',
            'view_employees',
        ]
    },
    'GUICHETIER': {
        'display_name': 'Guichetier',
        'permissions': [
            'view_tickets', 'create_tickets', 'edit_tickets',
            'view_parcels', 'create_parcels', 'edit_parcels',
            'view_trips',
        ]
    },
    'CHAUFFEUR': {
        'display_name': 'Chauffeur',
        'permissions': [
            'view_trips', 'edit_trips',
            'view_tickets',
        ]
    },
    'CONTROLEUR': {
        'display_name': 'Contrôleur',
        'permissions': [
            'view_tickets', 'edit_tickets',
            'view_trips', 'edit_trips',
            'view_employees',
        ]
    },
    'GESTIONNAIRE_COURRIER': {
        'display_name': 'Gestionnaire de Courrier',
        'permissions': [
            'view_parcels', 'create_parcels', 'edit_parcels',
            'view_cities',
        ]
    },
    'CLIENT': {
        'display_name': 'Client',
        'permissions': [
            'view_trips',
            'view_tickets',
            'view_parcels',
        ]
    },
}

# Utilisateurs à créer
USERS_CONFIG = [
    {
        'email': 'admin@transport.local',
        'username': 'admin',
        'first_name': 'Admin',
        'last_name': 'User',
        'password': 'admin@transport.local',
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
        'roles': ['ADMIN'],
    },
    {
        'email': 'comptable@transport.local',
        'username': 'comptable',
        'first_name': 'Comptable',
        'last_name': 'User',
        'password': 'comptable@transport.local',
        'is_active': True,
        'roles': ['COMPTABLE'],
    },
    {
        'email': 'guichetier@transport.local',
        'username': 'guichetier',
        'first_name': 'Guichetier',
        'last_name': 'User',
        'password': 'guichetier@transport.local',
        'is_active': True,
        'roles': ['GUICHETIER'],
    },
    {
        'email': 'chauffeur@transport.local',
        'username': 'chauffeur',
        'first_name': 'Chauffeur',
        'last_name': 'User',
        'password': 'chauffeur@transport.local',
        'is_active': True,
        'roles': ['CHAUFFEUR'],
    },
    {
        'email': 'controleur@transport.local',
        'username': 'controleur',
        'first_name': 'Contrôleur',
        'last_name': 'User',
        'password': 'controleur@transport.local',
        'is_active': True,
        'roles': ['CONTROLEUR'],
    },
    {
        'email': 'gestionnaire@transport.local',
        'username': 'gestionnaire',
        'first_name': 'Gestionnaire',
        'last_name': 'Courrier',
        'password': 'gestionnaire@transport.local',
        'is_active': True,
        'roles': ['GESTIONNAIRE_COURRIER'],
    },
    {
        'email': 'client@transport.local',
        'username': 'client',
        'first_name': 'Client',
        'last_name': 'User',
        'password': 'client@transport.local',
        'is_active': True,
        'roles': ['CLIENT'],
    },
]

def create_permissions():
    """Créer toutes les permissions"""
    print("📝 Création des permissions...")
    
    all_permissions = set()
    for role_config in ROLES_CONFIG.values():
        all_permissions.update(role_config['permissions'])
    
    created_count = 0
    for perm_name in all_permissions:
        perm, created = Permission.objects.get_or_create(
            code=perm_name,
            defaults={'name': perm_name.replace('_', ' ').title()}
        )
        if created:
            created_count += 1
            print(f"  ✅ Permission créée: {perm_name}")
        else:
            print(f"  ⏭️  Permission existante: {perm_name}")
    
    print(f"✓ {created_count} permissions créées\n")
    return Permission.objects.all()

def create_roles(permissions):
    """Créer tous les rôles avec leurs permissions"""
    print("👤 Création des rôles...")
    
    for role_code, role_config in ROLES_CONFIG.items():
        role, created = Role.objects.get_or_create(
            code=role_code,
            defaults={'name': role_config['display_name']}
        )
        
        # Ajouter les permissions au rôle
        perm_objects = Permission.objects.filter(
            code__in=role_config['permissions']
        )
        role.permissions.set(perm_objects)
        
        action = "créé" if created else "mis à jour"
        print(f"  ✅ Rôle {action}: {role_code} ({len(perm_objects)} permissions)")
    
    print(f"✓ {len(ROLES_CONFIG)} rôles créés/mis à jour\n")

def create_users():
    """Créer tous les utilisateurs"""
    print("👥 Création des utilisateurs...")
    
    created_count = 0
    for user_config in USERS_CONFIG:
        # Préparer les données de l'utilisateur
        email = user_config['email']
        username = user_config['username']
        password = user_config.pop('password')
        roles_list = user_config.pop('roles')
        
        # Créer ou récupérer l'utilisateur
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                **{k: v for k, v in user_config.items() if k not in ['roles']}
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"  ✅ Utilisateur créé: {email}")
        else:
            print(f"  ⏭️  Utilisateur existant: {email}")
        
        # Assigner les rôles
        role_objects = Role.objects.filter(code__in=roles_list)
        user.roles.set(role_objects)
        
        if created:
            created_count += 1
    
    print(f"✓ {created_count} utilisateurs créés\n")

def display_summary():
    """Afficher un résumé des utilisateurs créés"""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES UTILISATEURS CRÉÉS")
    print("="*60 + "\n")
    
    for user in User.objects.all().order_by('email'):
        roles = ', '.join([r.name for r in user.roles.all()]) or 'Aucun rôle'
        status = "✅ Actif" if user.is_active else "❌ Inactif"
        print(f"Email: {user.email}")
        print(f"  Nom: {user.first_name} {user.last_name}")
        print(f"  Rôles: {roles}")
        print(f"  Statut: {status}")
        print()

def main():
    print("\n" + "="*60)
    print("🚀 CRÉATION DES UTILISATEURS ET PERMISSIONS")
    print("="*60 + "\n")
    
    try:
        # Créer les permissions
        permissions = create_permissions()
        
        # Créer les rôles
        create_roles(permissions)
        
        # Créer les utilisateurs
        create_users()
        
        # Afficher le résumé
        display_summary()
        
        print("="*60)
        print("✅ TOUS LES UTILISATEURS ONT ÉTÉ CRÉÉS AVEC SUCCÈS!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
