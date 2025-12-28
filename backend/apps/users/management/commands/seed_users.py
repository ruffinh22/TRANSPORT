"""Management command pour créer les utilisateurs par défaut"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.common.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Créer les utilisateurs par défaut pour chaque rôle'

    def handle(self, *args, **options):
        """Créer les utilisateurs par défaut"""
        
        # Données des utilisateurs à créer
        users_data = [
            {
                'email': 'admin@transport.bf',
                'first_name': 'Admin',
                'last_name': 'TKF',
                'password': 'Admin@2025!',
                'roles': ['ADMIN'],
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
                'phone': '+226 25 30 00 00',
            },
            {
                'email': 'comptable@transport.bf',
                'first_name': 'Comptable',
                'last_name': 'TKF',
                'password': 'Comptable@2025!',
                'roles': ['COMPTABLE'],
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'phone': '+226 25 30 00 01',
            },
            {
                'email': 'guichetier@transport.bf',
                'first_name': 'Guichetier',
                'last_name': 'TKF',
                'password': 'Guichetier@2025!',
                'roles': ['GUICHETIER'],
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'phone': '+226 25 30 00 02',
            },
            {
                'email': 'chauffeur@transport.bf',
                'first_name': 'Chauffeur',
                'last_name': 'TKF',
                'password': 'Chauffeur@2025!',
                'roles': ['CHAUFFEUR'],
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'phone': '+226 25 30 00 03',
            },
            {
                'email': 'controleur@transport.bf',
                'first_name': 'Contrôleur',
                'last_name': 'TKF',
                'password': 'Controleur@2025!',
                'roles': ['CONTROLEUR'],
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'phone': '+226 25 30 00 04',
            },
            {
                'email': 'gestionnaire@transport.bf',
                'first_name': 'Gestionnaire',
                'last_name': 'Courrier',
                'password': 'Gestionnaire@2025!',
                'roles': ['GESTIONNAIRE_COURRIER'],
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'phone': '+226 25 30 00 05',
            },
            {
                'email': 'client@transport.bf',
                'first_name': 'Client',
                'last_name': 'TKF',
                'password': 'Client@2025!',
                'roles': ['CLIENT'],
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'phone': '+226 25 30 00 06',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in users_data:
            email = user_data['email']
            roles = user_data.pop('roles')
            
            # Créer ou récupérer l'utilisateur
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'phone': user_data.get('phone'),
                    'is_active': user_data['is_active'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                }
            )
            
            # Définir le mot de passe
            user.set_password(user_data['password'])
            user.save()
            
            # Assigner les rôles
            for role_code in roles:
                try:
                    role = Role.objects.get(code=role_code)
                    user.roles.add(role)
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Rôle {role_code} non trouvé pour {email}'
                        )
                    )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Utilisateur créé: {email} ({", ".join(roles)})'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Utilisateur mis à jour: {email} ({", ".join(roles)})'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {created_count} utilisateur(s) créé(s), {updated_count} mis à jour'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  IMPORTANT: Changez les mots de passe par défaut en production!'
            )
        )
