# apps/referrals/signals.py
# ===========================

import logging
from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Referral, ReferralCommission, PremiumSubscription, ReferralBonus, ReferralCode
from .tasks import (
    process_single_commission, send_new_referral_notification,
    send_commission_notification, create_milestone_bonuses
)

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_referral_code(sender, instance, created, **kwargs):
    """
    Créer automatiquement un code de parrainage lors de l'inscription d'un nouvel utilisateur.
    """
    if created:
        try:
            # Vérifier que l'utilisateur n'a pas déjà de code
            if not ReferralCode.objects.filter(user=instance).exists():
                code = ReferralCode.objects.create(user=instance)
                logger.info(f"Code de parrainage créé pour {instance.username}: {code.code}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du code de parrainage: {e}")


# ===== SIGNAUX POUR LES PARRAINAGES =====

@receiver(post_save, sender=Referral)
def handle_new_referral(sender, instance, created, **kwargs):
    """
    Traitement automatique après création d'un nouveau parrainage.
    """
    if created:
        logger.info(f"Nouveau parrainage créé: {instance.referrer.username} → {instance.referred.username}")
        
        # Envoyer notification au parrain
        send_new_referral_notification.delay(str(instance.id))
        
        # Créer bonus d'inscription si éligible
        create_signup_bonus.delay(str(instance.id))
        
        # Vérifier les paliers de parrainage
        create_milestone_bonuses.delay()


@receiver(pre_save, sender=Referral)
def handle_referral_status_change(sender, instance, **kwargs):
    """
    Gérer les changements de statut des parrainages.
    """
    if instance.pk:  # Modification d'un objet existant
        try:
            old_instance = Referral.objects.get(pk=instance.pk)
            
            # Si le statut change vers 'suspended' ou 'inactive'
            if (old_instance.status == 'active' and 
                instance.status in ['suspended', 'inactive']):
                
                # Annuler les commissions en attente
                pending_commissions = ReferralCommission.objects.filter(
                    referral=instance,
                    status='pending'
                )
                
                cancelled_count = pending_commissions.update(
                    status='cancelled',
                    failure_reason='Parrainage suspendu/inactif'
                )
                
                logger.info(
                    f"Parrainage {instance.id} désactivé: "
                    f"{cancelled_count} commissions annulées"
                )
                
        except Referral.DoesNotExist:
            pass  # Nouvelle création


# ===== SIGNAUX POUR LES JEUX =====

@receiver(post_save, sender='games.Game')
def handle_game_completion(sender, instance, created, **kwargs):
    """
    Traitement automatique après completion d'une partie.
    Créer les commissions de parrainage si applicable.
    """
    if not created and instance.status == 'completed':
        # Vérifier si le joueur a un parrain
        try:
            referral = Referral.objects.get(
                referred=instance.player,
                status='active'
            )
            
            # Lancer le calcul de commission en arrière-plan
            process_single_commission.delay(
                commission_id=None,  # Sera créé dans la tâche
                game_id=str(instance.id),
                referral_id=str(referral.id)
            )
            
            logger.info(f"Commission planifiée pour le jeu {instance.id}")
            
        except Referral.DoesNotExist:
            # Le joueur n'a pas de parrain
            pass
        except Exception as e:
            logger.error(f"Erreur lors de la planification de commission: {e}")


# ===== SIGNAUX POUR LES COMMISSIONS =====

@receiver(post_save, sender=ReferralCommission)
def handle_commission_status_change(sender, instance, created, **kwargs):
    """
    Gérer les changements de statut des commissions.
    """
    if not created:  # Modification d'une commission existante
        try:
            old_instance = ReferralCommission.objects.get(pk=instance.pk)
            
            # Si la commission passe de 'pending' à 'completed'
            if (old_instance.status == 'pending' and 
                instance.status == 'completed'):
                
                logger.info(f"Commission {instance.id} complétée: {instance.amount} {instance.currency}")
                
                # Envoyer notification au parrain
                send_commission_notification.delay(str(instance.id))
                
                # Vérifier les bonus de premier dépôt
                check_first_deposit_bonus.delay(str(instance.referral.id))
                
            # Si la commission échoue
            elif (old_instance.status == 'pending' and 
                  instance.status == 'failed'):
                
                logger.warning(f"Commission {instance.id} échouée: {instance.failure_reason}")
                
        except ReferralCommission.DoesNotExist:
            pass


# ===== SIGNAUX POUR LES ABONNEMENTS PREMIUM =====

@receiver(post_save, sender=PremiumSubscription)
def handle_premium_subscription(sender, instance, created, **kwargs):
    """
    Traitement automatique des abonnements premium.
    """
    if created and instance.status == 'active':
        logger.info(f"Nouvel abonnement premium: {instance.user.username} - {instance.plan_type}")
        
        # Mettre à jour immédiatement le statut des parrainages
        instance.update_referral_premium_status()
        
        # Créer un bonus de bienvenue premium
        create_premium_welcome_bonus.delay(str(instance.id))


@receiver(pre_save, sender=PremiumSubscription)
def handle_premium_status_change(sender, instance, **kwargs):
    """
    Gérer les changements de statut premium.
    """
    if instance.pk:
        try:
            old_instance = PremiumSubscription.objects.get(pk=instance.pk)
            
            # Si l'abonnement expire ou est annulé
            if (old_instance.status == 'active' and 
                instance.status in ['expired', 'cancelled']):
                
                logger.info(f"Abonnement premium terminé: {instance.user.username}")
                
                # Mettre à jour le statut des parrainages
                Referral.objects.filter(
                    referrer=instance.user
                ).update(is_premium_referrer=False)
                
        except PremiumSubscription.DoesNotExist:
            pass


# ===== SIGNAUX POUR LES UTILISATEURS =====

@receiver(post_save, sender=User)
def handle_user_creation(sender, instance, created, **kwargs):
    """
    Traitement après création d'un nouvel utilisateur.
    """
    if created:
        # Vérifier si l'utilisateur s'est inscrit avec un code de parrainage
        # Cette logique sera gérée par la vue d'inscription
        pass


@receiver(post_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """
    Nettoyage après suppression d'un utilisateur.
    """
    # Les contraintes CASCADE s'occupent de la suppression des relations
    # Mais on peut loguer l'événement
    logger.info(f"Utilisateur supprimé: {instance.username}")


# ===== TÂCHES DE CRÉATION DE BONUS =====

@receiver(post_save, sender=Referral)
def create_signup_bonus_handler(sender, instance, created, **kwargs):
    """Handler pour créer le bonus d'inscription."""
    if created:
        create_signup_bonus.delay(str(instance.id))


from celery import shared_task

@shared_task
def create_signup_bonus(referral_id: str):
    """
    Créer un bonus d'inscription pour un nouveau parrainage.
    """
    try:
        referral = Referral.objects.get(id=referral_id)
        
        # Vérifier qu'il n'existe pas déjà
        existing_bonus = ReferralBonus.objects.filter(
            referral=referral,
            bonus_type='signup'
        ).first()
        
        if not existing_bonus:
            bonus = ReferralBonus.objects.create(
                referral=referral,
                bonus_type='signup',
                amount=Decimal('500.00'),  # 500 FCFA
                currency='FCFA',
                description='Bonus d\'inscription pour nouveau filleul',
                status='approved',
                expires_at=timezone.now() + timezone.timedelta(days=30)
            )
            
            logger.info(f"Bonus d'inscription créé: {bonus.id}")
            return str(bonus.id)
        
    except Exception as e:
        logger.error(f"Erreur création bonus inscription: {e}")
        return None


@shared_task
def check_first_deposit_bonus(referral_id: str):
    """
    Vérifier et créer le bonus de premier dépôt si applicable.
    """
    try:
        referral = Referral.objects.get(id=referral_id)
        
        # Vérifier si c'est la première commission de ce filleul
        commission_count = ReferralCommission.objects.filter(
            referral=referral,
            status='completed'
        ).count()
        
        if commission_count == 1:  # Première commission
            # Créer le bonus de premier dépôt
            existing_bonus = ReferralBonus.objects.filter(
                referral=referral,
                bonus_type='first_deposit'
            ).first()
            
            if not existing_bonus:
                bonus = ReferralBonus.objects.create(
                    referral=referral,
                    bonus_type='first_deposit',
                    amount=Decimal('2000.00'),  # 2000 FCFA
                    currency='FCFA',
                    description='Bonus de première activité du filleul',
                    status='approved',
                    expires_at=timezone.now() + timezone.timedelta(days=60)
                )
                
                logger.info(f"Bonus premier dépôt créé: {bonus.id}")
                return str(bonus.id)
        
    except Exception as e:
        logger.error(f"Erreur création bonus premier dépôt: {e}")
        return None


@shared_task
def create_premium_welcome_bonus(subscription_id: str):
    """
    Créer un bonus de bienvenue pour nouvel abonnement premium.
    """
    try:
        subscription = PremiumSubscription.objects.get(id=subscription_id)
        
        # Trouver un parrainage actif pour associer le bonus
        referral = Referral.objects.filter(
            referrer=subscription.user,
            status='active'
        ).first()
        
        if referral:
            bonus = ReferralBonus.objects.create(
                referral=referral,
                bonus_type='special',
                amount=Decimal('5000.00'),  # 5000 FCFA
                currency='FCFA',
                description='Bonus de bienvenue premium',
                status='approved',
                expires_at=timezone.now() + timezone.timedelta(days=90)
            )
            
            logger.info(f"Bonus premium bienvenue créé: {bonus.id}")
            return str(bonus.id)
        
    except Exception as e:
        logger.error(f"Erreur création bonus premium: {e}")
        return None


# ===== SIGNAUX POUR AUDIT ET LOGGING =====

@receiver(post_save, sender=ReferralCommission)
def log_commission_audit(sender, instance, created, **kwargs):
    """
    Logger les événements de commission pour audit.
    """
    if created:
        logger.info(
            f"AUDIT: Commission créée - "
            f"ID:{instance.id}, Parrain:{instance.referral.referrer.username}, "
            f"Filleul:{instance.referral.referred.username}, "
            f"Montant:{instance.amount} {instance.currency}, "
            f"Jeu:{instance.game.id}"
        )
    else:
        logger.info(
            f"AUDIT: Commission modifiée - "
            f"ID:{instance.id}, Nouveau statut:{instance.status}"
        )


@receiver(post_save, sender=Referral)
def log_referral_audit(sender, instance, created, **kwargs):
    """
    Logger les événements de parrainage pour audit.
    """
    if created:
        logger.info(
            f"AUDIT: Parrainage créé - "
            f"ID:{instance.id}, Parrain:{instance.referrer.username}, "
            f"Filleul:{instance.referred.username}, "
            f"Programme:{instance.program.name}"
        )


# ===== SIGNAUX POUR LA SÉCURITÉ =====

@receiver(pre_save, sender=Referral)
def validate_referral_security(sender, instance, **kwargs):
    """
    Validations de sécurité avant sauvegarde d'un parrainage.
    """
    # Empêcher l'auto-parrainage
    if instance.referrer == instance.referred:
        raise ValueError("L'auto-parrainage n'est pas autorisé")
    
    # Vérifier qu'un utilisateur ne peut avoir qu'un seul parrain
    if not instance.pk:  # Nouvelle création
        existing_referral = Referral.objects.filter(
            referred=instance.referred
        ).first()
        
        if existing_referral:
            raise ValueError("Cet utilisateur a déjà un parrain")


@receiver(pre_save, sender=ReferralCommission)
def validate_commission_security(sender, instance, **kwargs):
    """
    Validations de sécurité pour les commissions.
    """
    # Vérifier que le montant est positif
    if instance.amount <= 0:
        raise ValueError("Le montant de la commission doit être positif")
    
    # Vérifier les limites quotidiennes
    if not instance.pk:  # Nouvelle création
        from datetime import date
        today = date.today()
        
        daily_total = ReferralCommission.objects.filter(
            referral__referrer=instance.referral.referrer,
            created_at__date=today,
            status='completed'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Limite quotidienne de sécurité (100k FCFA)
        if daily_total + instance.amount > Decimal('100000.00'):
            logger.warning(
                f"Limite quotidienne dépassée pour {instance.referral.referrer.username}: "
                f"{daily_total + instance.amount} FCFA"
            )


# ===== SIGNAUX POUR LES NOTIFICATIONS TEMPS RÉEL =====

@receiver(post_save, sender=ReferralCommission)
def send_realtime_notification(sender, instance, created, **kwargs):
    """
    Envoyer des notifications temps réel via WebSocket.
    """
    if instance.status == 'completed':
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            
            # Notification au parrain
            async_to_sync(channel_layer.group_send)(
                f"user_{instance.referral.referrer.id}",
                {
                    "type": "commission_earned",
                    "message": {
                        "commission_id": str(instance.id),
                        "amount": float(instance.amount),
                        "currency": instance.currency,
                        "referred_user": instance.referral.referred.username
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur notification temps réel: {e}")


# ===== NETTOYAGE DES SIGNAUX =====

def disconnect_referral_signals():
    """
    Déconnecter tous les signaux (utile pour les tests).
    """
    post_save.disconnect(handle_new_referral, sender=Referral)
    post_save.disconnect(handle_commission_status_change, sender=ReferralCommission)
    post_save.disconnect(handle_premium_subscription, sender=PremiumSubscription)
    # ... autres déconnexions


def reconnect_referral_signals():
    """
    Reconnecter tous les signaux.
    """
    post_save.connect(handle_new_referral, sender=Referral)
    post_save.connect(handle_commission_status_change, sender=ReferralCommission)
    post_save.connect(handle_premium_subscription, sender=PremiumSubscription)
    # ... autres reconnexions
