# apps/games/game_logic/chess_competitive.py
# =====================================================
# Moteur d'échecs COMPÉTITIF avec timer et système de points
# Inspiré de checkers_competitive.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict
from enum import Enum
import logging
import copy

logger = logging.getLogger(__name__)


class Color(Enum):
    """Couleurs des joueurs."""
    WHITE = 'white'
    BLACK = 'black'


@dataclass
class ChessTimer:
    """Timer pour les échecs compétitifs."""
    move_time_limit: int = 120  # 120 secondes par coup
    global_time_limit: int = 21000  # 21000 secondes total par joueur
    
    white_time_remaining: float = 21000.0
    black_time_remaining: float = 21000.0
    move_time_remaining: float = 120.0
    
    current_player: str = 'white'
    current_move_start: Optional[str] = None
    game_start_time: Optional[str] = None
    
    # Nouveau: timestamp du dernier update pour éviter les déductions multiples
    last_update: Optional[str] = None
    
    global_timeout: bool = False
    move_timeout: bool = False
    
    def start_game(self):
        """Démarrer le chronomètre de la partie."""
        now = datetime.now(timezone.utc).isoformat()
        self.game_start_time = now
        self.current_move_start = now
        logger.info(f"⏰ Chess timer started at {now}")
    
    def start_move(self):
        """Démarrer le chronomètre pour un nouveau coup."""
        self.current_move_start = datetime.now(timezone.utc).isoformat()
        self.move_time_remaining = float(self.move_time_limit)
        self.move_timeout = False
        logger.info(f"⏰ Move timer started for {self.current_player}")
    
    def update_times(self):
        """Mettre à jour les temps restants."""
        if not self.current_move_start:
            logger.debug("⏰ update_times called but no current_move_start")
            return
        
        now = datetime.now(timezone.utc)
        move_start = datetime.fromisoformat(self.current_move_start.replace('Z', '+00:00'))
        elapsed = (now - move_start).total_seconds()
        
        logger.debug(f"⏰ update_times - Player: {self.current_player}, Elapsed: {elapsed:.2f}s, "
                    f"White time: {self.white_time_remaining:.1f}s, Black time: {self.black_time_remaining:.1f}s")
        
        # Temps du coup (calculé depuis le début du coup actuel)
        self.move_time_remaining = max(0, self.move_time_limit - elapsed)
        
        # ⚠️ NE PAS déduire le temps global ici - il sera déduit uniquement dans switch_player()
        # Cela évite les déductions multiples lors d'appels répétés à update_times()
        
        # Vérifier timeout du coup (120 secondes)
        if self.move_time_remaining <= 0:
            self.move_timeout = True
            logger.warning(f"⏰ Move timeout detected: {elapsed:.1f}s elapsed (limit: {self.move_time_limit}s)")
        
        # Vérifier si le temps global total serait dépassé après ce coup
        projected_time = elapsed
        if self.current_player == 'white':
            if self.white_time_remaining - projected_time <= 0:
                self.global_timeout = True
                logger.warning(f"⏰ Global timeout for white: {self.white_time_remaining:.1f}s - {projected_time:.1f}s = {self.white_time_remaining - projected_time:.1f}s")
        else:
            if self.black_time_remaining - projected_time <= 0:
                self.global_timeout = True
                logger.warning(f"⏰ Global timeout for black: {self.black_time_remaining:.1f}s - {projected_time:.1f}s = {self.black_time_remaining - projected_time:.1f}s")
    
    def is_global_timeout(self) -> bool:
        """Vérifier si le temps global est écoulé."""
        self.update_times()
        return self.global_timeout
    
    def is_move_timeout(self) -> bool:
        """Vérifier si le timeout du coup est écoulé."""
        self.update_times()
        return self.move_timeout
    
    def switch_player(self):
        """Changer de joueur actif."""
        # Déduire le temps écoulé du joueur actuel (UNE SEULE FOIS lors du changement)
        if self.current_move_start:
            now = datetime.now(timezone.utc)
            move_start = datetime.fromisoformat(self.current_move_start.replace('Z', '+00:00'))
            elapsed = (now - move_start).total_seconds()
            
            # Déduire le temps du coup du temps global
            if self.current_player == 'white':
                self.white_time_remaining = max(0, self.white_time_remaining - elapsed)
                logger.info(f"⏰ White used {elapsed:.1f}s, {self.white_time_remaining:.1f}s remaining")
            else:
                self.black_time_remaining = max(0, self.black_time_remaining - elapsed)
                logger.info(f"⏰ Black used {elapsed:.1f}s, {self.black_time_remaining:.1f}s remaining")
        
        # Changer de joueur
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        # Réinitialiser les flags de timeout pour le nouveau coup
        self.move_timeout = False
        self.global_timeout = False
        
        # Démarrer le chronomètre pour le nouveau joueur
        self.start_move()
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire."""
        self.update_times()
        return {
            'move_time_limit': self.move_time_limit,
            'global_time_limit': self.global_time_limit,
            'white_time_remaining': self.white_time_remaining,
            'black_time_remaining': self.black_time_remaining,
            'move_time_remaining': self.move_time_remaining,
            'current_player': self.current_player,
            'current_move_start': self.current_move_start,
            'game_start_time': self.game_start_time,
            'global_timeout': self.global_timeout,
            'move_timeout': self.move_timeout
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChessTimer':
        """Créer depuis un dictionnaire."""
        timer = cls(
            move_time_limit=data.get('move_time_limit', 120),
            global_time_limit=data.get('global_time_limit', 21000),
            white_time_remaining=data.get('white_time_remaining', 21000.0),
            black_time_remaining=data.get('black_time_remaining', 21000.0),
            move_time_remaining=data.get('move_time_remaining', 120.0),
            current_player=data.get('current_player', 'white'),
            current_move_start=data.get('current_move_start'),
            game_start_time=data.get('game_start_time'),
            global_timeout=data.get('global_timeout', False),
            move_timeout=data.get('move_timeout', False)
        )
        return timer # 81.17.101.39


@dataclass
class ChessScore:
    """Score pour un joueur aux échecs compétitifs."""
    color: str
    points: int = 0
    pieces_captured: int = 0
    
    # Valeurs des pièces capturées
    pawns_captured: int = 0  # 1 point chacun
    knights_captured: int = 0  # 3 points chacun
    bishops_captured: int = 0  # 3 points chacun
    rooks_captured: int = 0  # 5 points chacun
    queens_captured: int = 0  # 9 points chacun
    
    def to_dict(self) -> dict:
        return {
            'color': self.color,
            'points': self.points,
            'pieces_captured': self.pieces_captured,
            'pawns_captured': self.pawns_captured,
            'knights_captured': self.knights_captured,
            'bishops_captured': self.bishops_captured,
            'rooks_captured': self.rooks_captured,
            'queens_captured': self.queens_captured
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChessScore':
        return cls(
            color=data.get('color', 'white'),
            points=data.get('points', 0),
            pieces_captured=data.get('pieces_captured', 0),
            pawns_captured=data.get('pawns_captured', 0),
            knights_captured=data.get('knights_captured', 0),
            bishops_captured=data.get('bishops_captured', 0),
            rooks_captured=data.get('rooks_captured', 0),
            queens_captured=data.get('queens_captured', 0)
        )


def create_competitive_chess_game() -> dict:
    """
    Créer une nouvelle partie d'échecs compétitive avec timer et système de points.
    """
    # Plateau initial d'échecs 8x8
    board = create_initial_chess_board()
    
    # Timer compétitif
    timer = ChessTimer()
    timer.start_game()
    
    # Scores
    white_score = ChessScore(color='white')
    black_score = ChessScore(color='black')
    
    game_state = {
        'board': board,
        'current_player': 'white',
        'timer': timer.to_dict(),
        'white_score': white_score.to_dict(),
        'black_score': black_score.to_dict(),
        'is_game_over': False,
        'winner': None,
        'move_history': [],
        'position_history': [],  # Pour détecter la répétition de position
        'castling_rights': {
            'white_kingside': True,
            'white_queenside': True,
            'black_kingside': True,
            'black_queenside': True
        },
        'en_passant_target': None,
        'halfmove_clock': 0,  # Pour la règle des 50 coups
        'fullmove_number': 1
    }
    
    logger.info("✅ Competitive chess game created")
    return game_state


def create_initial_chess_board() -> list:
    """Créer le plateau initial d'échecs 8x8."""
    return [
        # Rangée 8 (noirs)
        [
            {'type': 'R', 'color': 'black', 'has_moved': False},
            {'type': 'N', 'color': 'black', 'has_moved': False},
            {'type': 'B', 'color': 'black', 'has_moved': False},
            {'type': 'Q', 'color': 'black', 'has_moved': False},
            {'type': 'K', 'color': 'black', 'has_moved': False},
            {'type': 'B', 'color': 'black', 'has_moved': False},
            {'type': 'N', 'color': 'black', 'has_moved': False},
            {'type': 'R', 'color': 'black', 'has_moved': False}
        ],
        # Rangée 7 (pions noirs)
        [{'type': 'P', 'color': 'black', 'has_moved': False} for _ in range(8)],
        # Rangées 6-3 (vides)
        [None for _ in range(8)],
        [None for _ in range(8)],
        [None for _ in range(8)],
        [None for _ in range(8)],
        # Rangée 2 (pions blancs)
        [{'type': 'P', 'color': 'white', 'has_moved': False} for _ in range(8)],
        # Rangée 1 (blancs)
        [
            {'type': 'R', 'color': 'white', 'has_moved': False},
            {'type': 'N', 'color': 'white', 'has_moved': False},
            {'type': 'B', 'color': 'white', 'has_moved': False},
            {'type': 'Q', 'color': 'white', 'has_moved': False},
            {'type': 'K', 'color': 'white', 'has_moved': False},
            {'type': 'B', 'color': 'white', 'has_moved': False},
            {'type': 'N', 'color': 'white', 'has_moved': False},
            {'type': 'R', 'color': 'white', 'has_moved': False}
        ]
    ]


def convert_chess_board_to_unicode(game_state: dict) -> list:
    """Convertir le plateau en format Unicode pour le frontend."""
    piece_mapping = {
        # Pièces blanches
        ('K', 'white'): '♔',
        ('Q', 'white'): '♕',
        ('R', 'white'): '♖',
        ('B', 'white'): '♗',
        ('N', 'white'): '♘',
        ('P', 'white'): '♙',
        # Pièces noires
        ('K', 'black'): '♚',
        ('Q', 'black'): '♛',
        ('R', 'black'): '♜',
        ('B', 'black'): '♝',
        ('N', 'black'): '♞',
        ('P', 'black'): '♟'
    }
    
    board = game_state.get('board', [])
    unicode_board = []
    
    for row in board:
        unicode_row = []
        for cell in row:
            if cell and isinstance(cell, dict):
                piece_type = cell.get('type')
                color = cell.get('color')
                unicode_piece = piece_mapping.get((piece_type, color), '.')
                unicode_row.append(unicode_piece)
            else:
                unicode_row.append('.')
        unicode_board.append(unicode_row)
    
    return unicode_board


def get_piece_value(piece_type: str) -> int:
    """Obtenir la valeur en points d'une pièce."""
    values = {
        'P': 1,   # Pion
        'N': 3,   # Cavalier
        'B': 3,   # Fou
        'R': 5,   # Tour
        'Q': 9,   # Dame
        'K': 0    # Roi (valeur infinie, ne compte pas)
    }
    return values.get(piece_type, 0)


def update_score_for_capture(score: ChessScore, captured_piece_type: str) -> int:
    """Mettre à jour le score après une capture."""
    # Normaliser le type de pièce
    piece_type = captured_piece_type.upper() if len(captured_piece_type) == 1 else captured_piece_type
    
    # Mapper les pièces Unicode vers les lettres
    unicode_to_type = {
        '♙': 'P', '♟': 'P',  # Pion
        '♘': 'N', '♞': 'N',  # Cavalier
        '♗': 'B', '♝': 'B',  # Fou
        '♖': 'R', '♜': 'R',  # Tour
        '♕': 'Q', '♛': 'Q',  # Dame
    }
    
    if captured_piece_type in unicode_to_type:
        piece_type = unicode_to_type[captured_piece_type]
    
    points = get_piece_value(piece_type)
    score.points += points
    score.pieces_captured += 1
    
    # Compteur spécifique par type
    if piece_type == 'P':
        score.pawns_captured += 1
    elif piece_type == 'N':
        score.knights_captured += 1
    elif piece_type == 'B':
        score.bishops_captured += 1
    elif piece_type == 'R':
        score.rooks_captured += 1
    elif piece_type == 'Q':
        score.queens_captured += 1
    
    logger.info(f"📊 Captured {captured_piece_type} ({piece_type}), gained {points} points")
    return points


def check_and_auto_pass_turn_if_timeout(game_state: dict) -> tuple[dict, bool]:
    """
    Vérifier si le timeout de 120s est dépassé.
    Si un joueur dépasse 120s, son adversaire gagne automatiquement la partie.
    Retourne (new_game_state, was_timeout_triggered)
    """
    timer = ChessTimer.from_dict(game_state.get('timer', {}))
    
    logger.debug(f"🔍 Checking timeout - Player: {timer.current_player}, "
                f"Move time remaining: {timer.move_time_remaining:.1f}s, "
                f"White time: {timer.white_time_remaining:.1f}s, "
                f"Black time: {timer.black_time_remaining:.1f}s, "
                f"Move timeout flag: {timer.move_timeout}, "
                f"Global timeout flag: {timer.global_timeout}")
    
    # Vérifier le timeout de coup (120s) - L'adversaire gagne immédiatement
    if timer.is_move_timeout():
        timeout_player = timer.current_player
        winner = 'black' if timeout_player == 'white' else 'white'
        
        logger.warning(f"⏱️ 120s MOVE TIMEOUT for {timeout_player}. {winner.upper()} WINS!")
        
        # Marquer la partie comme terminée avec victoire par timeout
        game_state['game_over'] = True
        game_state['winner'] = winner
        game_state['game_over_details'] = {
            'reason': 'move_timeout',
            'timeout_player': timeout_player,
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
        game_state['status'] = f'finished_{winner}'
        
        # Mettre à jour le timer
        game_state['timer'] = timer.to_dict()
        
        return game_state, True
    
    # Vérifier aussi le timeout global (21000s = 2h) pour sécurité
    if timer.is_global_timeout():
        timeout_player = timer.current_player
        winner = 'black' if timeout_player == 'white' else 'white'
        
        logger.warning(f"⏱️ GLOBAL TIMEOUT (2h) for {timeout_player}. {winner.upper()} WINS!")
        
        # Marquer la partie comme terminée avec victoire par timeout global
        game_state['game_over'] = True
        game_state['winner'] = winner
        game_state['game_over_details'] = {
            'reason': 'global_timeout',
            'timeout_player': timeout_player,
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
        game_state['status'] = f'finished_{winner}'
        
        # Mettre à jour le timer
        game_state['timer'] = timer.to_dict()
        
        return game_state, True
    
    return game_state, False


def check_competitive_chess_game_over(game_state: dict) -> tuple[bool, Optional[str], dict]:
    """
    Vérifier si la partie d'échecs est terminée.
    Retourne (is_over, winner, details)
    """
    timer = ChessTimer.from_dict(game_state.get('timer', {}))
    board = game_state.get('board', [])
    current_player = game_state.get('current_player', 'white')
    
    # 1. Vérifier échec et mat
    if is_checkmate(board, current_player):
        winner = 'black' if current_player == 'white' else 'white'
        logger.info(f"♚ CHECKMATE! {winner.upper()} WINS!")
        return True, winner, {
            'reason': 'checkmate',
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
    
    # 2. Vérifier répétition de position (triple répétition)
    if is_threefold_repetition(game_state):
        # ✅ Triple répétition = Fin de partie MAIS on compare les points
        white_score = game_state.get('white_score', {}).get('points', 0)
        black_score = game_state.get('black_score', {}).get('points', 0)
        
        if white_score > black_score:
            winner = 'white'
            logger.info(f"🔄 THREEFOLD REPETITION! WHITE WINS by points ({white_score} vs {black_score})")
        elif black_score > white_score:
            winner = 'black'
            logger.info(f"🔄 THREEFOLD REPETITION! BLACK WINS by points ({black_score} vs {white_score})")
        else:
            winner = 'draw'
            logger.info(f"🔄 THREEFOLD REPETITION! Game is a DRAW (equal points: {white_score})")
        
        return True, winner, {
            'reason': 'threefold_repetition',
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
    
    # 3. Vérifier pat (stalemate)
    if is_stalemate(board, current_player):
        # ✅ PAT = Fin de partie MAIS on compare les points (comme timeout global)
        white_score = game_state.get('white_score', {}).get('points', 0)
        black_score = game_state.get('black_score', {}).get('points', 0)
        
        if white_score > black_score:
            winner = 'white'
            logger.info(f"♔ STALEMATE! WHITE WINS by points ({white_score} vs {black_score})")
        elif black_score > white_score:
            winner = 'black'
            logger.info(f"♔ STALEMATE! BLACK WINS by points ({black_score} vs {white_score})")
        else:
            winner = 'draw'
            logger.info(f"♔ STALEMATE! Game is a DRAW (equal points: {white_score})")
        
        return True, winner, {
            'reason': 'stalemate',
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
    
    # 3. Vérifier matériel insuffisant
    if is_insufficient_material(board):
        # ✅ Matériel insuffisant = Fin de partie MAIS on compare les points
        white_score = game_state.get('white_score', {}).get('points', 0)
        black_score = game_state.get('black_score', {}).get('points', 0)
        
        if white_score > black_score:
            winner = 'white'
            logger.info(f"♟ INSUFFICIENT MATERIAL! WHITE WINS by points ({white_score} vs {black_score})")
        elif black_score > white_score:
            winner = 'black'
            logger.info(f"♟ INSUFFICIENT MATERIAL! BLACK WINS by points ({black_score} vs {white_score})")
        else:
            winner = 'draw'
            logger.info(f"♟ INSUFFICIENT MATERIAL! Game is a DRAW (equal points: {white_score})")
        
        return True, winner, {
            'reason': 'insufficient_material',
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
    
    # 4. Vérifier règle des 50 coups
    halfmove_clock = game_state.get('halfmove_clock', 0)
    if halfmove_clock >= 100:  # 50 coups de chaque joueur
        # ✅ Règle des 50 coups = Fin de partie MAIS on compare les points
        white_score = game_state.get('white_score', {}).get('points', 0)
        black_score = game_state.get('black_score', {}).get('points', 0)
        
        if white_score > black_score:
            winner = 'white'
            logger.info(f"⏱ 50-MOVE RULE! WHITE WINS by points ({white_score} vs {black_score})")
        elif black_score > white_score:
            winner = 'black'
            logger.info(f"⏱ 50-MOVE RULE! BLACK WINS by points ({black_score} vs {white_score})")
        else:
            winner = 'draw'
            logger.info(f"⏱ 50-MOVE RULE! Game is a DRAW (equal points: {white_score})")
        
        return True, winner, {
            'reason': '50_move_rule',
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
    
    # 5. Timeout global
    if timer.is_global_timeout():
        white_score = game_state.get('white_score', {}).get('points', 0)
        black_score = game_state.get('black_score', {}).get('points', 0)
        
        if white_score > black_score:
            winner = 'white'
        elif black_score > white_score:
            winner = 'black'
        else:
            winner = 'draw'
        
        return True, winner, {
            'reason': 'global_timeout',
            'white_score': game_state.get('white_score'),
            'black_score': game_state.get('black_score')
        }
    
    return False, None, {}


def is_checkmate(board: list, color: str) -> bool:
    """Vérifier si le joueur est en échec et mat."""
    # D'abord vérifier s'il est en échec
    if not is_in_check(board, color):
        return False
    
    # Ensuite vérifier s'il a des mouvements légaux pour sortir de l'échec
    return not has_legal_moves(board, color)


def is_stalemate(board: list, color: str) -> bool:
    """Vérifier si le joueur est en pat (pas en échec mais aucun mouvement légal)."""
    # Ne pas être en échec
    if is_in_check(board, color):
        return False
    
    # Mais n'avoir aucun mouvement légal
    return not has_legal_moves(board, color)


def is_in_check(board: list, color: str) -> bool:
    """Vérifier si le roi de la couleur donnée est en échec."""
    # Trouver la position du roi
    king_pos = find_king(board, color)
    if not king_pos:
        return False
    
    king_row, king_col = king_pos
    opponent_color = 'black' if color == 'white' else 'white'
    
    # Vérifier si une pièce adverse attaque le roi
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and isinstance(piece, dict) and piece.get('color') == opponent_color:
                if can_piece_attack(board, row, col, king_row, king_col):
                    return True
    
    return False


def find_king(board: list, color: str) -> Optional[tuple]:
    """Trouver la position du roi de la couleur donnée."""
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and isinstance(piece, dict):
                if piece.get('type') == 'K' and piece.get('color') == color:
                    return (row, col)
    return None


def has_legal_moves(board: list, color: str) -> bool:
    """Vérifier si le joueur a des mouvements légaux."""
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and isinstance(piece, dict) and piece.get('color') == color:
                # Obtenir tous les mouvements possibles pour cette pièce
                moves = get_possible_moves(board, row, col)
                for move_row, move_col in moves:
                    # Vérifier si ce mouvement est légal (ne laisse pas le roi en échec)
                    if is_move_legal(board, row, col, move_row, move_col, color):
                        return True
    return False


def is_move_legal(board: list, from_row: int, from_col: int, to_row: int, to_col: int, color: str) -> bool:
    """Vérifier si un mouvement est légal (ne laisse pas le roi en échec)."""
    # ✅ CRITIQUE: Copie profonde pour éviter de modifier le board original
    temp_board = copy.deepcopy(board)
    moving_piece = temp_board[from_row][from_col]
    captured_piece = temp_board[to_row][to_col]
    
    temp_board[to_row][to_col] = moving_piece
    temp_board[from_row][from_col] = None
    
    # Vérifier si le roi est en échec après ce mouvement
    in_check = is_in_check(temp_board, color)
    
    return not in_check


def can_piece_attack(board: list, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
    """Vérifier si une pièce peut attaquer une case donnée."""
    piece = board[from_row][from_col]
    if not piece or not isinstance(piece, dict):
        return False
    
    piece_type = piece.get('type')
    moves = get_possible_moves(board, from_row, from_col, check_for_check=False)
    
    return (to_row, to_col) in moves


def get_possible_moves(board: list, row: int, col: int, check_for_check: bool = True) -> list:
    """Obtenir tous les mouvements possibles pour une pièce."""
    piece = board[row][col]
    if not piece or not isinstance(piece, dict):
        return []
    
    piece_type = piece.get('type')
    color = piece.get('color')
    moves = []
    
    if piece_type == 'P':  # Pion
        moves = get_pawn_moves(board, row, col, color)
    elif piece_type == 'N':  # Cavalier
        moves = get_knight_moves(board, row, col, color)
    elif piece_type == 'B':  # Fou
        moves = get_bishop_moves(board, row, col, color)
    elif piece_type == 'R':  # Tour
        moves = get_rook_moves(board, row, col, color)
    elif piece_type == 'Q':  # Dame
        moves = get_queen_moves(board, row, col, color)
    elif piece_type == 'K':  # Roi
        moves = get_king_moves(board, row, col, color)
    
    return moves


def get_pawn_moves(board: list, row: int, col: int, color: str) -> list:
    """Obtenir les mouvements possibles pour un pion."""
    moves = []
    direction = -1 if color == 'white' else 1
    start_row = 6 if color == 'white' else 1
    
    # Avancer d'une case
    new_row = row + direction
    if 0 <= new_row < 8 and board[new_row][col] is None:
        moves.append((new_row, col))
        
        # Avancer de deux cases depuis la position de départ
        if row == start_row:
            new_row2 = row + 2 * direction
            if board[new_row2][col] is None:
                moves.append((new_row2, col))
    
    # Captures diagonales
    for dcol in [-1, 1]:
        new_row = row + direction
        new_col = col + dcol
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target and isinstance(target, dict) and target.get('color') != color:
                moves.append((new_row, new_col))
    
    return moves


def get_knight_moves(board: list, row: int, col: int, color: str) -> list:
    """Obtenir les mouvements possibles pour un cavalier."""
    moves = []
    knight_moves = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    
    for drow, dcol in knight_moves:
        new_row, new_col = row + drow, col + dcol
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None or (isinstance(target, dict) and target.get('color') != color):
                moves.append((new_row, new_col))
    
    return moves


def get_bishop_moves(board: list, row: int, col: int, color: str) -> list:
    """Obtenir les mouvements possibles pour un fou."""
    return get_sliding_moves(board, row, col, color, [(-1, -1), (-1, 1), (1, -1), (1, 1)])


def get_rook_moves(board: list, row: int, col: int, color: str) -> list:
    """Obtenir les mouvements possibles pour une tour."""
    return get_sliding_moves(board, row, col, color, [(-1, 0), (1, 0), (0, -1), (0, 1)])


def get_queen_moves(board: list, row: int, col: int, color: str) -> list:
    """Obtenir les mouvements possibles pour une dame."""
    return get_sliding_moves(board, row, col, color, [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1)
    ])


def get_king_moves(board: list, row: int, col: int, color: str) -> list:
    """Obtenir les mouvements possibles pour un roi."""
    moves = []
    king_moves = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]
    
    for drow, dcol in king_moves:
        new_row, new_col = row + drow, col + dcol
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None or (isinstance(target, dict) and target.get('color') != color):
                moves.append((new_row, new_col))
    
    return moves


def get_sliding_moves(board: list, row: int, col: int, color: str, directions: list) -> list:
    """Obtenir les mouvements pour les pièces qui glissent (fou, tour, dame)."""
    moves = []
    
    for drow, dcol in directions:
        new_row, new_col = row + drow, col + dcol
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None:
                moves.append((new_row, new_col))
            elif isinstance(target, dict):
                if target.get('color') != color:
                    moves.append((new_row, new_col))
                break
            else:
                break
            new_row += drow
            new_col += dcol
    
    return moves


def is_insufficient_material(board: list) -> bool:
    """
    Vérifier s'il y a matériel insuffisant pour mater selon les règles FIDE.
    Retourne True si aucun mat n'est possible avec le matériel restant.
    """
    white_pieces = []
    black_pieces = []
    white_bishops_squares = []  # Pour vérifier la couleur des cases des fous
    black_bishops_squares = []
    
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and isinstance(piece, dict):
                piece_type = piece.get('type')
                color = piece.get('color')
                
                if color == 'white':
                    white_pieces.append(piece_type)
                    if piece_type == 'B':
                        # Couleur de la case: (row + col) % 2 == 0 → case blanche
                        white_bishops_squares.append((row + col) % 2)
                else:
                    black_pieces.append(piece_type)
                    if piece_type == 'B':
                        black_bishops_squares.append((row + col) % 2)
    
    # 1. Roi contre roi
    if len(white_pieces) == 1 and len(black_pieces) == 1:
        return True
    
    # 2. Roi et cavalier contre roi
    if (len(white_pieces) == 2 and 'N' in white_pieces and len(black_pieces) == 1) or \
       (len(black_pieces) == 2 and 'N' in black_pieces and len(white_pieces) == 1):
        return True
    
    # 3. Roi et fou contre roi
    if (len(white_pieces) == 2 and 'B' in white_pieces and len(black_pieces) == 1) or \
       (len(black_pieces) == 2 and 'B' in black_pieces and len(white_pieces) == 1):
        return True
    
    # 4. Roi et fou contre roi et fou (si fous sur cases de même couleur)
    if (len(white_pieces) == 2 and 'B' in white_pieces and 
        len(black_pieces) == 2 and 'B' in black_pieces):
        if white_bishops_squares and black_bishops_squares:
            if white_bishops_squares[0] == black_bishops_squares[0]:
                # Les deux fous sont sur des cases de même couleur → impossible de mater
                return True
    
    # 5. Roi et plusieurs fous de même couleur contre roi (rare mais possible)
    if len(white_pieces) >= 2 and all(p in ['K', 'B'] for p in white_pieces) and len(black_pieces) == 1:
        # Si tous les fous sont sur la même couleur de case
        if white_bishops_squares and all(sq == white_bishops_squares[0] for sq in white_bishops_squares):
            return True
    
    if len(black_pieces) >= 2 and all(p in ['K', 'B'] for p in black_pieces) and len(white_pieces) == 1:
        if black_bishops_squares and all(sq == black_bishops_squares[0] for sq in black_bishops_squares):
            return True
    
    return False


def board_to_position_hash(board: list, current_player: str, castling_rights: dict, en_passant_target: Optional[str]) -> str:
    """
    Créer un hash unique de la position pour détecter les répétitions.
    Une position est identique si:
    - Le plateau est identique
    - C'est au tour du même joueur
    - Les droits de roque sont identiques
    - La case en passant est identique
    """
    import hashlib
    import json
    
    # Simplifier le board pour le hash (sans has_moved qui n'affecte pas la position visuelle)
    simple_board = []
    for row in board:
        simple_row = []
        for cell in row:
            if cell and isinstance(cell, dict):
                simple_row.append(f"{cell.get('color', '')}_{cell.get('type', '')}")
            else:
                simple_row.append('empty')
        simple_board.append(simple_row)
    
    position_data = {
        'board': simple_board,
        'current_player': current_player,
        'castling_rights': castling_rights,
        'en_passant': en_passant_target
    }
    
    position_str = json.dumps(position_data, sort_keys=True)
    return hashlib.md5(position_str.encode()).hexdigest()


def is_threefold_repetition(game_state: dict) -> bool:
    """
    Vérifier si la position actuelle s'est répétée 3 fois.
    Selon les règles FIDE, une partie est nulle si la même position
    apparaît 3 fois avec le même joueur au trait.
    """
    position_history = game_state.get('position_history', [])
    
    if len(position_history) < 3:
        return False
    
    # Créer le hash de la position actuelle
    current_hash = board_to_position_hash(
        game_state.get('board', []),
        game_state.get('current_player', 'white'),
        game_state.get('castling_rights', {}),
        game_state.get('en_passant_target')
    )
    
    # Compter combien de fois cette position apparaît dans l'historique
    count = position_history.count(current_hash)
    
    # Si la position actuelle + l'historique = 3 fois ou plus → triple répétition
    return count >= 2  # 2 dans l'historique + 1 actuelle = 3 total
