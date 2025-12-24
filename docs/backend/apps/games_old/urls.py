# apps/games/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router REST
router = DefaultRouter()

# ✅ ORDRE IMPORTANT: Les ViewSets spécifiques AVANT le ViewSet principal
router.register(r'types', views.GameTypeViewSet, basename='gametype')
router.register(r'invitations', views.GameInvitationViewSet, basename='gameinvitation')
router.register(r'reports', views.GameReportViewSet, basename='gamereport')
router.register(r'tournaments', views.TournamentViewSet, basename='tournament')
router.register(r'leaderboard', views.LeaderboardViewSet, basename='leaderboard')

# ✅ GameViewSet en DERNIER avec route vide pour capturer le reste
router.register(r'', views.GameViewSet, basename='game')

app_name = 'games'

urlpatterns = [
    # ✅ Routes APIView AVANT le router (ordre critique!)
    path('statistics/', views.GameStatisticsView.as_view(), name='statistics'),
    path('statistics/leaderboard/', views.GameStatisticsView.as_view(), name='statistics_leaderboard'),
    path('search/', views.GameSearchView.as_view(), name='search'),
    path('quick-match/', views.QuickMatchView.as_view(), name='quick_match'),
    
    # ✅ Routes du router REST en dernier
    path('', include(router.urls)),
]

"""
URLs générées automatiquement par le router:

GameViewSet (basename='game'):
- GET    /api/v1/games/                       # Liste des parties (list)
- POST   /api/v1/games/                       # Créer une partie (create)
- GET    /api/v1/games/{id}/                  # Détails d'une partie (retrieve)
- PUT    /api/v1/games/{id}/                  # Modifier une partie (update)
- PATCH  /api/v1/games/{id}/                  # Modifier partiellement (partial_update)
- DELETE /api/v1/games/{id}/                  # Supprimer une partie (destroy)

Actions custom (@action):
- POST   /api/v1/games/{id}/join/             # Rejoindre (detail=True)
- POST   /api/v1/games/{id}/start/            # Démarrer (detail=True)
- POST   /api/v1/games/{id}/move/             # Mouvement (detail=True)
- POST   /api/v1/games/{id}/surrender/        # Abandonner (detail=True)
- POST   /api/v1/games/{id}/cancel/           # Annuler (detail=True)
- GET    /api/v1/games/{id}/spectate/         # Spectateur (detail=True)
- GET    /api/v1/games/waiting/               # Parties en attente (detail=False)
- GET    /api/v1/games/my-games/              # Mes parties (detail=False) ✅
- GET    /api/v1/games/leaderboard/           # Classement (detail=False) - CONFLIT!

⚠️ ATTENTION: Il y a un conflit entre:
- GameViewSet.leaderboard (action custom)
- LeaderboardViewSet (ViewSet séparé)

Le router va créer:
- /api/v1/games/leaderboard/ (LeaderboardViewSet) ❌ Pris en premier
- /api/v1/games/leaderboard/ (GameViewSet action) ❌ Ignoré!

SOLUTION: Renommer l'un des deux ou supprimer l'action du GameViewSet
"""
