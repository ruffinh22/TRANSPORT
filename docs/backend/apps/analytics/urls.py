from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('start-session/', views.start_session, name='start_session'),
    path('end-session/', views.end_session, name='end_session'),
    path('log-event/', views.log_event, name='log_event'),
    path('player/<str:player_id>/', views.player_stats, name='player_stats'),
    path('game-stats/', views.game_analytics, name='game_analytics'),
]
