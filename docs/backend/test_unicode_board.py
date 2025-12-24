#!/usr/bin/env python3
"""
Test de la conversion Unicode des pièces de dames
"""

from apps.games.game_logic.checkers_competitive import (
    create_competitive_checkers_game,
    convert_board_to_unicode
)

print("🎮 Test de conversion Unicode pour les Dames Compétitives")
print("=" * 60)

# Créer une partie
game = create_competitive_checkers_game()

# Convertir en Unicode
unicode_board = convert_board_to_unicode(game)

print("\n📋 Plateau initial (format Unicode):\n")

# Afficher avec numéros de rangées
print("   ", end="")
for col in range(10):
    print(f" {col} ", end="")
print()

for row_idx, row in enumerate(unicode_board):
    print(f"{row_idx}  ", end="")
    for cell in row:
        print(f" {cell} ", end="")
    print()

print("\n" + "=" * 60)
print("✅ Légende:")
print("   ⚪ = Pion rouge (Player 1)")
print("   ♕ = Dame rouge")
print("   ⚫ = Pion noir (Player 2)")
print("   ♛ = Dame noire")
print("   . = Case vide")
print("=" * 60)

# Vérifier le nombre de pièces
red_pieces = sum(row.count('⚪') for row in unicode_board)
black_pieces = sum(row.count('⚫') for row in unicode_board)

print(f"\n✅ Pièces rouges: {red_pieces}/20")
print(f"✅ Pièces noires: {black_pieces}/20")

print("\n✨ Test terminé avec succès!")
