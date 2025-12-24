#!/usr/bin/env python
"""
Test rapide pour vérifier has_legal_moves sur une nouvelle partie.
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
sys.path.insert(0, os.getcwd())
django.setup()

from apps.games.game_logic.chess_competitive import (
    create_competitive_chess_game,
    has_legal_moves,
    get_possible_moves
)

# Créer une nouvelle partie
game_state = create_competitive_chess_game()
board = game_state['board']

print("=" * 60)
print("TEST: has_legal_moves sur une nouvelle partie")
print("=" * 60)

# Compter les pièces blanches
white_pieces = 0
for row in range(8):
    for col in range(8):
        piece = board[row][col]
        if piece and isinstance(piece, dict) and piece.get('color') == 'white':
            white_pieces += 1
            if white_pieces <= 3:  # Afficher les 3 premières
                moves = get_possible_moves(board, row, col)
                print(f"  Pièce blanche en ({row},{col}): {piece.get('type')} - {len(moves)} mouvements possibles")

print(f"\nTotal pièces blanches: {white_pieces}")

# Test has_legal_moves
result_white = has_legal_moves(board, 'white')
result_black = has_legal_moves(board, 'black')

print(f"\n✅ has_legal_moves('white'): {result_white}")
print(f"✅ has_legal_moves('black'): {result_black}")

if not result_white or not result_black:
    print(f"\n❌ BUG TROUVÉ! Un joueur n'a pas de mouvements légaux au début!")
else:
    print(f"\n✅ OK - Les deux joueurs ont des mouvements légaux")

print("=" * 60)
