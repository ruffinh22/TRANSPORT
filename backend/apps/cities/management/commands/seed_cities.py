"""Commande pour créer des villes de seed"""
from django.core.management.base import BaseCommand
from apps.cities.models import City


class Command(BaseCommand):
    help = 'Crée des villes de seed pour l\'application TKF'

    def handle(self, *args, **options):
        cities_data = [
            {
                'name': 'Ouagadougou',
                'code': 'OUA',
                'address': 'Capital nationale',
                'region': 'Kadiogo',
                'population': 2500000,
                'latitude': 12.3714,
                'longitude': -1.5197,
                'city_name': 'Ouagadougou',
                'postal_code': '01',
                'country': 'Burkina Faso',
                'is_hub': True,
                'has_terminal': True,
                'has_parking': True,
                'description': 'Capitale du Burkina Faso - Hub principal TKF'
            },
            {
                'name': 'Bobo-Dioulasso',
                'code': 'BOB',
                'address': 'Deuxième ville',
                'region': 'Hauts-Bassins',
                'population': 750000,
                'latitude': 11.1769,
                'longitude': -4.2956,
                'city_name': 'Bobo-Dioulasso',
                'postal_code': '01',
                'country': 'Burkina Faso',
                'is_hub': True,
                'has_terminal': True,
                'has_parking': True,
                'description': 'Deuxième hub principal TKF - Région ouest'
            },
            {
                'name': 'Koudougou',
                'code': 'KOU',
                'address': 'Région ouest',
                'region': 'Hauts-Bassins',
                'population': 150000,
                'latitude': 12.2667,
                'longitude': -5.0333,
                'city_name': 'Koudougou',
                'postal_code': '02',
                'country': 'Burkina Faso',
                'is_hub': False,
                'has_terminal': True,
                'has_parking': False,
                'description': 'Terminal de l\'ouest'
            },
            {
                'name': 'Tamale',
                'code': 'TAM',
                'address': 'Région nord',
                'region': 'Nord',
                'population': 400000,
                'latitude': 9.4077,
                'longitude': -0.8917,
                'city_name': 'Tamale',
                'postal_code': '03',
                'country': 'Burkina Faso',
                'is_hub': False,
                'has_terminal': True,
                'has_parking': True,
                'description': 'Terminal du nord'
            },
            {
                'name': 'Soum',
                'code': 'SOU',
                'address': 'Région nord-est',
                'region': 'Sahel',
                'population': 80000,
                'latitude': 12.5,
                'longitude': -1.5,
                'city_name': 'Soum',
                'postal_code': '04',
                'country': 'Burkina Faso',
                'is_hub': False,
                'has_terminal': True,
                'has_parking': False,
                'description': 'Terminal du Sahel'
            },
            {
                'name': 'Gaoua',
                'code': 'GAO',
                'address': 'Région sud-ouest',
                'region': 'Cascades',
                'population': 50000,
                'latitude': 10.3333,
                'longitude': -5.8333,
                'city_name': 'Gaoua',
                'postal_code': '05',
                'country': 'Burkina Faso',
                'is_hub': False,
                'has_terminal': False,
                'has_parking': False,
                'description': 'Point de passage - Cascades'
            },
            {
                'name': 'Pô',
                'code': 'POA',
                'address': 'Région sud',
                'region': 'Sud-Ouest',
                'population': 30000,
                'latitude': 10.95,
                'longitude': -3.5667,
                'city_name': 'Pô',
                'postal_code': '06',
                'country': 'Burkina Faso',
                'is_hub': False,
                'has_terminal': False,
                'has_parking': False,
                'description': 'Point de passage - Sud'
            },
            {
                'name': 'Garango',
                'code': 'GAR',
                'address': 'Région est',
                'region': 'Est',
                'population': 40000,
                'latitude': 12.1,
                'longitude': 0.5,
                'city_name': 'Garango',
                'postal_code': '07',
                'country': 'Burkina Faso',
                'is_hub': False,
                'has_terminal': False,
                'has_parking': False,
                'description': 'Point de passage - Est'
            },
        ]

        created_count = 0
        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                code=city_data['code'],
                defaults=city_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Créée: {city.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Existe déjà: {city.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {created_count} villes créées avec succès!')
        )
