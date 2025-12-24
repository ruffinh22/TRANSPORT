# apps/games/consumers.py
# ========================

import json
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser

from .models import Game, GameType
from apps.accounts.models import User
from apps.core.utils import log_user_activity


class GameConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour les parties en temps réel."""
    
    async def connect(self):
        """Établir la connexion WebSocket."""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        self.user = self.scope.get('user')
        
        # Vérifier l'authentification
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
        
        # Vérifier si la partie existe et si l'utilisateur peut y accéder
        try:
            self.game = await self.get_game_by_room_code(self.room_name)
            if not await self.user_can_access_game(self.user, self.game):
                await self.close(code=4003)
                return
        except Game.DoesNotExist:
            await self.close(code=4004)
            return
        
        # Rejoindre le groupe de la partie
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état actuel de la partie
        await self.send_game_state()
        
        # Notifier les autres joueurs de la connexion
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_connected',
                'user': self.user.username,
                'message': f'{self.user.username} a rejoint la partie'
            }
        )
    
    async def disconnect(self, close_code):
        """Fermer la connexion WebSocket."""
        if hasattr(self, 'room_group_name'):
            # Notifier les autres joueurs de la déconnexion
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_disconnected',
                    'user': self.user.username if self.user else 'Unknown',
                    'message': f'{self.user.username if self.user else "Un joueur"} a quitté la partie'
                }
            )
            
            # Quitter le groupe
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Router les messages selon leur type
            handlers = {
                'make_move': self.handle_make_move,
                'join_game': self.handle_join_game,
                'start_game': self.handle_start_game,
                'surrender': self.handle_surrender,
                'send_message': self.handle_chat_message,
                'heartbeat': self.handle_heartbeat,
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self.send_error('Type de message invalide')
                
        except json.JSONDecodeError:
            await self.send_error('Format JSON invalide')
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_make_move(self, data):
        """Gérer un mouvement de jeu."""
        try:
            move_data = data.get('move_data')
            
            if not move_data:
                await self.send_error('Données de mouvement manquantes')
                return
            
            # Vérifier que c'est le tour du joueur
            if self.game.current_player_id != self.user.id:
                await self.send_error('Ce n\'est pas votre tour')
                return
            
            # Vérifier le timeout
            if await self.is_turn_timeout():
                await self.handle_timeout()
                return
            
            # Effectuer le mouvement
            success = await self.make_move(self.game, self.user, move_data)
            
            if success:
                # Envoyer l'état mis à jour à tous les joueurs
                await self.send_game_state_to_group()
                
                # Démarrer le timer pour le prochain tour
                await self.start_turn_timer()
                
                # Vérifier les conditions de victoire
                winner = await self.check_win_condition(self.game)
                if winner:
                    await self.handle_game_end(winner)
            else:
                await self.send_error('Mouvement invalide')
                
        except Exception as e:
            await self.send_error(f'Erreur lors du mouvement: {str(e)}')
    
    async def handle_join_game(self, data):
        """Gérer la demande de rejoindre une partie."""
        try:
            if self.game.status != 'waiting':
                await self.send_error('La partie n\'est plus disponible')
                return
            
            if self.game.player1_id == self.user.id:
                await self.send_error('Vous êtes déjà dans cette partie')
                return
            
            # Rejoindre la partie
            success = await self.join_game(self.game, self.user)
            
            if success:
                await self.send_game_state_to_group()
                
                # Notifier que la partie peut commencer
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_ready',
                        'message': 'La partie peut maintenant commencer!'
                    }
                )
            else:
                await self.send_error('Impossible de rejoindre la partie')
                
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_start_game(self, data):
        """Démarrer la partie."""
        try:
            if self.game.status != 'ready':
                await self.send_error('La partie n\'est pas prête à être démarrée')
                return
            
            # Seul le créateur peut démarrer
            if self.game.player1_id != self.user.id:
                await self.send_error('Seul le créateur peut démarrer la partie')
                return
            
            # Démarrer la partie
            await self.start_game(self.game)
            
            # Envoyer l'état de jeu à tous les joueurs
            await self.send_game_state_to_group()
            
            # Démarrer le timer du premier tour
            await self.start_turn_timer()
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_started',
                    'message': 'La partie a commencé!'
                }
            )
            
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_surrender(self, data):
        """Gérer l'abandon d'un joueur."""
        try:
            if self.game.status != 'playing':
                await self.send_error('La partie n\'est pas en cours')
                return
            
            # Déterminer le gagnant (l'adversaire)
            winner = await self.get_opponent(self.game, self.user)
            
            if winner:
                await self.end_game(self.game, winner, reason='surrender')
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_ended',
                        'winner': winner.username,
                        'reason': 'surrender',
                        'message': f'{self.user.username} a abandonné. {winner.username} remporte la partie!'
                    }
                )
                
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_chat_message(self, data):
        """Gérer les messages de chat."""
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        # Limiter la longueur du message
        if len(message) > 200:
            await self.send_error('Message trop long (max 200 caractères)')
            return
        
        # Envoyer le message à tous les joueurs
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user': self.user.username,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_heartbeat(self, data):
        """Gérer les pings de keepalive."""
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def start_turn_timer(self):
        """Démarrer le timer pour le tour actuel."""
        if self.game.status == 'playing':
            # Programmer la vérification du timeout
            asyncio.create_task(self.check_timeout_after_delay())
    
    async def check_timeout_after_delay(self):
        """Vérifier le timeout après un délai."""
        # Attendre la durée du timeout (2 minutes)
        await asyncio.sleep(120)
        
        # Recharger la partie pour vérifier l'état actuel
        current_game = await self.get_game_by_id(self.game.id)
        
        if current_game.status == 'playing' and await self.is_turn_timeout():
            await self.handle_timeout()
    
    async def handle_timeout(self):
        """Gérer le timeout d'un joueur."""
        try:
            # Déterminer le gagnant (l'adversaire du joueur actuel)
            current_player = await self.get_user_by_id(self.game.current_player_id)
            winner = await self.get_opponent(self.game, current_player)
            
            if winner:
                await self.end_game(self.game, winner, reason='timeout')
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_ended',
                        'winner': winner.username,
                        'reason': 'timeout',
                        'message': f'{current_player.username} a dépassé le temps limite. {winner.username} remporte la partie!'
                    }
                )
                
        except Exception as e:
            print(f"Erreur timeout: {e}")
    
    async def handle_game_end(self, winner):
        """Gérer la fin de partie."""
        await self.end_game(self.game, winner, reason='victory')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_ended',
                'winner': winner.username,
                'reason': 'victory',
                'message': f'{winner.username} remporte la partie!'
            }
        )
    
    async def send_game_state(self):
        """Envoyer l'état actuel de la partie."""
        game_state = await self.get_game_state(self.game)
        
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': game_state
        }))
    
    async def send_game_state_to_group(self):
        """Envoyer l'état de la partie à tous les joueurs du groupe."""
        game_state = await self.get_game_state(self.game)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state_update',
                'data': game_state
            }
        )
    
    async def send_error(self, message):
        """Envoyer un message d'erreur."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    # Handlers pour les messages du groupe
    async def game_state_update(self, event):
        """Envoyer la mise à jour de l'état de jeu."""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': event['data']
        }))
    
    async def player_connected(self, event):
        """Notifier qu'un joueur s'est connecté."""
        await self.send(text_data=json.dumps({
            'type': 'player_connected',
            'user': event['user'],
    async def player_disconnected(self, event):
        """Notifier qu'un joueur s'est déconnecté."""
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'user': event['user'],
            'message': event['message']
        }))
    
    async def game_ready(self, event):
        """Notifier que la partie est prête."""
        await self.send(text_data=json.dumps({
            'type': 'game_ready',
            'message': event['message']
        }))
    
    async def game_started(self, event):
        """Notifier que la partie a commencé."""
        await self.send(text_data=json.dumps({
            'type': 'game_started',
            'message': event['message']
        }))
    
    async def game_ended(self, event):
        """Notifier que la partie s'est terminée."""
        await self.send(text_data=json.dumps({
            'type': 'game_ended',
            'winner': event['winner'],
            'reason': event['reason'],
            'message': event['message']
        }))
    
    async def chat_message(self, event):
        """Envoyer un message de chat."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user': event['user'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
    
    async def turn_alert(self, event):
        """Envoyer une alerte de fin de tour."""
        await self.send(text_data=json.dumps({
            'type': 'turn_alert',
            'time_remaining': event['time_remaining'],
            'message': f'Plus que {event["time_remaining"]} secondes!'
        }))
    
    # Méthodes d'accès à la base de données (async)
    @database_sync_to_async
    def get_game_by_room_code(self, room_code):
        """Obtenir une partie par son code."""
        return Game.objects.select_related(
            'player1', 'player2', 'game_type', 'winner'
        ).get(room_code=room_code)
    
    @database_sync_to_async
    def get_game_by_id(self, game_id):
        """Obtenir une partie par son ID."""
        return Game.objects.select_related(
            'player1', 'player2', 'game_type', 'winner'
        ).get(id=game_id)
    
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """Obtenir un utilisateur par son ID."""
        return User.objects.get(id=user_id)
    
    @database_sync_to_async
    def user_can_access_game(self, user, game):
        """Vérifier si l'utilisateur peut accéder à la partie."""
        return user in [game.player1, game.player2] or not game.is_private
    
    @database_sync_to_async
    def join_game(self, game, user):
        """Rejoindre une partie."""
        try:
            game.join_game(user)
            return True
        except ValidationError:
            return False
    
    @database_sync_to_async
    def start_game(self, game):
        """Démarrer une partie."""
        game.start_game()
    
    @database_sync_to_async
    def make_move(self, game, user, move_data):
        """Effectuer un mouvement."""
        try:
            return game.make_move(user, move_data)
        except ValidationError:
            return False
    
    @database_sync_to_async
    def end_game(self, game, winner, reason='victory'):
        """Terminer une partie."""
        game.end_game(winner, reason)
    
    @database_sync_to_async
    def get_opponent(self, game, user):
        """Obtenir l'adversaire d'un joueur."""
        return game.get_opponent(user)
    
    @database_sync_to_async
    def is_turn_timeout(self):
        """Vérifier si le timeout est dépassé."""
        return self.game.is_turn_timeout()
    
    @database_sync_to_async
    def check_win_condition(self, game):
        """Vérifier les conditions de victoire."""
        if game.check_win_condition():
            # Retourner le joueur actuel comme gagnant
            return game.current_player
        return None
    
    @database_sync_to_async
    def get_game_state(self, game):
        """Obtenir l'état complet de la partie."""
        return {
            'id': str(game.id),
            'room_code': game.room_code,
            'game_type': {
                'name': game.game_type.name,
                'display_name': game.game_type.display_name,
                'category': game.game_type.category,
            },
            'status': game.status,
            'bet_amount': str(game.bet_amount),
            'currency': game.currency,
            'total_pot': str(game.total_pot),
            'winner_prize': str(game.winner_prize),
            'players': {
                'player1': {
                    'id': str(game.player1.id),
                    'username': game.player1.username,
                    'time_left': game.player1_time_left,
                } if game.player1 else None,
                'player2': {
                    'id': str(game.player2.id),
                    'username': game.player2.username,
                    'time_left': game.player2_time_left,
                } if game.player2 else None,
                'current_player': {
                    'id': str(game.current_player.id),
                    'username': game.current_player.username,
                } if game.current_player else None,
            },
            'game_data': game.game_data,
            'move_history': game.move_history,
            'turn_start_time': game.turn_start_time.isoformat() if game.turn_start_time else None,
            'turn_timeout': game.turn_timeout,
            'created_at': game.created_at.isoformat(),
            'started_at': game.started_at.isoformat() if game.started_at else None,
            'finished_at': game.finished_at.isoformat() if game.finished_at else None,
            'winner': {
                'id': str(game.winner.id),
                'username': game.winner.username,
            } if game.winner else None,
        }


class MatchmakingConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour le matchmaking."""
    
    async def connect(self):
        """Établir la connexion WebSocket."""
        self.user = self.scope.get('user')
        
        # Vérifier l'authentification
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        # Rejoindre le groupe personnel de l'utilisateur
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les parties en attente
        await self.send_waiting_games()
    
    async def disconnect(self, close_code):
        """Fermer la connexion WebSocket."""
        if hasattr(self, 'user_group_name'):
            # Annuler toutes les recherches de parties en cours
            await self.cancel_matchmaking_searches()
            
            # Quitter le groupe
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            handlers = {
                'search_game': self.handle_search_game,
                'cancel_search': self.handle_cancel_search,
                'create_private_game': self.handle_create_private_game,
                'get_waiting_games': self.handle_get_waiting_games,
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self.send_error('Type de message invalide')
                
        except json.JSONDecodeError:
            await self.send_error('Format JSON invalide')
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_search_game(self, data):
        """Gérer la recherche de partie."""
        try:
            game_type_name = data.get('game_type')
            bet_amount = data.get('bet_amount')
            currency = data.get('currency', 'FCFA')
            
            if not all([game_type_name, bet_amount]):
                await self.send_error('Paramètres manquants')
                return
            
            # Vérifier les fonds suffisants
            user_balance = await self.get_user_balance(self.user, currency)
            if user_balance < float(bet_amount):
                await self.send_error('Solde insuffisant')
                return
            
            # Chercher une partie existante ou en créer une nouvelle
            game = await self.find_or_create_game(
                self.user, game_type_name, bet_amount, currency
            )
            
            if game:
                await self.send(text_data=json.dumps({
                    'type': 'game_found',
                    'game': {
                        'id': str(game.id),
                        'room_code': game.room_code,
                        'game_type': game.game_type.display_name,
                        'bet_amount': str(game.bet_amount),
                        'currency': game.currency,
                    }
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'searching',
                    'message': 'Recherche d\'adversaire en cours...'
                }))
                
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_cancel_search(self, data):
        """Annuler la recherche de partie."""
        await self.cancel_user_searches(self.user)
        
        await self.send(text_data=json.dumps({
            'type': 'search_cancelled',
            'message': 'Recherche annulée'
        }))
    
    async def handle_create_private_game(self, data):
        """Créer une partie privée."""
        try:
            game_type_name = data.get('game_type')
            bet_amount = data.get('bet_amount')
            currency = data.get('currency', 'FCFA')
            
            game = await self.create_private_game(
                self.user, game_type_name, bet_amount, currency
            )
            
            await self.send(text_data=json.dumps({
                'type': 'private_game_created',
                'game': {
                    'id': str(game.id),
                    'room_code': game.room_code,
                    'game_type': game.game_type.display_name,
                    'bet_amount': str(game.bet_amount),
                    'currency': game.currency,
                }
            }))
            
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_get_waiting_games(self, data):
        """Obtenir les parties en attente."""
        await self.send_waiting_games()
    
    async def send_waiting_games(self):
        """Envoyer la liste des parties en attente."""
        waiting_games = await self.get_waiting_games()
        
        await self.send(text_data=json.dumps({
            'type': 'waiting_games',
            'games': waiting_games
        }))
    
    async def send_error(self, message):
        """Envoyer un message d'erreur."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    # Handlers pour les messages du groupe
    async def match_found(self, event):
        """Notifier qu'un match a été trouvé."""
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'game': event['game'],
            'opponent': event['opponent']
        }))
    
    # Méthodes d'accès à la base de données
    @database_sync_to_async
    def get_user_balance(self, user, currency):
        """Obtenir le solde utilisateur."""
        return float(user.get_balance(currency))
    
    @database_sync_to_async
    def find_or_create_game(self, user, game_type_name, bet_amount, currency):
        """Trouver une partie existante ou en créer une nouvelle."""
        from decimal import Decimal
        
        # Chercher une partie en attente
        game_type = GameType.objects.get(name=game_type_name, is_active=True)
        
        waiting_game = Game.objects.filter(
            game_type=game_type,
            bet_amount=Decimal(str(bet_amount)),
            currency=currency,
            status='waiting',
            is_private=False
        ).exclude(player1=user).first()
        
        if waiting_game:
            # Rejoindre la partie existante
            waiting_game.join_game(user)
            return waiting_game
        else:
            # Créer une nouvelle partie
            game = Game.objects.create(
                game_type=game_type,
                player1=user,
                bet_amount=Decimal(str(bet_amount)),
                currency=currency,
                status='waiting'
            )
            
            # Débiter la mise du créateur
            user.update_balance(currency, bet_amount, 'subtract')
            
            return game
    
    @database_sync_to_async
    def create_private_game(self, user, game_type_name, bet_amount, currency):
        """Créer une partie privée."""
        from decimal import Decimal
        
        game_type = GameType.objects.get(name=game_type_name, is_active=True)
        
        game = Game.objects.create(
            game_type=game_type,
            player1=user,
            bet_amount=Decimal(str(bet_amount)),
            currency=currency,
            status='waiting',
            is_private=True
        )
        
        # Débiter la mise du créateur
        user.update_balance(currency, bet_amount, 'subtract')
        
        return game
    
    @database_sync_to_async
    def get_waiting_games(self):
        """Obtenir les parties en attente."""
        games = Game.objects.filter(
            status='waiting',
            is_private=False
        ).select_related('player1', 'game_type')[:20]
        
        return [
            {
                'id': str(game.id),
                'room_code': game.room_code,
                'game_type': game.game_type.display_name,
                'bet_amount': str(game.bet_amount),
                'currency': game.currency,
                'creator': game.player1.username,
                'created_at': game.created_at.isoformat(),
            }
            for game in games
        ]
    
    @database_sync_to_async
    def cancel_user_searches(self, user):
        """Annuler les recherches de l'utilisateur."""
        # Supprimer les parties en attente créées par l'utilisateur
        user_waiting_games = Game.objects.filter(
            player1=user,
            status='waiting',
            player2__isnull=True
        )
        
        for game in user_waiting_games:
            # Rembourser la mise
            user.update_balance(game.currency, game.bet_amount, 'add')
            game.delete()
    
    @database_sync_to_async
    def cancel_matchmaking_searches(self):
        """Annuler toutes les recherches de matchmaking."""
        return self.cancel_user_searches(self.user)


class SpectatorConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour les spectateurs."""
    
    async def connect(self):
        """Établir la connexion WebSocket."""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}_spectators'
        self.user = self.scope.get('user')
        
        # Les spectateurs peuvent être anonymes
        try:
            self.game = await self.get_game_by_room_code(self.room_name)
            
            # Vérifier si les spectateurs sont autorisés
            if not self.game.spectators_allowed:
                await self.close(code=4003)
                return
                
        except Game.DoesNotExist:
            await self.close(code=4004)
            return
        
        # Rejoindre le groupe des spectateurs
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état actuel de la partie
        await self.send_game_state()
    
    async def disconnect(self, close_code):
        """Fermer la connexion WebSocket."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Les spectateurs ne peuvent que recevoir des messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_response',
                    'timestamp': timezone.now().isoformat()
                }))
        except:
            pass  # Ignorer les erreurs pour les spectateurs
    
    async def send_game_state(self):
        """Envoyer l'état actuel de la partie (version spectateur)."""
        game_state = await self.get_spectator_game_state(self.game)
        
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': game_state
        }))
    
    # Handlers pour les messages du groupe
    async def game_state_update(self, event):
        """Mise à jour de l'état de jeu pour les spectateurs."""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': event['data']
        }))
    
    async def game_ended(self, event):
        """Notifier que la partie s'est terminée."""
        await self.send(text_data=json.dumps({
            'type': 'game_ended',
            'winner': event['winner'],
            'reason': event['reason'],
            'message': event['message']
        }))
    
    # Méthodes d'accès à la base de données
    @database_sync_to_async
    def get_game_by_room_code(self, room_code):
        """Obtenir une partie par son code."""
        return Game.objects.select_related(
            'player1', 'player2', 'game_type', 'winner'
        ).get(room_code=room_code)
    
    @database_sync_to_async
    def get_spectator_game_state(self, game):
        """Obtenir l'état de la partie pour les spectateurs (sans données sensibles)."""
        return {
            'id': str(game.id),
            'room_code': game.room_code,
            'game_type': {
                'name': game.game_type.name,
                'display_name': game.game_type.display_name,
                'category': game.game_type.category,
            },
            'status': game.status,
            'bet_amount': str(game.bet_amount),
            'currency': game.currency,
            'players': {
                'player1': {
                    'username': game.player1.username,
                } if game.player1 else None,
                'player2': {
                    'username': game.player2.username,
                } if game.player2 else None,
                'current_player': {
                    'username': game.current_player.username,
                } if game.current_player else None,
            },
            'game_data': game.game_data,  # Les spectateurs peuvent voir l'état du jeu
            'move_history': game.move_history,
            'started_at': game.started_at.isoformat() if game.started_at else None,
            'winner': {
                'username': game.winner.username,
            } if game.winner else None,
        }message']
        }))
    
    async def player_disconnected(self, event):
        """Notifier qu'un joueur s'est déconnecté."""
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'user': event['user'],
            'message': event['
