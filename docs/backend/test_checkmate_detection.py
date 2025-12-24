#!/usr/bin/env python
"""
Test de détection d'échec et mat dans la position actuelle du jeu.
Position: Dame blanche en d8, roi noir en e8 (en échec)
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from apps.games.game_logic.chess_competitive import (
    is_checkmate,
    is_in_check,
    has_legal_moves,
    get_possible_moves,
    is_move_legal
)


def create_test_board():
    """
    Créer un échiquier de test avec la position actuelle du jeu :
    - Dame blanche en d8 (ligne 0, colonne 3)
    - Roi noir en e8 (ligne 0, colonne 4)
    - Autres pièces noires en positions initiales
    """
    board = [[None for _ in range(8)] for _ in range(8)]
    
    # Ligne 8 (index 0) - Pièces noires + Dame blanche
    board[0][0] = {'type': 'R', 'color': 'black', 'has_moved': False}  # Tour a8
    board[0][1] = {'type': 'N', 'color': 'black', 'has_moved': False}  # Cavalier b8
    board[0][2] = {'type': 'B', 'color': 'black', 'has_moved': False}  # Fou c8
    board[0][3] = {'type': 'Q', 'color': 'white', 'has_moved': True}   # DAME BLANCHE d8 !!!
    board[0][4] = {'type': 'K', 'color': 'black', 'has_moved': False}  # Roi noir e8
    board[0][5] = {'type': 'B', 'color': 'black', 'has_moved': False}  # Fou f8
    board[0][6] = {'type': 'N', 'color': 'black', 'has_moved': False}  # Cavalier g8
    board[0][7] = {'type': 'R', 'color': 'black', 'has_moved': False}  # Tour h8
    
    # Ligne 7 (index 1) - Pions noirs
    for col in range(8):
        board[1][col] = {'type': 'P', 'color': 'black', 'has_moved': False}
    
    # Ligne 2 (index 6) - Pions blancs
    for col in range(8):
        board[6][col] = {'type': 'P', 'color': 'white', 'has_moved': False}
    
    # Ligne 1 (index 7) - Pièces blanches (sans la dame qui est en d8)
    board[7][0] = {'type': 'R', 'color': 'white', 'has_moved': False}
    board[7][1] = {'type': 'N', 'color': 'white', 'has_moved': False}
    board[7][2] = {'type': 'B', 'color': 'white', 'has_moved': False}
    board[7][3] = None  # Pas de dame ici, elle est en d8
    board[7][4] = {'type': 'K', 'color': 'white', 'has_moved': False}
    board[7][5] = {'type': 'B', 'color': 'white', 'has_moved': False}
    board[7][6] = {'type': 'N', 'color': 'white', 'has_moved': False}
    board[7][7] = {'type': 'R', 'color': 'white', 'has_moved': False}
    
    return board


def print_board(board):
    """Afficher l'échiquier."""
    pieces_symbols = {
        'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟'
    }
    
    print("\n  a b c d e f g h")
    for i, row in enumerate(board):
        print(f"{8-i} ", end='')
        for piece in row:
            if piece:
                symbol = pieces_symbols.get(piece['type'], '?')
                if piece['color'] == 'white':
                    print(f"{symbol} ", end='')
                else:
                    print(f"{symbol} ", end='')
            else:
                print(". ", end='')
        print(f"{8-i}")
    print("  a b c d e f g h\n")


def test_checkmate_detection():
    """Tester la détection d'échec et mat."""
    board = create_test_board()
    
    print("="*60)
    print("TEST DE DÉTECTION D'ÉCHEC ET MAT")
    print("="*60)
    
    print_board(board)
    
    # Test 1: Le roi noir est-il en échec ?
    print("\n1️⃣  Le roi noir est-il en échec ?")
    in_check = is_in_check(board, 'black')
    print(f"   Résultat: {'✅ OUI - Le roi est en échec' if in_check else '❌ NON'}")
    
    # Test 2: Le roi noir a-t-il des mouvements légaux ?
    print("\n2️⃣  Le roi noir a-t-il des mouvements légaux ?")
    has_moves = has_legal_moves(board, 'black')
    print(f"   Résultat: {'✅ OUI - Il peut encore jouer' if has_moves else '❌ NON - Aucun coup légal'}")
    
    # Test 3: Afficher les mouvements possibles du roi
    print("\n3️⃣  Mouvements possibles du roi noir (e8):")
    king_moves = get_possible_moves(board, 0, 4)  # Roi en e8 (0, 4)
    if king_moves:
        for move in king_moves:
            row, col = move
            notation = f"{chr(col + ord('a'))}{8-row}"
            # Vérifier si le mouvement est légal
            legal = is_move_legal(board, 0, 4, row, col, 'black')
            status = "✅ LÉGAL" if legal else "❌ ILLÉGAL (roi reste en échec)"
            print(f"   • {notation} - {status}")
    else:
        print("   ❌ Aucun mouvement possible")
    
    # Test 4: Vérifier les autres pièces noires
    print("\n4️⃣  Les autres pièces noires peuvent-elles aider ?")
    pieces_with_moves = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.get('color') == 'black':
                moves = get_possible_moves(board, row, col)
                legal_moves = []
                for move_row, move_col in moves:
                    if is_move_legal(board, row, col, move_row, move_col, 'black'):
                        legal_moves.append((move_row, move_col))
                
                if legal_moves:
                    piece_notation = f"{chr(col + ord('a'))}{8-row}"
                    piece_type = piece.get('type')
                    pieces_with_moves.append((piece_type, piece_notation, legal_moves))
    
    if pieces_with_moves:
        print(f"   ✅ {len(pieces_with_moves)} pièce(s) peuvent jouer:")
        for piece_type, pos, moves in pieces_with_moves:
            print(f"   • {piece_type} en {pos} : {len(moves)} coup(s) légal(aux)")
            for move in moves[:3]:  # Afficher max 3 coups
                notation = f"{chr(move[1] + ord('a'))}{8-move[0]}"
                print(f"     - {notation}")
    else:
        print("   ❌ Aucune pièce ne peut jouer de coup légal")
    
    # Test 5: Est-ce échec et mat ?
    print("\n5️⃣  Est-ce échec et mat ?")
    checkmate = is_checkmate(board, 'black')
    print(f"   Résultat: {'♚ ÉCHEC ET MAT! Le blanc gagne!' if checkmate else '♔ Pas encore échec et mat'}")
    
    # Test 6: Vérifier si capturer la dame est possible
    print("\n6️⃣  Peut-on capturer la dame blanche en d8 ?")
    queen_pos = (0, 3)  # Dame en d8
    can_capture = False
    capturing_pieces = []
    
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.get('color') == 'black':
                if is_move_legal(board, row, col, queen_pos[0], queen_pos[1], 'black'):
                    piece_notation = f"{chr(col + ord('a'))}{8-row}"
                    piece_type = piece.get('type')
                    capturing_pieces.append((piece_type, piece_notation))
                    can_capture = True
    
    if can_capture:
        print(f"   ✅ OUI! {len(capturing_pieces)} pièce(s) peuvent capturer:")
        for piece_type, pos in capturing_pieces:
            print(f"   • {piece_type} en {pos}")
    else:
        print("   ❌ NON - Aucune pièce ne peut capturer la dame")
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("="*60)
    if checkmate:
        print("♚ C'EST ÉCHEC ET MAT! Les blancs ont gagné!")
    elif in_check:
        if has_moves:
            print("♔ Le roi noir est en échec mais peut encore jouer")
            print(f"   {len(pieces_with_moves)} pièce(s) ont des coups légaux")
        else:
            print("⚠️  ERREUR: En échec sans coups légaux = échec et mat non détecté!")
    else:
        print("✅ Jeu normal - aucun échec")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_checkmate_detection()
