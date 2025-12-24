"""
Service de gestion des commissions de parrainage RUMO RUSH

Règles implémentées:
- Parrain Premium (10,000 FCFA/mois): 10% commission ILLIMITÉE
- Parrain Non-Premium: 10% commission sur 3 PREMIÈRES parties gagnantes SEULEMENT
- Joueurs sans parrain: Aucune commission générée
"""

from decimal import Decimal
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
import logging

from apps.referrals.models import Referral, ReferralCommission
from apps.games.models import Game

logger = logging.getLogger(__name__)


class ReferralCommissionService:
    """Service pour gérer les commissions de parrainage."""
    
    @staticmethod
    def process_game_referral_commission(game, winner_user, game_bet_amount, is_win=True):
        """
        Traiter la commission de parrainage après une partie.
        
        FORMULE: Parrain reçoit 10% de la commission plateforme (14%)
        = game_bet_amount × 14% × 10% = game_bet_amount × 1.4%
        
        Args:
            game (Game): L'objet du jeu
            winner_user (User): L'utilisateur qui a gagné
            game_bet_amount (Decimal): La MISE originale du filleul (pas les gains)
            is_win (bool): True si c'est une victoire, False si défaite/match nul
            
        Returns:
            dict: Résultat du traitement
        """
        try:
            # Les commissions ne s'appliquent qu'aux VICTOIRES
            if not is_win:
                return {
                    'status': 'no_commission',
                    'reason': 'Commission uniquement sur victoires',
                    'commission': Decimal('0.00')
                }
            
            # Chercher le parrainage du gagnant
            referral = Referral.objects.filter(
                referred=winner_user,
                status='active'
            ).select_related('referrer', 'program').first()
            
            # Pas de parrain = pas de commission
            if not referral:
                return {
                    'status': 'no_referral',
                    'reason': 'Joueur sans parrain',
                    'commission': Decimal('0.00')
                }
            
            # Vérifier si le parrainage peut générer une commission
            can_earn, message = referral.can_earn_commission(game_won=True)
            
            if not can_earn:
                return {
                    'status': 'commission_blocked',
                    'reason': str(message),
                    'commission': Decimal('0.00'),
                    'premium_status': referral.get_premium_status_display()
                }
            
            # Calculer la commission: 10% de la commission plateforme (14%)
            # = game_bet_amount × 1.4%
            commission_amount, calc_message = referral.calculate_commission(
                game_bet_amount=game_bet_amount,
                game_won=True,
                game_currency='FCFA'
            )
            
            if commission_amount <= 0:
                return {
                    'status': 'commission_calculated_zero',
                    'reason': str(calc_message),
                    'commission': Decimal('0.00')
                }
            
            # Créer la transaction de commission (atomique)
            with transaction.atomic():
                # Créer l'enregistrement de commission
                commission = referral.add_commission(
                    game=game,
                    amount=commission_amount,
                    currency='FCFA'
                )
                
                # Mettre à jour les statistiques du parrainage
                referral.update_stats(
                    game_won=True,
                    commission_amount=commission_amount
                )
                
                # Traiter la commission (ajouter au portefeuille du parrain)
                commission.process_commission()
                
                logger.info(
                    f"✅ Commission traitée: "
                    f"Parrain={referral.referrer.username}, "
                    f"Filleul={winner_user.username}, "
                    f"Montant={commission_amount} FCFA, "
                    f"Premium={referral.is_premium_referrer}"
                )
            
            return {
                'status': 'success',
                'commission': float(commission_amount),
                'referrer_username': referral.referrer.username,
                'premium_status': referral.get_premium_status_display(),
                'winning_games_count': referral.winning_games_count,
                'total_earned': float(referral.total_commission_earned)
            }
            
        except Exception as e:
            logger.error(
                f"❌ Erreur traitement commission: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'reason': str(e),
                'commission': Decimal('0.00')
            }
    
    @staticmethod
    def get_referral_summary(user):
        """
        Obtenir un résumé du statut de parrainage d'un utilisateur.
        
        Args:
            user (User): L'utilisateur
            
        Returns:
            dict: Résumé du parrainage
        """
        # Vérifier si l'utilisateur a un parrain
        referral = Referral.objects.filter(
            referred=user,
            status='active'
        ).select_related('referrer').first()
        
        if not referral:
            return {
                'has_referrer': False,
                'referrer_username': None,
                'premium_status': None,
                'remaining_free_games': None,
                'message': 'Aucun parrain détecté. Vous pouvez en ajouter un lors de votre inscription.'
            }
        
        premium = referral.is_premium_referrer
        remaining = max(0, 3 - referral.winning_games_count) if not premium else None
        
        return {
            'has_referrer': True,
            'referrer_username': referral.referrer.username,
            'referrer_id': referral.referrer.id,
            'premium_status': referral.get_premium_status_display(),
            'is_premium': premium,
            'winning_games_so_far': referral.winning_games_count,
            'remaining_free_games': remaining,
            'total_commission_earned': float(referral.total_commission_earned),
            'message': (
                f"Parrain: {referral.referrer.username} "
                f"({referral.get_premium_status_display()})"
            )
        }
    
    @staticmethod
    def get_referrer_dashboard(referrer_user):
        """
        Obtenir le dashboard complet d'un parrain.
        
        Args:
            referrer_user (User): L'utilisateur parrain
            
        Returns:
            dict: Résumé des filleuls et commissions
        """
        referrals = Referral.objects.filter(
            referrer=referrer_user,
            status='active'
        ).select_related('referred', 'program')
        
        total_commission = sum(
            ref.total_commission_earned for ref in referrals
        )
        
        premium_count = referrals.filter(is_premium_referrer=True).count()
        non_premium_count = referrals.filter(is_premium_referrer=False).count()
        
        referrals_list = []
        for ref in referrals[:10]:  # Top 10
            referrals_list.append({
                'referred_username': ref.referred.username,
                'referred_id': ref.referred.id,
                'commission_earned': float(ref.total_commission_earned),
                'winning_games': ref.winning_games_count,
                'status': ref.get_premium_status_display(),
            })
        
        return {
            'total_referrals': referrals.count(),
            'premium_referrals': premium_count,
            'non_premium_referrals': non_premium_count,
            'total_commission_earned': float(total_commission),
            'top_referrals': referrals_list,
            'commission_rate': 10.0  # Fixe à 10%
        }
