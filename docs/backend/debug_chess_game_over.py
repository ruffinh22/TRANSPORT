#!/usr/bin/env python
"""
Script de debug pour tester la détection de fin de partie aux échecs.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
sys.path.insert(0, os.getcwd())
django.setup()

from apps.games.game_logic.chess_competitive import (
    create_competitive_chess_game,
    check_competitive_chess_game_over,
    is_checkmate,
    is_stalemate,
    is_in_check,
    has_legal_moves
)

print("=" * 60)
print("TEST: Vérifier si une nouvelle partie est déjà considérée comme terminée")
print("=" * 60)

# Créer une nouvelle partie
game_state = create_competitive_chess_game()

print(f"\n📋 État initial de la partie:")
print(f"  Current player: {game_state['current_player']}")
print(f"  White score: {game_state['white_score']}")
print(f"  Black score: {game_state['black_score']}")
print(f"  Is game over: {game_state['is_game_over']}")

# Vérifier si le jeu est terminé
print(f"\n🔍 Vérification de fin de partie...")
is_over, winner, details = check_competitive_chess_game_over(game_state)

print(f"\n📊 Résultats:")
print(f"  Is over: {is_over}")
print(f"  Winner: {winner}")
print(f"  Details: {details}")

# Tests individuels
board = game_state['board']
print(f"\n🔍 Tests individuels sur le joueur blanc:")
print(f"  Is in check: {is_in_check(board, 'white')}")
print(f"  Has legal moves: {has_legal_moves(board, 'white')}")
print(f"  Is checkmate: {is_checkmate(board, 'white')}")
print(f"  Is stalemate: {is_stalemate(board, 'white')}")

print(f"\n🔍 Tests individuels sur le joueur noir:")
print(f"  Is in check: {is_in_check(board, 'black')}")
print(f"  Has legal moves: {has_legal_moves(board, 'black')}")
print(f"  Is checkmate: {is_checkmate(board, 'black')}")
print(f"  Is stalemate: {is_stalemate(board, 'black')}")

print("\n" + "=" * 60)
print("CONCLUSION:")
if is_over:
    print(f"❌ PROBLÈME DÉTECTÉ! Le jeu est marqué comme terminé dès le début!")
    print(f"   Raison: {details.get('reason', 'unknown')}")
else:
    print(f"✅ OK - Le jeu n'est pas terminé au début")
print("=" * 60)
