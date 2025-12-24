# apps/games/urls.py
# =====================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router REST
router = DefaultRouter()
router.register(r'types', views.GameTypeViewSet, basename='gametype')
router.register(r'games', views.GameViewSet, basename='game')
router.register(r'invitations', views.GameInvitationViewSet, basename='gameinvitation')
router.register(r'reports', views.GameReportViewSet, basename='gamereport')
router.register(r'tournaments', views.TournamentViewSet, basename='tournament')
router.register(r'leaderboard', views.LeaderboardViewSet, basename='leaderboard')

app_name = 'games'

urlpatterns = [
    # Routes du router REST - sans préfixe 'api/' car c'est géré par le main urls.py
    path('', include(router.urls)),
    
    # Routes spécifiques
    path('statistics/', views.GameStatisticsView.as_view(), name='statistics'),
    path('statistics/leaderboard/', views.GameStatisticsView.as_view(), {'action': 'leaderboard'}, name='statistics_leaderboard'),
    path('search/', views.GameSearchView.as_view(), name='search'),
    path('quick-match/', views.QuickMatchView.as_view(), name='quick_match'),
    
    # WebSocket routing (sera utilisé dans routing.py)
    # Ces URLs sont documentées ici pour référence
    # ws://domain/ws/game/<room_code>/     - Connexion à une partie
    # ws://domain/ws/matchmaking/          - Matchmaking en temps réel  
    # ws://domain/ws/spectate/<room_code>/ - Mode spectateur
]

# URLs détaillées pour référence:
"""
API REST Endpoints:

Game Types:
- GET    /api/games/api/types/                    # Liste des types de jeux
- GET    /api/games/api/types/{id}/               # Détails d'un type de jeu
- GET    /api/games/api/types/categories/         # Catégories disponibles

Games:
- GET    /api/games/api/games/                    # Liste des parties
- POST   /api/games/api/games/                    # Créer une partie
- GET    /api/games/api/games/{id}/               # Détails d'une partie
- PUT    /api/games/api/games/{id}/               # Modifier une partie
- DELETE /api/games/api/games/{id}/               # Supprimer une partie
- POST   /api/games/api/games/{id}/join/          # Rejoindre une partie
- POST   /api/games/api/games/{id}/start/         # Démarrer une partie
- POST   /api/games/api/games/{id}/move/          # Effectuer un mouvement
- POST   /api/games/api/games/{id}/surrender/     # Abandonner
- POST   /api/games/api/games/{id}/cancel/        # Annuler une partie
- GET    /api/games/api/games/{id}/spectate/      # Mode spectateur
- GET    /api/games/api/games/waiting/            # Parties en attente
- GET    /api/games/api/games/my_games/           # Mes parties

Game Invitations:
- GET    /api/games/api/invitations/              # Liste des invitations
- POST   /api/games/api/invitations/              # Créer une invitation
- GET    /api/games/api/invitations/{id}/         # Détails d'une invitation
- POST   /api/games/api/invitations/{id}/accept/  # Accepter une invitation
- POST   /api/games/api/invitations/{id}/decline/ # Refuser une invitation
- GET    /api/games/api/invitations/received/     # Invitations reçues
- GET    /api/games/api/invitations/sent/         # Invitations envoyées

Game Reports:
- GET    /api/games/api/reports/                  # Liste des signalements
- POST   /api/games/api/reports/                  # Créer un signalement
- GET    /api/games/api/reports/{id}/             # Détails d'un signalement

Tournaments:
- GET    /api/games/api/tournaments/              # Liste des tournois
- GET    /api/games/api/tournaments/{id}/         # Détails d'un tournoi
- POST   /api/games/api/tournaments/{id}/register/ # S'inscrire
- POST   /api/games/api/tournaments/{id}/unregister/ # Se désinscrire
- GET    /api/games/api/tournaments/my_tournaments/ # Mes tournois

Leaderboard:
- GET    /api/games/api/leaderboard/              # Classements
- GET    /api/games/api/leaderboard/my_position/  # Ma position

Statistics & Search:
- GET    /api/games/api/statistics/               # Statistiques utilisateur
- GET    /api/games/api/statistics/leaderboard/   # Top joueurs
- GET    /api/games/api/search/                   # Rechercher des parties
- POST   /api/games/api/quick-match/              # Matchmaking rapide

Query Parameters disponibles:

Games List:
- ?status=waiting,playing,finished      # Filtrer par statut
- ?game_type=chess,checkers,ludo       # Filtrer par type
- ?currency=FCFA,EUR,USD               # Filtrer par devise
- ?is_private=true,false               # Parties privées/publiques
- ?search=room_code                    # Recherche par code
- ?ordering=-created_at,bet_amount     # Tri des résultats
- ?page=1&page_size=20                 # Pagination

Game Search:
- ?room_code=ABC123                    # Recherche par code exact
- ?game_type=chess                     # Type de jeu
- ?min_bet=100&max_bet=1000           # Fourchette de mise
- ?currency=FCFA                       # Devise

Leaderboard:
- ?type=global,monthly,weekly          # Type de classement
- ?game_type={id}                      # Pour classement par jeu

Tournaments:
- ?status=registration,ongoing         # Filtrer par statut
- ?game_type={id}                      # Type de jeu
- ?tournament_type=single_elimination  # Type de tournoi

WebSocket Endpoints:

Game Room:
- ws://domain/ws/game/{room_code}/
  Messages:
  - {"type": "make_move", "move_data": {...}}
  - {"type": "join_game"}
  - {"type": "start_game"}  
  - {"type": "surrender"}
  - {"type": "send_message", "message": "..."}
  - {"type": "heartbeat"}

Matchmaking:
- ws://domain/ws/matchmaking/
  Messages:
  - {"type": "search_game", "game_type": "chess", "bet_amount": 500}
  - {"type": "cancel_search"}
  - {"type": "create_private_game", ...}
  - {"type": "get_waiting_games"}

Spectator:
- ws://domain/ws/spectate/{room_code}/
  Messages (read-only):
  - {"type": "heartbeat"}

Réponses WebSocket communes:
- {"type": "game_state", "data": {...}}
- {"type": "game_started", "message": "..."}
- {"type": "game_ended", "winner": "...", "reason": "..."}
- {"type": "player_connected", "user": "..."}
- {"type": "player_disconnected", "user": "..."}
- {"type": "chat_message", "user": "...", "message": "..."}
- {"type": "error", "message": "..."}
- {"type": "match_found", "game": {...}}
- {"type": "searching", "message": "..."}
"""
