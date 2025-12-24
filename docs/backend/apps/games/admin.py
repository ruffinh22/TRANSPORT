from django.contrib import admin
from .models import GameType, Game, GameInvitation, GameReport, Tournament, TournamentParticipant, Leaderboard

# Enregistrements minimaux pour que Django démarre
admin.site.register(GameType)
admin.site.register(Game)
admin.site.register(GameInvitation) 
admin.site.register(GameReport)
admin.site.register(Tournament)
admin.site.register(TournamentParticipant)
admin.site.register(Leaderboard)
