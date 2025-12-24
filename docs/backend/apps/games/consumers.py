# apps/games/consumers.py
# ========================

import json
import asyncio
import logging
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

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
        self.timer_task = None  # Tâche pour le timer
        
        logger.info(f"WebSocket connection attempt by user: {self.user} for room: {self.room_name}")
        
        # Vérifier l'authentification
        if isinstance(self.user, AnonymousUser):
            logger.error(f"Anonymous user tried to connect to room {self.room_name}")
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
        
        # Démarrer le timer pour les jeux compétitifs (dames, échecs, ludo et cartes)
        game_type_name = await database_sync_to_async(lambda: self.game.game_type.name.lower())()
        if game_type_name in ['dames', 'échecs', 'ludo', 'cartes']:
            self.timer_task = asyncio.create_task(self.timer_loop())
            logger.info(f"⏰ Timer loop started for {game_type_name}")
        
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
        # Arrêter le timer
        if hasattr(self, 'timer_task') and self.timer_task:
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass
        
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
            logger.info(f"📨 RAW text_data received: {text_data[:200]}...")  # Log brut
            logger.info(f"📨 text_data type: {type(text_data)}")
            
            data = json.loads(text_data)
            logger.info(f"📨 Parsed data type: {type(data)}")
            
            message_type = data.get('type')
            
            logger.info(f"WebSocket message received from user {self.user} in room {self.room_name}:")
            logger.info(f"Message type: {message_type}")
            logger.info(f"Message data: {data}")
            
            # Router les messages selon leur type
            handlers = {
                'make_move': self.handle_make_move,
                'join_game': self.handle_join_game,
                'start_game': self.handle_start_game,
                'surrender': self.handle_surrender,
                'send_message': self.handle_chat_message,
                'heartbeat': self.handle_heartbeat,
                'get_game_state': self.handle_get_game_state,
            }
            
            logger.info(f"Looking for handler for message type: {message_type}")
            handler = handlers.get(message_type)
            if handler:
                logger.info(f"Found handler {handler.__name__} for {message_type}, calling it now...")
                await handler(data)
                logger.info(f"Handler {handler.__name__} completed for {message_type}")
            else:
                logger.error(f"No handler found for message type: {message_type}")
                await self.send_error('Type de message invalide')
                
        except json.JSONDecodeError:
            logger.error(f"JSON decode error for message from user {self.user}")
            await self.send_error('Format JSON invalide')
        except Exception as e:
            logger.error(f"Unexpected error in receive for user {self.user}: {str(e)}")
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_make_move(self, data):
        """Gérer un mouvement de jeu."""
        try:
            logger.info(f"🎮 HANDLE_MAKE_MOVE START for user {self.user.username}")
            logger.info(f"🎮 Room: {self.room_name}, Group: {self.room_group_name}")
            logger.info(f"🎮 Data received: {data}")
            move_data = data.get('move_data')
            
            logger.info(f"Received move_data: {move_data} from user {self.user.username}")
            
            if not move_data:
                logger.error("Move data is missing")
                await self.send_error('Données de mouvement manquantes')
                return
            
            # ✅ CORRECTION CRITIQUE: Toujours recharger depuis la DB pour avoir l'état le plus récent
            # Cela synchronise avec les modifications faites par le timer (passage automatique de tour)
            logger.debug(f"🔄 Reloading game from DB to get latest state...")
            await self.refresh_game_from_db()
            logger.debug(f"🔄 Game reloaded: game ID = {self.game.id}, status = {self.game.status}")
            
            # Accès async-safe au current_player
            from asgiref.sync import sync_to_async
            get_current_player = sync_to_async(lambda: self.game.current_player)
            current_player = await get_current_player()
            
            logger.debug(f"After refresh: game.current_player = {current_player}")
            logger.debug(f"Current player variable: {current_player}")
            
            if not current_player:
                logger.warning("No current player set in game - initializing to player1")
                # Initialiser le current_player si NULL
                await self.initialize_current_player()
                current_player = await get_current_player()
                logger.debug(f"After initialization: current_player = {current_player}")
                
            logger.debug(f"About to check turn: current_player.id={current_player.id}, user.id={self.user.id}")
            
            if current_player.id != self.user.id:
                logger.error(f"Not user's turn: current={current_player.username}, trying={self.user.username}")
                await self.send_error('Ce n\'est pas votre tour')
                return
            
            logger.info(f"Turn validation passed for {self.user.username}")
            
            # Vérifier le timeout
            if await self.is_turn_timeout():
                logger.warning(f"Turn timeout for {self.user.username}")
                await self.handle_timeout()
                return
            
            # Effectuer le mouvement
            success = await self.make_move(self.game, self.user, move_data)
            
            if success:
                logger.info(f"Move successful, broadcasting game state update")
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
            logger.error(f'Unexpected error in handle_make_move: {str(e)}', exc_info=True)
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
        """Gérer les pings de keepalive et vérifier les timeouts."""
        from asgiref.sync import sync_to_async
        
        # Vérifier les timeouts pour les jeux compétitifs
        if hasattr(self, 'game') and self.game:
            game = self.game
            
            # Recharger le jeu pour avoir l'état actuel
            await sync_to_async(game.refresh_from_db, thread_sensitive=True)()
            
            # Vérifier le timeout d'échecs
            if game.game_type.name == 'Échecs' and game.status == 'playing':
                from apps.games.game_logic.chess_competitive import check_and_auto_pass_turn_if_timeout
                
                new_game_data, turn_was_passed = check_and_auto_pass_turn_if_timeout(game.game_data)
                
                if turn_was_passed:
                    logger.warning(f"⏰ Chess timeout detected in heartbeat, switching turn")
                    game.game_data = new_game_data
                    
                    # Mettre à jour current_player
                    timer_data = game.game_data.get('timer', {})
                    next_color = timer_data.get('current_player', 'white')
                    
                    if next_color == 'white':
                        game.current_player = game.player1
                    else:
                        game.current_player = game.player2
                    
                    await sync_to_async(game.save)()
                    
                    # Broadcaster le nouvel état
                    await self.broadcast_game_state()
            
            # Vérifier le timeout de dames
            elif game.game_type.name == 'Dames' and game.status == 'playing':
                from apps.games.game_logic.checkers_competitive import check_and_auto_pass_turn_if_timeout as checkers_timeout
                
                new_game_data, turn_was_passed = checkers_timeout(game.game_data)
                
                if turn_was_passed:
                    logger.warning(f"⏰ Checkers timeout detected in heartbeat, switching turn")
                    game.game_data = new_game_data
                    
                    # Mettre à jour current_player
                    timer_data = game.game_data.get('timer', {})
                    next_color = timer_data.get('current_player', 'white')
                    
                    if next_color == 'white':
                        game.current_player = game.player1
                    else:
                        game.current_player = game.player2
                    
                    await sync_to_async(game.save)()
                    
                    # Broadcaster le nouvel état
                    await self.broadcast_game_state()
        
        # Utiliser datetime au lieu de timezone pour éviter le problème async
        from datetime import datetime
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def handle_get_game_state(self, data):
        """Gérer la demande explicite de l'état du jeu."""
        logger.info(f"🔄 GET_GAME_STATE requested by user {self.user.username}")
        await self.send_game_state()
    
    async def make_move(self, game, user, move_data):
        """Effectuer un mouvement via WebSocket - lien vers la méthode du modèle."""
        try:
            logger.info(f"🎯 WEBSOCKET make_move called for user {user.username}")
            logger.info(f"🎯 Game ID: {game.id}, Room: {game.room_code}")
            logger.info(f"🎯 Game Type: {game.game_type.name}")
            logger.info(f"🎯 Move data: {move_data}")
            
            # Utiliser database_sync_to_async pour appeler la méthode synchrone du modèle
            from asgiref.sync import sync_to_async
            
            # Appeler la méthode make_move du modèle Game
            result = await sync_to_async(game.make_move)(user, move_data)
            
            logger.info(f"Game model make_move result: {result}")
            
            if result.get('success'):
                logger.info(f"Move successful: {result.get('message')}")
                return True
            else:
                logger.error(f"Move failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Error in WebSocket make_move: {str(e)}", exc_info=True)
            return False
    
    async def refresh_game(self):
        """Recharger les données du jeu depuis la base de données."""
        try:
            from asgiref.sync import sync_to_async
            
            logger.debug(f"Refreshing game with ID: {self.game.id}")
            
            # Recharger le jeu depuis la base de données
            get_game = sync_to_async(lambda: Game.objects.select_related('player1', 'player2', 'current_player').get(id=self.game.id))
            self.game = await get_game()
            
            logger.debug(f"Game refreshed - status: {self.game.status}, current_player: {self.game.current_player}")
            
        except Exception as e:
            logger.error(f"Error refreshing game: {str(e)}", exc_info=True)
            raise
    
    async def refresh_game_from_db(self):
        """Alias pour refresh_game - recharger l'objet game depuis la DB."""
        await self.refresh_game()
    
    async def initialize_current_player(self):
        """Initialiser le joueur actuel si NULL."""
        try:
            from asgiref.sync import sync_to_async
            
            logger.info(f"Initializing current_player for game {self.game.id}")
            
            # Définir le player1 comme joueur actuel par défaut
            def set_current_player():
                self.game.current_player = self.game.player1
                self.game.save(update_fields=['current_player'])
                return self.game
            
            self.game = await sync_to_async(set_current_player)()
            
            logger.info(f"Current player initialized to: {self.game.current_player.username}")
            
        except Exception as e:
            logger.error(f"Error initializing current player: {str(e)}", exc_info=True)
            raise

    async def is_turn_timeout(self):
        """Vérifier si le tour actuel a expiré (timeout)."""
        # Pour l'instant, on désactive les timeouts pour simplifier
        return False

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
        
        logger.info(f"📡 BROADCASTING game state to group {self.room_group_name}")
        logger.info(f"📡 Game data keys: {game_state.keys()}")
        
        # Log pour Ludo - vérifier les pièces
        game_data = game_state.get('game_data', {})
        if 'pieces' in game_data:
            logger.info(f"📡 Ludo pieces count: {len(game_data['pieces'])}")
            logger.info(f"📡 Ludo pieces: {game_data['pieces'][:2]}...")  # Premiers 2 pions
        else:
            logger.info(f"📡 NO pieces in game_data")
            
        logger.info(f"📡 Game board first row: {game_state.get('game_data', {}).get('board', [[]])[0] if game_state.get('game_data', {}).get('board') else 'NO BOARD'}")
        logger.info(f"📡 Current player: {game_state.get('players', {}).get('current_player')}")
        logger.info(f"📡 Move history length: {len(game_state.get('move_history', []))}")
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state_update',
                'data': game_state
            }
        )
        
        logger.info(f"game_state_update sent to group {self.room_group_name}")
    
    async def send_error(self, message):
        """Envoyer un message d'erreur."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    async def timer_loop(self):
        """Boucle de vérification du timer pour les jeux compétitifs (dames et échecs)."""
        try:
            tick_count = 0
            while True:
                await asyncio.sleep(1)  # Vérifier toutes les secondes
                tick_count += 1
                
                # Vérifier uniquement si le jeu est en cours
                game_status = await database_sync_to_async(lambda: self.game.status)()
                if game_status != 'playing':
                    continue
                
                # Obtenir le type de jeu
                game_type_name = await database_sync_to_async(lambda: self.game.game_type.name.lower())()
                
                # ✅ CORRECTION: Diffuser toutes les 5 secondes pour synchronisation légère
                # Le frontend calcule le temps localement avec les timestamps
                if tick_count % 5 == 0:
                    await self.send_game_state_to_group()
                
                # Vérifier et gérer le timeout selon le type de jeu
                timeout_handled = False
                
                if game_type_name == 'dames':
                    timeout_handled = await self.check_and_handle_checkers_timeout()
                elif game_type_name == 'échecs':
                    timeout_handled = await self.check_and_handle_chess_timeout()
                elif game_type_name == 'ludo':
                    timeout_handled = await self.check_and_handle_ludo_timeout()
                elif game_type_name == 'cartes':
                    timeout_handled = await self.check_and_handle_cards_timeout()
                
                if timeout_handled:
                    # Le jeu est terminé par timeout ou le tour a été passé
                    # Envoyer la mise à jour à tous les joueurs immédiatement
                    logger.info("⏰ Timer: Game ended or turn passed by timeout, broadcasting update")
                    await self.send_game_state_to_group()
                    
                    # Si le jeu est terminé, arrêter le timer
                    game_status = await database_sync_to_async(lambda: self.game.status)()
                    if game_status == 'finished':
                        logger.info(f"🏁 Game finished by timeout, stopping timer loop for {self.room_name}")
                        break
                    
        except asyncio.CancelledError:
            logger.info(f"Timer loop cancelled for room {self.room_name}")
            raise
        except Exception as e:
            logger.error(f"Error in timer loop: {str(e)}", exc_info=True)
    
    @database_sync_to_async
    def check_and_handle_checkers_timeout(self):
        """Vérifier et gérer le timeout pour les dames compétitives (60s = victoire adversaire)."""
        try:
            from apps.games.game_logic.checkers_competitive import check_and_auto_pass_turn_if_timeout
            from apps.games.models import Game
            
            # Recharger le jeu depuis la DB
            db_game = Game.objects.get(pk=self.game.pk)
            
            # Vérifier si game_data existe dans la DB
            if not db_game.game_data:
                logger.warning(f"⏰ No game_data found for game {db_game.room_code}")
                return False
            
            # Vérifier le timeout sur l'état de la DB (60s)
            new_game_data, timeout_triggered = check_and_auto_pass_turn_if_timeout(db_game.game_data)
            
            if timeout_triggered:
                # Vérifier si le jeu est terminé par timeout
                if new_game_data.get('game_over'):
                    winner_color = new_game_data.get('winner')
                    logger.warning(f"🏁 Checkers GAME OVER by timeout: {winner_color} wins")
                    
                    # Mettre à jour game_data
                    db_game.game_data = new_game_data
                    db_game.status = 'finished'
                    
                    # Trouver le joueur gagnant
                    winner_player = db_game.player1 if winner_color == 'red' else db_game.player2
                    
                    # Terminer le jeu
                    if winner_player:
                        db_game.end_game(winner_player, reason='timeout')
                        logger.info(f"🏆 {winner_player.username} wins by timeout!")
                    
                    # Sauvegarder
                    db_game.save()
                    
                    # Mettre à jour self.game en mémoire
                    self.game.game_data = new_game_data
                    self.game.status = 'finished'
                    
                    return True
                else:
                    # Tour passé seulement (si la logique le permet encore)
                    logger.warning(f"⏰ Checkers Timer: Turn auto-passed for game {db_game.room_code}")
                    logger.info(f"⏰ Current move_history length: {len(db_game.move_history) if db_game.move_history else 0}")
                    
                    # Mettre à jour game_data avec le nouveau tour
                    db_game.game_data = new_game_data
                    
                    # Synchroniser current_player avec le game_data
                    current_player_color = new_game_data.get('current_player')
                    if current_player_color == 'red':
                        db_game.current_player = db_game.player1
                        logger.info(f"⏰ Updated current_player to RED (player1: {db_game.player1.username})")
                    elif current_player_color == 'black':
                        db_game.current_player = db_game.player2
                        logger.info(f"⏰ Updated current_player to BLACK (player2: {db_game.player2.username})")
                    
                    # Mettre à jour le début du tour
                    db_game.turn_start_time = timezone.now()
                    
                    # Sauvegarder les champs modifiés
                    db_game.save(update_fields=['game_data', 'current_player', 'turn_start_time'])
                    
                    # Mettre à jour self.game en mémoire
                    self.game.game_data = new_game_data
                    self.game.current_player = db_game.current_player
                    self.game.turn_start_time = db_game.turn_start_time
                    
                    logger.info(f"⏰ Game state saved to DB - move_history preserved with {len(db_game.move_history) if db_game.move_history else 0} moves")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"⏰ Error checking checkers timeout: {str(e)}")
            return False
    
    @database_sync_to_async
    def check_and_handle_chess_timeout(self):
        """Vérifier et gérer le timeout pour les échecs compétitifs.
        Si 60s écoulé sans jouer → adversaire gagne immédiatement."""
        try:
            from apps.games.game_logic.chess_competitive import check_and_auto_pass_turn_if_timeout
            from apps.games.models import Game
            
            # Recharger le jeu depuis la DB
            db_game = Game.objects.get(pk=self.game.pk)
            
            # Vérifier si game_data existe
            if not db_game.game_data:
                logger.warning(f"⏰ No game_data found for chess game {db_game.room_code}")
                return False
            
            # Vérifier le timeout (60s → game over, adversaire gagne)
            new_game_data, timeout_triggered = check_and_auto_pass_turn_if_timeout(db_game.game_data)
            
            if timeout_triggered:
                # Le timeout déclenche toujours un game over (victoire adversaire)
                if new_game_data.get('game_over'):
                    winner_color = new_game_data.get('winner')
                    timeout_reason = new_game_data.get('game_over_details', {}).get('reason', 'timeout')
                    logger.warning(f"🏁 Chess GAME OVER by {timeout_reason}: {winner_color} wins")
                    
                    # Mettre à jour game_data
                    db_game.game_data = new_game_data
                    db_game.status = 'finished'
                    
                    # Trouver le joueur gagnant
                    winner_player = db_game.player1 if winner_color == 'white' else db_game.player2
                    
                    # Terminer le jeu
                    if winner_player:
                        db_game.end_game(winner_player, reason='timeout')
                        logger.info(f"🏆 {winner_player.username} wins by timeout!")
                    
                    # Sauvegarder
                    db_game.save()
                    
                    # Mettre à jour self.game en mémoire
                    self.game.game_data = new_game_data
                    self.game.status = 'finished'
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"⏰ Error checking chess timeout: {str(e)}")
            return False
    
    @database_sync_to_async
    def check_and_handle_ludo_timeout(self):
        """Vérifier et gérer le timeout pour Ludo compétitif (60s = victoire adversaire)."""
        try:
            from apps.games.game_logic.ludo_competitive import check_and_auto_pass_turn_if_timeout
            from apps.games.models import Game
            
            # Recharger le jeu depuis la DB
            db_game = Game.objects.get(pk=self.game.pk)
            
            # Vérifier si game_data existe
            if not db_game.game_data:
                logger.warning(f"⏰ No game_data found for ludo game {db_game.room_code}")
                return False
            
            # Vérifier le timeout (60s)
            new_game_data, timeout_triggered = check_and_auto_pass_turn_if_timeout(db_game.game_data)
            
            if timeout_triggered:
                # Le jeu est terminé par timeout
                winner_color = new_game_data.get('winner')
                timeout_player = new_game_data.get('win_reason', '').replace('timeout_', '') if 'timeout_' in new_game_data.get('win_reason', '') else None
                
                logger.warning(f"🏁 Ludo GAME OVER by timeout: {winner_color} wins (opponent {timeout_player} exceeded 60s)")
                
                # Mettre à jour game_data
                db_game.game_data = new_game_data
                db_game.status = 'finished'
                
                # Trouver le joueur gagnant
                player_colors = new_game_data.get('player_colors', {})
                winner_player = None
                
                for player_id, color in player_colors.items():
                    if color == winner_color:
                        if str(db_game.player1.id) == player_id:
                            winner_player = db_game.player1
                        elif db_game.player2 and str(db_game.player2.id) == player_id:
                            winner_player = db_game.player2
                        break
                
                # Terminer le jeu avec victoire par timeout
                if winner_player:
                    db_game.end_game(winner_player, reason='timeout')
                    logger.info(f"🏆 {winner_player.username} wins by timeout!")
                
                # Sauvegarder
                db_game.save()
                
                # Mettre à jour self.game en mémoire
                self.game.game_data = new_game_data
                self.game.status = 'finished'
                
                logger.info(f"⏰ Ludo game ended by timeout and saved to DB")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"⏰ Error checking ludo timeout: {str(e)}")
            return False
    
    @database_sync_to_async
    def check_and_handle_cards_timeout(self):
        """Vérifier et gérer le timeout pour le jeu de cartes (60s = victoire adversaire)."""
        try:
            from datetime import datetime, timezone as dt_timezone
            from apps.games.models import Game
            
            # Recharger le jeu depuis la DB
            db_game = Game.objects.get(pk=self.game.pk)
            
            # Vérifier si game_data existe
            if not db_game.game_data:
                logger.warning(f"⏰ No game_data found for cards game {db_game.room_code}")
                return False
            
            timer = db_game.game_data.get('timer', {})
            if not timer:
                return False
            
            current_move_start = timer.get('current_move_start')
            if not current_move_start:
                return False
            
            try:
                move_start = datetime.fromisoformat(current_move_start.replace('Z', '+00:00'))
                now = datetime.now(dt_timezone.utc)
                elapsed = (now - move_start).total_seconds()
                
                # Si le temps écoulé dépasse 60 secondes
                if elapsed > 60:
                    current_player = db_game.current_player
                    logger.warning(f"...............: {current_player}")
                    winner = db_game.player2 if current_player == db_game.player1 else db_game.player1
                    
                    logger.warning(f"🏁 Cards GAME OVER by timeout: {winner.username} wins (opponent {current_player.username} exceeded 60s)")
                    
                    # Mettre à jour le statut
                    db_game.status = 'finished'
                    
                    # Terminer le jeu avec victoire par timeout
                    db_game.end_game(winner, reason='timeout')
                    logger.info(f"🏆 {winner.username} wins by timeout!")
                    
                    # Sauvegarder
                    db_game.save()
                    
                    # Mettre à jour self.game en mémoire
                    self.game.status = 'finished'
                    
                    logger.info(f"⏰ Cards game ended by timeout and saved to DB")
                    return True
            except Exception as e:
                logger.warning(f"Error checking cards timeout: {e}")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"⏰ Error checking cards timeout: {str(e)}")
            return False
    
    # Handlers pour les messages du groupe
    async def game_state_update(self, event):
        """Envoyer la mise à jour de l'état de jeu."""
        logger.info(f"🚀 SENDING game_state to client for user {self.user.username}")
        logger.info(f"🚀 Event data keys: {event['data'].keys()}")
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': event['data']
        }))
        logger.info(f"🚀 game_state SENT to client for user {self.user.username}")

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')

        if message_type == 'roll_dice':
            await self.handle_roll_dice()
        elif message_type == 'make_move':
            await self.handle_make_move(content)
        # autres types...

    async def handle_roll_dice(self):
        # Vérifier que c'est le tour du joueur
        if self.game.current_player_id != self.user.id:
            await self.send_error("Ce n'est pas votre tour")
            return

        # Vérifier que le joueur ne doit pas déjà faire un mouvement
        if self.game.game_data.get('must_move', False):
            await self.send_error("Vous devez d'abord effectuer un mouvement")
            return

        # Appeler la logique Ludo pour lancer le dé
        new_game_data, success, message, dice_value = await self.roll_ludo_dice(self.game.game_data)

        if success:
            self.game.game_data = new_game_data
            self.game.save()

            # Envoyer l'état mis à jour à tous
            await self.send_game_state_to_group()

            # Si pas de mouvements possibles, le tour peut être passé automatiquement
            # (logique déjà gérée dans roll_ludo_dice)
        else:
            await self.send_error(message)

    @database_sync_to_async
    def roll_ludo_dice(self, game_data):
        """Fonction placeholder pour le lancer de dé Ludo."""
        # TODO: Implémenter la logique de lancer de dé Ludo
        # Pour le moment, retourner des valeurs par défaut
        import random
        dice_value = random.randint(1, 6)
        return game_data, True, f"Dé lancé: {dice_value}", dice_value
    
    async def player_connected(self, event):
        """Notifier qu'un joueur s'est connecté."""
        await self.send(text_data=json.dumps({
            'type': 'player_connected',
            'user': event['user'],
            'message': event['message']
        }))
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
    def refresh_game(self):
        """Recharger l'objet game depuis la base de données."""
        self.game.refresh_from_db()
    
    @database_sync_to_async
    def initialize_current_player(self):
        """Initialiser le current_player s'il est NULL."""
        if not self.game.current_player:
            self.game.current_player = self.game.player1
            self.game.turn_start_time = timezone.now()
            self.game.save()
            logger.info(f"Initialized current_player to {self.game.player1.username}")

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
        # ✅ Recharger le jeu depuis la base pour avoir l'état le plus récent
        # Cela synchronise self.game avec la DB après les sauvegardes
        game.refresh_from_db()
        
        logger.info(f"📊 GET_GAME_STATE: Game {game.id} - {game.room_code}")
        logger.info(f"📊 Game type: {game.game_type.name}")
        logger.info(f"📊 Game status: {game.status}")
        logger.info(f"📊 Game data keys: {game.game_data.keys() if game.game_data else 'NO GAME_DATA'}")
        if game.game_data and 'board' in game.game_data:
            logger.info(f"📊 Board first row: {game.game_data['board'][0] if game.game_data['board'] else 'NO BOARD'}")
        logger.info(f"📊 Move history length: {len(game.move_history) if game.move_history else 0}")
        
        # Ajouter board_unicode pour les jeux de dames si pas déjà présent
        if game.game_type.name.lower() == 'dames' and game.game_data:
            # ✅ TOUJOURS régénérer board_unicode pour s'assurer qu'il est à jour après les mouvements
            from apps.games.game_logic.checkers_competitive import convert_board_to_unicode
            game.game_data['board_unicode'] = convert_board_to_unicode(game.game_data)
            logger.info(f"✅ Regenerated board_unicode for checkers game")
        
        result = {
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
        
        logger.info(f"📊 GET_GAME_STATE result keys: {result.keys()}")
        
        # Convertir tous les Decimal en float/string pour msgpack
        from decimal import Decimal
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = convert_decimals(result)
        
        return result


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
        }


# Consumer pour les jeux de cartes spécifiquement
class CardGameConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket spécialisé pour les jeux de cartes."""
    
    async def connect(self):
        """Établir la connexion WebSocket pour jeu de cartes."""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'card_game_{self.room_name}'
        self.user = self.scope.get('user')
        
        # Vérifier l'authentification
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
        
        try:
            self.game = await self.get_game_by_room_code(self.room_name)
            if not await self.user_can_access_game(self.user, self.game):
                await self.close(code=4003)
                return
        except Game.DoesNotExist:
            await self.close(code=4004)
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        await self.send_game_state()
    
    async def disconnect(self, close_code):
        """Fermer la connexion WebSocket."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            handlers = {
                'play_card': self.handle_play_card,
                'draw_card': self.handle_draw_card,
                'surrender': self.handle_surrender,
                'chat_message': self.handle_chat_message,
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
    
    async def handle_play_card(self, data):
        """Gérer le jeu d'une carte."""
        try:
            card_id = data.get('card_id')
            if not card_id:
                await self.send_error('ID de carte manquant')
                return
            
            if self.game.current_player_id != self.user.id:
                await self.send_error('Ce n\'est pas votre tour')
                return
            
            # Logique de jeu de carte ici
            success = await self.play_card(self.game, self.user, card_id)
            
            if success:
                await self.send_game_state_to_group()
                # Vérifier les conditions de fin de partie
                winner = await self.check_win_condition(self.game)
                if winner:
                    await self.handle_game_end(winner)
            else:
                await self.send_error('Carte invalide')
                
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_draw_card(self, data):
        """Gérer le tirage d'une carte."""
        try:
            if self.game.current_player_id != self.user.id:
                await self.send_error('Ce n\'est pas votre tour')
                return
            
            success = await self.draw_card(self.game, self.user)
            
            if success:
                await self.send_game_state_to_group()
            else:
                await self.send_error('Impossible de tirer une carte')
                
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def send_game_state(self):
        """Envoyer l'état actuel de la partie."""
        game_state = await self.get_game_state(self.game)
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': game_state
        }))
    
    async def send_game_state_to_group(self):
        """Envoyer l'état de la partie à tous les joueurs."""
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
    
    # Méthodes d'accès à la base de données
    @database_sync_to_async
    def get_game_by_room_code(self, room_code):
        """Obtenir une partie par son code."""
        return Game.objects.select_related(
            'player1', 'player2', 'game_type', 'winner'
        ).get(room_code=room_code)
    
    @database_sync_to_async
    def user_can_access_game(self, user, game):
        """Vérifier si l'utilisateur peut accéder à la partie."""
        return user in [game.player1, game.player2]
    
    @database_sync_to_async
    def play_card(self, game, user, card_id):
        """Jouer une carte."""
        # Logique de jeu de carte à implémenter
        return True
    
    @database_sync_to_async
    def draw_card(self, game, user):
        """Tirer une carte."""
        # Logique de tirage de carte à implémenter
        return True
    
    @database_sync_to_async
    def get_game_state(self, game):
        """Obtenir l'état complet de la partie."""
        return {
            'id': str(game.id),
            'room_code': game.room_code,
            'status': game.status,
            'game_data': game.game_data,
            'current_player': {
                'id': str(game.current_player.id),
                'username': game.current_player.username,
            } if game.current_player else None,
        }
    
    @database_sync_to_async
    def check_win_condition(self, game):
        """Vérifier les conditions de victoire."""
        if game.check_win_condition():
            # Retourner le joueur actuel comme gagnant
            return game.current_player
        return None
    
    @database_sync_to_async
    def get_opponent(self, game, user):
        """Obtenir l'adversaire d'un joueur."""
        return game.get_opponent(user)
    
    @database_sync_to_async
    def end_game(self, game, winner, reason='victory'):
        """Terminer une partie."""
        game.end_game(winner, reason)
    
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
    
    # Handlers pour les messages du groupe
    async def game_state_update(self, event):
        """Envoyer la mise à jour de l'état de jeu."""
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
    
    async def chat_message(self, event):
        """Envoyer un message de chat."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user': event['user'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))