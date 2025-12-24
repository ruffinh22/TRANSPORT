# apps/games/game_logic/checkers_competitive.py
# ====================================
# Règles officielles des Dames - Variante compétitive 10x10
# Avec système de points et gestion du temps

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import copy
import logging

logger = logging.getLogger(__name__)


class PieceType(Enum):
    """Types de pièces pour les dames."""
    MAN = 'man'      # Pion simple
    KING = 'king'    # Dame (roi)


class Color(Enum):
    """Couleurs des joueurs."""
    RED = 'red'      # Joueur 1 (light)
    BLACK = 'black'  # Joueur 2 (dark)


@dataclass
class Position:
    """Position sur le damier 10x10."""
    row: int
    col: int
    
    def __str__(self):
        return f"({self.row}, {self.col})"
    
    def is_valid(self) -> bool:
        """Vérifier si la position est valide pour un plateau 10x10."""
        return 0 <= self.row < 10 and 0 <= self.col < 10
    
    def is_dark_square(self) -> bool:
        """Vérifier si c'est une case sombre (jouable)."""
        return (self.row + self.col) % 2 == 1
    
    def __eq__(self, other):
        return isinstance(other, Position) and self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))


@dataclass
class CheckersPiece:
    """Pièce de dames."""
    piece_type: PieceType
    color: Color
    
    def __str__(self):
        if self.color == Color.RED:
            return 'R' if self.piece_type == PieceType.MAN else 'RK'
        else:
            return 'B' if self.piece_type == PieceType.MAN else 'BK'
    
    def can_move_backward(self) -> bool:
        """Les dames peuvent reculer."""
        return self.piece_type == PieceType.KING
    
    def get_move_directions(self) -> List[Tuple[int, int]]:
        """Obtenir les directions de mouvement possibles."""
        if self.piece_type == PieceType.KING:
            # Les dames peuvent bouger dans toutes les directions diagonales
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            # Les pions ne peuvent avancer que vers l'avant
            if self.color == Color.RED:
                return [(-1, -1), (-1, 1)]  # Vers le haut
            else:
                return [(1, -1), (1, 1)]    # Vers le bas


@dataclass
class Move:
    """Mouvement dans les dames avec informations de score."""
    from_pos: Position
    to_pos: Position
    captured_pieces: List[Position]
    is_promotion: bool = False
    points_earned: int = 0
    is_multi_capture: bool = False
    
    def __str__(self):
        capture_str = f" captures {len(self.captured_pieces)} pièce(s)" if self.captured_pieces else ""
        promotion_str = " (promotion)" if self.is_promotion else ""
        multi_str = " (multi-capture)" if self.is_multi_capture else ""
        return f"{self.from_pos} -> {self.to_pos}{capture_str}{promotion_str}{multi_str} [{self.points_earned} pts]"
    
    def is_capture(self) -> bool:
        """Vérifier si c'est un mouvement de capture."""
        return len(self.captured_pieces) > 0
    
    def calculate_points(self, captured_piece_types: List[PieceType]) -> int:
        """
        Calculer les points gagnés pour ce mouvement.
        - Capture d'un pion: +1
        - Capture d'une dame: +3
        - Promotion en dame: +2
        - Coup multiple (enchaînement): +1 bonus
        """
        points = 0
        
        # Points pour les captures
        for piece_type in captured_piece_types:
            if piece_type == PieceType.MAN:
                points += 1
            elif piece_type == PieceType.KING:
                points += 3
        
        # Bonus pour coup multiple
        if len(captured_piece_types) > 1:
            points += 1
            self.is_multi_capture = True
        
        # Points pour promotion
        if self.is_promotion:
            points += 2
        
        self.points_earned = points
        return points


@dataclass
class PlayerScore:
    """Score d'un joueur."""
    color: Color
    points: int = 0
    pieces_captured: int = 0
    kings_captured: int = 0
    promotions: int = 0
    multi_captures: int = 0
    
    def add_move_score(self, move: Move, captured_piece_types: List[PieceType]):
        """Ajouter les points d'un mouvement."""
        self.points += move.points_earned
        
        for piece_type in captured_piece_types:
            if piece_type == PieceType.MAN:
                self.pieces_captured += 1
            elif piece_type == PieceType.KING:
                self.kings_captured += 1
        
        if move.is_promotion:
            self.promotions += 1
        
        if move.is_multi_capture:
            self.multi_captures += 1
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire."""
        return {
            'color': self.color.value,
            'points': self.points,
            'pieces_captured': self.pieces_captured,
            'kings_captured': self.kings_captured,
            'promotions': self.promotions,
            'multi_captures': self.multi_captures
        }


@dataclass
class GameTimer:
    """Gestion du temps de jeu."""
    move_time_limit: int = 120  # 120 secondes par coup (temporaire pour debug)
    global_time_limit: int = 21000  # 2 heures total (21000 secondes)
    
    # Temps restant pour chaque joueur
    red_time_remaining: float = 21000.0
    black_time_remaining: float = 21000.0
    
    # Timer du coup actuel
    current_move_start: Optional[datetime] = None
    current_player: Optional[Color] = None
    
    # Temps global de la partie
    game_start_time: Optional[datetime] = None
    
    def start_game(self):
        """Démarrer le chrono global."""
        self.game_start_time = datetime.now()
    
    def start_move(self, color: Color):
        """Démarrer le timer pour un coup."""
        self.current_move_start = datetime.now()
        self.current_player = color
    
    def end_move(self) -> tuple[bool, float]:
        """
        Terminer le timer du coup.
        Retourne (dépassement_20s, temps_utilisé)
        """
        if not self.current_move_start or not self.current_player:
            return False, 0.0
        
        elapsed = (datetime.now() - self.current_move_start).total_seconds()
        
        # Vérifier dépassement du coup (20s max par coup)
        move_timeout = elapsed > self.move_time_limit
        
        self.current_move_start = None
        self.current_player = None
        
        return move_timeout, elapsed
    
    def is_global_timeout(self) -> bool:
        """Vérifier si le temps global de la partie (300s) est écoulé."""
        if not self.game_start_time:
            return False
        
        elapsed = (datetime.now() - self.game_start_time).total_seconds()
        return elapsed >= self.global_time_limit
    
    def get_player_time_remaining(self, color: Color) -> float:
        """
        Obtenir le temps restant dans la partie (temps global - temps écoulé).
        Note: Le temps est GLOBAL pour tous les joueurs (300s pour toute la partie).
        """
        if not self.game_start_time:
            return self.global_time_limit
        
        elapsed = (datetime.now() - self.game_start_time).total_seconds()
        return max(0, self.global_time_limit - elapsed)
    
    def get_move_time_remaining(self) -> float:
        """Obtenir le temps restant pour le coup actuel."""
        if not self.current_move_start:
            return self.move_time_limit
        
        elapsed = (datetime.now() - self.current_move_start).total_seconds()
        return max(0, self.move_time_limit - elapsed)
    
    def has_player_timeout(self, color: Color) -> bool:
        """Vérifier si un joueur a dépassé les 20s pour son coup actuel."""
        if self.current_player != color or not self.current_move_start:
            return False
        
        elapsed = (datetime.now() - self.current_move_start).total_seconds()
        return elapsed > self.move_time_limit
    
    def to_dict(self) -> dict:
        """
        Convertir en dictionnaire avec temps EN TEMPS RÉEL.
        Les temps sont calculés à l'instant T pour être identiques pour tous les joueurs.
        """
        return {
            'move_time_limit': self.move_time_limit,
            'global_time_limit': self.global_time_limit,
            # Temps restant CALCULÉ EN TEMPS RÉEL (identique pour tous les clients)
            'red_time_remaining': self.get_player_time_remaining(Color.RED),
            'black_time_remaining': self.get_player_time_remaining(Color.BLACK),
            'move_time_remaining': self.get_move_time_remaining(),
            'global_timeout': self.is_global_timeout(),
            # Timestamps pour synchronisation côté frontend (backup si besoin)
            'current_move_start': self.current_move_start.isoformat() if self.current_move_start else None,
            'game_start_time': self.game_start_time.isoformat() if self.game_start_time else None,
            'current_player': self.current_player.value if self.current_player else None
        }


class CheckersBoard:
    """Plateau de dames 10x10 avec règles compétitives."""
    
    def __init__(self):
        self.size = 10  # Plateau 10x10 pour les dames internationales
        self.board: List[List[Optional[CheckersPiece]]] = [[None for _ in range(10)] for _ in range(10)]
        self.current_player = Color.RED
        self.move_history: List[Move] = []
        self.mandatory_capture_piece: Optional[Position] = None
        
        # Système de score
        self.red_score = PlayerScore(Color.RED)
        self.black_score = PlayerScore(Color.BLACK)
        
        # Gestion du temps
        self.timer = GameTimer()
        
        # Règles de nul
        self.position_history: List[str] = []  # Pour détecter 3 répétitions
        self.moves_since_capture: int = 0  # Pour règle des 50 coups
        self.game_over = False
        self.winner: Optional[Color] = None
        self.draw_reason: Optional[str] = None  # 'threefold_repetition', 'fifty_move_rule', 'stalemate'
        self.game_over_reason: Optional[str] = None  # ✅ Added for consistency with chess/ludo/cards: 'move_timeout', 'global_timeout', etc.
        
        self._setup_initial_position()
    
    def _setup_initial_position(self):
        """
        Placer les 20 pièces par joueur sur les 4 premières rangées.
        Plateau 10x10 - seulement cases noires utilisées.
        """
        # Pièces noires (dark) sur les 4 premières rangées
        for row in range(4):
            for col in range(10):
                if (row + col) % 2 == 1:  # Cases sombres seulement
                    self.board[row][col] = CheckersPiece(PieceType.MAN, Color.BLACK)
        
        # Pièces rouges (light) sur les 4 dernières rangées
        for row in range(6, 10):
            for col in range(10):
                if (row + col) % 2 == 1:  # Cases sombres seulement
                    self.board[row][col] = CheckersPiece(PieceType.MAN, Color.RED)
    
    def get_piece(self, position: Position) -> Optional[CheckersPiece]:
        """Obtenir la pièce à une position."""
        if not position.is_valid():
            return None
        return self.board[position.row][position.col]
    
    def set_piece(self, position: Position, piece: Optional[CheckersPiece]):
        """Placer une pièce à une position."""
        if position.is_valid():
            self.board[position.row][position.col] = piece
    
    def get_all_pieces(self, color: Color) -> List[Tuple[Position, CheckersPiece]]:
        """Obtenir toutes les pièces d'une couleur."""
        pieces = []
        for row in range(10):
            for col in range(10):
                pos = Position(row, col)
                piece = self.get_piece(pos)
                if piece and piece.color == color:
                    pieces.append((pos, piece))
        return pieces
    
    def _get_position_hash(self) -> str:
        """Obtenir un hash unique de la position actuelle (pour détecter répétitions)."""
        position_str = f"{self.current_player.value}:"
        for row in range(10):
            for col in range(10):
                piece = self.board[row][col]
                if piece:
                    position_str += f"{row}{col}{piece.piece_type.value}{piece.color.value},"
        return position_str
    
    def _check_promotion(self, piece: CheckersPiece, new_position: Position) -> bool:
        """
        Vérifier si une pièce doit être promue en dame.
        Un pion devient dame en atteignant la dernière rangée adverse.
        """
        if piece.piece_type == PieceType.KING:
            return False
        
        # Rouge atteint la rangée 0 (haut)
        if piece.color == Color.RED and new_position.row == 0:
            return True
        # Noir atteint la rangée 9 (bas)
        elif piece.color == Color.BLACK and new_position.row == 9:
            return True
        
        return False
    
    def get_possible_moves(self, position: Position) -> List[Move]:
        """
        Obtenir tous les mouvements possibles pour une pièce.
        RÈGLE: Si une capture est possible, elle est OBLIGATOIRE.
        """
        piece = self.get_piece(position)
        if not piece or piece.color != self.current_player:
            return []
        
        # ✅ CORRECTION CRITIQUE: Valider que mandatory_capture_piece existe toujours et peut capturer
        if self.mandatory_capture_piece:
            mandatory_piece = self.get_piece(self.mandatory_capture_piece)
            if not mandatory_piece or mandatory_piece.color != self.current_player:
                # La pièce obligatoire n'existe plus ou a changé de couleur, réinitialiser
                logger.warning(f"⚠️ mandatory_capture_piece {self.mandatory_capture_piece} no longer valid, resetting")
                self.mandatory_capture_piece = None
            else:
                # Vérifier si la pièce obligatoire peut encore capturer
                mandatory_captures = self._get_capture_moves(self.mandatory_capture_piece, mandatory_piece)
                if not mandatory_captures:
                    # Plus de captures possibles avec cette pièce, réinitialiser
                    logger.warning(f"⚠️ mandatory_capture_piece {self.mandatory_capture_piece} has no more captures, resetting")
                    self.mandatory_capture_piece = None
        
        # Si une capture est obligatoire et que cette pièce n'est pas celle qui doit capturer
        if self.mandatory_capture_piece and self.mandatory_capture_piece != position:
            return []
        
        # Vérifier d'abord les captures obligatoires
        capture_moves = self._get_capture_moves(position, piece)
        if capture_moves:
            return capture_moves
        
        # Si pas de captures obligatoires, mouvements normaux
        if not self.mandatory_capture_piece:
            return self._get_normal_moves(position, piece)
        
        return []
    
    def _get_normal_moves(self, position: Position, piece: CheckersPiece) -> List[Move]:
        """
        Obtenir les mouvements normaux (sans capture).
        - Pion: 1 case en diagonale vers l'avant
        - Dame: autant de cases qu'elle veut en diagonale
        """
        moves = []
        directions = piece.get_move_directions()
        
        for dr, dc in directions:
            if piece.piece_type == PieceType.MAN:
                # Pion: un seul pas
                new_pos = Position(position.row + dr, position.col + dc)
                if new_pos.is_valid() and new_pos.is_dark_square():
                    if self.get_piece(new_pos) is None:
                        is_promotion = self._check_promotion(piece, new_pos)
                        move = Move(position, new_pos, [], is_promotion)
                        move.calculate_points([])
                        moves.append(move)
            
            else:
                # Dame: plusieurs pas possibles
                for distance in range(1, 10):
                    new_pos = Position(position.row + dr * distance, position.col + dc * distance)
                    if not new_pos.is_valid() or not new_pos.is_dark_square():
                        break
                    
                    target_piece = self.get_piece(new_pos)
                    if target_piece is None:
                        move = Move(position, new_pos, [])
                        move.calculate_points([])
                        moves.append(move)
                    else:
                        break  # Pièce bloque le chemin
        
        return moves
    
    def _get_capture_moves(self, position: Position, piece: CheckersPiece) -> List[Move]:
        """
        Obtenir les mouvements de capture.
        Les captures multiples sont automatiquement calculées.
        """
        captures = []
        directions = piece.get_move_directions()
        
        for dr, dc in directions:
            if piece.piece_type == PieceType.MAN:
                # Capture simple pour les pions
                captures.extend(self._get_man_captures(position, piece, dr, dc, []))
            else:
                # Capture pour les dames (à distance)
                captures.extend(self._get_king_captures(position, piece, dr, dc, []))
        
        # Filtrer pour ne garder que les captures maximales (règle de priorité)
        if captures:
            max_captures = max(len(move.captured_pieces) for move in captures)
            captures = [move for move in captures if len(move.captured_pieces) == max_captures]
        
        return captures
    
    def _get_man_captures(self, position: Position, piece: CheckersPiece, 
                          dr: int, dc: int, already_captured: List[Position]) -> List[Move]:
        """
        Captures pour un pion (saut par-dessus une pièce ennemie).
        ⚠️ IMPORTANT: Ne retourne QUE les captures IMMÉDIATES (une seule capture).
        Les captures multiples sont gérées par le système mandatory_capture_piece.
        """
        captures = []
        
        enemy_pos = Position(position.row + dr, position.col + dc)
        landing_pos = Position(position.row + 2*dr, position.col + 2*dc)
        
        logger.debug(f"🎯 Checking capture: from {position} dir ({dr},{dc}) enemy {enemy_pos} landing {landing_pos}")
        
        if (enemy_pos.is_valid() and landing_pos.is_valid() and
            enemy_pos.is_dark_square() and landing_pos.is_dark_square() and
            enemy_pos not in already_captured):
            
            enemy_piece = self.get_piece(enemy_pos)
            landing_piece = self.get_piece(landing_pos)
            
            logger.debug(f"  Enemy piece: {enemy_piece}, Landing: {landing_piece}")
            
            if (enemy_piece and enemy_piece.color != piece.color and 
                landing_piece is None):
                logger.info(f"✅ CAPTURE IMMÉDIATE POSSIBLE: {position} -> {landing_pos} capturing {enemy_pos}")
                
                new_captured = [enemy_pos]  # ✅ Une seule capture
                is_promotion = self._check_promotion(piece, landing_pos)
                
                # ✅ NE PAS chercher les captures additionnelles ici
                # Le système mandatory_capture_piece s'en occupera
                move = Move(position, landing_pos, new_captured, is_promotion)
                captured_types = [self.get_piece(pos).piece_type for pos in new_captured]
                move.calculate_points(captured_types)
                captures.append(move)
        
        return captures
    
    def _get_additional_man_captures(self, position: Position, original_piece: CheckersPiece,
                                     already_captured: List[Position], 
                                     is_promoted: bool) -> List[Move]:
        """Chercher des captures additionnelles pour un pion (captures multiples)."""
        additional_moves = []
        
        # Si le pion vient d'être promu, il ne peut pas continuer à capturer ce tour
        if is_promoted:
            return []
        
        directions = original_piece.get_move_directions()
        
        for dr, dc in directions:
            enemy_pos = Position(position.row + dr, position.col + dc)
            landing_pos = Position(position.row + 2*dr, position.col + 2*dc)
            
            if (enemy_pos.is_valid() and landing_pos.is_valid() and
                enemy_pos.is_dark_square() and landing_pos.is_dark_square() and
                enemy_pos not in already_captured):
                
                enemy_piece = self.get_piece(enemy_pos)
                landing_piece = self.get_piece(landing_pos)
                
                if (enemy_piece and enemy_piece.color != original_piece.color and 
                    landing_piece is None):
                    
                    new_captured = already_captured + [enemy_pos]
                    new_promotion = self._check_promotion(original_piece, landing_pos)
                    
                    # Récursion pour chercher encore plus de captures
                    further = self._get_additional_man_captures(
                        landing_pos, original_piece, new_captured, new_promotion
                    )
                    
                    if further:
                        additional_moves.extend(further)
                    else:
                        # Fin de la chaîne de captures
                        # Retrouver la position de départ
                        original_pos = self._reconstruct_origin(position, already_captured)
                        move = Move(original_pos, landing_pos, new_captured, new_promotion)
                        captured_types = [self.get_piece(pos).piece_type for pos in new_captured]
                        move.calculate_points(captured_types)
                        additional_moves.append(move)
        
        return additional_moves
    
    def _get_king_captures(self, position: Position, piece: CheckersPiece,
                          dr: int, dc: int, already_captured: List[Position]) -> List[Move]:
        """
        Captures pour une dame.
        La dame peut capturer à distance et atterrir sur n'importe quelle case libre après la pièce capturée.
        ⚠️ IMPORTANT: Ne retourne QUE les captures IMMÉDIATES (une seule capture).
        Les captures multiples sont gérées par le système mandatory_capture_piece.
        """
        captures = []
        
        # Chercher la première pièce ennemie dans cette direction
        for distance in range(1, 10):
            enemy_pos = Position(position.row + dr * distance, position.col + dc * distance)
            if not enemy_pos.is_valid() or not enemy_pos.is_dark_square():
                break
            
            if enemy_pos in already_captured:
                break
            
            enemy_piece = self.get_piece(enemy_pos)
            if enemy_piece:
                if enemy_piece.color != piece.color:
                    # Trouver toutes les cases d'atterrissage possibles après la capture
                    for landing_distance in range(distance + 1, 10):
                        landing_pos = Position(
                            position.row + dr * landing_distance,
                            position.col + dc * landing_distance
                        )
                        
                        if not landing_pos.is_valid() or not landing_pos.is_dark_square():
                            break
                        
                        if self.get_piece(landing_pos) is None:
                            new_captured = [enemy_pos]  # ✅ Une seule capture
                            
                            # ✅ NE PAS chercher les captures additionnelles ici
                            # Le système mandatory_capture_piece s'en occupera
                            move = Move(position, landing_pos, new_captured)
                            captured_types = [self.get_piece(pos).piece_type for pos in new_captured]
                            move.calculate_points(captured_types)
                            captures.append(move)
                        else:
                            break
                break
            
        return captures
    
    def _get_additional_king_captures(self, position: Position, piece: CheckersPiece,
                                      already_captured: List[Position]) -> List[Move]:
        """Chercher des captures additionnelles pour une dame."""
        additional_moves = []
        directions = piece.get_move_directions()
        
        for dr, dc in directions:
            # Chercher une pièce ennemie dans cette direction
            for distance in range(1, 10):
                enemy_pos = Position(position.row + dr * distance, position.col + dc * distance)
                if not enemy_pos.is_valid() or not enemy_pos.is_dark_square():
                    break
                
                if enemy_pos in already_captured:
                    break
                
                enemy_piece = self.get_piece(enemy_pos)
                if enemy_piece:
                    if enemy_piece.color != piece.color:
                        # Cases d'atterrissage possibles
                        for landing_distance in range(distance + 1, 10):
                            landing_pos = Position(
                                position.row + dr * landing_distance,
                                position.col + dc * landing_distance
                            )
                            
                            if not landing_pos.is_valid() or not landing_pos.is_dark_square():
                                break
                            
                            if self.get_piece(landing_pos) is None:
                                new_captured = already_captured + [enemy_pos]
                                
                                # Récursion
                                further = self._get_additional_king_captures(landing_pos, piece, new_captured)
                                
                                if further:
                                    additional_moves.extend(further)
                                else:
                                    original_pos = self._reconstruct_origin(position, already_captured)
                                    move = Move(original_pos, landing_pos, new_captured)
                                    captured_types = [self.get_piece(pos).piece_type for pos in new_captured]
                                    move.calculate_points(captured_types)
                                    additional_moves.append(move)
                            else:
                                break
                    break
        
        return additional_moves
    
    def _reconstruct_origin(self, current_pos: Position, captures: List[Position]) -> Position:
        """
        Reconstruire la position d'origine d'un enchaînement de captures.
        Cette méthode est simplifiée - dans une vraie implémentation,
        il faudrait tracer le chemin complet.
        """
        # Pour l'instant, on retourne la position actuelle
        # TODO: Implémenter un traçage correct du chemin
        return current_pos
    
    def has_mandatory_captures(self, color: Color) -> bool:
        """
        Vérifier s'il y a des captures obligatoires.
        RÈGLE: Si une capture est possible, elle est OBLIGATOIRE.
        """
        pieces = self.get_all_pieces(color)
        
        for pos, piece in pieces:
            capture_moves = self._get_capture_moves(pos, piece)
            if capture_moves:
                return True
        
        return False
    
    def check_and_handle_move_timeout(self) -> bool:
        """
        Vérifier si le joueur actuel a dépassé 120s sans jouer.
        Si oui, déclarer l'adversaire gagnant automatiquement.
        Retourne True si le timeout a été géré, False sinon.
        """
        if not self.timer.current_move_start:
            # Timer pas démarré - cela ne devrait pas arriver car le timer
            # est démarré lors de la création du jeu et à chaque changement de tour
            logger.warning(f"⚠️ Timer not started for {self.current_player.value} - starting now")
            self.timer.start_move(self.current_player)
            return False
        
        # 🔍 DEBUG: Vérifier la synchronisation board vs timer
        logger.info(f"🔍 DEBUG SYNC: board.current_player={self.current_player.value}, timer.current_player={self.timer.current_player.value if self.timer.current_player else 'None'}")
        
        elapsed = (datetime.now() - self.timer.current_move_start).total_seconds()
        
        if elapsed > self.timer.move_time_limit:
            timeout_player = self.current_player
            winner = Color.BLACK if timeout_player == Color.RED else Color.RED
            
            logger.warning(f"⏱️ {self.timer.move_time_limit}s TIMEOUT for {timeout_player.value}. {winner.value.upper()} WINS!")
            logger.warning(f"🔍 DEBUG TIMEOUT: current_player={timeout_player.value}, timeout_player={timeout_player.value}, winner={winner.value}")
            logger.warning(f"🔍 DEBUG TIMEOUT: elapsed={elapsed}s, move_time_limit={self.timer.move_time_limit}s")
            
            # ✅ Déclarer l'adversaire gagnant et terminer la partie
            self.game_over = True
            self.winner = winner
            # Pas de draw_reason car il y a un winner
            
            # ✅ Ajouter game_over_details pour cohérence avec chess/ludo/cards
            self.game_over_reason = 'move_timeout'
            
            return True
        
        return False
    
    def make_move(self, move: Move) -> bool:
        """
        Effectuer un mouvement.
        Met à jour le plateau, le score et gère le timer.
        """
        # Vérifier d'abord si le joueur actuel a déjà timeout (20s écoulées)
        if self.check_and_handle_move_timeout():
            logger.warning(f"Move rejected: {self.current_player.value} has already timed out")
            return False
        
        # Si le timer du coup n'est pas démarré, le démarrer maintenant
        if not self.timer.current_move_start:
            logger.info(f"Starting move timer for {self.current_player.value}")
            self.timer.start_move(self.current_player)
        
        piece = self.get_piece(move.from_pos)
        if not piece or piece.color != self.current_player:
            logger.error(f"make_move failed: no piece or wrong color. Piece: {piece}, current_player: {self.current_player}")
            return False
        
        # Vérifier que le mouvement est légal
        possible_moves = self.get_possible_moves(move.from_pos)
        logger.info(f"make_move: found {len(possible_moves)} possible moves for {move.from_pos}")
        
        # Trouver le mouvement correspondant
        matching_move = None
        logger.info(f"Looking for match: to_pos={move.to_pos} (type: {type(move.to_pos)}), captured={move.captured_pieces}")
        
        for i, possible_move in enumerate(possible_moves):
            logger.info(f"  Possible move {i}: to_pos={possible_move.to_pos} (type: {type(possible_move.to_pos)}), captured={possible_move.captured_pieces}")
            logger.info(f"    Position match: {possible_move.to_pos == move.to_pos}")
            logger.info(f"    Captured match: {set(possible_move.captured_pieces) == set(move.captured_pieces)}")
            
            # Compare positions by coordinates
            pos_match = (possible_move.to_pos.row == move.to_pos.row and 
                        possible_move.to_pos.col == move.to_pos.col)
            
            # ✅ CORRECTION: Si le frontend n'a pas fourni captured_pieces, on accepte le mouvement
            # basé uniquement sur la position de destination
            if not move.captured_pieces:
                # Frontend n'a pas fourni les captures, on fait confiance au backend
                logger.info(f"  🔧 Frontend didn't provide captured_pieces, matching by position only")
                captured_match = True  # On accepte n'importe quel mouvement vers cette position
            else:
                # Frontend a fourni les captures, on vérifie qu'elles correspondent
                captured_match = len(possible_move.captured_pieces) == len(move.captured_pieces)
                if captured_match and move.captured_pieces:
                    for cap in move.captured_pieces:
                        found = False
                        for poss_cap in possible_move.captured_pieces:
                            if poss_cap.row == cap.row and poss_cap.col == cap.col:
                                found = True
                                break
                        if not found:
                            captured_match = False
                            break
            
            logger.info(f"    Position match: {pos_match}")
            logger.info(f"    Captured match: {captured_match}")
            logger.info(f"    Final match result: pos_match={pos_match}, captured_match={captured_match}")
            
            if pos_match and captured_match:
                matching_move = possible_move
                logger.info(f"  ✅ Found matching move at index {i}")
                break
        
        if not matching_move:
            logger.error(f"make_move failed: no matching move found. Wanted: {move.from_pos} -> {move.to_pos}, captured: {move.captured_pieces}")
            logger.error(f"Possible moves: {[(m.to_pos, m.captured_pieces) for m in possible_moves]}")
            return False
        
        # Utiliser le mouvement validé avec les points corrects
        move = matching_move
        logger.info(f"✅ Using matched move: {move}")
        
        # Terminer le timer du coup
        timeout, time_used = self.timer.end_move()
        logger.info(f"Timer ended: timeout={timeout}, time_used={time_used}s")
        
        if timeout:
            # Le joueur a dépassé 20 secondes, il perd son tour
            logger.warning(f"⏰ Move timeout detected ({time_used}s > 20s), switching player")
            self._switch_player()
            return False
        
        logger.info(f"✅ Timer OK, proceeding with move execution")
        
        # Effectuer le mouvement
        self.set_piece(move.from_pos, None)
        
        # Récupérer les types de pièces capturées avant de les supprimer
        captured_types = [self.get_piece(pos).piece_type for pos in move.captured_pieces]
        
        # Supprimer les pièces capturées
        for captured_pos in move.captured_pieces:
            self.set_piece(captured_pos, None)
        
        # Gérer la promotion
        if move.is_promotion:
            promoted_piece = CheckersPiece(PieceType.KING, piece.color)
            self.set_piece(move.to_pos, promoted_piece)
        else:
            self.set_piece(move.to_pos, piece)
        
        # Mettre à jour le score
        if piece.color == Color.RED:
            self.red_score.add_move_score(move, captured_types)
        else:
            self.black_score.add_move_score(move, captured_types)
        
        # Vérifier si d'autres captures sont possibles avec la même pièce
        if move.is_capture():
            current_piece = self.get_piece(move.to_pos)
            additional_captures = self._get_capture_moves(move.to_pos, current_piece)
            if additional_captures:
                # La même pièce doit continuer à capturer
                self.mandatory_capture_piece = move.to_pos
                logger.warning(f"🔄 CAPTURES MULTIPLES: La pièce en {move.to_pos} DOIT continuer à capturer!")
                logger.warning(f"   {len(additional_captures)} capture(s) supplémentaire(s) possible(s)")
                logger.warning(f"   Le joueur {self.current_player.value} DOIT rejouer avec cette pièce")
            else:
                self.mandatory_capture_piece = None
                logger.info(f"✅ Pas de capture supplémentaire, changement de joueur")
                self._switch_player()
            
            # Réinitialiser le compteur de coups sans capture
            self.moves_since_capture = 0
        else:
            self.mandatory_capture_piece = None
            self._switch_player()
            
            # Incrémenter le compteur de coups sans capture
            self.moves_since_capture += 1
        
        # Ajouter à l'historique
        self.move_history.append(move)
        
        # Enregistrer la position actuelle dans l'historique (pour règle des 3 répétitions)
        position_hash = self._get_position_hash()
        self.position_history.append(position_hash)
        
        logger.info(f"✅ Move completed successfully! New state: player={self.current_player.value}, mandatory_capture={self.mandatory_capture_piece}")
        logger.info(f"   Moves since capture: {self.moves_since_capture}, Position history size: {len(self.position_history)}")
        return True
    
    def _switch_player(self):
        """Changer de joueur et démarrer son timer."""
        self.current_player = Color.BLACK if self.current_player == Color.RED else Color.RED
        self.timer.start_move(self.current_player)
    
    def is_game_over(self) -> bool:
        """
        Vérifier si le jeu est terminé.
        Causes: plus de pièces, aucun mouvement possible, timeout de 120s par coup,
        timeout global (21000s), 3 répétitions de position, 50 coups sans capture, ou pat (stalemate).
        """
        if self.game_over:
            return True
        
        # Timeout global de la partie (21000s pour tous les joueurs)
        if self.timer.is_global_timeout():
            self.game_over = True
            # ✅ Determine winner by who has more pieces or time advantage
            timeout_player = self.timer.current_player
            self.winner = Color.BLACK if timeout_player == Color.RED else Color.RED
            self.game_over_reason = 'global_timeout'
            return True
        
        # Règle des 3 répétitions → nul
        if self._check_threefold_repetition():
            self.game_over = True
            self.winner = None
            self.draw_reason = 'threefold_repetition'
            self.game_over_reason = 'threefold_repetition'
            return True
        
        # Règle des 50 coups sans capture → nul
        if self.moves_since_capture >= 50:
            self.game_over = True
            self.winner = None
            self.draw_reason = 'fifty_move_rule'
            self.game_over_reason = 'fifty_move_rule'
            return True
        
        # Pat (stalemate) → nul (pas défaite)
        if self._is_stalemate():
            self.game_over = True
            self.winner = None
            self.draw_reason = 'stalemate'
            self.game_over_reason = 'stalemate'
            return True
        
        # Plus de pièces ou aucun mouvement
        return self.get_winner_by_pieces() is not None
    
    def get_winner_by_pieces(self) -> Optional[Color]:
        """Déterminer le gagnant par élimination/blocage (mais pas pat)."""
        red_pieces = self.get_all_pieces(Color.RED)
        black_pieces = self.get_all_pieces(Color.BLACK)
        
        # Pas de pièces = défaite
        if not red_pieces:
            self.game_over = True
            self.winner = Color.BLACK
            self.game_over_reason = 'elimination'
            return Color.BLACK
        elif not black_pieces:
            self.game_over = True
            self.winner = Color.RED
            self.game_over_reason = 'elimination'
            return Color.RED
        
        # Pas de mouvements légaux uniquement si c'est le tour du joueur
        # et qu'il a encore des pièces (sinon c'est un pat)
        if self.current_player == Color.RED:
            red_moves = self._count_legal_moves(Color.RED)
            if red_moves == 0 and red_pieces:
                # Vérifier si c'est un pat ou un blocage
                # Si l'adversaire peut aussi bouger, c'est un blocage, sinon pat
                black_moves = self._count_legal_moves(Color.BLACK)
                if black_moves > 0:
                    self.game_over = True
                    self.winner = Color.BLACK
                    self.game_over_reason = 'no_moves'
                    return Color.BLACK  # Rouge bloqué, noir gagne
        elif self.current_player == Color.BLACK:
            black_moves = self._count_legal_moves(Color.BLACK)
            if black_moves == 0 and black_pieces:
                red_moves = self._count_legal_moves(Color.RED)
                if red_moves > 0:
                    self.game_over = True
                    self.winner = Color.RED
                    self.game_over_reason = 'no_moves'
                    return Color.RED  # Noir bloqué, rouge gagne
        
        return None
    
    def _count_legal_moves(self, color: Color) -> int:
        """Compter le nombre de mouvements légaux."""
        pieces = self.get_all_pieces(color)
        total = 0
        
        # IMPORTANT: Sauvegarder le joueur actuel
        original_player = self.current_player
        
        # Temporairement changer le joueur actuel pour compter ses mouvements
        self.current_player = color
        
        for pos, piece in pieces:
            moves = self.get_possible_moves(pos)
            total += len(moves)
            
            # ✅ DEBUG: Logger si aucun mouvement mais pièce existe
            if len(moves) == 0 and self.mandatory_capture_piece:
                logger.debug(f"🔍 Piece {piece} at {pos} has 0 moves (mandatory_capture={self.mandatory_capture_piece})")
        
        # ✅ DEBUG: Logger le total
        logger.debug(f"🔍 Total legal moves for {color.value}: {total} pieces")
        
        # Restaurer le joueur actuel
        self.current_player = original_player
        
        return total
    
    def get_winner(self) -> Optional[Color]:
        """
        Obtenir le gagnant final.
        Retourne None si match nul (3 répétitions, 50 coups, stalemate, égalité de points).
        Si timeout global: gagne celui avec le plus de points.
        Sinon: gagne par élimination/blocage.
        """
        # ✅ PRIORITÉ 1: Si le winner a déjà été défini (timeout, surrender, etc.), le retourner
        if self.winner is not None:
            return self.winner
        
        # Match nul explicite (règles de nul)
        if self.winner is None and self.draw_reason:
            return None
        
        # Victoire par élimination/blocage
        winner_by_pieces = self.get_winner_by_pieces()
        if winner_by_pieces:
            return winner_by_pieces
        
        # Victoire par timeout global (21000s écoulées): celui avec le plus de points
        if self.timer.is_global_timeout():
            return self._get_winner_by_score()
        
        return None
    
    def _get_winner_by_score(self) -> Optional[Color]:
        """Déterminer le gagnant par les points."""
        if self.red_score.points > self.black_score.points:
            return Color.RED
        elif self.black_score.points > self.red_score.points:
            return Color.BLACK
        else:
            return None  # Match nul
    
    def _check_threefold_repetition(self) -> bool:
        """Vérifier si la position actuelle s'est répétée 3 fois."""
        if len(self.position_history) < 6:  # Besoin d'au moins 6 coups pour 3 répétitions
            return False
        
        current_position = self._get_position_hash()
        count = self.position_history.count(current_position)
        return count >= 2  # 2 dans l'historique + 1 actuelle = 3 répétitions
    
    def _is_stalemate(self) -> bool:
        """Vérifier si c'est un pat (joueur actuel ne peut pas bouger mais n'est pas bloqué)."""
        current_player_pieces = self.get_all_pieces(self.current_player)
        if not current_player_pieces:
            return False  # Pas de pièces = défaite, pas pat
        
        current_moves = self._count_legal_moves(self.current_player)
        if current_moves > 0:
            return False  # Peut bouger = pas pat
        
        # Le joueur ne peut pas bouger
        # C'est un pat si les deux joueurs ne peuvent pas bouger
        # ou si c'est une position où personne ne peut progresser
        opponent = Color.BLACK if self.current_player == Color.RED else Color.RED
        opponent_moves = self._count_legal_moves(opponent)
        
        # Pat si les deux joueurs sont bloqués
        return opponent_moves == 0
    
    def get_game_result(self) -> Optional[dict]:
        """Obtenir le résultat détaillé de la partie."""
        if not self.is_game_over():
            return None
        
        winner = self.get_winner()
        
        result = {
            'winner': winner.value if winner else 'draw',
            'red_score': self.red_score.to_dict(),
            'black_score': self.black_score.to_dict(),
            'timer': self.timer.to_dict(),
            'total_moves': len(self.move_history),
            'moves_since_capture': self.moves_since_capture
        }
        
        # Déterminer la raison de la fin
        if self.draw_reason:
            result['reason'] = self.draw_reason
        elif self.timer.is_global_timeout():
            result['reason'] = 'global_timeout'
        elif not self.get_all_pieces(Color.RED if winner == Color.BLACK else Color.BLACK):
            result['reason'] = 'elimination'
        else:
            result['reason'] = 'no_legal_moves'
        
        return result
    
    def to_dict(self) -> dict:
        """Convertir l'état complet en dictionnaire."""
        board_state = []
        for row in range(10):
            board_row = []
            for col in range(10):
                piece = self.board[row][col]
                if piece:
                    board_row.append({
                        'type': piece.piece_type.value,
                        'color': piece.color.value
                    })
                else:
                    board_row.append(None)
            board_state.append(board_row)
        
        return {
            'board': board_state,
            'current_player': self.current_player.value,
            'size': self.size,
            'mandatory_capture_piece': {
                'row': self.mandatory_capture_piece.row,
                'col': self.mandatory_capture_piece.col
            } if self.mandatory_capture_piece else None,
            'has_mandatory_capture': self.mandatory_capture_piece is not None,  # ✅ Indicateur clair pour le frontend
            'red_score': self.red_score.to_dict(),
            'black_score': self.black_score.to_dict(),
            'timer': self.timer.to_dict(),
            'game_over': self.is_game_over(),  # ✅ Changed from 'is_game_over' to 'game_over' for consistency with chess/ludo/cards
            'is_game_over': self.is_game_over(),  # ✅ Keep for backward compatibility with frontend
            'winner': self.get_winner().value if self.get_winner() else None,
            'game_result': self.get_game_result(),
            'moves_since_capture': self.moves_since_capture,
            'draw_reason': self.draw_reason,
            'game_over_details': {  # ✅ Added for consistency with chess/ludo/cards
                'reason': self.game_over_reason or self.draw_reason or 'normal',
                'red_score': self.red_score.to_dict(),
                'black_score': self.black_score.to_dict()
            } if self.is_game_over() else None,
            'position_history': self.position_history
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CheckersBoard':
        """Créer un plateau depuis un dictionnaire."""
        board = cls.__new__(cls)
        board.size = 10
        board.board = [[None for _ in range(10)] for _ in range(10)]
        
        # Restaurer les pièces
        for row in range(10):
            for col in range(10):
                if row < len(data['board']) and col < len(data['board'][row]):
                    piece_data = data['board'][row][col]
                    if piece_data:
                        piece_type = PieceType(piece_data['type'])
                        color = Color(piece_data['color'])
                        board.board[row][col] = CheckersPiece(piece_type, color)
        
        # Restaurer l'état
        board.current_player = Color(data['current_player'])
        
        if data.get('mandatory_capture_piece'):
            board.mandatory_capture_piece = Position(
                data['mandatory_capture_piece']['row'],
                data['mandatory_capture_piece']['col']
            )
        else:
            board.mandatory_capture_piece = None
        
        # Restaurer les scores
        if 'red_score' in data:
            red_data = data['red_score']
            board.red_score = PlayerScore(
                Color.RED,
                red_data.get('points', 0),
                red_data.get('pieces_captured', 0),
                red_data.get('kings_captured', 0),
                red_data.get('promotions', 0),
                red_data.get('multi_captures', 0)
            )
        else:
            board.red_score = PlayerScore(Color.RED)
        
        if 'black_score' in data:
            black_data = data['black_score']
            board.black_score = PlayerScore(
                Color.BLACK,
                black_data.get('points', 0),
                black_data.get('pieces_captured', 0),
                black_data.get('kings_captured', 0),
                black_data.get('promotions', 0),
                black_data.get('multi_captures', 0)
            )
        else:
            board.black_score = PlayerScore(Color.BLACK)
        
        # Restaurer le timer
        if 'timer' in data:
            timer_data = data['timer']
            board.timer = GameTimer(
                move_time_limit=timer_data.get('move_time_limit', 120),
                global_time_limit=timer_data.get('global_time_limit', 21000)
            )
            # Note: red_time_remaining et black_time_remaining ne sont plus utilisés
            # car le temps est GLOBAL (21000s pour toute la partie)
            
            # Restaurer les timestamps pour calcul temps réel (convert to naive datetime)
            # IMPORTANT: Restaurer current_move_start pour que le timeout fonctionne
            if timer_data.get('current_move_start'):
                ts = datetime.fromisoformat(timer_data['current_move_start'])
                board.timer.current_move_start = ts.replace(tzinfo=None) if ts.tzinfo else ts
            else:
                board.timer.current_move_start = None
            
            if timer_data.get('game_start_time'):
                ts = datetime.fromisoformat(timer_data['game_start_time'])
                board.timer.game_start_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
            if timer_data.get('current_player'):
                board.timer.current_player = Color(timer_data['current_player'])
        else:
            board.timer = GameTimer()
        
        # Restaurer les nouveaux champs pour règles de nul
        board.position_history = data.get('position_history', [])
        board.moves_since_capture = data.get('moves_since_capture', 0)
        board.game_over = data.get('is_game_over', False) or data.get('game_over', False)  # ✅ Support both keys
        board.draw_reason = data.get('draw_reason', None)
        board.game_over_reason = data.get('game_over_details', {}).get('reason') if data.get('game_over_details') else None  # ✅ Added
        
        # Restaurer winner si présent
        if data.get('winner'):
            board.winner = Color(data['winner'])
        else:
            board.winner = None
        
        board.move_history = []
        
        return board


# ==========================================
# Fonctions utilitaires pour l'intégration
# ==========================================

def create_competitive_checkers_game() -> dict:
    """Créer une nouvelle partie de dames compétitive."""
    board = CheckersBoard()
    board.timer.start_game()
    board.timer.start_move(Color.RED)
    return board.to_dict()

def make_competitive_checkers_move(game_data: dict, move_data: dict) -> tuple[dict, bool, str]:
    """
    Effectuer un mouvement dans une partie de dames compétitive.
    
    move_data format:
    {
        'from': {'row': int, 'col': int},
        'to': {'row': int, 'col': int}
    }
    """
    try:
        # Reconstruire l'état du jeu
        board = CheckersBoard.from_dict(game_data)
        
        # Créer le mouvement
        from_pos = Position(move_data['from']['row'], move_data['from']['col'])
        to_pos = Position(move_data['to']['row'], move_data['to']['col'])
        
        # Trouver le mouvement légal correspondant
        possible_moves = board.get_possible_moves(from_pos)
        
        for move in possible_moves:
            if move.to_pos == to_pos:
                # Effectuer le mouvement
                success = board.make_move(move)
                
                if success:
                    new_state = board.to_dict()
                    return new_state, True, f"Mouvement effectué : {move}"
                else:
                    return game_data, False, "Échec de l'exécution du mouvement"
        
        return game_data, False, "Mouvement illégal"
        
    except Exception as e:
        return game_data, False, f"Erreur: {str(e)}"

def get_competitive_legal_moves(game_data: dict, row: int, col: int) -> list:
    """Obtenir les mouvements légaux pour une position."""
    try:
        board = CheckersBoard.from_dict(game_data)
        pos = Position(row, col)
        moves = board.get_possible_moves(pos)
        
        return [
            {
                'to': {'row': move.to_pos.row, 'col': move.to_pos.col},
                'captured': [{'row': cap.row, 'col': cap.col} for cap in move.captured_pieces],
                'is_capture': move.is_capture(),
                'is_promotion': move.is_promotion,
                'is_multi_capture': move.is_multi_capture,
                'points': move.points_earned
            }
            for move in moves
        ]
        
    except Exception:
        return []

def make_competitive_move(game_data: dict, from_row: int, from_col: int, to_row: int, to_col: int) -> dict:
    """
    Effectuer un mouvement dans le jeu.
    Retourne un dictionnaire avec le résultat du mouvement.
    """
    try:
        board = CheckersBoard.from_dict(game_data)
        from_pos = Position(from_row, from_col)
        to_pos = Position(to_row, to_col)
        
        # Obtenir tous les mouvements possibles pour cette pièce
        possible_moves = board.get_possible_moves(from_pos)
        
        logger.info(f"🔍 POSSIBLE MOVES COUNT for ({from_row},{from_col}): {len(possible_moves)}")
        for i, m in enumerate(possible_moves):
            logger.info(f"🔍 Move {i}: ({m.from_pos.row},{m.from_pos.col}) -> ({m.to_pos.row},{m.to_pos.col}), captures: {len(m.captured_pieces)}")
            if m.captured_pieces:
                for cap in m.captured_pieces:
                    logger.info(f"   - Would capture: ({cap.row},{cap.col})")
        
        # ✅ Trouver le mouvement correspondant basé sur la position de destination uniquement
        # Le backend gère automatiquement les captures
        target_move = None
        for move in possible_moves:
            if move.to_pos.row == to_row and move.to_pos.col == to_col:
                target_move = move
                logger.info(f"✅ FOUND MATCHING MOVE: captures {len(move.captured_pieces)} pieces")
                break
        
        if not target_move:
            logger.error(f"❌ NO MATCHING MOVE FOUND for ({from_row},{from_col}) -> ({to_row},{to_col})")
            logger.error(f"❌ Available moves were: {[(m.to_pos.row, m.to_pos.col) for m in possible_moves]}")
            return {
                'success': False,
                'error': 'Mouvement invalide',
                'game_state': game_data
            }
        
        # Effectuer le mouvement
        success = board.make_move(target_move)
        
        if success:
            # Convertir l'état du jeu mis à jour
            updated_game = board.to_dict()
            
            # Vérifier si la partie est terminée
            is_over = board.is_game_over()
            winner = None
            if is_over:
                winner_color = board.get_winner()
                winner = winner_color.value if winner_color else None
            
            return {
                'success': True,
                'points_gained': target_move.points_earned,
                'game_state': updated_game,
                'is_game_over': is_over,
                'winner': winner,
                'captured_pieces': [{'row': cap.row, 'col': cap.col} for cap in target_move.captured_pieces],
                'is_promotion': target_move.is_promotion
            }
        else:
            return {
                'success': False,
                'error': 'Le mouvement a échoué',
                'game_state': game_data
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'game_state': game_data
        }

def convert_board_to_unicode(game_data: dict) -> list:
    """
    Convertir le plateau compétitif en format Unicode pour le frontend.
    Retourne un tableau 10x10 avec des emojis.
    """
    piece_mapping = {
        'red_man': '⚪',      # Pion rouge (clair)
        'red_king': '♕',     # Dame rouge
        'black_man': '⚫',    # Pion noir (sombre)
        'black_king': '♛',   # Dame noire
    }
    
    board_data = game_data.get('board', [])
    unicode_board = []
    
    for row_idx, row in enumerate(board_data):
        unicode_row = []
        for col_idx, cell in enumerate(row):
            if cell and isinstance(cell, dict):
                piece_color = cell.get('color', '')
                piece_type = cell.get('type', '')
                key = f"{piece_color}_{piece_type}"
                unicode_piece = piece_mapping.get(key, '.')
                
                # ✅ Debug: Logger TOUTES les pièces kings
                if piece_type == 'king':
                    logger.info(f"👑 KING at ({row_idx},{col_idx}): color='{piece_color}', type='{piece_type}', key='{key}' → '{unicode_piece}'")
                
                unicode_row.append(unicode_piece)
            else:
                unicode_row.append('.')
        unicode_board.append(unicode_row)
    
    return unicode_board

def check_competitive_game_over(game_data: dict) -> tuple[bool, Optional[str], dict]:
    """
    Vérifier si la partie est terminée.
    Retourne (is_over, winner, details)
    """
    try:
        board = CheckersBoard.from_dict(game_data)
        
        if board.is_game_over():
            winner = board.get_winner()
            result = board.get_game_result()
            return True, winner.value if winner else 'draw', result
        
        return False, None, {}
        
    except Exception as e:
        return False, None, {'error': str(e)}

def check_and_auto_pass_turn_if_timeout(game_data: dict) -> tuple[dict, bool]:
    """
    Vérifier si le joueur actuel a dépassé 120s.
    Si oui, déclencher un timeout et déclarer l'adversaire gagnant.
    Retourne (new_game_data, timeout_triggered)
    """
    try:
        board = CheckersBoard.from_dict(game_data)
        
        # Vérifier et gérer le timeout (120s = game over, adversaire gagne)
        timeout_triggered = board.check_and_handle_move_timeout()
        
        if timeout_triggered:
            # ✅ Timeout détecté : la partie est TERMINÉE (game_over=True)
            # Retourner le nouvel état avec is_game_over=True et winner défini
            return board.to_dict(), True
        else:
            # Pas de timeout, retourner l'état inchangé
            return game_data, False
            
    except Exception as e:
        logger.error(f"Error checking timeout: {str(e)}")
        return game_data, False