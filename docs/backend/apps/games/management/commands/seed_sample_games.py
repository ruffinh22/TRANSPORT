# apps/games/management/commands/seed_sample_games.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from apps.games.models import GameType, Game

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample games for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of games to create (default: 20)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing games before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('🗑️  Deleting existing games...'))
            Game.objects.all().delete()

        count = options['count']
        
        # Get available users and game types
        users = list(User.objects.all())
        game_types = list(GameType.objects.all())
        
        if len(users) < 2:
            self.stdout.write(self.style.ERROR('❌ Need at least 2 users to create games'))
            return
            
        if len(game_types) == 0:
            self.stdout.write(self.style.ERROR('❌ Need at least 1 game type to create games'))
            return

        self.stdout.write(self.style.SUCCESS(f'🎮 Creating {count} sample games...'))

        # Game status distribution
        status_weights = {
            'finished': 0.6,  # 60% finished games
            'playing': 0.2,   # 20% active games
            'waiting': 0.15,  # 15% waiting for players
            'cancelled': 0.05 # 5% cancelled games
        }

        # Bet amounts (FCFA)
        bet_amounts = [500, 1000, 1500, 2000, 2500, 5000, 7500, 10000, 15000, 25000]

        created_games = []
        
        for i in range(count):
            # Random game configuration
            game_type = random.choice(game_types)
            player1 = random.choice(users)
            
            # Determine status
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]
            
            # Configure players based on status
            if status == 'waiting':
                player2 = None
                current_player = None
                winner = None
            else:
                # Ensure player2 is different from player1
                available_players = [u for u in users if u != player1]
                player2 = random.choice(available_players) if available_players else None
                
                if status == 'playing':
                    current_player = random.choice([player1, player2]) if player2 else player1
                    winner = None
                elif status == 'finished':
                    current_player = None
                    winner = random.choice([player1, player2]) if player2 else player1
                else:  # cancelled
                    current_player = None
                    winner = None

            # Random bet amount within game type limits
            min_bet = float(game_type.min_bet_fcfa)
            max_bet = min(float(game_type.max_bet_fcfa), max(bet_amounts))
            valid_bets = [b for b in bet_amounts if min_bet <= b <= max_bet]
            bet_amount = Decimal(str(random.choice(valid_bets) if valid_bets else min_bet))

            # Random creation time (last 30 days)
            hours_ago = random.uniform(0.5, 24 * 30)
            created_at = timezone.now() - timedelta(hours=hours_ago)

            # Create the game
            game = Game.objects.create(
                game_type=game_type,
                player1=player1,
                player2=player2,
                bet_amount=bet_amount,
                status=status,
                current_player=current_player,
                winner=winner,
                created_at=created_at
            )

            # Set additional timestamps based on status
            if status in ['playing', 'finished', 'cancelled']:
                # Game was started
                start_delay = random.uniform(0.1, 2)  # Started within 2 hours of creation
                game.started_at = created_at + timedelta(hours=start_delay)
                
                if status in ['finished', 'cancelled']:
                    # Game was finished/cancelled
                    game_duration = random.uniform(0.2, 2)  # Game lasted 0.2 to 2 hours
                    game.finished_at = game.started_at + timedelta(hours=game_duration)

                game.save()

            # Add some move history for active/finished games
            if status in ['playing', 'finished'] and player2:
                moves_count = random.randint(5, 30)
                for move_num in range(moves_count):
                    current_move_player = player1 if move_num % 2 == 0 else player2
                    move_time = game.started_at + timedelta(minutes=move_num * 2)
                    
                    game.move_history.append({
                        'player': current_move_player.username,
                        'move': self.generate_sample_move(game_type.name),
                        'timestamp': move_time.isoformat(),
                        'turn_number': move_num + 1
                    })
                
                game.save(update_fields=['move_history'])

            created_games.append(game)
            
            status_icon = {
                'waiting': '⏳',
                'playing': '🎮',
                'finished': '✅',
                'cancelled': '❌'
            }
            
            self.stdout.write(
                f'{status_icon.get(status, "🎯")} Game {i+1}: {game.room_code} - '
                f'{game_type.display_name} - {bet_amount} FCFA - {status}'
            )

        # Summary
        status_counts = {}
        for game in created_games:
            status_counts[game.status] = status_counts.get(game.status, 0) + 1

        self.stdout.write(self.style.SUCCESS(f'\n🎯 Created {len(created_games)} games:'))
        for status, count in status_counts.items():
            self.stdout.write(f'  - {status}: {count}')
        
        self.stdout.write(self.style.SUCCESS('✅ Sample games creation completed!'))

    def generate_sample_move(self, game_type):
        """Generate sample move data based on game type"""
        if game_type == 'chess':
            pieces = ['P', 'R', 'N', 'B', 'Q', 'K']
            files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
            
            return {
                'from': f"{random.choice(files)}{random.choice(ranks)}",
                'to': f"{random.choice(files)}{random.choice(ranks)}",
                'piece': random.choice(pieces)
            }
        
        elif game_type == 'checkers':
            return {
                'from': [random.randint(0, 7), random.randint(0, 7)],
                'to': [random.randint(0, 7), random.randint(0, 7)],
                'capture': random.choice([True, False])
            }
        
        elif game_type == 'ludo':
            return {
                'piece': random.randint(0, 3),
                'dice': random.randint(1, 6),
                'from_position': random.randint(0, 51),
                'to_position': random.randint(0, 51)
            }
        
        elif game_type == 'cards':
            suits = ['hearts', 'diamonds', 'clubs', 'spades']
            values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
            
            return {
                'action': random.choice(['play', 'draw', 'discard']),
                'card': {
                    'suit': random.choice(suits),
                    'value': random.choice(values)
                }
            }
        
        else:
            return {
                'action': 'move',
                'data': random.randint(1, 100)
            }