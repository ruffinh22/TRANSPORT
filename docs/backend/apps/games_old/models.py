# apps/games/models.py
# ====================

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError


class GameType(models.Model):
    """Types de jeux disponibles."""
    
    GAME_CATEGORIES = [
        ('strategy', _('Stratégie')),
        ('cards', _('Cartes')),
        ('board', _('Plateau')),
        ('puzzle', _('Puzzle')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nom'), max_length=50, unique=True)
    display_name = models.CharField(_('Nom d\'affichage'), max_length=100)
    description = models.TextField(_('Description'))
    category = models.CharField(_('Catégorie'), max_length=20, choices=GAME_CATEGORIES)
    
    # Configuration du jeu
    min_players = models.PositiveIntegerField(_('Joueurs minimum'), default=2)
    max_players = models.PositiveIntegerField(_('Joueurs maximum'), default=2)
    estimated_duration = models.PositiveIntegerField(_('Durée estimée (minutes)'), default=15)
    
    # Paramètres de mise
    min_bet_fcfa = models.DecimalField(_('Mise minimum FCFA'), max_digits=10, decimal_places=2, default=500)
    max_bet_fcfa = models.DecimalField(_('Mise maximum FCFA'), max_digits=10, decimal_places=2, default=1000000)
    
    # Métadonnées
    is_active = models.BooleanField(_('Actif'), default=True)
    icon = models.ImageField(_('Icône'), upload_to='game_icons/', null=True, blank=True)
    rules_url = models.URLField(_('Lien vers les règles'), blank=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'game_types'
        verbose_name = _('Type de jeu')
        verbose_name_plural = _('Types de jeux')
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class Game(models.Model):
    """Modèle principal pour les parties de jeu."""
    
    GAME_STATUS_CHOICES = [
        ('waiting', _('En attente d\'un joueur')),
        ('ready', _('Prêt à commencer')),
        ('playing', _('En cours')),
        ('paused', _('En pause')),
        ('finished', _('Terminé')),
        ('cancelled', _('Annulé')),
        ('disputed', _('En litige')),
        ('abandoned', _('Abandonné')),
    ]
    
    CURRENCIES = [
        ('FCFA', 'FCFA'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_code = models.CharField(_('Code de partie'), max_length=8, unique=True, blank=True)
    
    # Configuration du jeu
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        related_name='games',
        verbose_name=_('Type de jeu')
    )
    
    # Joueurs
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player1',
        verbose_name=_('Joueur 1')
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player2',
        verbose_name=_('Joueur 2'),
        null=True,
        blank=True
    )
    current_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='current_games',
        verbose_name=_('Joueur actuel'),
        null=True,
        blank=True
    )
    
    # Mise et monnaie
    bet_amount = models.DecimalField(
        _('Montant de la mise'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('Devise'), max_length=5, choices=CURRENCIES, default='FCFA')
    total_pot = models.DecimalField(
        _('Cagnotte totale'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    commission = models.DecimalField(
        _('Commission'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    winner_prize = models.DecimalField(
        _('Prix du gagnant'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # État de la partie
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=GAME_STATUS_CHOICES,
        default='waiting'
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_games',
        verbose_name=_('Gagnant')
    )
    
    # Données du jeu
    game_data = models.JSONField(_('Données de la partie'), default=dict)
    move_history = models.JSONField(_('Historique des coups'), default=list)
    
    # Gestion du temps
    turn_start_time = models.DateTimeField(_('Début du tour'), null=True, blank=True)
    turn_timeout = models.PositiveIntegerField(_('Timeout du tour (secondes)'), default=120)
    player1_time_left = models.PositiveIntegerField(_('Temps restant J1 (secondes)'), default=600)  # 10 min
    player2_time_left = models.PositiveIntegerField(_('Temps restant J2 (secondes)'), default=600)  # 10 min
    
    # Métadonnées temporelles
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    started_at = models.DateTimeField(_('Commencé le'), null=True, blank=True)
    finished_at = models.DateTimeField(_('Terminé le'), null=True, blank=True)
    last_move_at = models.DateTimeField(_('Dernier coup le'), null=True, blank=True)
    
    # Paramètres avancés
    is_private = models.BooleanField(_('Partie privée'), default=False)
    is_rated = models.BooleanField(_('Partie classée'), default=True)
    spectators_allowed = models.BooleanField(_('Spectateurs autorisés'), default=True)
    
    class Meta:
        db_table = 'games'
        verbose_name = _('Partie')
        verbose_name_plural = _('Parties')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['player1', 'created_at']),
            models.Index(fields=['player2', 'created_at']),
            models.Index(fields=['room_code']),
            models.Index(fields=['game_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.game_type.display_name} - {self.room_code}"
    
    def save(self, *args, **kwargs):
        # Générer un code de partie unique
        if not self.room_code:
            self.room_code = self.generate_room_code()
        
        # Calculer les montants financiers
        if self.bet_amount and self.bet_amount > 0:
            self.total_pot = self.bet_amount * 2
            commission_rate = Decimal(str(settings.GAME_SETTINGS.get('COMMISSION_RATE', 0.14)))
            self.commission = self.total_pot * commission_rate
            self.winner_prize = self.total_pot - self.commission
        
        super().save(*args, **kwargs)
    
    def generate_room_code(self):
        """Générer un code de partie unique."""
        import string
        import secrets
        
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if not Game.objects.filter(room_code=code).exists():
                return code
    
    def can_join(self, user):
        """Vérifier si un utilisateur peut rejoindre la partie."""
        if self.status != 'waiting':
            return False, _('La partie n\'est plus en attente de joueurs')
        
        if self.player1 == user:
            return False, _('Vous êtes déjà dans cette partie')
        
        # Vérifier les fonds suffisants
        balance = user.get_balance(self.currency)
        if balance < self.bet_amount:
            return False, _('Solde insuffisant')
        
        # Vérifier le KYC pour les gros montants
        if self.bet_amount >= Decimal('10000') and user.kyc_status != 'approved':
            return False, _('Vérification KYC requise pour cette mise')
        
        return True, _('Peut rejoindre la partie')
    
    def join_game(self, user):
        """Faire rejoindre un utilisateur à la partie."""
        can_join, message = self.can_join(user)
        if not can_join:
            raise ValidationError(message)
        
        # Débiter le montant de la mise
        user.update_balance(self.currency, self.bet_amount, 'subtract')
        
        # Assigner le joueur
        self.player2 = user
        self.status = 'ready'
        self.save()
        
        return True
    
    def start_game(self):
        """Démarrer la partie."""
        if self.status != 'ready':
            raise ValidationError(_('La partie n\'est pas prête à être démarrée'))
        
        if not self.player1 or not self.player2:
            raise ValidationError(_('Il manque des joueurs'))
        
        self.status = 'playing'
        self.started_at = timezone.now()
        self.current_player = self.player1  # Le créateur commence
        self.turn_start_time = timezone.now()
        self.save()
        
        # Initialiser les données de jeu selon le type
        self.initialize_game_data()
    
    def initialize_game_data(self):
        """Initialiser les données de jeu selon le type."""
        game_logic_map = {
            'chess': self.initialize_chess,
            'checkers': self.initialize_checkers,
            'ludo': self.initialize_ludo,
            'cards': self.initialize_cards,
        }
        
        initializer = game_logic_map.get(self.game_type.name)
        if initializer:
            initializer()
    
    def initialize_chess(self):
        """Initialiser une partie d'échecs."""
        self.game_data = {
            'board': self.get_initial_chess_board(),
            'castling_rights': {
                'white': {'kingside': True, 'queenside': True},
                'black': {'kingside': True, 'queenside': True}
            },
            'en_passant': None,
            'halfmove_clock': 0,
            'fullmove_number': 1
        }
        self.save()
    
    def initialize_checkers(self):
        """Initialiser une partie de dames."""
        self.game_data = {
            'board': self.get_initial_checkers_board(),
            'must_capture': False,
            'current_piece': None
        }
        self.save()
    
    def initialize_ludo(self):
        """Initialiser une partie de ludo."""
        self.game_data = {
            'board': {str(i): None for i in range(52)},  # 52 cases sur le plateau
            'player1_pieces': [0, 0, 0, 0],  # Positions des 4 pièces
            'player2_pieces': [0, 0, 0, 0],
            'dice_value': 0,
            'consecutive_sixes': 0
        }
        self.save()
    
    def initialize_cards(self):
        """Initialiser une partie de cartes."""
        import random
        
        # Créer et mélanger un jeu de cartes
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [{'suit': suit, 'value': value} for suit in suits for value in values]
        random.shuffle(deck)
        
        self.game_data = {
            'deck': deck,
            'player1_hand': deck[:7],
            'player2_hand': deck[7:14],
            'discard_pile': [deck[14]],
            'current_card': deck[14]
        }
        self.save()
    
    def get_initial_chess_board(self):
        """Obtenir la position initiale des échecs."""
        return [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
    
    def get_initial_checkers_board(self):
        """Obtenir la position initiale des dames."""
        board = [['.' for _ in range(8)] for _ in range(8)]
        
        # Placer les pièces noires (joueur 1)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = 'b'
        
        # Placer les pièces blanches (joueur 2)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = 'w'
        
        return board
    
    def make_move(self, player, move_data):
        """Effectuer un mouvement dans la partie."""
        if self.status != 'playing':
            raise ValidationError(_('La partie n\'est pas en cours'))
        
        if self.current_player != player:
            raise ValidationError(_('Ce n\'est pas votre tour'))
        
        # Vérifier le timeout
        if self.is_turn_timeout():
            self.handle_timeout()
            return False
        
        # Valider et appliquer le mouvement selon le type de jeu
        move_validator_map = {
            'chess': self.validate_chess_move,
            'checkers': self.validate_checkers_move,
            'ludo': self.validate_ludo_move,
            'cards': self.validate_cards_move,
        }
        
        validator = move_validator_map.get(self.game_type.name)
        if validator and validator(move_data):
            # Ajouter le mouvement à l'historique
            self.move_history.append({
                'player': player.username,
                'move': move_data,
                'timestamp': timezone.now().isoformat(),
                'turn_number': len(self.move_history) + 1
            })
            
            # Changer de joueur
            self.switch_turn()
            
            # Vérifier les conditions de victoire
            if self.check_win_condition():
                self.end_game(player)
            
            self.last_move_at = timezone.now()
            self.save()
            return True
        
        return False
    
    def validate_chess_move(self, move_data):
        """Valider un mouvement d'échecs."""
        # Implémentation simplifiée - à développer selon les règles complètes
        from_pos = move_data.get('from')
        to_pos = move_data.get('to')
        
        if not from_pos or not to_pos:
            return False
        
        # Ici, implémenter la validation complète des règles d'échecs
        return True
    
    def validate_checkers_move(self, move_data):
        """Valider un mouvement de dames."""
        # Implémentation simplifiée
        return True
    
    def validate_ludo_move(self, move_data):
        """Valider un mouvement de ludo."""
        # Implémentation simplifiée
        return True
    
    def validate_cards_move(self, move_data):
        """Valider un mouvement de cartes."""
        # Implémentation simplifiée
        return True
    
    def switch_turn(self):
        """Changer de joueur actuel."""
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        self.turn_start_time = timezone.now()
    
    def is_turn_timeout(self):
        """Vérifier si le timeout du tour est dépassé."""
        if not self.turn_start_time:
            return False
        
        elapsed = (timezone.now() - self.turn_start_time).seconds
        return elapsed > self.turn_timeout
    
    def handle_timeout(self):
        """Gérer le timeout d'un joueur."""
        # Le joueur actuel perd par timeout
        winner = self.player2 if self.current_player == self.player1 else self.player1
        self.end_game(winner, reason='timeout')
    
    def check_win_condition(self):
        """Vérifier les conditions de victoire selon le type de jeu."""
        win_checker_map = {
            'chess': self.check_chess_win,
            'checkers': self.check_checkers_win,
            'ludo': self.check_ludo_win,
            'cards': self.check_cards_win,
        }
        
        checker = win_checker_map.get(self.game_type.name)
        return checker() if checker else False
    
    def check_chess_win(self):
        """Vérifier les conditions de victoire aux échecs."""
        # Implémentation simplifiée - échec et mat, pat, etc.
        return False
    
    def check_checkers_win(self):
        """Vérifier les conditions de victoire aux dames."""
        # Vérifier s'il reste des pièces à l'adversaire
        return False
    
    def check_ludo_win(self):
        """Vérifier les conditions de victoire au ludo."""
        # Vérifier si toutes les pièces sont arrivées
        return False
    
    def check_cards_win(self):
        """Vérifier les conditions de victoire aux cartes."""
        # Vérifier si un joueur n'a plus de cartes
        return False
    
    def end_game(self, winner, reason='victory'):
        """Terminer la partie."""
        self.winner = winner
        self.status = 'finished'
        self.finished_at = timezone.now()
        
        # Distribuer les gains
        if winner and self.winner_prize > 0:
            winner.update_balance(self.currency, self.winner_prize, 'add')
        
        # Enregistrer les statistiques
        self.update_player_statistics(reason)
        
        self.save()
    
    def update_player_statistics(self, reason):
        """Mettre à jour les statistiques des joueurs."""
        from apps.analytics.models import PlayerStatistics
        
        # Statistiques pour le joueur 1
        stats1, _ = PlayerStatistics.objects.get_or_create(user=self.player1)
        stats1.games_played += 1
        if self.winner == self.player1:
            stats1.games_won += 1
        else:
            stats1.games_lost += 1
        stats1.total_bet += self.bet_amount
        if self.winner == self.player1:
            stats1.total_winnings += self.winner_prize
        stats1.save()
        
        # Statistiques pour le joueur 2
        if self.player2:
            stats2, _ = PlayerStatistics.objects.get_or_create(user=self.player2)
            stats2.games_played += 1
            if self.winner == self.player2:
                stats2.games_won += 1
            else:
                stats2.games_lost += 1
            stats2.total_bet += self.bet_amount
            if self.winner == self.player2:
                stats2.total_winnings += self.winner_prize
            stats2.save()
    
    def cancel_game(self, reason='cancelled'):
        """Annuler la partie et rembourser les mises."""
        if self.status in ['finished', 'cancelled']:
            return
        
        self.status = 'cancelled'
        self.finished_at = timezone.now()
        
        # Rembourser les mises
        if self.player1:
            self.player1.update_balance(self.currency, self.bet_amount, 'add')
        if self.player2:
            self.player2.update_balance(self.currency, self.bet_amount, 'add')
        
        self.save()
    
    def get_opponent(self, player):
        """Obtenir l'adversaire d'un joueur."""
        if player == self.player1:
            return self.player2
        elif player == self.player2:
            return self.player1
        return None
    
    def get_time_left(self, player):
        """Obtenir le temps restant pour un joueur."""
        if player == self.player1:
            return self.player1_time_left
        elif player == self.player2:
            return self.player2_time_left
        return 0
    
    def update_time_left(self, player, time_used):
        """Mettre à jour le temps restant d'un joueur."""
        if player == self.player1:
            self.player1_time_left = max(0, self.player1_time_left - time_used)
        elif player == self.player2:
            self.player2_time_left = max(0, self.player2_time_left - time_used)
        
        self.save(update_fields=['player1_time_left', 'player2_time_left'])


class GameInvitation(models.Model):
    """Invitations à des parties privées."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('accepted', _('Acceptée')),
        ('declined', _('Refusée')),
        ('expired', _('Expirée')),
        ('cancelled', _('Annulée')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('Partie')
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name=_('Invitant')
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations',
        verbose_name=_('Invité')
    )
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(_('Message'), blank=True)
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    responded_at = models.DateTimeField(_('Répondu le'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Expire le'))
    
    class Meta:
        db_table = 'game_invitations'
        verbose_name = _('Invitation de partie')
        verbose_name_plural = _('Invitations de parties')
        unique_together = ['game', 'invitee']
    
    def __str__(self):
        return f"{self.inviter.username} → {self.invitee.username} ({self.game.room_code})"
    
    def accept(self):
        """Accepter l'invitation."""
        if self.status != 'pending':
            raise ValidationError(_('Cette invitation n\'est plus valide'))
        
        if timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            raise ValidationError(_('Cette invitation a expiré'))
        
        # Rejoindre la partie
        self.game.join_game(self.invitee)
        
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
    
    def decline(self):
        """Refuser l'invitation."""
        if self.status != 'pending':
            raise ValidationError(_('Cette invitation n\'est plus valide'))
        
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()


class GameReport(models.Model):
    """Signalements de parties."""
    
    REPORT_TYPES = [
        ('cheating', _('Triche')),
        ('inappropriate_behavior', _('Comportement inapproprié')),
        ('harassment', _('Harcèlement')),
        ('technical_issue', _('Problème technique')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('under_review', _('En cours de traitement')),
        ('resolved', _('Résolu')),
        ('dismissed', _('Rejeté')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Partie')
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        verbose_name=_('Signalant')
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reports',
        verbose_name=_('Utilisateur signalé')
    )
    
    report_type = models.CharField(_('Type de signalement'), max_length=30, choices=REPORT_TYPES)
    description = models.TextField(_('Description'))
    evidence = models.JSONField(_('Preuves'), default=dict, blank=True)
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(_('Notes admin'), blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_reports',
        verbose_name=_('Résolu par')
    )
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    resolved_at = models.DateTimeField(_('Résolu le'), null=True, blank=True)
    
    class Meta:
        db_table = 'game_reports'
        verbose_name = _('Signalement de partie')
        verbose_name_plural = _('Signalements de parties')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Signalement #{self.id.hex[:8]} - {self.get_report_type_display()}"


class Tournament(models.Model):
    """Tournois organisés."""
    
    TOURNAMENT_TYPES = [
        ('single_elimination', _('Élimination directe')),
        ('double_elimination', _('Double élimination')),
        ('round_robin', _('Round robin')),
        ('swiss', _('Système suisse')),
    ]
    
    STATUS_CHOICES = [
        ('upcoming', _('À venir')),
        ('registration', _('Inscriptions ouvertes')),
        ('ready', _('Prêt à commencer')),
        ('ongoing', _('En cours')),
        ('finished', _('Terminé')),
        ('cancelled', _('Annulé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        related_name='tournaments',
        verbose_name=_('Type de jeu')
    )
    
    tournament_type = models.CharField(_('Type de tournoi'), max_length=20, choices=TOURNAMENT_TYPES)
    
    # Configuration
    max_participants = models.PositiveIntegerField(_('Participants maximum'))
    entry_fee = models.DecimalField(_('Frais d\'inscription'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Devise'), max_length=5, choices=Game.CURRENCIES, default='FCFA')
    
    # Prix
    total_prize_pool = models.DecimalField(_('Cagnotte totale'), max_digits=12, decimal_places=2, default=0)
    winner_prize = models.DecimalField(_('Prix du gagnant'), max_digits=10, decimal_places=2, default=0)
    runner_up_prize = models.DecimalField(_('Prix du finaliste'), max_digits=10, decimal_places=2, default=0)
    
    # Timing
    registration_start = models.DateTimeField(_('Début des inscriptions'))
    registration_end = models.DateTimeField(_('Fin des inscriptions'))
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'), null=True, blank=True)
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Organisateur
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_tournaments',
        verbose_name=_('Organisateur')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'tournaments'
        verbose_name = _('Tournoi')
        verbose_name_plural = _('Tournois')
        ordering = ['start_date']
    
    def __str__(self):
        return self.name


class TournamentParticipant(models.Model):
    """Participants aux tournois."""
    
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('Tournoi')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tournament_participations',
        verbose_name=_('Utilisateur')
    )
    
    seed = models.PositiveIntegerField(_('Tête de série'), null=True, blank=True)
    current_round = models.PositiveIntegerField(_('Tour actuel'), default=1)
    is_eliminated = models.BooleanField(_('Éliminé'), default=False)
    final_position = models.PositiveIntegerField(_('Position finale'), null=True, blank=True)
    
    registered_at = models.DateTimeField(_('Inscrit le'), auto_now_add=True)
    
    class Meta:
        db_table = 'tournament_participants'
        verbose_name = _('Participant au tournoi')
        verbose_name_plural = _('Participants aux tournois')
        unique_together = ['tournament', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.tournament.name}"


class Leaderboard(models.Model):
    """Classements des joueurs."""
    
    LEADERBOARD_TYPES = [
        ('global', _('Global')),
        ('monthly', _('Mensuel')),
        ('weekly', _('Hebdomadaire')),
        ('game_type', _('Par type de jeu')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        verbose_name=_('Utilisateur')
    )
    
    leaderboard_type = models.CharField(_('Type de classement'), max_length=20, choices=LEADERBOARD_TYPES)
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboard_entries',
        verbose_name=_('Type de jeu')
    )
    
    # Statistiques
    rank = models.PositiveIntegerField(_('Rang'))
    points = models.PositiveIntegerField(_('Points'), default=0)
    games_played = models.PositiveIntegerField(_('Parties jouées'), default=0)
    games_won = models.PositiveIntegerField(_('Parties gagnées'), default=0)
    win_rate = models.DecimalField(_('Taux de victoire'), max_digits=5, decimal_places=2, default=0)
    total_winnings = models.DecimalField(_('Gains totaux'), max_digits=12, decimal_places=2, default=0)
    
    # Période
    period_start = models.DateField(_('Début de période'))
    period_end = models.DateField(_('Fin de période'))
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'leaderboards'
        verbose_name = _('Classement')
        verbose_name_plural = _('Classements')
        ordering = ['rank']
        indexes = [
            models.Index(fields=['leaderboard_type', 'rank']),
            models.Index(fields=['game_type', 'rank']),
            models.Index(fields=['user', 'leaderboard_type']),
        ]
    
    def __str__(self):
        return f"#{self.rank} {self.user.username} ({self.get_leaderboard_type_display()})"
