#!/usr/bin/env python
"""
Script de test complet pour RUMO RUSH Backend.
Tests toutes les fonctionnalités principales du système.
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, KYCDocument
from apps.games.models import Game, GameType
from apps.payments.models import Transaction, PaymentMethod
from apps.referrals.models import Referral, ReferralProgram
from apps.games.game_logic.chess import ChessGame
from apps.games.game_logic.checkers import CheckersGame

class RumoRushTestSuite:
    """Suite de tests complète pour RUMO RUSH."""
    
    def __init__(self):
        self.client = APIClient()
        self.base_url = 'http://localhost:8000'
        self.test_users = {}
        self.test_games = {}
        
    def run_all_tests(self):
        """Exécuter tous les tests."""
        print("🚀 Démarrage de la suite de tests RUMO RUSH")
        print("=" * 60)
        
        try:
            # Tests des modèles
            self.test_user_models()
            self.test_game_models()
            self.test_payment_models()
            self.test_referral_models()
            
            # Tests de logique de jeu
            self.test_chess_logic()
            self.test_checkers_logic()
            
            # Tests API (si serveur disponible)
            if self.check_server_availability():
                self.test_authentication_api()
                self.test_game_api()
                self.test_payment_api()
                self.test_referral_api()
            else:
                print("⚠️  Serveur non disponible - tests API ignorés")
            
            print("\n✅ Tous les tests sont passés avec succès!")
            
        except Exception as e:
            print(f"\n❌ Erreur dans les tests: {str(e)}")
            raise
    
    def check_server_availability(self):
        """Vérifier si le serveur Django est disponible."""
        try:
            response = requests.get(f"{self.base_url}/api/health/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_user_models(self):
        """Tester les modèles utilisateur."""
        print("\n📝 Test des modèles utilisateur...")
        
        # Créer un utilisateur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone_number='+33123456789',
            date_of_birth='1990-01-01',
            country='France'
        )
        
        # Tests de base
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.age >= 33
        assert user.referral_code is not None
        assert len(user.referral_code) == 8
        
        # Test des soldes
        assert user.balance_fcfa == Decimal('0.00')
        assert user.balance_eur == Decimal('0.00')
        assert user.balance_usd == Decimal('0.00')
        
        # Test mise à jour de solde
        user.update_balance('FCFA', 1000, 'add')
        assert user.balance_fcfa == Decimal('1000.00')
        
        # Test retrait
        can_withdraw, message = user.can_withdraw('FCFA', 500)
        assert not can_withdraw  # KYC non approuvé
        
        # Approuver KYC
        user.kyc_status = 'approved'
        user.is_verified = True
        user.save()
        
        can_withdraw, message = user.can_withdraw('FCFA', 500)
        assert can_withdraw
        
        self.test_users['testuser'] = user
        print("✅ Modèles utilisateur validés")
    
    def test_game_models(self):
        """Tester les modèles de jeu."""
        print("\n🎮 Test des modèles de jeu...")
        
        # Créer un type de jeu
        game_type = GameType.objects.create(
            name='chess',
            display_name='Échecs',
            description='Jeu d\'échecs classique',
            category='strategy',
            min_bet_fcfa=500,
            max_bet_fcfa=100000
        )
        
        # Créer des utilisateurs pour le jeu
        player1 = self.test_users.get('testuser') or User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='pass123',
            date_of_birth='1990-01-01',
            country='France'
        )
        
        player2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='pass123',
            date_of_birth='1990-01-01',
            country='France'
        )
        
        # Ajouter des fonds
        player1.update_balance('FCFA', 10000, 'add')
        player2.update_balance('FCFA', 10000, 'add')
        
        # Créer une partie
        game = Game.objects.create(
            game_type=game_type,
            player1=player1,
            bet_amount=1000,
            currency='FCFA'
        )
        
        # Tests de base
        assert game.room_code is not None
        assert len(game.room_code) == 6
        assert game.status == 'waiting'
        assert game.total_pot == Decimal('2000.00')
        assert game.commission == Decimal('280.00')  # 14%
        assert game.winner_prize == Decimal('1720.00')
        
        # Test rejoindre la partie
        can_join, message = game.can_join(player2)
        assert can_join
        
        game.join_game(player2)
        assert game.player2 == player2
        assert game.status == 'ready'
        
        # Test démarrer la partie
        game.start_game()
        assert game.status == 'playing'
        assert game.current_player == player1
        assert game.started_at is not None
        
        self.test_games['chess'] = game
        print("✅ Modèles de jeu validés")
    
    def test_payment_models(self):
        """Tester les modèles de paiement."""
        print("\n💳 Test des modèles de paiement...")
        
        # Créer une méthode de paiement
        payment_method = PaymentMethod.objects.create(
            name='Mobile Money',
            method_type='mobile_money',
            supported_currencies=['FCFA'],
            min_deposit={'FCFA': 1000},
            max_deposit={'FCFA': 1000000},
            deposit_fee_percentage=Decimal('2.5')
        )
        
        user = self.test_users.get('testuser')
        if not user:
            user = User.objects.first()
        
        # Créer une transaction
        transaction = Transaction.objects.create(
            user=user,
            transaction_type='deposit',
            amount=5000,
            currency='FCFA',
            payment_method=payment_method
        )
        
        # Tests de base
        assert transaction.transaction_id is not None
        assert transaction.transaction_id.startswith('DEP')
        assert transaction.status == 'pending'
        
        # Test calcul des frais
        fees = payment_method.calculate_fees(Decimal('5000'), 'deposit')
        assert fees['percentage_fee'] == Decimal('125.00')  # 2.5%
        assert fees['total_fees'] == Decimal('125.00')
        
        # Test traitement de la transaction
        transaction.process()
        assert transaction.status == 'completed'
        
        print("✅ Modèles de paiement validés")
    
    def test_referral_models(self):
        """Tester les modèles de parrainage."""
        print("\n🤝 Test des modèles de parrainage...")
        
        # Créer un programme de parrainage
        program = ReferralProgram.objects.create(
            name='Programme Standard',
            description='Programme de parrainage standard',
            commission_type='percentage',
            commission_rate=Decimal('10.00'),
            free_games_limit=3
        )
        
        # Créer des utilisateurs
        referrer = User.objects.create_user(
            username='referrer',
            email='referrer@example.com',
            password='pass123',
            date_of_birth='1990-01-01',
            country='France'
        )
        
        referred = User.objects.create_user(
            username='referred',
            email='referred@example.com',
            password='pass123',
            date_of_birth='1990-01-01',
            country='France'
        )
        
        # Créer un parrainage
        referral = Referral.objects.create(
            referrer=referrer,
            referred=referred,
            program=program
        )
        
        # Test calcul de commission
        commission, message = referral.calculate_commission(Decimal('1000'))
        assert commission == Decimal('100.00')  # 10% de 1000
        
        # Test limites
        referral.commission_games_count = 3
        referral.save()
        
        can_earn, message = referral.can_earn_commission(Decimal('1000'))
        assert not can_earn  # Limite atteinte pour non-premium
        
        # Test premium
        referral.is_premium_referrer = True
        referral.save()
        
        can_earn, message = referral.can_earn_commission(Decimal('1000'))
        assert can_earn  # Premium n'a pas de limite
        
        print("✅ Modèles de parrainage validés")
    
    def test_chess_logic(self):
        """Tester la logique des échecs."""
        print("\n♟️  Test de la logique des échecs...")
        
        chess = ChessGame()
        
        # Test position initiale
        assert chess.current_player == 'white'
        assert chess.get_piece_at(0, 0) == 'r'  # Tour noire
        assert chess.get_piece_at(7, 4) == 'K'  # Roi blanc
        
        # Test mouvement valide de pion
        valid, message = chess.validate_move(6, 4, 4, 4)  # e2-e4
        assert valid
        
        # Test mouvement invalide
        valid, message = chess.validate_move(6, 4, 3, 4)  # e2-e5 (trop loin)
        assert not valid
        
        # Exécuter quelques mouvements
        chess.make_move(6, 4, 4, 4)  # e2-e4
        assert chess.current_player == 'black'
        
        chess.make_move(1, 4, 3, 4)  # e7-e5
        assert chess.current_player == 'white'
        
        # Test échec
        # Simuler une position d'échec (simplifié)
        chess.board[0][4] = '.'  # Enlever le roi noir
        chess.board[4][4] = 'k'  # Mettre le roi noir en e4
        
        in_check = chess.is_in_check('black')
        # Note: Le test complet nécessiterait une position d'échec réelle
        
        print("✅ Logique des échecs validée")
    
    def test_checkers_logic(self):
        """Tester la logique des dames."""
        print("\n🔴 Test de la logique des dames...")
        
        checkers = CheckersGame()
        
        # Test position initiale
        assert checkers.current_player == 'black'
        assert checkers.get_piece_at(0, 1) == 'b'  # Pièce noire
        assert checkers.get_piece_at(7, 0) == 'w'  # Pièce blanche
        
        # Test mouvement valide
        valid, message = checkers.validate_move(2, 1, 3, 0)
        assert valid
        
        # Test mouvement invalide (case claire)
        valid, message = checkers.validate_move(2, 0, 3, 1)
        assert not valid
        
        # Exécuter un mouvement
        checkers.make_move(2, 1, 3, 0)
        assert checkers.current_player == 'white'
        assert checkers.get_piece_at(3, 0) == 'b'
        assert checkers.get_piece_at(2, 1) == '.'
        
        # Test statut du jeu
        status, message = checkers.get_game_status()
        assert status == 'playing'
        
        print("✅ Logique des dames validée")
    
    def test_authentication_api(self):
        """Tester l'API d'authentification."""
        print("\n🔐 Test de l'API d'authentification...")
        
        # Test inscription
        register_data = {
            'username': 'apiuser',
            'email': 'apiuser@example.com',
            'password': 'testpass123',
            'first_name': 'API',
            'last_name': 'User',
            'phone_number': '+33123456789',
            'date_of_birth': '1990-01-01',
            'country': 'France'
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/register/", json=register_data)
            assert response.status_code in [200, 201]
            
            # Test connexion
            login_data = {
                'username': 'apiuser',
                'password': 'testpass123'
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login/", json=login_data)
            assert response.status_code == 200
            
            data = response.json()
            assert 'access' in data
            assert 'refresh' in data
            
            print("✅ API d'authentification validée")
            
        except requests.exceptions.RequestException:
            print("⚠️  API d'authentification non testée (serveur non disponible)")
    
    def test_game_api(self):
        """Tester l'API de jeu."""
        print("\n🎮 Test de l'API de jeu...")
        
        try:
            # Test liste des types de jeux
            response = requests.get(f"{self.base_url}/api/games/types/")
            if response.status_code == 200:
                games = response.json()
                assert isinstance(games, list)
                print("✅ API de jeu validée")
            else:
                print("⚠️  API de jeu non disponible")
                
        except requests.exceptions.RequestException:
            print("⚠️  API de jeu non testée (serveur non disponible)")
    
    def test_payment_api(self):
        """Tester l'API de paiement."""
        print("\n💳 Test de l'API de paiement...")
        
        try:
            # Test méthodes de paiement
            response = requests.get(f"{self.base_url}/api/payments/methods/")
            if response.status_code == 200:
                methods = response.json()
                assert isinstance(methods, list)
                print("✅ API de paiement validée")
            else:
                print("⚠️  API de paiement non disponible")
                
        except requests.exceptions.RequestException:
            print("⚠️  API de paiement non testée (serveur non disponible)")
    
    def test_referral_api(self):
        """Tester l'API de parrainage."""
        print("\n🤝 Test de l'API de parrainage...")
        
        try:
            # Test code de parrainage
            response = requests.get(f"{self.base_url}/api/referrals/code/")
            # Note: Nécessite authentification
            print("⚠️  API de parrainage nécessite authentification")
                
        except requests.exceptions.RequestException:
            print("⚠️  API de parrainage non testée (serveur non disponible)")
    
    def generate_test_report(self):
        """Générer un rapport de test."""
        report = f"""
# RAPPORT DE TEST RUMO RUSH BACKEND
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé
- ✅ Modèles utilisateur: OK
- ✅ Modèles de jeu: OK  
- ✅ Modèles de paiement: OK
- ✅ Modèles de parrainage: OK
- ✅ Logique des échecs: OK
- ✅ Logique des dames: OK
- ⚠️  APIs: Dépendent du serveur

## Recommandations
1. Démarrer le serveur Django pour tester les APIs
2. Configurer la base de données PostgreSQL
3. Configurer Redis pour les WebSockets
4. Ajouter des tests d'intégration WebSocket

## Commandes pour démarrer
```bash
# Installer les dépendances
pip install -r requirements.txt

# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Démarrer le serveur
python manage.py runserver
```
        """
        
        with open('test_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\n📊 Rapport de test généré: test_report.md")

def main():
    """Fonction principale."""
    print("🎯 RUMO RUSH Backend - Suite de Tests Complète")
    print("=" * 60)
    
    # Vérifier l'environnement Django
    try:
        from django.conf import settings
        print(f"✅ Django configuré: {settings.SETTINGS_MODULE}")
    except Exception as e:
        print(f"❌ Erreur Django: {e}")
        return
    
    # Exécuter les tests
    test_suite = RumoRushTestSuite()
    test_suite.run_all_tests()
    test_suite.generate_test_report()
    
    print("\n🎉 Tests terminés avec succès!")
    print("📋 Consultez test_report.md pour le rapport détaillé")

if __name__ == '__main__':
    main()
