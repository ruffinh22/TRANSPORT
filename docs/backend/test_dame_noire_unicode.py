#!/usr/bin/env python
"""Test de la conversion Unicode pour les dames noires."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.games.game_logic.checkers_competitive import convert_board_to_unicode

def test_unicode_conversion():
    print("\n" + "="*60)
    print("🧪 TEST: Conversion Unicode des dames")
    print("="*60)
    
    # Créer un game_data avec une dame noire et une dame rouge
    game_data = {
        'board': [
            [None] * 10 for _ in range(10)
        ]
    }
    
    # Ajouter une dame rouge en (0, 1)
    game_data['board'][0][1] = {'type': 'king', 'color': 'red'}
    
    # Ajouter une dame noire en (0, 3)
    game_data['board'][0][3] = {'type': 'king', 'color': 'black'}
    
    # Ajouter un pion rouge en (1, 0)
    game_data['board'][1][0] = {'type': 'man', 'color': 'red'}
    
    # Ajouter un pion noir en (1, 2)
    game_data['board'][1][2] = {'type': 'man', 'color': 'black'}
    
    print(f"\n📊 Game data créé:")
    print(f"   Dame rouge (0,1): {game_data['board'][0][1]}")
    print(f"   Dame noire (0,3): {game_data['board'][0][3]}")
    print(f"   Pion rouge (1,0): {game_data['board'][1][0]}")
    print(f"   Pion noir (1,2): {game_data['board'][1][2]}")
    
    # Convertir en Unicode
    print(f"\n🔄 Conversion en Unicode...")
    unicode_board = convert_board_to_unicode(game_data)
    
    print(f"\n📊 Résultats de conversion:")
    print(f"   Position (0,1): '{unicode_board[0][1]}' (attendu: '♕' dame rouge)")
    print(f"   Position (0,3): '{unicode_board[0][3]}' (attendu: '♛' dame noire)")
    print(f"   Position (1,0): '{unicode_board[1][0]}' (attendu: '⚪' pion rouge)")
    print(f"   Position (1,2): '{unicode_board[1][2]}' (attendu: '⚫' pion noir)")
    
    # Vérifications
    errors = []
    
    if unicode_board[0][1] != '♕':
        errors.append(f"❌ Dame rouge incorrecte: obtenu '{unicode_board[0][1]}' au lieu de '♕'")
    else:
        print(f"   ✅ Dame rouge correcte: ♕")
    
    if unicode_board[0][3] != '♛':
        errors.append(f"❌ Dame noire incorrecte: obtenu '{unicode_board[0][3]}' au lieu de '♛'")
    else:
        print(f"   ✅ Dame noire correcte: ♛")
    
    if unicode_board[1][0] != '⚪':
        errors.append(f"❌ Pion rouge incorrect: obtenu '{unicode_board[1][0]}' au lieu de '⚪'")
    else:
        print(f"   ✅ Pion rouge correct: ⚪")
    
    if unicode_board[1][2] != '⚫':
        errors.append(f"❌ Pion noir incorrect: obtenu '{unicode_board[1][2]}' au lieu de '⚫'")
    else:
        print(f"   ✅ Pion noir correct: ⚫")
    
    print(f"\n" + "="*60)
    if errors:
        print(f"❌ TEST ÉCHOUÉ! {len(errors)} erreur(s):")
        for err in errors:
            print(f"   {err}")
    else:
        print(f"✅ ✅ ✅ TEST RÉUSSI! ✅ ✅ ✅")
        print(f"Toutes les conversions Unicode sont correctes!")
    print("="*60 + "\n")

if __name__ == '__main__':
    test_unicode_conversion()
