#!/usr/bin/env python3
"""Script pour corriger le current_player des parties Ludo existantes."""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, '/var/www/html/rumo_rush/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from apps.games.models import Game

def fix_ludo_games():
    """Corriger les parties Ludo avec un current_player incorrect."""
    ludo_games = Game.objects.filter(game_type='Ludo', status__in=['waiting', 'playing'])
    
    print(f"🔍 Trouvé {ludo_games.count()} parties Ludo actives")
    
    for game in ludo_games:
        game_data = game.game_data
        active_colors = game_data.get('active_colors', [])
        current_player = game_data.get('current_player')
        
        print(f"\n📋 Partie {game.room_code}:")
        print(f"   Couleurs actives: {active_colors}")
        print(f"   Current player actuel: {current_player}")
        
        # Si current_player n'est pas dans active_colors, corriger
        if current_player not in active_colors and active_colors:
            # Prendre la première couleur active comme nouveau current_player
            new_current_player = active_colors[0]
            game_data['current_player'] = new_current_player
            
            # Corriger aussi le timer si présent
            if 'timer' in game_data:
                game_data['timer']['current_player'] = new_current_player
            
            game.save()
            print(f"   ✅ Corrigé: {current_player} → {new_current_player}")
        else:
            print(f"   ✓ Pas besoin de correction")

if __name__ == '__main__':
    fix_ludo_games()
    print("\n✨ Terminé!")
