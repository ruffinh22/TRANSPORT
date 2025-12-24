from django.test import TestCase, Client
from django.utils import timezone
from .models import GameSession, PlayerStats, GameEvent
import json


class AnalyticsModelsTest(TestCase):
    def setUp(self):
        self.player_id = "test_player_123"
        self.session = GameSession.objects.create(
            player_id=self.player_id,
            score=1000,
            level_reached=5
        )
    
    def test_game_session_creation(self):
        """Test GameSession model creation"""
        self.assertEqual(self.session.player_id, self.player_id)
        self.assertEqual(self.session.score, 1000)
        self.assertEqual(self.session.level_reached, 5)
        self.assertIsNotNone(self.session.start_time)
    
    def test_player_stats_creation(self):
        """Test PlayerStats model creation"""
        stats = PlayerStats.objects.create(
            player_id=self.player_id,
            total_sessions=1,
            highest_score=1000,
            highest_level=5
        )
        self.assertEqual(stats.player_id, self.player_id)
        self.assertEqual(stats.total_sessions, 1)
        self.assertEqual(stats.highest_score, 1000)
    
    def test_game_event_creation(self):
        """Test GameEvent model creation"""
        event = GameEvent.objects.create(
            session=self.session,
            event_type='level_complete',
            data={'level': 3, 'time_taken': 120}
        )
        self.assertEqual(event.session, self.session)
        self.assertEqual(event.event_type, 'level_complete')
        self.assertEqual(event.data['level'], 3)


class AnalyticsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.player_id = "test_player_456"
    
    def test_start_session_api(self):
        """Test start session API endpoint"""
        response = self.client.post(
            '/analytics/start-session/',
            json.dumps({'player_id': self.player_id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['player_id'], self.player_id)
        self.assertIn('session_id', data)
    
    def test_player_stats_api(self):
        """Test player stats API endpoint"""
        # Create player stats first
        PlayerStats.objects.create(
            player_id=self.player_id,
            total_sessions=5,
            highest_score=2000
        )
        
        response = self.client.get(f'/analytics/player/{self.player_id}/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['player_id'], self.player_id)
        self.assertEqual(data['total_sessions'], 5)
        self.assertEqual(data['highest_score'], 2000)
    
    def test_game_analytics_api(self):
        """Test general analytics API endpoint"""
        # Create some test data
        GameSession.objects.create(player_id="player1", score=1000)
        GameSession.objects.create(player_id="player2", score=1500)
        
        response = self.client.get('/analytics/game-stats/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('total_sessions', data)
        self.assertIn('average_score', data)
        self.assertIn('highest_score', data)
