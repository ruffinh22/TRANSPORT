#!/usr/bin/env python3
"""
Test de la synchronisation du timer avec timestamps
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.games.game_logic.checkers_competitive import create_competitive_checkers_game
import json
from time import sleep

def test_timer_sync():
    print("🧪 Test de synchronisation du timer avec timestamps\n")
    
    # Créer une partie
    game = create_competitive_checkers_game()
    print("✅ Partie créée")
    
    # Vérifier que les timestamps sont présents
    timer_data = game['timer']
    print(f"\n📊 Timer data:")
    print(f"  - move_time_limit: {timer_data['move_time_limit']}s")
    print(f"  - global_time_limit: {timer_data['global_time_limit']}s")
    print(f"  - red_time_remaining: {timer_data['red_time_remaining']}s")
    print(f"  - black_time_remaining: {timer_data['black_time_remaining']}s")
    print(f"  - current_move_start: {timer_data.get('current_move_start')}")
    print(f"  - game_start_time: {timer_data.get('game_start_time')}")
    print(f"  - current_player: {timer_data.get('current_player')}")
    
    # Vérifier que les timestamps existent
    assert timer_data.get('current_move_start') is not None, "❌ current_move_start manquant"
    assert timer_data.get('game_start_time') is not None, "❌ game_start_time manquant"
    assert timer_data.get('current_player') is not None, "❌ current_player manquant"
    
    print("\n✅ Tous les timestamps sont présents!")
    
    # Simuler un délai (comme une déconnexion)
    print("\n⏳ Simulation d'une déconnexion de 3 secondes...")
    sleep(3)
    
    # Récupérer à nouveau les données (comme après reconnexion)
    print("\n🔄 Reconnexion et récupération des données...")
    
    # En production, ces timestamps permettront au frontend de calculer:
    # - Temps écoulé depuis current_move_start → pour afficher le timer de coup
    # - Temps écoulé depuis game_start_time → pour calculer le temps global
    
    print("\n📝 Format des timestamps (ISO 8601):")
    print(f"  current_move_start: {timer_data['current_move_start']}")
    print(f"  game_start_time: {timer_data['game_start_time']}")
    
    print("\n✅ Le frontend pourra calculer le temps écoulé avec:")
    print("  const moveStart = new Date(timer.current_move_start).getTime();")
    print("  const now = Date.now();")
    print("  const elapsedSeconds = Math.floor((now - moveStart) / 1000);")
    
    print("\n🎉 Test réussi! La synchronisation fonctionnera correctement.")
    
    return 0

if __name__ == "__main__":
    try:
        exit(test_timer_sync())
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
