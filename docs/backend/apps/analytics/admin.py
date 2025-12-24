from django.contrib import admin
from .models import GameSession, PlayerStats, GameEvent

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'player_id', 'start_time', 'end_time', 'score', 'level_reached')
    list_filter = ('start_time', 'level_reached')
    search_fields = ('player_id',)
    readonly_fields = ('start_time', 'end_time')

@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ('player_id', 'total_sessions', 'highest_score', 'highest_level', 'total_playtime')
    search_fields = ('player_id',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'event_type', 'timestamp', 'data')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('session__player_id', 'event_type')
    readonly_fields = ('timestamp',)
