# apps/games/matchmaking.py
# ============================

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import Game, GameType
from apps.core.utils import log_user_activity

User = get_user_model()
logger = logging.getLogger(__name__)


@dataclass
class MatchmakingRequest:
    """Requête de matchmaking."""
    user_id: str
    username: str
    game_type: str
    bet_amount: Decimal
    currency: str
    skill_level: int = 0
    preferred_time_control: int = 600
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = timezone.now()
    
    @property
    def cache_key(self) -> str:
        """Clé de cache pour cette requête."""
        return f"matchmaking:{self.user_id}"
    
    @property
    def queue_key(self) -> str:
        """Clé de file d'attente."""
        return f"queue:{self.game_type}:{self.currency}:{int(self.bet_amount)}"
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'game_type': self.game_type,
            'bet_amount': str(self.bet_amount),
            'currency': self.currency,
            'skill_level': self.skill_level,
            'preferred_time_control': self.preferred_time_control,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MatchmakingRequest':
        """Créer depuis un dictionnaire."""
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            game_type=data['game_type'],
            bet_amount=Decimal(data['bet_amount']),
            currency=data['currency'],
            skill_level=data.get('skill_level', 0),
            preferred_time_control=data.get('preferred_time_control', 600),
            created_at=datetime.fromisoformat(data['created_at'])
        )


class MatchmakingEngine:
    """Moteur de matchmaking intelligent."""
    
    def __init__(self):
        self.active_requests: Dict[str, MatchmakingRequest] = {}
        self.match_queues: Dict[str, List[MatchmakingRequest]] = {}
        self.match_callbacks: Dict[str, callable] = {}
        self.running = False
        
    async def start(self):
        """Démarrer le moteur de matchmaking."""
        if self.running:
            return
        
        self.running = True
        logger.info("Matchmaking engine started")
        
        # Charger les requêtes existantes depuis le cache
        await self._load_from_cache()
        
        # Démarrer les tâches de matchmaking
        asyncio.create_task(self._matchmaking_loop())
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Arrêter le moteur."""
        self.running = False
        await self._save_to_cache()
        logger.info("Matchmaking engine stopped")
    
    async def add_request(self, request: MatchmakingRequest, callback: callable = None) -> bool:
        """Ajouter une requête de matchmaking."""
        try:
            # Vérifier si l'utilisateur a déjà une requête active
            if request.user_id in self.active_requests:
                await self.cancel_request(request.user_id)
            
            # Valider la requête
            if not await self._validate_request(request):
                return False
            
            # Ajouter à la file d'attente
            self.active_requests[request.user_id] = request
            
            queue_key = request.queue_key
            if queue_key not in self.match_queues:
                self.match_queues[queue_key] = []
            
            self.match_queues[queue_key].append(request)
            
            if callback:
                self.match_callbacks[request.user_id] = callback
            
            # Sauvegarder en cache
            await self._save_request_to_cache(request)
            
            logger.info(f"Added matchmaking request for user {request.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding matchmaking request: {e}")
            return False
    
    async def cancel_request(self, user_id: str) -> bool:
        """Annuler une requête de matchmaking."""
        try:
            if user_id not in self.active_requests:
                return False
            
            request = self.active_requests[user_id]
            
            # Retirer de la file d'attente
            queue_key = request.queue_key
            if queue_key in self.match_queues:
                self.match_queues[queue_key] = [
                    req for req in self.match_queues[queue_key] 
                    if req.user_id != user_id
                ]
                
                # Supprimer la file si elle est vide
                if not self.match_queues[queue_key]:
                    del self.match_queues[queue_key]
            
            # Nettoyer les structures de données
            del self.active_requests[user_id]
            self.match_callbacks.pop(user_id, None)
            
            # Supprimer du cache
            cache.delete(request.cache_key)
            
            logger.info(f"Cancelled matchmaking request for user {request.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling matchmaking request: {e}")
            return False
    
    async def find_match(self, request: MatchmakingRequest) -> Optional[Tuple[MatchmakingRequest, MatchmakingRequest]]:
        """Trouver un match pour une requête."""
        queue_key = request.queue_key
        
        if queue_key not in self.match_queues:
            return None
        
        queue = self.match_queues[queue_key]
        
        # Chercher le meilleur match
        for potential_match in queue:
            if potential_match.user_id == request.user_id:
                continue
            
            if await self._is_good_match(request, potential_match):
                # Retirer les deux requêtes de la file
                queue.remove(request)
                queue.remove(potential_match)
                
                # Nettoyer si la file est vide
                if not queue:
                    del self.match_queues[queue_key]
                
                return (request, potential_match)
        
        return None
    
    async def get_queue_status(self, game_type: str = None, currency: str = None) -> Dict:
        """Obtenir le statut des files d'attente."""
        status = {
            'total_requests': len(self.active_requests),
            'queues': {},
            'timestamp': timezone.now().isoformat()
        }
        
        for queue_key, requests in self.match_queues.items():
            parts = queue_key.split(':')
            if len(parts) >= 4:
                q_game_type, q_currency, q_bet = parts[1], parts[2], parts[3]
                
                # Filtrer si nécessaire
                if game_type and q_game_type != game_type:
                    continue
                if currency and q_currency != currency:
                    continue
                
                status['queues'][queue_key] = {
                    'game_type': q_game_type,
                    'currency': q_currency,
                    'bet_amount': q_bet,
                    'players_waiting': len(requests),
                    'average_wait_time': self._calculate_average_wait_time(requests)
                }
        
        return status
    
    async def _matchmaking_loop(self):
        """Boucle principale de matchmaking."""
        while self.running:
            try:
                matches_found = 0
                
                # Parcourir toutes les files d'attente
                for queue_key in list(self.match_queues.keys()):
                    queue = self.match_queues.get(queue_key, [])
                    
                    if len(queue) < 2:
                        continue
                    
                    # Essayer de matcher les joueurs
                    i = 0
                    while i < len(queue) - 1:
                        request1 = queue[i]
                        
                        # Chercher un match pour ce joueur
                        match_pair = await self.find_match(request1)
                        
                        if match_pair:
                            await self._create_match(match_pair[0], match_pair[1])
                            matches_found += 1
                        else:
                            i += 1
                
                if matches_found > 0:
                    logger.info(f"Created {matches_found} matches")
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in matchmaking loop: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self):
        """Boucle de nettoyage des requêtes expirées."""
        while self.running:
            try:
                current_time = timezone.now()
                expired_requests = []
                
                # Identifier les requêtes expirées (plus de 10 minutes)
                for user_id, request in self.active_requests.items():
                    if current_time - request.created_at > timedelta(minutes=10):
                        expired_requests.append(user_id)
                
                # Supprimer les requêtes expirées
                for user_id in expired_requests:
                    await self.cancel_request(user_id)
                    logger.info(f"Removed expired matchmaking request for user {user_id}")
                
                # Sauvegarder l'état en cache périodiquement
                if expired_requests:
                    await self._save_to_cache()
                
                # Attendre 1 minute avant le prochain nettoyage
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _validate_request(self, request: MatchmakingRequest) -> bool:
        """Valider une requête de matchmaking."""
        try:
            # Vérifier que l'utilisateur existe et a les fonds
            user = await database_sync_to_async(User.objects.get)(id=request.user_id)
            balance = await database_sync_to_async(user.get_balance)(request.currency)
            
            if balance < request.bet_amount:
                logger.warning(f"User {request.username} has insufficient balance")
                return False
            
            # Vérifier que le type de jeu existe
            game_type_exists = await database_sync_to_async(
                GameType.objects.filter(name=request.game_type, is_active=True).exists
            )()
            
            if not game_type_exists:
                logger.warning(f"Invalid game type: {request.game_type}")
                return False
            
            return True
            
        except User.DoesNotExist:
            logger.warning(f"User not found: {request.user_id}")
            return False
        except Exception as e:
            logger.error(f"Error validating request: {e}")
            return False
    
    async def _is_good_match(self, request1: MatchmakingRequest, request2: MatchmakingRequest) -> bool:
        """Déterminer si deux requêtes forment un bon match."""
        # Critères de base (déjà vérifiés par la file d'attente)
        if (request1.game_type != request2.game_type or
            request1.bet_amount != request2.bet_amount or
            request1.currency != request2.currency):
            return False
        
        # Critères de niveau de compétence (si disponible)
        skill_diff = abs(request1.skill_level - request2.skill_level)
        max_skill_diff = self._calculate_max_skill_diff(request1.created_at)
        
        if skill_diff > max_skill_diff:
            return False
        
        # Critères de temps de contrôle
        time_diff = abs(request1.preferred_time_control - request2.preferred_time_control)
        if time_diff > 300:  # Max 5 minutes de différence
            return False
        
        return True
    
    def _calculate_max_skill_diff(self, request_time: datetime) -> int:
        """Calculer la différence de niveau maximale selon le temps d'attente."""
        wait_time = (timezone.now() - request_time).total_seconds()
        
        # Plus on attend, plus on accepte une différence de niveau importante
        if wait_time < 30:      # < 30 secondes
            return 50
        elif wait_time < 60:    # < 1 minute
            return 100
        elif wait_time < 300:   # < 5 minutes
            return 200
        else:                   # > 5 minutes
            return 500
    
    def _calculate_average_wait_time(self, requests: List[MatchmakingRequest]) -> float:
        """Calculer le temps d'attente moyen."""
        if not requests:
            return 0.0
        
        current_time = timezone.now()
        total_wait = sum(
            (current_time - req.created_at).total_seconds() 
            for req in requests
        )
        
        return total_wait / len(requests)
    
    async def _create_match(self, request1: MatchmakingRequest, request2: MatchmakingRequest):
        """Créer une partie depuis deux requêtes matchées."""
        try:
            # Nettoyer les structures de données
            self.active_requests.pop(request1.user_id, None)
            self.active_requests.pop(request2.user_id, None)
            
            # Supprimer du cache
            cache.delete(request1.cache_key)
            cache.delete(request2.cache_key)
            
            # Créer la partie en base de données
            game = await self._create_game_from_requests(request1, request2)
            
            # Notifier les callbacks
            callback1 = self.match_callbacks.pop(request1.user_id, None)
            callback2 = self.match_callbacks.pop(request2.user_id, None)
            
            if callback1:
                asyncio.create_task(callback1({
                    'type': 'match_found',
                    'game': {
                        'id': str(game.id),
                        'room_code': game.room_code,
                        'game_type': game.game_type.display_name,
                        'bet_amount': str(game.bet_amount),
                        'currency': game.currency,
                    },
                    'opponent': {
                        'username': request2.username,
                    }
                }))
            
            if callback2:
                asyncio.create_task(callback2({
                    'type': 'match_found',
                    'game': {
                        'id': str(game.id),
                        'room_code': game.room_code,
                        'game_type': game.game_type.display_name,
                        'bet_amount': str(game.bet_amount),
                        'currency': game.currency,
                    },
                    'opponent': {
                        'username': request1.username,
                    }
                }))
            
            logger.info(f"Created match between {request1.username} and {request2.username}")
            
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            # Remettre les requêtes en file d'attente en cas d'erreur
            await self.add_request(request1)
            await self.add_request(request2)
    
    @database_sync_to_async
    def _create_game_from_requests(self, request1: MatchmakingRequest, request2: MatchmakingRequest) -> Game:
        """Créer une partie en base de données."""
        with transaction.atomic():
            # Obtenir les objets utilisateur et type de jeu
            user1 = User.objects.get(id=request1.user_id)
            user2 = User.objects.get(id=request2.user_id)
            game_type = GameType.objects.get(name=request1.game_type, is_active=True)
            
            # Débiter les mises
            user1.update_balance(request1.currency, request1.bet_amount, 'subtract')
            user2.update_balance(request2.currency, request2.bet_amount, 'subtract')
            
            # Créer la partie
            game = Game.objects.create(
                game_type=game_type,
                player1=user1,
                player2=user2,
                bet_amount=request1.bet_amount,
                currency=request1.currency,
                status='ready',
                turn_timeout=max(request1.preferred_time_control, request2.preferred_time_control)
            )
            
            # Log des activités
            log_user_activity(
                user=user1,
                activity_type='game_matched',
                description=f'Match trouvé: {game.room_code}',
                metadata={'game_id': str(game.id), 'opponent': user2.username}
            )
            
            log_user_activity(
                user=user2,
                activity_type='game_matched',
                description=f'Match trouvé: {game.room_code}',
                metadata={'game_id': str(game.id), 'opponent': user1.username}
            )
            
            return game
    
    async def _save_to_cache(self):
        """Sauvegarder l'état en cache."""
        try:
            cache_data = {
                'requests': [req.to_dict() for req in self.active_requests.values()],
                'timestamp': timezone.now().isoformat()
            }
            cache.set('matchmaking_state', cache_data, 3600)  # 1 heure
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    async def _save_request_to_cache(self, request: MatchmakingRequest):
        """Sauvegarder une requête spécifique en cache."""
        try:
            cache.set(request.cache_key, request.to_dict(), 600)  # 10 minutes
            
        except Exception as e:
            logger.error(f"Error saving request to cache: {e}")
    
    async def _load_from_cache(self):
        """Charger l'état depuis le cache."""
        try:
            cache_data = cache.get('matchmaking_state')
            if not cache_data:
                return
            
            # Recharger les requêtes actives
            for req_data in cache_data['requests']:
                request = MatchmakingRequest.from_dict(req_data)
                
                # Vérifier si la requête n'est pas trop ancienne
                if (timezone.now() - request.created_at).total_seconds() < 600:
                    await self.add_request(request)
            
            logger.info(f"Loaded {len(self.active_requests)} requests from cache")
            
        except Exception as e:
            logger.error(f"Error loading from cache: {e}")


# Instance globale du moteur de matchmaking
matchmaking_engine = MatchmakingEngine()


class MatchmakingService:
    """Service de matchmaking pour l'application."""
    
    @staticmethod
    async def start_matchmaking():
        """Démarrer le service de matchmaking."""
        await matchmaking_engine.start()
    
    @staticmethod
    async def stop_matchmaking():
        """Arrêter le service de matchmaking."""
        await matchmaking_engine.stop()
    
    @staticmethod
    async def search_game(user_id: str, username: str, game_type: str, 
                         bet_amount: Decimal, currency: str = 'FCFA',
                         skill_level: int = 0, callback: callable = None) -> bool:
        """Rechercher une partie."""
        request = MatchmakingRequest(
            user_id=user_id,
            username=username,
            game_type=game_type,
            bet_amount=bet_amount,
            currency=currency,
            skill_level=skill_level
        )
        
        return await matchmaking_engine.add_request(request, callback)
    
    @staticmethod
    async def cancel_search(user_id: str) -> bool:
        """Annuler la recherche."""
        return await matchmaking_engine.cancel_request(user_id)
    
    @staticmethod
    async def get_queue_status(game_type: str = None, currency: str = None) -> Dict:
        """Obtenir le statut des files d'attente."""
        return await matchmaking_engine.get_queue_status(game_type, currency)
    
    @staticmethod
    def is_user_searching(user_id: str) -> bool:
        """Vérifier si un utilisateur recherche une partie."""
        return user_id in matchmaking_engine.active_requests
    
    @staticmethod
    def get_user_request(user_id: str) -> Optional[MatchmakingRequest]:
        """Obtenir la requête d'un utilisateur."""
        return matchmaking_engine.active_requests.get(user_id)
