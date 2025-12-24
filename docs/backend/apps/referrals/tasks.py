# apps/referrals/tasks.py
# ==========================

import logging
from datetime import timedelta, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg, F
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import (
    ReferralProgram, Referral, ReferralCommission, 
    PremiumSubscription, ReferralStatistics, ReferralBonus
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ===== TÂCHES DE CALCUL DES COMMISSIONS =====

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_pending_commissions(self):
    """
    Calculer et traiter toutes les commissions de parrainage en attente.
    Exécuté toutes les heures.
    """
    try:
        processed_count = 0
        failed_count = 0
        total_amount = Decimal('0.00')
        
        # Récupérer toutes les commissions en attente
        pending_commissions = ReferralCommission.objects.filter(
            status='pending'
        ).select_related('referral', 'referral__referrer', 'game')
        
        logger.info(f"Traitement de {pending_commissions.count()} commissions en attente")
        
        for commission in pending_commissions:
            try:
                # Vérifier si la commission peut encore être traitée
                can_earn, message = commission.referral.can_earn_commission(
                    commission.game.bet_amount
                )
                
                if not can_earn:
                    commission.status = 'cancelled'
                    commission.failure_reason = str(message)
                    commission.save()
                    failed_count += 1
                    continue
                
                # Traiter la commission
                with transaction.atomic():
                    commission.process_commission()
                    processed_count += 1
                    total_amount += commission.amount
                    
                    # Notification au parrain
                    send_commission_notification.delay(commission.id)
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement de la commission {commission.id}: {e}")
                failed_count += 1
                
                # Marquer comme échouée après plusieurs tentatives
                commission.status = 'failed'
                commission.failure_reason = str(e)
                commission.save()
        
        # Mettre à jour les statistiques
        update_daily_statistics.delay()
        
        logger.info(
            f"Traitement des commissions terminé: {processed_count} réussies, "
            f"{failed_count} échouées, montant total: {total_amount} FCFA"
        )
        
        return {
            'processed': processed_count,
            'failed': failed_count,
            'total_amount': float(total_amount)
        }
        
    except Exception as exc:
        logger.error(f"Erreur dans calculate_pending_commissions: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def process_single_commission(self, commission_id: str, game_id: str, referral_id: str):
    """
    Traiter une commission de parrainage spécifique.
    Appelé automatiquement après chaque partie terminée.
    """
    try:
        from apps.games.models import Game
        
        # Récupérer les objets nécessaires
        game = Game.objects.get(id=game_id)
        referral = Referral.objects.select_related('program', 'referrer').get(id=referral_id)
        
        # Vérifier si le jeu génère une commission
        if game.player != referral.referred or game.status != 'completed':
            return {'status': 'skipped', 'reason': 'Game not eligible for commission'}
        
        # Calculer la commission
        commission_amount, message = referral.calculate_commission(
            game.bet_amount, 
            game.currency
        )
        
        if commission_amount <= 0:
            return {'status': 'no_commission', 'reason': str(message)}
        
        # Créer la commission
        commission = referral.add_commission(
            game=game,
            amount=commission_amount,
            currency=game.currency
        )
        
        logger.info(
            f"Commission créée: {commission_amount} {game.currency} "
            f"pour le parrain {referral.referrer.username}"
        )
        
        # Planifier le traitement de la commission
        calculate_pending_commissions.apply_async(countdown=10)
        
        return {
            'status': 'created',
            'commission_id': str(commission.id),
            'amount': float(commission_amount)
        }
        
    except Exception as exc:
        logger.error(f"Erreur dans process_single_commission: {exc}")
        raise self.retry(exc=exc)


# ===== GESTION DES ABONNEMENTS PREMIUM =====

@shared_task(bind=True, max_retries=2)
def check_premium_subscriptions(self):
    """
    Vérifier et mettre à jour le statut des abonnements premium.
    Exécuté quotidiennement à 6h.
    """
    try:
        expired_count = 0
        renewed_count = 0
        expiring_soon_count = 0
        
        # Marquer les abonnements expirés
        expired_subscriptions = PremiumSubscription.objects.filter(
            status='active',
            end_date__lt=timezone.now(),
            plan_type__in=['monthly', 'quarterly', 'yearly']
        )
        
        for subscription in expired_subscriptions:
            if subscription.auto_renewal:
                # Tenter le renouvellement automatique
                renewed = attempt_auto_renewal.delay(subscription.id)
                if renewed:
                    renewed_count += 1
                else:
                    subscription.status = 'expired'
                    subscription.save()
                    expired_count += 1
            else:
                subscription.status = 'expired'
                subscription.save()
                expired_count += 1
        
        # Notifier les abonnements qui expirent bientôt (7 jours)
        expiring_soon = PremiumSubscription.objects.filter(
            status='active',
            end_date__lte=timezone.now() + timedelta(days=7),
            end_date__gt=timezone.now()
        )
        
        for subscription in expiring_soon:
            send_subscription_expiry_notification.delay(subscription.id)
            expiring_soon_count += 1
        
        logger.info(
            f"Vérification premium terminée: {expired_count} expirés, "
            f"{renewed_count} renouvelés, {expiring_soon_count} expirent bientôt"
        )
        
        return {
            'expired': expired_count,
            'renewed': renewed_count,
            'expiring_soon': expiring_soon_count
        }
        
    except Exception as exc:
        logger.error(f"Erreur dans check_premium_subscriptions: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def attempt_auto_renewal(self, subscription_id: str):
    """
    Tenter le renouvellement automatique d'un abonnement premium.
    """
    try:
        subscription = PremiumSubscription.objects.get(id=subscription_id)
        
        if not subscription.auto_renewal:
            return False
        
        # TODO: Intégrer avec le système de paiement
        # Pour l'instant, simuler un renouvellement réussi
        
        # Créer un nouvel abonnement
        new_subscription = subscription.renew()
        
        if new_subscription:
            # Notification de renouvellement
            send_subscription_renewal_notification.delay(new_subscription.id)
            logger.info(f"Abonnement renouvelé automatiquement: {subscription.user.username}")
            return True
        
        return False
        
    except Exception as exc:
        logger.error(f"Erreur dans attempt_auto_renewal: {exc}")
        return False


# ===== CALCUL DES STATISTIQUES =====

@shared_task(bind=True, max_retries=2)
def update_referral_statistics(self):
    """
    Calculer et mettre à jour les statistiques de parrainage.
    Exécuté quotidiennement à 1h.
    """
    try:
        updated_stats = {
            'daily': 0,
            'weekly': 0,
            'monthly': 0,
            'yearly': 0
        }
        
        # Récupérer tous les utilisateurs ayant des parrainages
        users_with_referrals = User.objects.filter(
            referrals_made__isnull=False
        ).distinct()
        
        today = timezone.now().date()
        
        for user in users_with_referrals:
            # Statistiques quotidiennes
            daily_stats = ReferralStatistics.calculate_statistics(
                user=user,
                period_type='daily',
                start_date=today,
                end_date=today
            )
            updated_stats['daily'] += 1
            
            # Statistiques hebdomadaires (lundi de la semaine)
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            weekly_stats = ReferralStatistics.calculate_statistics(
                user=user,
                period_type='weekly',
                start_date=week_start,
                end_date=week_end
            )
            updated_stats['weekly'] += 1
            
            # Statistiques mensuelles (premier du mois)
            if today.day == 1 or today.day <= 7:  # Calculer en début de mois
                month_start = today.replace(day=1)
                next_month = month_start + timedelta(days=32)
                month_end = next_month.replace(day=1) - timedelta(days=1)
                
                monthly_stats = ReferralStatistics.calculate_statistics(
                    user=user,
                    period_type='monthly',
                    start_date=month_start,
                    end_date=month_end
                )
                updated_stats['monthly'] += 1
            
            # Statistiques annuelles (premier de l'année)
            if today.month == 1 and today.day <= 7:
                year_start = today.replace(month=1, day=1)
                year_end = today.replace(month=12, day=31)
                
                yearly_stats = ReferralStatistics.calculate_statistics(
                    user=user,
                    period_type='yearly',
                    start_date=year_start,
                    end_date=year_end
                )
                updated_stats['yearly'] += 1
        
        logger.info(f"Statistiques mises à jour: {updated_stats}")
        return updated_stats
        
    except Exception as exc:
        logger.error(f"Erreur dans update_referral_statistics: {exc}")
        raise self.retry(exc=exc)


@shared_task
def update_daily_statistics():
    """
    Mettre à jour les statistiques quotidiennes uniquement.
    Appelé après traitement des commissions.
    """
    try:
        today = timezone.now().date()
        users_updated = 0
        
        # Utilisateurs avec de l'activité aujourd'hui
        active_users = User.objects.filter(
            Q(referrals_made__commissions__created_at__date=today) |
            Q(referrals_made__created_at__date=today)
        ).distinct()
        
        for user in active_users:
            ReferralStatistics.calculate_statistics(
                user=user,
                period_type='daily',
                start_date=today,
                end_date=today
            )
            users_updated += 1
        
        logger.info(f"Statistiques quotidiennes mises à jour pour {users_updated} utilisateurs")
        return users_updated
        
    except Exception as e:
        logger.error(f"Erreur dans update_daily_statistics: {e}")
        return 0


# ===== GESTION DES BONUS =====

@shared_task(bind=True, max_retries=2)
def cleanup_expired_bonuses(self):
    """
    Nettoyer les bonus expirés et marquer comme périmés.
    Exécuté quotidiennement à 2h.
    """
    try:
        expired_bonuses = ReferralBonus.objects.filter(
            status__in=['pending', 'approved'],
            expires_at__lt=timezone.now()
        )
        
        expired_count = expired_bonuses.count()
        expired_bonuses.update(status='expired')
        
        logger.info(f"Nettoyage terminé: {expired_count} bonus marqués comme expirés")
        return expired_count
        
    except Exception as exc:
        logger.error(f"Erreur dans cleanup_expired_bonuses: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def create_milestone_bonuses(self):
    """
    Créer des bonus pour les parrains ayant atteint certains paliers.
    Exécuté quotidiennement.
    """
    try:
        bonuses_created = 0
        
        # Paliers prédéfinis
        milestones = [
            (5, Decimal('2000'), 'Premier palier - 5 filleuls'),
            (10, Decimal('5000'), 'Palier argent - 10 filleuls'),
            (25, Decimal('12000'), 'Palier or - 25 filleuls'),
            (50, Decimal('25000'), 'Palier platine - 50 filleuls'),
            (100, Decimal('50000'), 'Palier diamant - 100 filleuls')
        ]
        
        for target_count, bonus_amount, description in milestones:
            # Trouver les parrains ayant atteint ce palier
            eligible_referrers = User.objects.annotate(
                active_referral_count=Count(
                    'referrals_made',
                    filter=Q(referrals_made__status='active')
                )
            ).filter(
                active_referral_count=target_count
            )
            
            for referrer in eligible_referrers:
                # Vérifier si le bonus n'a pas déjà été créé
                existing_bonus = ReferralBonus.objects.filter(
                    referral__referrer=referrer,
                    bonus_type='milestone',
                    amount=bonus_amount
                ).first()
                
                if not existing_bonus:
                    # Prendre le premier parrainage actif pour associer le bonus
                    referral = referrer.referrals_made.filter(status='active').first()
                    
                    if referral:
                        bonus = ReferralBonus.objects.create(
                            referral=referral,
                            bonus_type='milestone',
                            amount=bonus_amount,
                            currency='FCFA',
                            description=description,
                            status='approved',
                            expires_at=timezone.now() + timedelta(days=30)
                        )
                        
                        # Notification du nouveau bonus
                        send_bonus_notification.delay(bonus.id)
                        bonuses_created += 1
        
        logger.info(f"Bonus de paliers créés: {bonuses_created}")
        return bonuses_created
        
    except Exception as exc:
        logger.error(f"Erreur dans create_milestone_bonuses: {exc}")
        raise self.retry(exc=exc)


# ===== NOTIFICATIONS =====

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_commission_notification(self, commission_id: str):
    """
    Envoyer une notification de commission gagnée.
    """
    try:
        commission = ReferralCommission.objects.select_related(
            'referral__referrer', 'referral__referred', 'game'
        ).get(id=commission_id)
        
        referrer = commission.referral.referrer
        
        # Email notification
        subject = f"Commission de {commission.amount} {commission.currency} reçue!"
        
        context = {
            'referrer': referrer,
            'commission': commission,
            'referred_user': commission.referral.referred,
            'game': commission.game,
        }
        
        html_content = render_to_string(
            'referrals/emails/commission_earned.html',
            context
        )
        
        send_mail(
            subject=subject,
            message='',  # Version texte
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[referrer.email],
            fail_silently=False
        )
        
        # TODO: Notification push mobile
        # TODO: Notification WebSocket en temps réel
        
        logger.info(f"Notification de commission envoyée à {referrer.username}")
        return True
        
    except Exception as exc:
        logger.error(f"Erreur dans send_commission_notification: {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_subscription_expiry_notification(subscription_id: str):
    """
    Notifier l'expiration prochaine d'un abonnement premium.
    """
    try:
        subscription = PremiumSubscription.objects.select_related('user').get(
            id=subscription_id
        )
        
        days_remaining = (subscription.end_date.date() - timezone.now().date()).days
        
        subject = f"Votre abonnement premium expire dans {days_remaining} jour(s)"
        
        context = {
            'user': subscription.user,
            'subscription': subscription,
            'days_remaining': days_remaining,
        }
        
        html_content = render_to_string(
            'referrals/emails/subscription_expiring.html',
            context
        )
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            fail_silently=False
        )
        
        logger.info(f"Notification d'expiration envoyée à {subscription.user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans send_subscription_expiry_notification: {e}")
        return False


@shared_task
def send_subscription_renewal_notification(subscription_id: str):
    """
    Notifier le renouvellement automatique d'un abonnement premium.
    """
    try:
        subscription = PremiumSubscription.objects.select_related('user').get(
            id=subscription_id
        )
        
        subject = "Votre abonnement premium a été renouvelé automatiquement"
        
        context = {
            'user': subscription.user,
            'subscription': subscription,
        }
        
        html_content = render_to_string(
            'referrals/emails/subscription_renewed.html',
            context
        )
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            fail_silently=False
        )
        
        logger.info(f"Notification de renouvellement envoyée à {subscription.user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans send_subscription_renewal_notification: {e}")
        return False


@shared_task
def send_bonus_notification(bonus_id: str):
    """
    Notifier la disponibilité d'un nouveau bonus.
    """
    try:
        bonus = ReferralBonus.objects.select_related(
            'referral__referrer'
        ).get(id=bonus_id)
        
        referrer = bonus.referral.referrer
        
        subject = f"Nouveau bonus de {bonus.amount} {bonus.currency} disponible!"
        
        context = {
            'user': referrer,
            'bonus': bonus,
        }
        
        html_content = render_to_string(
            'referrals/emails/bonus_available.html',
            context
        )
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[referrer.email],
            fail_silently=False
        )
        
        logger.info(f"Notification de bonus envoyée à {referrer.username}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans send_bonus_notification: {e}")
        return False


@shared_task
def send_new_referral_notification(referral_id: str):
    """
    Notifier qu'un nouveau filleul s'est inscrit.
    """
    try:
        referral = Referral.objects.select_related(
            'referrer', 'referred'
        ).get(id=referral_id)
        
        subject = f"Nouveau filleul: {referral.referred.username} s'est inscrit!"
        
        context = {
            'referrer': referral.referrer,
            'referral': referral,
            'referred': referral.referred,
        }
        
        html_content = render_to_string(
            'referrals/emails/new_referral.html',
            context
        )
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[referral.referrer.email],
            fail_silently=False
        )
        
        logger.info(f"Notification nouveau filleul envoyée à {referral.referrer.username}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans send_new_referral_notification: {e}")
        return False


# ===== TÂCHES DE MAINTENANCE ET NETTOYAGE =====

@shared_task(bind=True, max_retries=2)
def cleanup_old_statistics(self):
    """
    Nettoyer les anciennes statistiques pour éviter l'encombrement.
    Conserver seulement les données des 2 dernières années.
    """
    try:
        cutoff_date = timezone.now().date() - timedelta(days=730)  # 2 ans
        
        # Supprimer les statistiques quotidiennes anciennes (garder 90 jours)
        daily_cutoff = timezone.now().date() - timedelta(days=90)
        deleted_daily = ReferralStatistics.objects.filter(
            period_type='daily',
            period_start__lt=daily_cutoff
        ).delete()
        
        # Supprimer les statistiques hebdomadaires anciennes (garder 1 an)
        weekly_cutoff = timezone.now().date() - timedelta(days=365)
        deleted_weekly = ReferralStatistics.objects.filter(
            period_type='weekly',
            period_start__lt=weekly_cutoff
        ).delete()
        
        # Garder toutes les statistiques mensuelles et annuelles
        
        logger.info(
            f"Nettoyage des statistiques: {deleted_daily[0]} quotidiennes, "
            f"{deleted_weekly[0]} hebdomadaires supprimées"
        )
        
        return {
            'daily_deleted': deleted_daily[0],
            'weekly_deleted': deleted_weekly[0]
        }
        
    except Exception as exc:
        logger.error(f"Erreur dans cleanup_old_statistics: {exc}")
        raise self.retry(exc=exc)


@shared_task
def archive_old_commissions():
    """
    Archiver les anciennes commissions pour optimiser les performances.
    """
    try:
        # Marquer les commissions de plus de 1 an comme archivées
        cutoff_date = timezone.now() - timedelta(days=365)
        
        archived_count = ReferralCommission.objects.filter(
            created_at__lt=cutoff_date,
            status='completed'
        ).update(
            # Ajouter un champ 'archived' au modèle si nécessaire
            # archived=True
        )
        
        logger.info(f"Commissions archivées: {archived_count}")
        return archived_count
        
    except Exception as e:
        logger.error(f"Erreur dans archive_old_commissions: {e}")
        return 0


# ===== TÂCHES DE REPORTING ET ANALYTICS =====

@shared_task
def generate_monthly_report():
    """
    Générer le rapport mensuel des parrainages.
    Exécuté le 1er de chaque mois.
    """
    try:
        # Calculer la période (mois précédent)
        today = timezone.now().date()
        if today.month == 1:
            last_month = today.replace(year=today.year-1, month=12, day=1)
        else:
            last_month = today.replace(month=today.month-1, day=1)
        
        # Statistiques globales du mois
        month_stats = ReferralCommission.objects.filter(
            created_at__date__gte=last_month,
            created_at__date__lt=today.replace(day=1),
            status='completed'
        ).aggregate(
            total_commissions=Sum('amount'),
            commission_count=Count('id'),
            unique_referrers=Count('referral__referrer', distinct=True)
        )
        
        # Top 10 des parrains
        top_referrers = User.objects.filter(
            referrals_made__commissions__created_at__date__gte=last_month,
            referrals_made__commissions__created_at__date__lt=today.replace(day=1),
            referrals_made__commissions__status='completed'
        ).annotate(
            month_commission=Sum('referrals_made__commissions__amount')
        ).order_by('-month_commission')[:10]
        
        # Créer le rapport
        report_data = {
            'period': f"{last_month.strftime('%B %Y')}",
            'total_commissions': float(month_stats['total_commissions'] or 0),
            'commission_count': month_stats['commission_count'] or 0,
            'unique_referrers': month_stats['unique_referrers'] or 0,
            'top_referrers': [
                {
                    'username': user.username,
                    'commission': float(user.month_commission)
                }
                for user in top_referrers
            ]
        }
        
        # Envoyer le rapport aux administrateurs
        send_monthly_report_email.delay(report_data)
        
        logger.info(f"Rapport mensuel généré pour {last_month.strftime('%B %Y')}")
        return report_data
        
    except Exception as e:
        logger.error(f"Erreur dans generate_monthly_report: {e}")
        return None


@shared_task
def send_monthly_report_email(report_data: Dict):
    """
    Envoyer le rapport mensuel par email aux administrateurs.
    """
    try:
        admin_emails = User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', flat=True)
        
        if not admin_emails:
            return False
        
        subject = f"Rapport mensuel de parrainage - {report_data['period']}"
        
        html_content = render_to_string(
            'referrals/emails/monthly_report.html',
            {'report': report_data}
        )
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(admin_emails),
            fail_silently=False
        )
        
        logger.info(f"Rapport mensuel envoyé à {len(admin_emails)} administrateurs")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans send_monthly_report_email: {e}")
        return False


# ===== TÂCHES DE DÉTECTION DE FRAUDE =====

@shared_task
def detect_suspicious_activity():
    """
    Détecter les activités suspectes de parrainage.
    """
    try:
        suspicious_activities = []
        
        # 1. Détection de auto-parrainage
        self_referrals = Referral.objects.filter(
            referrer=F('referred')
        )
        
        for referral in self_referrals:
            suspicious_activities.append({
                'type': 'self_referral',
                'user': referral.referrer.username,
                'referral_id': str(referral.id)
            })
            
            # Suspendre automatiquement
            referral.status = 'suspended'
            referral.save()
        
        # 2. Commission excessive en peu de temps
        yesterday = timezone.now() - timedelta(days=1)
        high_earners = User.objects.filter(
            referrals_made__commissions__created_at__gte=yesterday,
            referrals_made__commissions__status='completed'
        ).annotate(
            daily_commission=Sum('referrals_made__commissions__amount')
        ).filter(
            daily_commission__gte=Decimal('50000')  # Plus de 50k FCFA par jour
        )
        
        for user in high_earners:
            suspicious_activities.append({
                'type': 'high_daily_earnings',
                'user': user.username,
                'amount': float(user.daily_commission)
            })
        
        # 3. Trop de nouveaux parrainages en peu de temps
        recent_high_referrers = User.objects.filter(
            referrals_made__created_at__gte=yesterday
        ).annotate(
            recent_referrals=Count('referrals_made')
        ).filter(
            recent_referrals__gte=10  # Plus de 10 nouveaux filleuls par jour
        )
        
        for user in recent_high_referrers:
            suspicious_activities.append({
                'type': 'high_referral_rate',
                'user': user.username,
                'count': user.recent_referrals
            })
        
        # Notifier les administrateurs si activité suspecte
        if suspicious_activities:
            notify_admins_suspicious_activity.delay(suspicious_activities)
        
        logger.info(f"Détection terminée: {len(suspicious_activities)} activités suspectes")
        return suspicious_activities
        
    except Exception as e:
        logger.error(f"Erreur dans detect_suspicious_activity: {e}")
        return []


@shared_task
def notify_admins_suspicious_activity(activities: List[Dict]):
    """
    Notifier les administrateurs des activités suspectes détectées.
    """
    try:
        admin_emails = User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', flat=True)
        
        if not admin_emails:
            return False
        
        subject = f"Activités suspectes détectées - {len(activities)} cas"
        
        context = {
            'activities': activities,
            'total_count': len(activities),
            'timestamp': timezone.now()
        }
        
        html_content = render_to_string(
            'referrals/emails/suspicious_activity.html',
            context
        )
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(admin_emails),
            fail_silently=False
        )
        
        logger.info(f"Notification d'activité suspecte envoyée aux admins")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans notify_admins_suspicious_activity: {e}")
        return False


# ===== TÂCHES UTILITAIRES =====

@shared_task
def recalculate_user_statistics(user_id: str):
    """
    Recalculer toutes les statistiques d'un utilisateur spécifique.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Supprimer les anciennes statistiques
        ReferralStatistics.objects.filter(user=user).delete()
        
        # Recalculer par période
        today = timezone.now().date()
        
        # Les 30 derniers jours
        for i in range(30):
            date = today - timedelta(days=i)
            ReferralStatistics.calculate_statistics(
                user=user,
                period_type='daily',
                start_date=date,
                end_date=date
            )
        
        # Les 12 dernières semaines
        for i in range(12):
            week_start = today - timedelta(weeks=i, days=today.weekday())
            week_end = week_start + timedelta(days=6)
            ReferralStatistics.calculate_statistics(
                user=user,
                period_type='weekly',
                start_date=week_start,
                end_date=week_end
            )
        
        # Les 12 derniers mois
        for i in range(12):
            if today.month - i <= 0:
                month = 12 + (today.month - i)
                year = today.year - 1
            else:
                month = today.month - i
                year = today.year
            
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)
            
            ReferralStatistics.calculate_statistics(
                user=user,
                period_type='monthly',
                start_date=month_start,
                end_date=month_end
            )
        
        logger.info(f"Statistiques recalculées pour l'utilisateur {user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans recalculate_user_statistics: {e}")
        return False


# ===== TÂCHE DE SYNCHRONISATION =====

@shared_task
def sync_premium_status():
    """
    Synchroniser le statut premium entre les abonnements et les parrainages.
    """
    try:
        synchronized_users = 0
        
        # Récupérer tous les utilisateurs avec abonnements
        users_with_subscriptions = User.objects.filter(
            premium_subscriptions__isnull=False
        ).distinct()
        
        for user in users_with_subscriptions:
            # Vérifier le statut premium actuel
            active_subscription = user.premium_subscriptions.filter(
                status='active'
            ).first()
            
            is_premium = active_subscription.is_active() if active_subscription else False
            
            # Mettre à jour les parrainages
            updated_count = Referral.objects.filter(
                referrer=user
            ).update(
                is_premium_referrer=is_premium
            )
            
            if updated_count > 0:
                synchronized_users += 1
        
        logger.info(f"Statut premium synchronisé pour {synchronized_users} utilisateurs")
        return synchronized_users
        
    except Exception as e:
        logger.error(f"Erreur dans sync_premium_status: {e}")
        return 0
