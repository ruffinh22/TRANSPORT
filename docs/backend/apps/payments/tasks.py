"""
Celery tasks pour les paiements et retraits
Gestion des vérifications de statut différées pour les payouts
"""
from celery import shared_task
from django.utils import timezone
import logging

from .feexpay_payout import FeexPayPayout
from .models import FeexPayWithdrawal

logger = logging.getLogger(__name__)


@shared_task(name='payments.check_pending_payout_status')
def check_pending_payout_status(withdrawal_id: int):
    """
    Vérifier le statut d'un payout en attente (PENDING)
    
    Selon la documentation FeexPay:
    - Attendre 5 minutes minimum avant de vérifier le statut
    - Utiliser GET /api/payouts/status/public/{reference}
    
    Args:
        withdrawal_id: ID du retrait à vérifier
    """
    try:
        withdrawal = FeexPayWithdrawal.objects.get(id=withdrawal_id)
        
        if withdrawal.status != 'pending':
            logger.info(f"⏭️ Retrait {withdrawal_id} n'est plus pending ({withdrawal.status})")
            return
        
        if not withdrawal.feexpay_transfer_id:
            logger.error(f"❌ Retrait {withdrawal_id} n'a pas de référence FeexPay")
            return
        
        logger.info(f"🔍 Vérification status payout - Withdrawal ID: {withdrawal_id}, Ref: {withdrawal.feexpay_transfer_id}")
        
        # Appeler l'API FeexPay pour vérifier le statut
        feexpay = FeexPayPayout()
        status_result = feexpay.check_transfer_status(withdrawal.feexpay_transfer_id)
        
        if not status_result['success']:
            logger.error(f"❌ Erreur vérification status: {status_result.get('message')}")
            return
        
        # Récupérer le nouveau statut
        payout_status = status_result.get('status', '').lower()
        logger.info(f"📊 Nouveau status: {payout_status} pour withdrawal {withdrawal_id}")
        
        if payout_status == 'successful':
            # Payout réussi
            withdrawal.mark_as_completed(
                transfer_id=withdrawal.feexpay_transfer_id,
                response_data=status_result.get('data', {})
            )
            logger.info(f"✅ Payout {withdrawal.id} marqué comme SUCCESSFUL")
            
        elif payout_status == 'failed':
            # Payout échoué - restaurer le solde utilisateur
            withdrawal.mark_as_failed(
                error_message='Payout échoué après vérification',
                response_data=status_result.get('data', {})
            )
            
            # Restaurer le solde
            user = withdrawal.user
            total_amount = withdrawal.amount + withdrawal.fee
            user.balance_fcfa += total_amount
            user.save()
            
            logger.error(f"❌ Payout {withdrawal.id} marqué comme FAILED - Solde restauré")
            
        elif payout_status == 'pending':
            # Toujours en attente - reprogrammer une vérification dans 5 min
            logger.info(f"⏳ Payout {withdrawal.id} toujours PENDING - Re-vérification dans 5min")
            check_pending_payout_status.apply_async(
                args=[withdrawal_id],
                countdown=300  # 5 minutes
            )
        
    except FeexPayWithdrawal.DoesNotExist:
        logger.error(f"❌ Withdrawal {withdrawal_id} introuvable")
    except Exception as e:
        logger.error(f"❌ Erreur check_pending_payout_status: {e}")


@shared_task(name='payments.check_all_pending_payouts')
def check_all_pending_payouts():
    """
    Vérifier tous les payouts en attente depuis plus de 5 minutes
    
    À exécuter périodiquement (ex: toutes les 10 minutes via Celery Beat)
    """
    try:
        from datetime import timedelta
        
        # Chercher les retraits pending depuis plus de 5 minutes
        five_min_ago = timezone.now() - timedelta(minutes=5)
        
        pending_withdrawals = FeexPayWithdrawal.objects.filter(
            status='pending',
            created_at__lte=five_min_ago,
            feexpay_transfer_id__isnull=False
        )
        
        count = pending_withdrawals.count()
        logger.info(f"🔍 Vérification de {count} payouts pending...")
        
        for withdrawal in pending_withdrawals:
            # Lancer la vérification pour chaque retrait
            check_pending_payout_status.delay(withdrawal.id)
        
        logger.info(f"✅ {count} vérifications de payouts lancées")
        
    except Exception as e:
        logger.error(f"❌ Erreur check_all_pending_payouts: {e}")
