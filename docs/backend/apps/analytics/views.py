from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Avg, Max, Sum, Count
from .models import GameSession, PlayerStats, GameEvent
import json


@csrf_exempt
@require_http_methods(["POST"])
def start_session(request):
    """Start a new game session"""
    try:
        data = json.loads(request.body)
        player_id = data.get('player_id')
        
        if not player_id:
            return JsonResponse({'error': 'player_id is required'}, status=400)
        
        session = GameSession.objects.create(player_id=player_id)
        
        # Update or create player stats
        player_stats, created = PlayerStats.objects.get_or_create(
            player_id=player_id,
            defaults={'first_played': timezone.now()}
        )
        player_stats.total_sessions += 1
        player_stats.last_played = timezone.now()
        player_stats.save()
        
        return JsonResponse({
            'session_id': str(session.id),
            'player_id': player_id,
            'start_time': session.start_time.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def end_session(request):
    """End a game session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        score = data.get('score', 0)
        level_reached = data.get('level_reached', 1)
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        session = get_object_or_404(GameSession, id=session_id)
        session.end_time = timezone.now()
        session.score = score
        session.level_reached = level_reached
        session.save()
        
        # Update player stats
        player_stats = PlayerStats.objects.get(player_id=session.player_id)
        if score > player_stats.highest_score:
            player_stats.highest_score = score
        if level_reached > player_stats.highest_level:
            player_stats.highest_level = level_reached
        player_stats.total_playtime += session.duration_seconds or 0
        player_stats.save()
        
        return JsonResponse({
            'session_id': str(session.id),
            'duration': session.duration_seconds,
            'final_score': session.score
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def log_event(request):
    """Log a game event"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        event_type = data.get('event_type')
        event_data = data.get('data', {})
        
        if not session_id or not event_type:
            return JsonResponse({'error': 'session_id and event_type are required'}, status=400)
        
        session = get_object_or_404(GameSession, id=session_id)
        
        event = GameEvent.objects.create(
            session=session,
            event_type=event_type,
            data=event_data
        )
        
        return JsonResponse({
            'event_id': event.id,
            'timestamp': event.timestamp.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def player_stats(request, player_id):
    """Get player statistics"""
    try:
        stats = get_object_or_404(PlayerStats, player_id=player_id)
        
        return JsonResponse({
            'player_id': stats.player_id,
            'total_sessions': stats.total_sessions,
            'highest_score': stats.highest_score,
            'highest_level': stats.highest_level,
            'total_playtime': stats.total_playtime,
            'first_played': stats.first_played.isoformat(),
            'last_played': stats.last_played.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def game_analytics(request):
    """Get general game analytics"""
    try:
        total_sessions = GameSession.objects.count()
        total_players = PlayerStats.objects.count()
        avg_score = GameSession.objects.aggregate(Avg('score'))['score__avg'] or 0
        max_score = GameSession.objects.aggregate(Max('score'))['score__max'] or 0
        avg_playtime = PlayerStats.objects.aggregate(Avg('total_playtime'))['total_playtime__avg'] or 0
        
        return JsonResponse({
            'total_sessions': total_sessions,
            'total_players': total_players,
            'average_score': round(avg_score, 2),
            'highest_score': max_score,
            'average_playtime_seconds': round(avg_playtime, 2)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
