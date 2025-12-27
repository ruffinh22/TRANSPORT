"""
Fixtures pour les rôles et permissions système
Exécuter: python manage.py loaddata roles_permissions
"""
import json
from django.core.management.base import BaseCommand
from apps.common.models import Role, Permission


class Command(BaseCommand):
    help = 'Initialiser les rôles et permissions système'
    
    def handle(self, *args, **options):
        """Créer les rôles et permissions"""
        
        # Permissions système
        permissions_data = [
            {
                'code': 'users.view_user',
                'name': 'Voir les utilisateurs',
                'module': 'USERS'
            },
            {
                'code': 'users.manage_users',
                'name': 'Gérer les utilisateurs',
                'module': 'USERS'
            },
            {
                'code': 'vehicles.view_vehicle',
                'name': 'Voir les véhicules',
                'module': 'VEHICLES'
            },
            {
                'code': 'vehicles.manage_vehicles',
                'name': 'Gérer les véhicules',
                'module': 'VEHICLES'
            },
            {
                'code': 'trips.view_trip',
                'name': 'Voir les trajets',
                'module': 'TRIPS'
            },
            {
                'code': 'trips.manage_trips',
                'name': 'Gérer les trajets',
                'module': 'TRIPS'
            },
            {
                'code': 'tickets.view_ticket',
                'name': 'Voir les billets',
                'module': 'TICKETS'
            },
            {
                'code': 'tickets.manage_tickets',
                'name': 'Gérer les billets',
                'module': 'TICKETS'
            },
            {
                'code': 'payments.view_payment',
                'name': 'Voir les paiements',
                'module': 'PAYMENTS'
            },
            {
                'code': 'payments.manage_payments',
                'name': 'Gérer les paiements',
                'module': 'PAYMENTS'
            },
            {
                'code': 'reports.view_report',
                'name': 'Voir les rapports',
                'module': 'REPORTS'
            },
            {
                'code': 'parcels.view_parcel',
                'name': 'Voir les colis',
                'module': 'PARCELS'
            },
            {
                'code': 'parcels.manage_parcels',
                'name': 'Gérer les colis',
                'module': 'PARCELS'
            },
            {
                'code': 'settings.manage_settings',
                'name': 'Gérer les paramètres',
                'module': 'SETTINGS'
            },
        ]
        
        # Créer les permissions
        for perm_data in permissions_data:
            Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'module': perm_data['module'],
                    'is_active': True
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {len(permissions_data)} permissions créées')
        )
        
        # Rôles avec permissions - 7 rôles du cahier des charges TKF
        roles_data = [
            {
                'code': 'SUPER_ADMIN',
                'name': 'Super Administrateur',
                'description': 'Accès complet au système - réservé IT',
                'permissions': [p['code'] for p in permissions_data]
            },
            {
                'code': 'ADMIN',
                'name': 'Administrateur Système',
                'description': 'Gestion administrative complète du système',
                'permissions': [
                    'users.view_user', 'users.manage_users',
                    'vehicles.view_vehicle', 'vehicles.manage_vehicles',
                    'trips.view_trip', 'trips.manage_trips',
                    'tickets.view_ticket', 'tickets.manage_tickets',
                    'payments.view_payment', 'payments.manage_payments',
                    'reports.view_report',
                    'settings.manage_settings'
                ]
            },
            {
                'code': 'MANAGER',
                'name': 'Manager Opérations',
                'description': 'Gestion opérationnelle des trajets et véhicules',
                'permissions': [
                    'vehicles.view_vehicle', 'vehicles.manage_vehicles',
                    'trips.view_trip', 'trips.manage_trips',
                    'tickets.view_ticket',
                    'payments.view_payment',
                    'reports.view_report'
                ]
            },
            {
                'code': 'COMPTABLE',
                'name': 'Comptable / Manager Finance',
                'description': 'Gestion financière, recettes et rapports comptables',
                'permissions': [
                    'payments.view_payment', 'payments.manage_payments',
                    'trips.view_trip',
                    'tickets.view_ticket',
                    'reports.view_report'
                ]
            },
            {
                'code': 'GUICHETIER',
                'name': 'Guichetier',
                'description': 'Vente de tickets, gestion caisses et enregistrement passagers',
                'permissions': [
                    'tickets.view_ticket', 'tickets.manage_tickets',
                    'trips.view_trip',
                    'payments.view_payment', 'payments.manage_payments'
                ]
            },
            {
                'code': 'CHAUFFEUR',
                'name': 'Chauffeur',
                'description': 'Conduite véhicule et suivi des trajets assignés',
                'permissions': [
                    'trips.view_trip',
                    'tickets.view_ticket',
                    'vehicles.view_vehicle'
                ]
            },
            {
                'code': 'CONTROLEUR',
                'name': 'Contrôleur',
                'description': 'Validation des tickets et contrôle des passagers',
                'permissions': [
                    'tickets.view_ticket', 'tickets.manage_tickets',
                    'trips.view_trip',
                    'payments.view_payment'
                ]
            },
            {
                'code': 'GESTIONNAIRE_COURRIER',
                'name': 'Gestionnaire Courrier',
                'description': 'Gestion des colis, suivi et livraison',
                'permissions': [
                    'parcels.view_parcel', 'parcels.manage_parcels',
                    'trips.view_trip',
                    'payments.view_payment'
                ]
            },
        ]
        
        # Créer les rôles
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'permissions': role_data['permissions'],
                    'is_system': True,
                    'is_active': True
                }
            )
            
            if not created:
                # Mettre à jour les permissions
                role.permissions = role_data['permissions']
                role.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {len(roles_data)} rôles créés/mis à jour')
        )
