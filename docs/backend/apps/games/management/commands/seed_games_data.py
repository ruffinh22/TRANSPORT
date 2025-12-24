# apps/games/management/commands/seed_games_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random
import uuid

from apps.games.models import (
    GameType, Game, GameInvitation, GameReport, 
    Tournament, TournamentParticipant, Leaderboard
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with comprehensive games data for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing data before creating new ones',
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='Create only test users',
        )
        parser.add_argument(
            '--games-only',
            action='store_true',
            help='Create only games data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('🗑️  Deleting existing games data...'))
            self.reset_data()

        if options['users_only']:
            self.create_test_users()
        elif options['games_only']:
            self.create_games_data()
        else:
            self.create_test_users()
            self.create_game_types()
            self.create_games_data()
            self.create_tournaments()
            self.create_leaderboards()

        self.stdout.write(self.style.SUCCESS('✅ Games data seeding completed!'))

    def reset_data(self):
        """Reset all games related data"""
        Leaderboard.objects.all().delete()
        TournamentParticipant.objects.all().delete()
        Tournament.objects.all().delete()
        GameReport.objects.all().delete()
        GameInvitation.objects.all().delete()
        Game.objects.all().delete()
        GameType.objects.all().delete()
        
        # Only delete test users (those with username starting with 'player')
        User.objects.filter(username__startswith='player').delete()
        
        self.stdout.write(self.style.SUCCESS('🗑️  Data reset completed'))

    def create_test_users(self):
        """Create test users for games"""
        self.stdout.write(self.style.SUCCESS('👥 Creating test users...'))
        
        test_users_data = [
            {
                'username': 'player1',
                'email': 'player1@rumorush.com',
                'first_name': 'Amadou',
                'last_name': 'Diallo'
            },
            {
                'username': 'player2', 
                'email': 'player2@rumorush.com',
                'first_name': 'Fatou',
                'last_name': 'Sow'
            },
            {
                'username': 'player3',
                'email': 'player3@rumorush.com', 
                'first_name': 'Moussa',
                'last_name': 'Traoré'
            },
            {
                'username': 'player4',
                'email': 'player4@rumorush.com',
                'first_name': 'Aïcha',
                'last_name': 'Koné'
            },
            {
                'username': 'player5',
                'email': 'player5@rumorush.com',
                'first_name': 'Ibrahim',
                'last_name': 'Sangaré'
            },
            {
                'username': 'player6',
                'email': 'player6@rumorush.com',
                'first_name': 'Mariam',
                'last_name': 'Coulibaly'
            },
            {
                'username': 'player7',
                'email': 'player7@rumorush.com',
                'first_name': 'Sekou',
                'last_name': 'Camara'
            },
            {
                'username': 'player8',
                'email': 'player8@rumorush.com',
                'first_name': 'Kadiatou',
                'last_name': 'Bah'
            }
        ]

        created_users = []
        for user_data in test_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                created_users.append(user)
                self.stdout.write(f'✅ Created user: {user.username}')
            else:
                self.stdout.write(f'⚠️  User already exists: {user.username}')

        self.stdout.write(self.style.SUCCESS(f'👥 Created {len(created_users)} test users'))

    def create_game_types(self):
        """Create comprehensive game types"""
        self.stdout.write(self.style.SUCCESS('🎮 Creating game types...'))
        
        game_types_data = [
            {
                'name': 'chess',
                'display_name': 'Échecs',
                'description': 'Jeu de stratégie classique opposant deux armées sur un échiquier 8x8. Développez votre stratégie pour capturer le roi adverse.',
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
                'display_name': 'Dames',
                'description': 'Jeu de dames traditionnel sur plateau 8x8. Capturez toutes les pièces adverses ou bloquez leurs mouvements.',
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
                'display_name': 'Ludo',
                'description': 'Jeu de plateau familial où il faut faire le tour du plateau avec ses 4 pions avant les adversaires.',
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
                'display_name': 'Cartes (Rami)',
                'description': 'Jeu de cartes où il faut former des combinaisons (suites et brelans) pour se débarrasser de toutes ses cartes.',
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
                'display_name': 'Dominos',
                'description': 'Jeu de dominos traditionnel. Placez vos dominos bout à bout en respectant les valeurs identiques.',
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
                'name': 'awale',
                'display_name': 'Awalé',
                'description': 'Jeu traditionnel africain de stratégie. Capturez le maximum de graines en déplaçant celles de vos cases.',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 22,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('80000'),
                'is_active': True,
                'rules_url': 'https://rumorush.com/rules/awale'
            }
        ]

        created_count = 0
        for game_data in game_types_data:
            game_type, created = GameType.objects.get_or_create(
                name=game_data['name'],
                defaults=game_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✅ Created game type: {game_type.display_name}')
            else:
                # Update existing
                for field, value in game_data.items():
                    if field != 'name':
                        setattr(game_type, field, value)
                game_type.save()
                self.stdout.write(f'⚠️  Updated game type: {game_type.display_name}')

        self.stdout.write(self.style.SUCCESS(f'🎮 Game types ready: {GameType.objects.count()} total'))

    def create_games_data(self):
        """Create sample games, invitations, and reports"""
        self.stdout.write(self.style.SUCCESS('🎯 Creating games data...'))
        
        users = list(User.objects.all()[:8])
        game_types = list(GameType.objects.all())
        
        if len(users) < 2:
            self.stdout.write(self.style.ERROR('❌ Need at least 2 users to create games'))
            return
            
        if len(game_types) == 0:
            self.stdout.write(self.style.ERROR('❌ Need at least 1 game type to create games'))
            return

        # Create sample games in different states
        games_data = [
            # Finished games
            {
                'game_type': random.choice(game_types),
                'player1': users[0],
                'player2': users[1],
                'bet_amount': Decimal('1000'),
                'status': 'finished',
                'winner': users[0],
                'created_hours_ago': 24,
                'finished_hours_ago': 23
            },
            {
                'game_type': random.choice(game_types),
                'player1': users[2],
                'player2': users[3], 
                'bet_amount': Decimal('2500'),
                'status': 'finished',
                'winner': users[3],
                'created_hours_ago': 48,
                'finished_hours_ago': 47
            },
            {
                'game_type': random.choice(game_types),
                'player1': users[4],
                'player2': users[5],
                'bet_amount': Decimal('5000'),
                'status': 'finished',
                'winner': users[4],
                'created_hours_ago': 72,
                'finished_hours_ago': 71
            },
            # Active games
            {
                'game_type': random.choice(game_types),
                'player1': users[1],
                'player2': users[2],
                'bet_amount': Decimal('1500'),
                'status': 'playing',
                'current_player': users[1],
                'created_hours_ago': 2,
                'started_hours_ago': 2
            },
            {
                'game_type': random.choice(game_types),
                'player1': users[3],
                'player2': users[4],
                'bet_amount': Decimal('3000'),
                'status': 'playing',
                'current_player': users[4],
                'created_hours_ago': 1,
                'started_hours_ago': 1
            },
            # Waiting games
            {
                'game_type': random.choice(game_types),
                'player1': users[5],
                'player2': None,
                'bet_amount': Decimal('2000'),
                'status': 'waiting',
                'created_hours_ago': 0.5
            },
            {
                'game_type': random.choice(game_types),
                'player1': users[6],
                'player2': None,
                'bet_amount': Decimal('1000'),
                'status': 'waiting',
                'created_hours_ago': 1
            }
        ]

        created_games = []
        for game_data in games_data:
            created_at = timezone.now() - timedelta(hours=game_data['created_hours_ago'])
            
            game = Game.objects.create(
                game_type=game_data['game_type'],
                player1=game_data['player1'],
                player2=game_data['player2'],
                bet_amount=game_data['bet_amount'],
                status=game_data['status'],
                current_player=game_data.get('current_player'),
                winner=game_data.get('winner'),
                created_at=created_at
            )
            
            if game_data['status'] == 'playing' and 'started_hours_ago' in game_data:
                game.started_at = timezone.now() - timedelta(hours=game_data['started_hours_ago'])
                game.save()
                
            if game_data['status'] == 'finished' and 'finished_hours_ago' in game_data:
                game.finished_at = timezone.now() - timedelta(hours=game_data['finished_hours_ago'])
                game.save()
            
            created_games.append(game)
            self.stdout.write(f'✅ Created game: {game.room_code} ({game.status})')

        # Create game invitations
        invitation_count = 0
        for i in range(3):
            if len(users) >= 4:
                inviter = users[i]
                invitee = users[i + 2]
                game = random.choice([g for g in created_games if g.status == 'waiting'])
                
                if game:
                    invitation = GameInvitation.objects.create(
                        game=game,
                        inviter=inviter,
                        invitee=invitee,
                        message=f"Salut {invitee.first_name}! Veux-tu jouer une partie de {game.game_type.display_name}?",
                        expires_at=timezone.now() + timedelta(hours=24)
                    )
                    invitation_count += 1
                    self.stdout.write(f'✅ Created invitation: {invitation.id}')

        # Create game reports
        report_count = 0
        finished_games = [g for g in created_games if g.status == 'finished']
        for game in finished_games[:2]:
            if game.player2:
                report = GameReport.objects.create(
                    game=game,
                    reporter=game.player2,
                    reported_user=game.player1,
                    report_type='inappropriate_behavior',
                    description="Le joueur a eu un comportement irrespectueux pendant la partie."
                )
                report_count += 1
                self.stdout.write(f'✅ Created report: {report.id}')

        self.stdout.write(self.style.SUCCESS(
            f'🎯 Games data created:\n'
            f'  - Games: {len(created_games)}\n'
            f'  - Invitations: {invitation_count}\n'
            f'  - Reports: {report_count}'
        ))

    def create_tournaments(self):
        """Create sample tournaments"""
        self.stdout.write(self.style.SUCCESS('🏆 Creating tournaments...'))
        
        users = list(User.objects.all()[:8])
        game_types = list(GameType.objects.all())
        
        if len(users) < 4 or len(game_types) == 0:
            self.stdout.write(self.style.WARNING('⚠️  Need at least 4 users and 1 game type for tournaments'))
            return

        tournaments_data = [
            {
                'name': 'Tournoi Hebdomadaire d\'Échecs',
                'description': 'Tournoi hebdomadaire ouvert à tous les joueurs d\'échecs. Prix attractifs!',
                'game_type': next((gt for gt in game_types if gt.name == 'chess'), game_types[0]),
                'tournament_type': 'single_elimination',
                'max_participants': 16,
                'entry_fee': Decimal('2000'),
                'status': 'registration',
                'organizer': users[0],
                'registration_start': timezone.now() - timedelta(days=1),
                'registration_end': timezone.now() + timedelta(days=5),
                'start_date': timezone.now() + timedelta(days=7)
            },
            {
                'name': 'Championnat de Dames',
                'description': 'Grand championnat de dames avec les meilleurs joueurs de la plateforme.',
                'game_type': next((gt for gt in game_types if gt.name == 'checkers'), game_types[0]),
                'tournament_type': 'double_elimination',
                'max_participants': 32,
                'entry_fee': Decimal('5000'),
                'status': 'upcoming',
                'organizer': users[1],
                'registration_start': timezone.now() + timedelta(days=3),
                'registration_end': timezone.now() + timedelta(days=10),
                'start_date': timezone.now() + timedelta(days=14)
            },
            {
                'name': 'Tournoi Express Ludo',
                'description': 'Tournoi rapide de Ludo pour une soirée de divertissement.',
                'game_type': next((gt for gt in game_types if gt.name == 'ludo'), game_types[0]),
                'tournament_type': 'round_robin',
                'max_participants': 8,
                'entry_fee': Decimal('1000'),
                'status': 'finished',
                'organizer': users[2],
                'registration_start': timezone.now() - timedelta(days=10),
                'registration_end': timezone.now() - timedelta(days=8),
                'start_date': timezone.now() - timedelta(days=7),
                'end_date': timezone.now() - timedelta(days=6)
            }
        ]

        created_tournaments = []
        for tournament_data in tournaments_data:
            tournament = Tournament.objects.create(**tournament_data)
            
            # Calculate prize pool
            tournament.total_prize_pool = tournament.entry_fee * tournament.max_participants
            tournament.winner_prize = tournament.total_prize_pool * Decimal('0.5')
            tournament.runner_up_prize = tournament.total_prize_pool * Decimal('0.3')
            tournament.save()
            
            created_tournaments.append(tournament)
            self.stdout.write(f'✅ Created tournament: {tournament.name}')
            
            # Add participants for tournaments
            if tournament.status in ['registration', 'finished']:
                participant_count = min(len(users), tournament.max_participants // 2)
                for i in range(participant_count):
                    participant = TournamentParticipant.objects.create(
                        tournament=tournament,
                        user=users[i],
                        seed=i + 1
                    )
                    if tournament.status == 'finished':
                        participant.final_position = i + 1
                        participant.is_eliminated = i > 0  # Winner is not eliminated
                        participant.save()

        self.stdout.write(self.style.SUCCESS(f'🏆 Created {len(created_tournaments)} tournaments'))

    def create_leaderboards(self):
        """Create sample leaderboard entries"""
        self.stdout.write(self.style.SUCCESS('🏅 Creating leaderboards...'))
        
        users = list(User.objects.all()[:8])
        game_types = list(GameType.objects.all())
        
        if len(users) < 3:
            self.stdout.write(self.style.WARNING('⚠️  Need at least 3 users for leaderboards'))
            return

        # Global leaderboard
        global_stats = [
            {'user': users[0], 'points': 2850, 'games_played': 45, 'games_won': 32, 'total_winnings': Decimal('125000')},
            {'user': users[1], 'points': 2720, 'games_played': 38, 'games_won': 26, 'total_winnings': Decimal('98000')},
            {'user': users[2], 'points': 2590, 'games_played': 42, 'games_won': 28, 'total_winnings': Decimal('87500')},
            {'user': users[3], 'points': 2410, 'games_played': 35, 'games_won': 22, 'total_winnings': Decimal('76000')},
            {'user': users[4], 'points': 2280, 'games_played': 30, 'games_won': 18, 'total_winnings': Decimal('54000')},
        ]

        # Current month period
        period_start = timezone.now().date().replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        created_count = 0
        for rank, stats in enumerate(global_stats, 1):
            win_rate = (stats['games_won'] / stats['games_played']) * 100 if stats['games_played'] > 0 else 0
            
            leaderboard = Leaderboard.objects.create(
                user=stats['user'],
                leaderboard_type='global',
                rank=rank,
                points=stats['points'],
                games_played=stats['games_played'],
                games_won=stats['games_won'],
                win_rate=Decimal(str(round(win_rate, 2))),
                total_winnings=stats['total_winnings'],
                period_start=period_start,
                period_end=period_end
            )
            created_count += 1
            self.stdout.write(f'✅ Created leaderboard entry: #{rank} {stats["user"].username}')

        # Game-specific leaderboards
        for game_type in game_types[:2]:  # Create for first 2 game types
            for rank, stats in enumerate(global_stats[:3], 1):  # Top 3 only
                win_rate = (stats['games_won'] / stats['games_played']) * 100 if stats['games_played'] > 0 else 0
                
                leaderboard = Leaderboard.objects.create(
                    user=stats['user'],
                    leaderboard_type='game_type',
                    game_type=game_type,
                    rank=rank,
                    points=stats['points'] - (rank * 50),  # Slight variation
                    games_played=max(1, stats['games_played'] - rank * 2),
                    games_won=max(1, stats['games_won'] - rank),
                    win_rate=Decimal(str(round(win_rate, 2))),
                    total_winnings=stats['total_winnings'] - Decimal(str(rank * 5000)),
                    period_start=period_start,
                    period_end=period_end
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'🏅 Created {created_count} leaderboard entries'))

    def display_summary(self):
        """Display a summary of created data"""
        self.stdout.write(self.style.SUCCESS('\n📊 DATABASE SUMMARY:'))
        self.stdout.write(f'👥 Users: {User.objects.count()}')
        self.stdout.write(f'🎮 Game Types: {GameType.objects.count()}')
        self.stdout.write(f'🎯 Games: {Game.objects.count()}')
        self.stdout.write(f'📨 Invitations: {GameInvitation.objects.count()}')
        self.stdout.write(f'📋 Reports: {GameReport.objects.count()}')
        self.stdout.write(f'🏆 Tournaments: {Tournament.objects.count()}')
        self.stdout.write(f'👤 Tournament Participants: {TournamentParticipant.objects.count()}')
        self.stdout.write(f'🏅 Leaderboard Entries: {Leaderboard.objects.count()}')