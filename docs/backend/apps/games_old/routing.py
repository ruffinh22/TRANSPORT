# apps/games/routing.py
# ======================

from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # WebSocket pour les parties de jeu en temps réel
    re_path(r'ws/game/(?P<room_name>\w+)/$', consumers.GameConsumer.as_asgi()),
    
    # WebSocket pour le matchmaking
    path('ws/matchmaking/', consumers.MatchmakingConsumer.as_asgi()),
    
    # WebSocket pour les spectateurs
    re_path(r'ws/spectate/(?P<room_name>\w+)/$', consumers.SpectatorConsumer.as_asgi()),
    
    # WebSocket pour les tournois (optionnel - pour extension future)
    re_path(r'ws/tournament/(?P<tournament_id>\w+)/$', consumers.TournamentConsumer.as_asgi()),
]

"""
Configuration WebSocket pour RUMO RUSH Games

1. GameConsumer (ws/game/<room_code>/)
   - Connexion des joueurs à une partie spécifique
   - Échange de mouvements en temps réel
   - Gestion des timeouts et abandons
   - Chat intégré entre joueurs
   
   Messages supportés:
   - join_game: Rejoindre la partie
   - make_move: Effectuer un mouvement
   - start_game: Démarrer la partie (créateur uniquement)
   - surrender: Abandonner la partie
   - send_message: Envoyer un message de chat
   - heartbeat: Maintenir la connexion active

2. MatchmakingConsumer (ws/matchmaking/)
   - Recherche d'adversaires automatique
   - Création de parties privées
   - Notifications de match trouvé
   - Gestion des files d'attente
   
   Messages supportés:
   - search_game: Rechercher une partie
   - cancel_search: Annuler la recherche
   - create_private_game: Créer une partie privée
   - get_waiting_games: Obtenir les parties en attente

3. SpectatorConsumer (ws/spectate/<room_code>/)
   - Mode spectateur en lecture seule
   - Suivi des parties en cours
   - Pas d'interaction avec le jeu
   
   Messages supportés:
   - heartbeat: Maintenir la connexion

4. TournamentConsumer (ws/tournament/<tournament_id>/)
   - Suivi des tournois en temps réel
   - Notifications des matchs
   - Classements en direct
   - Chat général du tournoi

Utilisation côté client:

JavaScript:
```javascript
// Connexion à une partie
const gameSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/game/' + roomCode + '/'
);

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'game_state':
            updateGameBoard(data.data);
            break;
        case 'player_connected':
            showPlayerJoined(data.user);
            break;
        case 'game_ended':
            showGameResult(data.winner, data.reason);
            break;
        case 'chat_message':
            displayChatMessage(data.user, data.message);
            break;
    }
};

// Effectuer un mouvement
function makeMove(moveData) {
    gameSocket.send(JSON.stringify({
        'type': 'make_move',
        'move_data': moveData
    }));
}

// Matchmaking
const matchSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/matchmaking/'
);

function searchGame(gameType, betAmount, currency) {
    matchSocket.send(JSON.stringify({
        'type': 'search_game',
        'game_type': gameType,
        'bet_amount': betAmount,
        'currency': currency
    }));
}
```

Authentification WebSocket:
Les WebSockets utilisent l'authentification Django session.
L'utilisateur doit être connecté pour accéder aux WebSockets protégés.

Gestion des erreurs:
- Code 4001: Non authentifié
- Code 4003: Accès refusé
- Code 4004: Ressource non trouvée
- Code 4429: Trop de connexions

Configuration ASGI requise dans settings.py:
```python
ASGI_APPLICATION = 'rumo_rush.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```
"""
