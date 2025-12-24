# apps/games/management/commands/update_game_types.py

from django.core.management.base import BaseCommand
from apps.games.models import GameType
from decimal import Decimal

class Command(BaseCommand):
    help = 'Update existing game types with enhanced data for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if game type already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Updating game types with enhanced data...'))

        # Enhanced game types data for production
        enhanced_game_types = [
            {
                'name': 'chess',
                'display_name': 'Échecs Classiques',
                'description': 'Le roi des jeux de stratégie. Affrontez vos adversaires dans des parties d\'échecs passionnantes avec des enjeux réels. Développez votre stratégie, anticipez les coups de votre adversaire et visez l\'échec et mat!',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 30,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('100000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/chess'
            },
            {
                'name': 'checkers',
                'display_name': 'Dames Internationales',
                'description': 'Jeu de dames traditionnel revisité. Capturez les pièces adverses et transformez vos pions en dames pour dominer le plateau. Stratégie pure et réflexion tactique garanties!',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 25,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('75000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/checkers'
            },
            {
                'name': 'ludo',
                'display_name': 'Ludo Africain',
                'description': 'Le jeu de plateau familial le plus populaire d\'Afrique! Lancez les dés, déplacez vos pions et soyez le premier à faire rentrer tous vos pions à la maison. Fun et suspense garantis!',
                'category': 'board',
                'min_players': 2,
                'max_players': 4,
                'estimated_duration': 20,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('50000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/ludo'
            },
            {
                'name': 'cards',
                'display_name': 'Rami Express',
                'description': 'Jeu de cartes rapide et excitant! Formez des suites et des brelans pour vous débarrasser de toutes vos cartes avant vos adversaires. Mélange parfait de chance et de stratégie.',
                'category': 'cards',
                'min_players': 2,
                'max_players': 6,
                'estimated_duration': 15,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('60000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/rami'
            },
            {
                'name': 'dominos',
                'display_name': 'Dominos Africains',
                'description': 'Jeu de dominos traditionnel avec une touche africaine. Placez vos dominos stratégiquement en respectant les valeurs identiques. Simple à apprendre, difficile à maîtriser!',
                'category': 'board',
                'min_players': 2,
                'max_players': 4,
                'estimated_duration': 18,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('40000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/dominos'
            },
            {
                'name': 'dame_de_pique',
                'display_name': 'Dame de Pique',
                'description': 'Jeu de cartes stratégique où il faut éviter certaines cartes tout en collectionnant les bonnes. Anticipation et bluff sont vos meilleurs atouts!',
                'category': 'cards',
                'min_players': 3,
                'max_players': 6,
                'estimated_duration': 25,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('45000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/dame-de-pique'
            },
            
        ]

        updated_count = 0
        created_count = 0

        for game_data in enhanced_game_types:
            try:
                game_type = GameType.objects.get(name=game_data['name'])
                
                if options['force']:
                    # Update existing
                    for field, value in game_data.items():
                        setattr(game_type, field, value)
                    game_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Updated: {game_type.display_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Exists: {game_type.display_name} (use --force to update)')
                    )
                    
            except GameType.DoesNotExist:
                # Create new game type
                game_type = GameType.objects.create(**game_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'🆕 Created: {game_type.display_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Summary:\n'
                f'  - Created: {created_count} game types\n'
                f'  - Updated: {updated_count} game types\n'
                f'  - Total in database: {GameType.objects.count()}'
            )
        )

        # Display all active game types
        self.stdout.write(self.style.SUCCESS('\n🎮 Active Game Types:'))
        for game_type in GameType.objects.filter(is_active=True).order_by('category', 'display_name'):
            category_icon = {
                'strategy': '🧠',
                'cards': '🃏', 
                'board': '🎲',
                'puzzle': '🧩'
            }
            
            icon = category_icon.get(game_type.category, '🎮')
            self.stdout.write(
                f'  {icon} {game_type.display_name} '
                f'({game_type.min_players}-{game_type.max_players} joueurs) '
                f'- {game_type.min_bet_fcfa}-{game_type.max_bet_fcfa} FCFA'
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Game types update completed!'))