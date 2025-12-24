from django.db import models
from django.utils import timezone
import uuid


class GameSession(models.Model):
    """Model to track individual game sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player_id = models.CharField(max_length=100, db_index=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    level_reached = models.IntegerField(default=1)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Game Session'
        verbose_name_plural = 'Game Sessions'
    
    def __str__(self):
        return f"Session {self.id} - Player {self.player_id}"
    
    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
        super().save(*args, **kwargs)


class PlayerStats(models.Model):
    """Model to track aggregated player statistics"""
    player_id = models.CharField(max_length=100, unique=True, db_index=True)
    total_sessions = models.IntegerField(default=0)
    highest_score = models.IntegerField(default=0)
    highest_level = models.IntegerField(default=0)
    total_playtime = models.IntegerField(default=0)  # in seconds
    first_played = models.DateTimeField(default=timezone.now)
    last_played = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Player Statistics'
        verbose_name_plural = 'Player Statistics'
    
    def __str__(self):
        return f"Stats for Player {self.player_id}"


class GameEvent(models.Model):
    """Model to track specific game events for detailed analytics"""
    EVENT_TYPES = [
        ('level_start', 'Level Start'),
        ('level_complete', 'Level Complete'),
        ('game_over', 'Game Over'),
        ('power_up_used', 'Power Up Used'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('item_collected', 'Item Collected'),
        ('obstacle_hit', 'Obstacle Hit'),
    ]
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField(default=dict, blank=True)  # Additional event data
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Game Event'
        verbose_name_plural = 'Game Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.session.player_id} at {self.timestamp}"
