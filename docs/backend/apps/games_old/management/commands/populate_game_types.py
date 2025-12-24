# apps/games/management/commands/populate_game_types.py
# Create this file: apps/games/management/commands/populate_game_types.py

from django.core.management.base import BaseCommand
from apps.games.models import GameType
import uuid

class Command(BaseCommand):
    help = 'Populate the database with default game types'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing game types before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Deleting existing game types...'))
            GameType.objects.all().delete()

        # Game types data matching your frontend config
        game_types_data = [
            {
                'name': 'Échecs',
                'display_name': 'Échecs',
                'description': 'Jeu de stratégie classique',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 30,
                'min_bet_fcfa': 500,
                'max_bet_fcfa': 100000,
                'is_active': True,
            },
            {
                'name': 'Dames',
                'display_name': 'Dames',
                'description': 'Jeu de dames traditionnel',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 25,
                'min_bet_fcfa': 500,
                'max_bet_fcfa': 100000,
                'is_active': True,
            },
            {
                'name': 'Ludo',
                'display_name': 'Ludo',
                'description': 'Jeu de plateau familial',
                'category': 'board',
                'min_players': 2,
                'max_players': 4,
                'estimated_duration': 20,
                'min_bet_fcfa': 500,
                'max_bet_fcfa': 50000,
                'is_active': True,
            },
            {
                'name': 'Cartes',
                'display_name': 'Cartes',
                'description': 'Jeux de cartes variés',
                'category': 'cards',
                'min_players': 2,
                'max_players': 8,
                'estimated_duration': 15,
                'min_bet_fcfa': 500,
                'max_bet_fcfa': 75000,
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for game_data in game_types_data:
            game_type, created = GameType.objects.get_or_create(
                name=game_data['name'],
                defaults={
                    'display_name': game_data['display_name'],
                    'description': game_data['description'],
                    'category': game_data['category'],
                    'min_players': game_data['min_players'],
                    'max_players': game_data['max_players'],
                    'estimated_duration': game_data['estimated_duration'],
                    'min_bet_fcfa': game_data['min_bet_fcfa'],
                    'max_bet_fcfa': game_data['max_bet_fcfa'],
                    'is_active': game_data['is_active'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created: {game_type.name} ({game_type.id})')
                )
            else:
                # Update existing game type
                for field, value in game_data.items():
                    if field != 'name':  # Don't update the name field
                        setattr(game_type, field, value)
                game_type.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Updated: {game_type.name} ({game_type.id})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎮 Summary:\n'
                f'  - Created: {created_count} game types\n'
                f'  - Updated: {updated_count} game types\n'
                f'  - Total: {GameType.objects.count()} game types in database'
            )
        )

        # Display all game types
        self.stdout.write(self.style.SUCCESS('\n📋 All game types in database:'))
        for game_type in GameType.objects.all():
            status = "🟢 Active" if game_type.is_active else "🔴 Inactive"
            self.stdout.write(
                f'  - {game_type.icon} {game_type.name} '
                f'({game_type.min_players}-{game_type.max_players} players) '
                f'[{game_type.id}] {status}'
            )

        self.stdout.write(
            self.style.SUCCESS('\n✅ Game types population completed!')
        )
