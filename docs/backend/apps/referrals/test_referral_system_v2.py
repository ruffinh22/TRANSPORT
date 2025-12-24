"""
Tests pour le système de parrainage RUMO RUSH - VERSION 2 CORRIGÉE

FORMULE CORRECTE:
- Commission Parrain = Mise × 14% (plateforme) × 10% (parrain) = Mise × 1.4%
- Parrain Premium: Illimité
- Parrain Non-Premium: 3 premières parties gagnantes SEULEMENT
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.referrals.models import ReferralProgram, Referral
from apps.referrals.services import ReferralCommissionService

User = get_user_model()


class ReferralSystemV2TestCase(TestCase):
    """Tests du système de parrainage VERSION 2 avec formule corrigée."""
    
    def setUp(self):
        """Préparation des données de test."""
        # Créer le programme de parrainage par défaut
        self.program = ReferralProgram.objects.create(
            name='Programme Test V2',
            description='Programme de test version 2',
            commission_type='percentage',
            commission_rate=Decimal('10.00'),  # 10% de la commission plateforme
            fixed_commission=Decimal('0.00'),
            max_commission_per_referral=Decimal('0.00'),
            max_daily_commission=Decimal('0.00'),
            max_monthly_commission=Decimal('0.00'),
            min_bet_for_commission=Decimal('100.00'),
            free_games_limit=3,
            status='active',
            is_default=True
        )
        
        # Créer les utilisateurs
        self.referrer_premium = User.objects.create_user(
            username='parrain_premium',
            email='premium@test.com',
            password='test123'
        )
        
        self.referrer_free = User.objects.create_user(
            username='parrain_gratuit',
            email='free@test.com',
            password='test123'
        )
        
        self.filleul_premium = User.objects.create_user(
            username='filleul_premium',
            email='filleul_premium@test.com',
            password='test123'
        )
        
        self.filleul_free = User.objects.create_user(
            username='filleul_gratuit',
            email='filleul_free@test.com',
            password='test123'
        )
        
        self.filleul_no_referrer = User.objects.create_user(
            username='sans_parrain',
            email='sans_parrain@test.com',
            password='test123'
        )
        
        # Créer les relations de parrainage
        self.referral_premium = Referral.objects.create(
            referrer=self.referrer_premium,
            referred=self.filleul_premium,
            program=self.program,
            is_premium_referrer=True
        )
        
        self.referral_free = Referral.objects.create(
            referrer=self.referrer_free,
            referred=self.filleul_free,
            program=self.program,
            is_premium_referrer=False
        )
    
    # ====== TESTS POUR PARRAIN PREMIUM ======
    
    def test_premium_commission_formula(self):
        """
        Test: Formule de commission Parrain Premium
        Commission = Mise × 14% × 10% = Mise × 1.4%
        """
        # Mise de 10,000 FCFA
        game_bet_amount = Decimal('10000.00')
        expected_commission = Decimal('140.00')  # 10000 × 1.4%
        
        # Calculer la commission
        commission, msg = self.referral_premium.calculate_commission(
            game_bet_amount=game_bet_amount,
            game_won=True
        )
        
        self.assertEqual(
            commission, 
            expected_commission,
            f"Commission devrait être {expected_commission} FCFA (10% de 14% de 10000)"
        )
    
    def test_premium_commission_various_amounts(self):
        """
        Test: Commission pour diverses mises
        """
        test_cases = [
            (Decimal('1000.00'), Decimal('14.00')),      # 1000 × 1.4%
            (Decimal('5000.00'), Decimal('70.00')),      # 5000 × 1.4%
            (Decimal('10000.00'), Decimal('140.00')),    # 10000 × 1.4%
            (Decimal('50000.00'), Decimal('700.00')),    # 50000 × 1.4%
            (Decimal('100000.00'), Decimal('1400.00')),  # 100000 × 1.4%
        ]
        
        for game_bet, expected_commission in test_cases:
            commission, msg = self.referral_premium.calculate_commission(
                game_bet_amount=game_bet,
                game_won=True
            )
            
            self.assertEqual(
                commission,
                expected_commission,
                f"Mise {game_bet} devrait générer {expected_commission} FCFA"
            )
    
    def test_premium_commission_unlimited(self):
        """Test: Parrain PREMIUM reçoit commission ILLIMITÉE."""
        # Vérifier que 10 victoires consécutives génèrent toutes une commission
        for i in range(10):
            can_earn, msg = self.referral_premium.can_earn_commission(game_won=True)
            self.assertTrue(can_earn, f"Victoire {i+1} devrait générer commission")
            
            commission, msg = self.referral_premium.calculate_commission(
                game_bet_amount=Decimal('10000.00'),
                game_won=True
            )
            self.assertEqual(commission, Decimal('140.00'), f"Commission devrait être 140 FCFA (victoire {i+1})")
            
            # Simuler une mise à jour
            self.referral_premium.update_stats(game_won=True, commission_amount=commission)
        
        # Vérifier que toutes les 10 victoires ont généré une commission
        self.assertEqual(self.referral_premium.winning_games_count, 10)
        # Vérifier le total gagné
        self.assertEqual(self.referral_premium.total_commission_earned, Decimal('1400.00'))
    
    def test_premium_status_display(self):
        """Test: Affichage du statut premium."""
        status = self.referral_premium.get_premium_status_display()
        self.assertIn('Premium', status)
        self.assertIn('10% illimité', status)
    
    # ====== TESTS POUR PARRAIN NON-PREMIUM ======
    
    def test_free_commission_formula(self):
        """
        Test: Formule de commission Parrain Non-Premium
        Commission = Mise × 14% × 10% = Mise × 1.4%
        (Limité à 3 premières parties gagnantes)
        """
        game_bet_amount = Decimal('10000.00')
        expected_commission = Decimal('140.00')  # 10000 × 1.4%
        
        commission, msg = self.referral_free.calculate_commission(
            game_bet_amount=game_bet_amount,
            game_won=True
        )
        
        self.assertEqual(
            commission,
            expected_commission,
            f"Commission devrait être {expected_commission} FCFA pour non-premium aussi"
        )
    
    def test_free_commission_limit_3_games(self):
        """Test: Parrain NON-PREMIUM reçoit commission sur 3 victoires SEULEMENT."""
        # 1ère victoire: ✅ Commission
        can_earn, msg = self.referral_free.can_earn_commission(game_won=True)
        self.assertTrue(can_earn, "1ère victoire devrait générer commission")
        
        commission, msg = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('10000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('140.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=commission)
        
        # 2ème victoire: ✅ Commission
        can_earn, msg = self.referral_free.can_earn_commission(game_won=True)
        self.assertTrue(can_earn, "2ème victoire devrait générer commission")
        
        commission, msg = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('10000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('140.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=commission)
        
        # 3ème victoire: ✅ Commission
        can_earn, msg = self.referral_free.can_earn_commission(game_won=True)
        self.assertTrue(can_earn, "3ème victoire devrait générer commission")
        
        commission, msg = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('10000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('140.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=commission)
        
        # 4ème victoire: ❌ PAS de commission
        can_earn, msg = self.referral_free.can_earn_commission(game_won=True)
        self.assertFalse(can_earn, "4ème victoire ne devrait PAS générer commission")
        
        commission, msg = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('10000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('0.00'), "Pas de commission après 3 victoires")
        
        # Vérifier le total
        self.assertEqual(self.referral_free.winning_games_count, 3)
        self.assertEqual(self.referral_free.total_commission_earned, Decimal('420.00'))
    
    def test_free_status_display(self):
        """Test: Affichage du statut non-premium."""
        # Avant toute victoire: 3 restantes
        status = self.referral_free.get_premium_status_display()
        self.assertIn('Non-premium', status)
        self.assertIn('3 parties gagnantes restantes', status)
        
        # Après 1 victoire: 2 restantes
        self.referral_free.update_stats(game_won=True, commission_amount=Decimal('140.00'))
        status = self.referral_free.get_premium_status_display()
        self.assertIn('2 parties gagnantes restantes', status)
        
        # Après 3 victoires: 0 restantes
        self.referral_free.update_stats(game_won=True, commission_amount=Decimal('140.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=Decimal('140.00'))
        status = self.referral_free.get_premium_status_display()
        self.assertIn('0 parties gagnantes restantes', status)
    
    # ====== TESTS GÉNÉRAUX ======
    
    def test_no_commission_without_win(self):
        """Test: Pas de commission si pas de victoire."""
        can_earn, msg = self.referral_premium.can_earn_commission(game_won=False)
        self.assertFalse(can_earn, "Pas de commission sans victoire")
        
        commission, msg = self.referral_premium.calculate_commission(
            game_bet_amount=Decimal('10000.00'),
            game_won=False
        )
        self.assertEqual(commission, Decimal('0.00'))
    
    def test_no_referral_no_commission(self):
        """Test: Aucune commission pour joueur sans parrain."""
        # Le filleul sans parrain ne peut pas générer de commission
        referral = Referral.objects.filter(referred=self.filleul_no_referrer).first()
        self.assertIsNone(referral, "Aucun parrain pour ce filleul")
    
    def test_inactive_referral_no_commission(self):
        """Test: Parrainage inactif n'engendre pas de commission."""
        self.referral_premium.status = 'inactive'
        self.referral_premium.save()
        
        can_earn, msg = self.referral_premium.can_earn_commission(game_won=True)
        self.assertFalse(can_earn, "Parrainage inactif ne peut pas générer commission")
    
    def test_inactive_program_no_commission(self):
        """Test: Programme inactif n'engendre pas de commission."""
        self.program.status = 'inactive'
        self.program.save()
        
        can_earn, msg = self.referral_premium.can_earn_commission(game_won=True)
        self.assertFalse(can_earn, "Programme inactif ne peut pas générer commission")
    
    # ====== TESTS AVEC SERVICE ======
    
    def test_service_premium_commission(self):
        """Test: Service traite correctement commission premium."""
        # Créer un mock game (dans un vrai test, ce serait un objet Game)
        # Pour ce test, on suppose que le game existe
        # game = Game.objects.create(...)
        # result = ReferralCommissionService.process_game_referral_commission(
        #     game=game,
        #     winner_user=self.filleul_premium,
        #     game_bet_amount=Decimal('10000.00'),
        #     is_win=True
        # )
        # self.assertEqual(result['status'], 'success')
        # self.assertEqual(result['commission'], 140.00)
        pass  # À activer quand Game model est disponible
    
    # ====== TESTS DE SCÉNARIOS RÉALISTES ======
    
    def test_scenario_premium_50_victories(self):
        """Scénario: Parrain Premium avec 50 victoires."""
        total_expected = Decimal('7000.00')  # 50 × 140
        
        for i in range(50):
            can_earn, msg = self.referral_premium.can_earn_commission(game_won=True)
            self.assertTrue(can_earn)
            
            commission, msg = self.referral_premium.calculate_commission(
                game_bet_amount=Decimal('10000.00'),
                game_won=True
            )
            self.referral_premium.update_stats(game_won=True, commission_amount=commission)
        
        self.assertEqual(self.referral_premium.winning_games_count, 50)
        self.assertEqual(self.referral_premium.total_commission_earned, total_expected)
    
    def test_scenario_free_progressive(self):
        """Scénario: Parrain Non-Premium avec mises progressives."""
        # Victoire 1: 5,000 mise → 70 FCFA
        commission, _ = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('5000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('70.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=commission)
        
        # Victoire 2: 10,000 mise → 140 FCFA
        commission, _ = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('10000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('140.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=commission)
        
        # Victoire 3: 20,000 mise → 280 FCFA
        commission, _ = self.referral_free.calculate_commission(
            game_bet_amount=Decimal('20000.00'),
            game_won=True
        )
        self.assertEqual(commission, Decimal('280.00'))
        self.referral_free.update_stats(game_won=True, commission_amount=commission)
        
        # Vérifier le total
        expected_total = Decimal('70.00') + Decimal('140.00') + Decimal('280.00')
        self.assertEqual(self.referral_free.total_commission_earned, expected_total)
        self.assertEqual(self.referral_free.winning_games_count, 3)
