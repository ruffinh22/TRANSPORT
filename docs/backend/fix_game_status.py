#!/usr/bin/env python
"""Fix game_data.status for finished games"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from apps.games.models import Game

game_id = 'efd3fc42-231f-4a8d-a077-6fc71ad978f3'

try:
    game = Game.objects.get(id=game_id)
    print(f'Before: status={game.status}, game_data.status={game.game_data.get("status")}')
    
    game.game_data['status'] = 'finished'
    game.save()
    
    print(f'After: status={game.status}, game_data.status={game.game_data.get("status")}')
    print('✅ Game data synchronized!')
except Game.DoesNotExist:
    print(f'❌ Game {game_id} not found')
except Exception as e:
    print(f'❌ Error: {e}')
