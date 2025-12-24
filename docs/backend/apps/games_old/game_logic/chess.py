# apps/games/game_logic/chess.py
# ===================================

import copy
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum


class PieceType(Enum):
    """Types de pièces d'échecs."""
    PAWN = 'P'
    ROOK = 'R'
    KNIGHT = 'N'
    BISHOP = 'B'
    QUEEN = 'Q'
    KING = 'K'


class Color(Enum):
    """Couleurs des joueurs."""
    WHITE = 'white'
    BLACK = 'black'


@dataclass
class Position:
    """Position sur l'échiquier."""
    row: int
    col: int
    
    def __str__(self):
        """Notation algébrique (a1, b2, etc.)."""
        return f"{chr(ord('a') + self.col)}{8 - self.row}"
    
    @classmethod
    def from_notation(cls, notation: str) -> 'Position':
        """Créer depuis la notation algébrique."""
        col = ord(notation[0].lower()) - ord('a')
        row = 8 - int(notation[1])
        return cls(row, col)
    
    def is_valid(self) -> bool:
        """Vérifier si la position est valide."""
        return 0 <= self.row < 8 and 0 <= self.col < 8
    
    def __eq__(self, other):
        return isinstance(other, Position) and self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))


@dataclass
class Move:
    """Mouvement aux échecs."""
    from_pos: Position
    to_pos: Position
    piece_type: PieceType
    color: Color
    captured_piece: Optional[PieceType] = None
    promotion: Optional[PieceType] = None
    is_castling: bool = False
    is_en_passant: bool = False
    
    def __str__(self):
        """Notation algébrique du mouvement."""
        notation = ""
        
        if self.is_castling:
            if self.to_pos.col > self.from_pos.col:
                return "O-O"  # Petit roque
            else:
                return "O-O-O"  # Grand roque
        
        # Type de pièce (sauf pion)
        if self.piece_type != PieceType.PAWN:
            notation += self.piece_type.value
        
        # Capture
        if self.captured_piece or self.is_en_passant:
            if self.piece_type == PieceType.PAWN:
                notation += str(self.from_pos)[0]  # Colonne du pion
            notation += "x"
        
        # Case d'arrivée
        notation += str(self.to_pos)
        
        # Promotion
        if self.promotion:
            notation += "=" + self.promotion.value
        
        return notation


class ChessPiece:
    """Pièce d'échecs."""
    
    def __init__(self, piece_type: PieceType, color: Color):
        self.piece_type = piece_type
        self.color = color
        self.has_moved = False
    
    def __str__(self):
        """Représentation textuelle."""
        symbol = self.piece_type.value
        return symbol if self.color == Color.WHITE else symbol.lower()
    
    def get_possible_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Obtenir tous les mouvements possibles pour cette pièce."""
        moves = []
        
        if self.piece_type == PieceType.PAWN:
            moves = self._get_pawn_moves(position, board)
        elif self.piece_type == PieceType.ROOK:
            moves = self._get_rook_moves(position, board)
        elif self.piece_type == PieceType.KNIGHT:
            moves = self._get_knight_moves(position, board)
        elif self.piece_type == PieceType.BISHOP:
            moves = self._get_bishop_moves(position, board)
        elif self.piece_type == PieceType.QUEEN:
            moves = self._get_queen_moves(position, board)
        elif self.piece_type == PieceType.KING:
            moves = self._get_king_moves(position, board)
        
        # Filtrer les positions invalides
        return [pos for pos in moves if pos.is_valid()]
    
    def _get_pawn_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Mouvements du pion."""
        moves = []
        direction = -1 if self.color == Color.WHITE else 1
        
        # Mouvement vers l'avant
        forward_pos = Position(position.row + direction, position.col)
        if forward_pos.is_valid() and board.get_piece(forward_pos) is None:
            moves.append(forward_pos)
            
            # Double mouvement initial
            if not self.has_moved:
                double_forward = Position(position.row + 2 * direction, position.col)
                if double_forward.is_valid() and board.get_piece(double_forward) is None:
                    moves.append(double_forward)
        
        # Captures diagonales
        for col_offset in [-1, 1]:
            capture_pos = Position(position.row + direction, position.col + col_offset)
            if capture_pos.is_valid():
                target_piece = board.get_piece(capture_pos)
                if target_piece and target_piece.color != self.color:
                    moves.append(capture_pos)
                # En passant
                elif board.can_en_passant(position, capture_pos):
                    moves.append(capture_pos)
        
        return moves
    
    def _get_rook_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Mouvements de la tour."""
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_pos = Position(position.row + i * dr, position.col + i * dc)
                if not new_pos.is_valid():
                    break
                
                target_piece = board.get_piece(new_pos)
                if target_piece is None:
                    moves.append(new_pos)
                elif target_piece.color != self.color:
                    moves.append(new_pos)
                    break
                else:
                    break
        
        return moves
    
    def _get_knight_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Mouvements du cavalier."""
        moves = []
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in knight_moves:
            new_pos = Position(position.row + dr, position.col + dc)
            if new_pos.is_valid():
                target_piece = board.get_piece(new_pos)
                if target_piece is None or target_piece.color != self.color:
                    moves.append(new_pos)
        
        return moves
    
    def _get_bishop_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Mouvements du fou."""
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_pos = Position(position.row + i * dr, position.col + i * dc)
                if not new_pos.is_valid():
                    break
                
                target_piece = board.get_piece(new_pos)
                if target_piece is None:
                    moves.append(new_pos)
                elif target_piece.color != self.color:
                    moves.append(new_pos)
                    break
                else:
                    break
        
        return moves
    
    def _get_queen_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Mouvements de la reine (combinaison tour + fou)."""
        return self._get_rook_moves(position, board) + self._get_bishop_moves(position, board)
    
    def _get_king_moves(self, position: Position, board: 'ChessBoard') -> List[Position]:
        """Mouvements du roi."""
        moves = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dr, dc in directions:
            new_pos = Position(position.row + dr, position.col + dc)
            if new_pos.is_valid():
                target_piece = board.get_piece(new_pos)
                if target_piece is None or target_piece.color != self.color:
                    moves.append(new_pos)
        
        return moves


class ChessBoard:
    """Plateau d'échecs."""
    
    def __init__(self):
        self.board: List[List[Optional[ChessPiece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = Color.WHITE
        self.move_history: List[Move] = []
        self.castling_rights = {
            Color.WHITE: {'kingside': True, 'queenside': True},
            Color.BLACK: {'kingside': True, 'queenside': True}
        }
        self.en_passant_target: Optional[Position] = None
        self.halfmove_clock = 0  # Coups depuis dernière capture ou mouvement de pion
        self.fullmove_number = 1  # Numéro du coup
        
        self._setup_initial_position()
    
    def _setup_initial_position(self):
        """Placer les pièces en position initiale."""
        # Pions
        for col in range(8):
            self.board[1][col] = ChessPiece(PieceType.PAWN, Color.BLACK)
            self.board[6][col] = ChessPiece(PieceType.PAWN, Color.WHITE)
        
        # Pièces majeures et mineures
        piece_order = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
            PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK
        ]
        
        for col, piece_type in enumerate(piece_order):
            self.board[0][col] = ChessPiece(piece_type, Color.BLACK)
            self.board[7][col] = ChessPiece(piece_type, Color.WHITE)
    
    def get_piece(self, position: Position) -> Optional[ChessPiece]:
        """Obtenir la pièce à une position."""
        if not position.is_valid():
            return None
        return self.board[position.row][position.col]
    
    def set_piece(self, position: Position, piece: Optional[ChessPiece]):
        """Placer une pièce à une position."""
        if position.is_valid():
            self.board[position.row][position.col] = piece
    
    def find_king(self, color: Color) -> Optional[Position]:
        """Trouver la position du roi."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.piece_type == PieceType.KING and piece.color == color:
                    return Position(row, col)
        return None
    
    def is_square_attacked(self, position: Position, by_color: Color) -> bool:
        """Vérifier si une case est attaquée par une couleur."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == by_color:
                    piece_pos = Position(row, col)
                    possible_moves = piece.get_possible_moves(piece_pos, self)
                    if position in possible_moves:
                        return True
        return False
    
    def is_in_check(self, color: Color) -> bool:
        """Vérifier si le roi est en échec."""
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        
        opponent_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        return self.is_square_attacked(king_pos, opponent_color)
    
    def can_en_passant(self, pawn_pos: Position, target_pos: Position) -> bool:
        """Vérifier si la prise en passant est possible."""
        if not self.en_passant_target or self.en_passant_target != target_pos:
            return False
        
        # Vérifier que c'est bien un pion qui tente la prise
        pawn = self.get_piece(pawn_pos)
        if not pawn or pawn.piece_type != PieceType.PAWN:
            return False
        
        # Vérifier qu'il y a bien un pion ennemi adjacent
        enemy_pawn_pos = Position(pawn_pos.row, target_pos.col)
        enemy_pawn = self.get_piece(enemy_pawn_pos)
        
        return (enemy_pawn and 
                enemy_pawn.piece_type == PieceType.PAWN and 
                enemy_pawn.color != pawn.color)
    
    def can_castle(self, color: Color, side: str) -> bool:
        """Vérifier si le roque est possible."""
        if not self.castling_rights[color][side]:
            return False
        
        if self.is_in_check(color):
            return False
        
        king_row = 7 if color == Color.WHITE else 0
        king_col = 4
        
        if side == 'kingside':
            # Vérifier que les cases entre roi et tour sont vides
            for col in range(5, 7):
                if self.board[king_row][col] is not None:
                    return False
                # Vérifier que le roi ne passe pas par une case attaquée
                if self.is_square_attacked(Position(king_row, col), 
                                         Color.BLACK if color == Color.WHITE else Color.WHITE):
                    return False
        else:  # queenside
            # Vérifier que les cases entre roi et tour sont vides
            for col in range(1, 4):
                if self.board[king_row][col] is not None:
                    return False
            # Vérifier que le roi ne passe pas par une case attaquée
            for col in range(2, 4):
                if self.is_square_attacked(Position(king_row, col), 
                                         Color.BLACK if color == Color.WHITE else Color.WHITE):
                    return False
        
        return True
    
    def make_move(self, move: Move) -> bool:
        """Effectuer un mouvement."""
        # Vérifications de base
        piece = self.get_piece(move.from_pos)
        if not piece or piece.color != self.current_player:
            return False
        
        # Vérifier que le mouvement est légal
        if not self.is_legal_move(move):
            return False
        
        # Sauvegarder l'état pour l'annulation si nécessaire
        captured_piece = self.get_piece(move.to_pos)
        
        # Effectuer le mouvement
        if move.is_castling:
            self._execute_castling(move)
        elif move.is_en_passant:
            self._execute_en_passant(move)
        else:
            self._execute_normal_move(move)
        
        # Vérifier que le roi n'est pas en échec après le mouvement
        if self.is_in_check(self.current_player):
            # Annuler le mouvement
            self._undo_move(move, captured_piece)
            return False
        
        # Mettre à jour les droits de roque
        self._update_castling_rights(move)
        
        # Mettre à jour en passant
        self._update_en_passant(move)
        
        # Mettre à jour les compteurs
        self._update_move_counters(move, captured_piece is not None)
        
        # Marquer la pièce comme ayant bougé
        piece.has_moved = True
        
        # Ajouter à l'historique
        self.move_history.append(move)
        
        # Changer de joueur
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        
        return True
    
    def is_legal_move(self, move: Move) -> bool:
        """Vérifier si un mouvement est légal."""
        piece = self.get_piece(move.from_pos)
        if not piece:
            return False
        
        # Vérifier que c'est la bonne pièce et la bonne couleur
        if piece.piece_type != move.piece_type or piece.color != move.color:
            return False
        
        # Vérifier les mouvements spéciaux
        if move.is_castling:
            return self._is_legal_castling(move)
        elif move.is_en_passant:
            return self._is_legal_en_passant(move)
        
        # Vérifier que la destination est dans les mouvements possibles
        possible_moves = piece.get_possible_moves(move.from_pos, self)
        return move.to_pos in possible_moves
    
    def _execute_normal_move(self, move: Move):
        """Exécuter un mouvement normal."""
        piece = self.get_piece(move.from_pos)
        self.set_piece(move.from_pos, None)
        
        # Promotion
        if move.promotion and move.piece_type == PieceType.PAWN:
            promoted_piece = ChessPiece(move.promotion, piece.color)
            promoted_piece.has_moved = True
            self.set_piece(move.to_pos, promoted_piece)
        else:
            self.set_piece(move.to_pos, piece)
    
    def _execute_castling(self, move: Move):
        """Exécuter le roque."""
        king = self.get_piece(move.from_pos)
        king_row = move.from_pos.row
        
        # Déplacer le roi
        self.set_piece(move.from_pos, None)
        self.set_piece(move.to_pos, king)
        
        # Déplacer la tour
        if move.to_pos.col > move.from_pos.col:  # Petit roque
            rook_from = Position(king_row, 7)
            rook_to = Position(king_row, 5)
        else:  # Grand roque
            rook_from = Position(king_row, 0)
            rook_to = Position(king_row, 3)
        
        rook = self.get_piece(rook_from)
        self.set_piece(rook_from, None)
        self.set_piece(rook_to, rook)
    
    def _execute_en_passant(self, move: Move):
        """Exécuter la prise en passant."""
        pawn = self.get_piece(move.from_pos)
        self.set_piece(move.from_pos, None)
        self.set_piece(move.to_pos, pawn)
        
        # Supprimer le pion capturé
        captured_pawn_pos = Position(move.from_pos.row, move.to_pos.col)
        self.set_piece(captured_pawn_pos, None)
    
    def _is_legal_castling(self, move: Move) -> bool:
        """Vérifier si le roque est légal."""
        if move.to_pos.col > move.from_pos.col:
            return self.can_castle(move.color, 'kingside')
        else:
            return self.can_castle(move.color, 'queenside')
    
    def _is_legal_en_passant(self, move: Move) -> bool:
        """Vérifier si la prise en passant est légale."""
        return self.can_en_passant(move.from_pos, move.to_pos)
    
    def _update_castling_rights(self, move: Move):
        """Mettre à jour les droits de roque."""
        # Roi bougé
        if move.piece_type == PieceType.KING:
            self.castling_rights[move.color]['kingside'] = False
            self.castling_rights[move.color]['queenside'] = False
        
        # Tour bougée
        elif move.piece_type == PieceType.ROOK:
            king_row = 7 if move.color == Color.WHITE else 0
            if move.from_pos == Position(king_row, 0):  # Tour dame
                self.castling_rights[move.color]['queenside'] = False
            elif move.from_pos == Position(king_row, 7):  # Tour roi
                self.castling_rights[move.color]['kingside'] = False
        
        # Tour capturée
        if move.captured_piece == PieceType.ROOK:
            opponent_color = Color.BLACK if move.color == Color.WHITE else Color.WHITE
            opponent_king_row = 0 if opponent_color == Color.BLACK else 7
            
            if move.to_pos == Position(opponent_king_row, 0):
                self.castling_rights[opponent_color]['queenside'] = False
            elif move.to_pos == Position(opponent_king_row, 7):
                self.castling_rights[opponent_color]['kingside'] = False
    
    def _update_en_passant(self, move: Move):
        """Mettre à jour la cible en passant."""
        self.en_passant_target = None
        
        # Mouvement de pion de 2 cases
        if (move.piece_type == PieceType.PAWN and 
            abs(move.to_pos.row - move.from_pos.row) == 2):
            # La cible en passant est la case traversée
            target_row = (move.from_pos.row + move.to_pos.row) // 2
            self.en_passant_target = Position(target_row, move.from_pos.col)
    
    def _update_move_counters(self, move: Move, is_capture: bool):
        """Mettre à jour les compteurs de coups."""
        # Règle des 50 coups
        if move.piece_type == PieceType.PAWN or is_capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        
        # Numéro de coup complet
        if self.current_player == Color.BLACK:
            self.fullmove_number += 1
    
    def _undo_move(self, move: Move, captured_piece: Optional[ChessPiece]):
        """Annuler un mouvement (pour les vérifications d'échec)."""
        if move.is_castling:
            # Annuler le roque
            king = self.get_piece(move.to_pos)
            self.set_piece(move.from_pos, king)
            self.set_piece(move.to_pos, None)
            
            # Remettre la tour
            king_row = move.from_pos.row
            if move.to_pos.col > move.from_pos.col:  # Petit roque
                rook_from = Position(king_row, 5)
                rook_to = Position(king_row, 7)
            else:  # Grand roque
                rook_from = Position(king_row, 3)
                rook_to = Position(king_row, 0)
            
            rook = self.get_piece(rook_from)
            self.set_piece(rook_from, None)
            self.set_piece(rook_to, rook)
            
        elif move.is_en_passant:
            # Annuler la prise en passant
            pawn = self.get_piece(move.to_pos)
            self.set_piece(move.from_pos, pawn)
            self.set_piece(move.to_pos, None)
            
            # Remettre le pion capturé
            captured_pawn_pos = Position(move.from_pos.row, move.to_pos.col)
            captured_pawn = ChessPiece(PieceType.PAWN, 
                                     Color.BLACK if move.color == Color.WHITE else Color.WHITE)
            self.set_piece(captured_pawn_pos, captured_pawn)
            
        else:
            # Mouvement normal
            piece = self.get_piece(move.to_pos)
            self.set_piece(move.from_pos, piece)
            self.set_piece(move.to_pos, captured_piece)
    
    def is_checkmate(self, color: Color) -> bool:
        """Vérifier s'il y a échec et mat."""
        if not self.is_in_check(color):
            return False
        
        return len(self.get_legal_moves(color)) == 0
    
    def is_stalemate(self, color: Color) -> bool:
        """Vérifier s'il y a pat."""
        if self.is_in_check(color):
            return False
        
        return len(self.get_legal_moves(color)) == 0
    
    def is_draw_by_repetition(self) -> bool:
        """Vérifier la nulle par répétition."""
        # Simplification: vérifier les 8 derniers coups
        if len(self.move_history) < 8:
            return False
        
        current_fen = self.to_fen_position()
        repetitions = 1
        
        # Vérifier les positions tous les 4 coups (2 coups par joueur)
        for i in range(len(self.move_history) - 4, -1, -4):
            # Ici on devrait reconstituer la position, mais c'est complexe
            # Pour simplifier, on compte les répétitions de notation
            if len(self.move_history) > i + 3:
                repetitions += 1
                if repetitions >= 3:
                    return True
        
        return False
    
    def is_draw_by_fifty_moves(self) -> bool:
        """Vérifier la nulle par la règle des 50 coups."""
        return self.halfmove_clock >= 100  # 50 coups pour chaque joueur
    
    def get_legal_moves(self, color: Color) -> List[Move]:
        """Obtenir tous les mouvements légaux pour une couleur."""
        legal_moves = []
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    piece_pos = Position(row, col)
                    possible_moves = piece.get_possible_moves(piece_pos, self)
                    
                    for target_pos in possible_moves:
                        target_piece = self.get_piece(target_pos)
                        move = Move(
                            from_pos=piece_pos,
                            to_pos=target_pos,
                            piece_type=piece.piece_type,
                            color=piece.color,
                            captured_piece=target_piece.piece_type if target_piece else None
                        )
                        
                        # Tester si le mouvement est légal
                        if self.is_legal_move(move):
                            legal_moves.append(move)
        
        # Ajouter les roques
        if self.can_castle(color, 'kingside'):
            king_pos = self.find_king(color)
            if king_pos:
                castle_move = Move(
                    from_pos=king_pos,
                    to_pos=Position(king_pos.row, 6),
                    piece_type=PieceType.KING,
                    color=color,
                    is_castling=True
                )
                legal_moves.append(castle_move)
        
        if self.can_castle(color, 'queenside'):
            king_pos = self.find_king(color)
            if king_pos:
                castle_move = Move(
                    from_pos=king_pos,
                    to_pos=Position(king_pos.row, 2),
                    piece_type=PieceType.KING,
                    color=color,
                    is_castling=True
                )
                legal_moves.append(castle_move)
        
        return legal_moves
    
    def to_fen_position(self) -> str:
        """Convertir la position en notation FEN (simplifiée)."""
        fen_parts = []
        
        # Position des pièces
        for row in range(8):
            row_str = ""
            empty_count = 0
            
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += str(piece)
                else:
                    empty_count += 1
            
            if empty_count > 0:
                row_str += str(empty_count)
            
            fen_parts.append(row_str)
        
        position = "/".join(fen_parts)
        
        # Joueur actuel
        current_player = "w" if self.current_player == Color.WHITE else "b"
        
        # Droits de roque
        castling = ""
        if self.castling_rights[Color.WHITE]['kingside']:
            castling += "K"
        if self.castling_rights[Color.WHITE]['queenside']:
            castling += "Q"
        if self.castling_rights[Color.BLACK]['kingside']:
            castling += "k"
        if self.castling_rights[Color.BLACK]['queenside']:
            castling += "q"
        if not castling:
            castling = "-"
        
        # En passant
        en_passant = str(self.en_passant_target) if self.en_passant_target else "-"
        
        return f"{position} {current_player} {castling} {en_passant} {self.halfmove_clock} {self.fullmove_number}"
    
    def to_dict(self) -> dict:
        """Convertir l'état du plateau en dictionnaire pour sérialisation."""
        board_state = []
        for row in range(8):
            board_row = []
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    board_row.append({
                        'type': piece.piece_type.value,
                        'color': piece.color.value,
                        'has_moved': piece.has_moved
                    })
                else:
                    board_row.append(None)
            board_state.append(board_row)
        
        return {
            'board': board_state,
            'current_player': self.current_player.value,
            'castling_rights': {
                'white': self.castling_rights[Color.WHITE],
                'black': self.castling_rights[Color.BLACK]
            },
            'en_passant_target': str(self.en_passant_target) if self.en_passant_target else None,
            'halfmove_clock': self.halfmove_clock,
            'fullmove_number': self.fullmove_number,
            'move_history': [str(move) for move in self.move_history]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChessBoard':
        """Créer un plateau depuis un dictionnaire."""
        board = cls.__new__(cls)
        board.board = [[None for _ in range(8)] for _ in range(8)]
        
        # Restaurer les pièces
        for row in range(8):
            for col in range(8):
                piece_data = data['board'][row][col]
                if piece_data:
                    piece_type = PieceType(piece_data['type'])
                    color = Color(piece_data['color'])
                    piece = ChessPiece(piece_type, color)
                    piece.has_moved = piece_data.get('has_moved', False)
                    board.board[row][col] = piece
        
        # Restaurer l'état
        board.current_player = Color(data['current_player'])
        board.castling_rights = {
            Color.WHITE: data['castling_rights']['white'],
            Color.BLACK: data['castling_rights']['black']
        }
        board.en_passant_target = (
            Position.from_notation(data['en_passant_target']) 
            if data['en_passant_target'] else None
        )
        board.halfmove_clock = data['halfmove_clock']
        board.fullmove_number = data['fullmove_number']
        board.move_history = []  # Simplification: ne pas restaurer l'historique complet
        
        return board


class ChessGameEngine:
    """Moteur de jeu d'échecs pour RUMO RUSH."""
    
    def __init__(self):
        self.board = ChessBoard()
    
    def get_game_state(self) -> dict:
        """Obtenir l'état complet du jeu."""
        state = self.board.to_dict()
        
        # Ajouter des informations de jeu
        current_color = self.board.current_player
        opponent_color = Color.BLACK if current_color == Color.WHITE else Color.WHITE
        
        state.update({
            'status': self._get_game_status(),
            'in_check': self.board.is_in_check(current_color),
            'legal_moves': self._get_legal_moves_notation(current_color),
            'captured_pieces': self._get_captured_pieces(),
            'game_result': self._get_game_result()
        })
        
        return state
    
    def make_move_from_notation(self, from_square: str, to_square: str, 
                               promotion: str = None) -> tuple[bool, str]:
        """Effectuer un mouvement depuis la notation algébrique."""
        try:
            from_pos = Position.from_notation(from_square)
            to_pos = Position.from_notation(to_square)
            
            piece = self.board.get_piece(from_pos)
            if not piece:
                return False, "Aucune pièce à cette position"
            
            if piece.color != self.board.current_player:
                return False, "Ce n'est pas votre tour"
            
            # Détecter les mouvements spéciaux
            is_castling = self._is_castling_move(from_pos, to_pos, piece)
            is_en_passant = self._is_en_passant_move(from_pos, to_pos, piece)
            
            # Créer le mouvement
            target_piece = self.board.get_piece(to_pos)
            move = Move(
                from_pos=from_pos,
                to_pos=to_pos,
                piece_type=piece.piece_type,
                color=piece.color,
                captured_piece=target_piece.piece_type if target_piece else None,
                promotion=PieceType(promotion) if promotion else None,
                is_castling=is_castling,
                is_en_passant=is_en_passant
            )
            
            # Effectuer le mouvement
            if self.board.make_move(move):
                return True, f"Mouvement effectué: {move}"
            else:
                return False, "Mouvement illégal"
                
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def make_move_from_dict(self, move_data: dict) -> tuple[bool, str]:
        """Effectuer un mouvement depuis un dictionnaire."""
        try:
            from_square = move_data.get('from')
            to_square = move_data.get('to')
            promotion = move_data.get('promotion')
            
            if not from_square or not to_square:
                return False, "Cases de départ et d'arrivée requises"
            
            return self.make_move_from_notation(from_square, to_square, promotion)
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def get_legal_moves_for_square(self, square: str) -> list:
        """Obtenir les mouvements légaux pour une case."""
        try:
            pos = Position.from_notation(square)
            piece = self.board.get_piece(pos)
            
            if not piece or piece.color != self.board.current_player:
                return []
            
            legal_moves = []
            possible_moves = piece.get_possible_moves(pos, self.board)
            
            for target_pos in possible_moves:
                target_piece = self.board.get_piece(target_pos)
                move = Move(
                    from_pos=pos,
                    to_pos=target_pos,
                    piece_type=piece.piece_type,
                    color=piece.color,
                    captured_piece=target_piece.piece_type if target_piece else None
                )
                
                if self.board.is_legal_move(move):
                    legal_moves.append(str(target_pos))
            
            return legal_moves
            
        except Exception:
            return []
    
    def is_game_over(self) -> bool:
        """Vérifier si le jeu est terminé."""
        current_color = self.board.current_player
        return (self.board.is_checkmate(current_color) or 
                self.board.is_stalemate(current_color) or
                self.board.is_draw_by_fifty_moves() or
                self.board.is_draw_by_repetition())
    
    def get_winner(self) -> Optional[str]:
        """Obtenir le gagnant si le jeu est terminé."""
        current_color = self.board.current_player
        
        if self.board.is_checkmate(current_color):
            winner_color = Color.BLACK if current_color == Color.WHITE else Color.WHITE
            return winner_color.value
        
        return None  # Match nul ou jeu en cours
    
    def _get_game_status(self) -> str:
        """Obtenir le statut du jeu."""
        current_color = self.board.current_player
        
        if self.board.is_checkmate(current_color):
            return 'checkmate'
        elif self.board.is_stalemate(current_color):
            return 'stalemate'
        elif self.board.is_draw_by_fifty_moves():
            return 'fifty_move_rule'
        elif self.board.is_draw_by_repetition():
            return 'repetition'
        elif self.board.is_in_check(current_color):
            return 'check'
        else:
            return 'playing'
    
    def _get_legal_moves_notation(self, color: Color) -> list:
        """Obtenir tous les mouvements légaux en notation."""
        legal_moves = self.board.get_legal_moves(color)
        return [str(move) for move in legal_moves]
    
    def _get_captured_pieces(self) -> dict:
        """Obtenir les pièces capturées."""
        captured = {'white': [], 'black': []}
        
        # Compter les pièces manquantes
        initial_pieces = {
            PieceType.PAWN: 8, PieceType.ROOK: 2, PieceType.KNIGHT: 2,
            PieceType.BISHOP: 2, PieceType.QUEEN: 1, PieceType.KING: 1
        }
        
        current_pieces = {'white': {}, 'black': {}}
        
        # Compter les pièces actuelles
        for row in range(8):
            for col in range(8):
                piece = self.board.board[row][col]
                if piece:
                    color_key = piece.color.value
                    piece_type = piece.piece_type
                    current_pieces[color_key][piece_type] = current_pieces[color_key].get(piece_type, 0) + 1
        
        # Calculer les pièces capturées
        for color in ['white', 'black']:
            for piece_type, initial_count in initial_pieces.items():
                current_count = current_pieces[color].get(piece_type, 0)
                captured_count = initial_count - current_count
                
                for _ in range(captured_count):
                    captured[color].append(piece_type.value)
        
        return captured
    
    def _get_game_result(self) -> Optional[dict]:
        """Obtenir le résultat du jeu."""
        if not self.is_game_over():
            return None
        
        current_color = self.board.current_player
        
        if self.board.is_checkmate(current_color):
            winner = Color.BLACK if current_color == Color.WHITE else Color.WHITE
            return {
                'result': 'win',
                'winner': winner.value,
                'reason': 'checkmate'
            }
        elif self.board.is_stalemate(current_color):
            return {
                'result': 'draw',
                'reason': 'stalemate'
            }
        elif self.board.is_draw_by_fifty_moves():
            return {
                'result': 'draw',
                'reason': 'fifty_move_rule'
            }
        elif self.board.is_draw_by_repetition():
            return {
                'result': 'draw',
                'reason': 'repetition'
            }
        
        return None
    
    def _is_castling_move(self, from_pos: Position, to_pos: Position, piece: ChessPiece) -> bool:
        """Vérifier si c'est un mouvement de roque."""
        return (piece.piece_type == PieceType.KING and 
                abs(to_pos.col - from_pos.col) == 2)
    
    def _is_en_passant_move(self, from_pos: Position, to_pos: Position, piece: ChessPiece) -> bool:
        """Vérifier si c'est une prise en passant."""
        return (piece.piece_type == PieceType.PAWN and 
                self.board.can_en_passant(from_pos, to_pos))
    
    def reset_game(self):
        """Réinitialiser le jeu."""
        self.board = ChessBoard()
    
    def load_from_fen(self, fen: str) -> bool:
        """Charger une position depuis la notation FEN."""
        # Implémentation simplifiée
        # Dans une version complète, il faudrait parser complètement le FEN
        try:
            parts = fen.split()
            if len(parts) != 6:
                return False
            
            # Pour l'instant, on réinitialise simplement
            self.reset_game()
            return True
            
        except Exception:
            return False
    
    def get_fen(self) -> str:
        """Obtenir la notation FEN de la position actuelle."""
        return self.board.to_fen_position()
    
    def validate_move_format(self, move_data: dict) -> tuple[bool, str]:
        """Valider le format des données de mouvement."""
        required_fields = ['from', 'to']
        
        for field in required_fields:
            if field not in move_data:
                return False, f"Champ '{field}' manquant"
        
        # Valider le format des cases
        try:
            Position.from_notation(move_data['from'])
            Position.from_notation(move_data['to'])
        except Exception:
            return False, "Format de case invalide"
        
        # Valider la promotion si présente
        if 'promotion' in move_data:
            promotion = move_data['promotion']
            if promotion not in ['Q', 'R', 'B', 'N']:
                return False, "Type de promotion invalide"
        
        return True, "Format valide"


# Fonctions utilitaires pour l'intégration avec Django

def create_chess_game() -> dict:
    """Créer une nouvelle partie d'échecs."""
    engine = ChessGameEngine()
    return engine.get_game_state()

def make_chess_move(game_data: dict, move_data: dict) -> tuple[dict, bool, str]:
    """Effectuer un mouvement dans une partie d'échecs."""
    try:
        # Reconstruire l'état du jeu
        engine = ChessGameEngine()
        engine.board = ChessBoard.from_dict(game_data)
        
        # Valider le format du mouvement
        is_valid, message = engine.validate_move_format(move_data)
        if not is_valid:
            return game_data, False, message
        
        # Effectuer le mouvement
        success, message = engine.make_move_from_dict(move_data)
        
        # Retourner l'état mis à jour
        new_game_state = engine.get_game_state()
        return new_game_state, success, message
        
    except Exception as e:
        return game_data, False, f"Erreur interne: {str(e)}"

def check_chess_win_condition(game_data: dict) -> tuple[bool, Optional[str], str]:
    """Vérifier les conditions de victoire aux échecs."""
    try:
        engine = ChessGameEngine()
        engine.board = ChessBoard.from_dict(game_data)
        
        if engine.is_game_over():
            winner = engine.get_winner()
            result = engine._get_game_result()
            
            if result:
                return True, winner, result['reason']
        
        return False, None, "Jeu en cours"
        
    except Exception as e:
        return False, None, f"Erreur: {str(e)}"

def get_chess_legal_moves(game_data: dict, square: str) -> list:
    """Obtenir les mouvements légaux pour une case."""
    try:
        engine = ChessGameEngine()
        engine.board = ChessBoard.from_dict(game_data)
        return engine.get_legal_moves_for_square(square)
    except Exception:
        return []
        
